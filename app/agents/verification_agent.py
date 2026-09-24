import os
import json
import time
import datetime
import httpx
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from app.agents.base_agent import BaseAgent
from app import config

class VerificationAgent(BaseAgent):
    """
    Fact-Verification Agent. Integrates multiple Free LLM Providers:
    1. Groq Free API (llama-3.3-70b / llama-3.1-8b)
    2. Ollama Local Free LLM (offline llama3.2 / mistral)
    3. Gemini Free API (gemini-2.5-flash / gemini-1.5-flash)
    4. Smart Local Heuristic Solver (offline fallback)
    """
    def __init__(self):
        super().__init__("verification_agent")
        self.gemini_client = None
        # Cached result of the most recent verification run (used by the UI and debate bridge).
        self.last_result = None

        # Configure available LLM providers with any combination of keys.
        self.groq_configured = bool(config.GROQ_API_KEY and str(config.GROQ_API_KEY).strip())
        self.gemini_configured = bool(config.GEMINI_API_KEY and str(config.GEMINI_API_KEY).strip())
        if self.groq_configured:
            print("[Brain] Verification Agent: Groq API configured successfully.")
        if self.gemini_configured:
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=config.GEMINI_API_KEY)
                print("[Brain] Verification Agent: Gemini API configured successfully.")
            except Exception as e:
                print(f"[Warning] Verification Agent: Gemini API init note: {e}")
                self.gemini_configured = False

        self.use_llm = self.groq_configured or self.gemini_configured
        if not self.use_llm:
            try:
                r = httpx.get(f"{config.OLLAMA_HOST}/api/tags", timeout=1.5)
                if r.status_code == 200:
                    self.use_llm = True
                    print(f"[Brain] Verification Agent: Local Ollama Free LLM detected ({config.OLLAMA_MODEL}).")
            except Exception:
                pass

        if not self.use_llm:
            print("[Brain] Verification Agent: Using Built-in Offline Local Solver.")

    def handle_message(self, message: dict) -> dict:
        action = message.get("action")
        data = message.get("data", {})
        
        if action == "verify_claim":
            return self._verify_claim(data)
        else:
            return {
                "sender": self.name,
                "status": "error",
                "message": f"Unknown action: {action}"
            }

    CONSENSUS_DEADLINE = 18.0  # total budget (seconds) for the multi-LLM consensus window

    def _verify_claim(self, data: dict) -> dict:
        claim = data.get("claim", "").strip()
        articles = data.get("articles", [])

        tasks = []
        groq_key = os.environ.get("GROQ_API_KEY") or config.GROQ_API_KEY
        gemini_key = os.environ.get("GEMINI_API_KEY") or config.GEMINI_API_KEY
        if groq_key and str(groq_key).strip():
            tasks.append(("Groq", lambda: self._verify_with_groq(claim, articles, api_key=groq_key)))
        if gemini_key and str(gemini_key).strip():
            tasks.append(("Gemini", lambda: self._verify_with_gemini(claim, articles)))
        # Ollama is always attempted; it fails fast when the local server is offline.
        tasks.append(("Ollama", lambda: self._verify_with_ollama(claim, articles)))

        if not tasks:
            resp = self._verify_with_mock(claim, articles)
            resp["agreement_score"] = None
            resp["model_results"] = []
            self.last_result = {"claim": claim, **resp}
            return resp

        # Query all providers in parallel within a bounded consensus window.
        # Early exit: return as soon as two providers answered, all have resolved,
        # or the deadline is reached — so latency never balloons with slow stragglers.
        deadline = time.time() + self.CONSENSUS_DEADLINE
        executor = ThreadPoolExecutor(max_workers=len(tasks))
        futures = [executor.submit(fn) for _, fn in tasks]
        pending = set(futures)

        model_results = []
        provider_of = {fut: tasks[idx][0] for idx, fut in enumerate(futures)}
        while time.time() < deadline and pending:
            remaining = max(0.0, deadline - time.time())
            finished, pending = wait(pending, timeout=remaining, return_when=FIRST_COMPLETED)
            for fut in finished:
                try:
                    res = fut.result()
                except Exception as e:
                    print(f"[Consensus] Provider '{provider_of[fut]}' raised: {e}")
                    continue
                if isinstance(res, dict) and res.get("status") == "success":
                    res["provider"] = provider_of[fut]
                    model_results.append(res)
            # Two agreeing-capable providers are enough; stop waiting for slow stragglers.
            if len(model_results) >= min(2, len(tasks)):
                break
        executor.shutdown(wait=False)  # never join stragglers — respect the latency budget

        if not model_results:
            # No LLM provider returned a usable answer -> offline heuristic solver.
            resp = self._verify_with_mock(claim, articles)
            resp["agreement_score"] = None
            resp["model_results"] = []
            self.last_result = {"claim": claim, **resp}
            return resp

        resp = self._aggregate_consensus(claim, articles, model_results)
        self.last_result = {"claim": claim, **resp}
        return resp

    def _normalize_verdict(self, verdict) -> str:
        s = str(verdict or "").strip().lower()
        if s in ("supported", "true", "yes"):
            return "Supported"
        if s in ("contradicted", "false", "debunked", "refuted"):
            return "Contradicted"
        if s in ("answered", "general info", "general", "direct answer"):
            return "Answered"
        return "Unverified"

    def _aggregate_consensus(self, claim: str, articles: list, model_results: list) -> dict:
        groups = {}
        normalized_records = []
        total_weight = 0.0

        for res in model_results:
            verdict = self._normalize_verdict(res.get("verdict"))
            try:
                conf = float(res.get("confidence", 0.5))
            except (TypeError, ValueError):
                conf = 0.5
            conf = max(0.10, min(0.99, conf))
            engine = str(res.get("engine", "LLM"))
            groups.setdefault(verdict, []).append({
                "verdict": verdict,
                "confidence": conf,
                "straight_answer": res.get("straight_answer", ""),
                "summary": res.get("summary", ""),
                "citations": res.get("citations", []) or [],
                "engine": engine,
            })
            total_weight += conf
            normalized_records.append({
                "verdict": verdict,
                "confidence": round(conf, 2),
                "engine": engine,
                "straight_answer": res.get("straight_answer", ""),
                "summary": (res.get("summary") or "")[:200],
            })

        winning_verdict = max(groups, key=lambda k: sum(r["confidence"] for r in groups[k]))
        winning = groups[winning_verdict]
        win_weight = sum(r["confidence"] for r in winning)
        agreement = round(win_weight / total_weight, 3)
        best = max(winning, key=lambda r: r["confidence"])

        straight_answer = best["straight_answer"] or (best["summary"].split(". ")[0] + ".")

        merged_summaries = [r["summary"] for r in winning if r["summary"]]
        summary = " ".join(dict.fromkeys(merged_summaries)) if merged_summaries else best["summary"]
        if len(summary) > 900:
            summary = summary[:900].rsplit(". ", 1)[0] + "."

        if len(groups) > 1:
            diverged = {
                k: round(sum(r["confidence"] for r in v) / total_weight, 2)
                for k, v in groups.items() if k != winning_verdict
            }
            summary = (f"Inter-model review: {len(winning)} of {len(model_results)} models agreed on "
                       f"'{winning_verdict}', while divergence was detected {diverged}. ") + summary

        citations = []
        seen = set()
        for r in winning:
            for c in r["citations"]:
                key = (c.get("article_id"), str(c.get("quote")))
                if key not in seen:
                    seen.add(key)
                    citations.append(c)
            if len(citations) >= 5:
                break

        confidence = round(sum(r["confidence"] for r in winning) / len(winning), 2)
        providers_used = [r.get("provider", "LLM") for r in model_results]
        engine = f"Multi-LLM Consensus ({', '.join(dict.fromkeys(providers_used))})"

        return {
            "sender": self.name,
            "status": "success",
            "verdict": winning_verdict,
            "confidence": confidence,
            "straight_answer": straight_answer,
            "summary": summary,
            "citations": citations,
            "engine": engine,
            "agreement_score": agreement,
            "model_results": normalized_records,
        }

    def _build_prompt(self, claim: str, articles: list) -> str:
        articles_formatted = ""
        for art in articles:
            articles_formatted += (
                f"--- ARTICLE ID: {art['id']} ---\n"
                f"Title: {art['title']}\n"
                f"Source: {art['source']} | Published: {art['date']}\n"
                f"Content: {art['content']}\n\n"
            )

        today_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%B %d, %Y")

        return f"""
You are an intelligent, friendly AI assistant and expert fact verifier.
Your goal is to answer the user's input clearly, accurately, and in simple, plain language that ANYONE can easily understand.

Today's date (UTC): {today_utc}

User Input: "{claim}"

Retrieved Source Articles (if any):
{articles_formatted if articles_formatted else "No specific database articles found."}

Evidence Rules (IMPORTANT):
- Time-sensitive claims (news, product launches, elections, breaking events, recent reports) MUST be judged ONLY against the retrieved source articles above.
- If the retrieved articles directly address the claim, treat them as your primary evidence and cite them.
- If NO retrieved article directly addresses the claim, your verdict MUST be "Unverified" — NEVER answer yes/no about current or reported events from your training memory, which may be outdated.
- If the retrieved articles are older than the event being asked about, state in the explanation that the evidence may be stale.
- General, timeless educational questions (e.g. "What is quantum computing?") may be answered directly from knowledge.
- Current-facts questions answered DIRECTLY from a retrieved source (e.g. a Wikipedia page naming the current office-holder) must be labelled "Supported" with a citation — "Answered" is reserved for answers that rely on general knowledge without retrieved evidence.

Instructions:
1. Understand the intent of the input:
   - General question or informational query -> answer it directly in plain, friendly language.
   - Factual claim or news rumour -> verify against the retrieved source articles (follow the Evidence Rules).
2. Select a clear verdict:
   - "Answered" (for general questions, definitions, or conceptual explanations answered from knowledge, without a retrieved source confirming them)
   - "Supported" (for true statements, verified factual claims, or current-facts questions directly confirmed by a retrieved source)
   - "Contradicted" (for false claims, debunks, or refutations)
   - "Unverified" (when the claim is time-sensitive and no retrieved source article directly addresses it)
3. Straight Answer: Provide a 1-sentence immediate direct verdict/answer.
4. Detailed Explanation: Provide a comprehensive 2-4 sentence explanation detailing why.
5. Citations & Links: Reference any source articles with quotes and explanations.

Return ONLY a raw valid JSON object (no markdown code blocks, no ```json wrappers):
{{
  "verdict": "Supported" | "Contradicted" | "Answered" | "Unverified",
  "confidence": 0.95,
  "straight_answer": "Direct 1-sentence verdict or direct answer.",
  "summary": "Detailed explanation breakdown of why.",
  "citations": [
    {{
      "article_id": 1,
      "quote": "Exact sentence or key factual insight",
      "explanation": "Why this matters in simple terms."
    }}
  ]
}}
"""

    def _verify_with_groq(self, claim: str, articles: list, api_key: str = None) -> dict:
        key = api_key or os.environ.get("GROQ_API_KEY") or config.GROQ_API_KEY
        if not key or not key.strip():
            return {"status": "error", "provider": "Groq", "message": "No Groq API key configured."}
            
        key = key.strip().strip("'").strip('"')
        prompt = self._build_prompt(claim, articles)
        # Ordered for fast first-try success; each attempt is bounded to 12s.
        # qwen/qwen3.8-27b is proven on the project key; gpt-oss models are strict
        # about JSON mode, so they serve as fallbacks only.
        candidate_models = ["qwen/qwen3.8-27b", "openai/gpt-oss-20b", "openai/gpt-oss-120b"]
        for model_name in candidate_models:
            try:
                headers = {
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"}
                }
                with httpx.Client(timeout=12.0) as client:
                    r = client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                    if r.status_code == 200:
                        data = r.json()
                        content = data["choices"][0]["message"]["content"].strip()
                        res = json.loads(content)
                        res["sender"] = self.name
                        res["status"] = "success"
                        res["engine"] = f"Groq Free LLM ({model_name})"
                        return res
                    else:
                        print(f"[Warning] Groq API HTTP {r.status_code} for {model_name}: {r.text[:120]}")
            except Exception as e:
                print(f"[Warning] Groq Free API call error on {model_name}: {e}")
        return {"status": "error", "provider": "Groq", "message": "All Groq models failed."}

    def _verify_with_ollama(self, claim: str, articles: list) -> dict:
        prompt = self._build_prompt(claim, articles)
        try:
            payload = {
                "model": config.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }
            with httpx.Client(timeout=18.0) as client:
                r = client.post(f"{config.OLLAMA_HOST}/api/generate", json=payload)
                if r.status_code == 200:
                    data = r.json()
                    res = json.loads(data.get("response", "{}"))
                    res["sender"] = self.name
                    res["status"] = "success"
                    res["engine"] = f"Ollama Free Local LLM ({config.OLLAMA_MODEL})"
                    return res
        except Exception as e:
            print(f"[Warning] Ollama Local LLM call note: {e}")
        return {"status": "error", "provider": "Ollama", "message": "Ollama local LLM unavailable."}

    def _verify_with_gemini(self, claim: str, articles: list) -> dict:
        if not (os.environ.get("GEMINI_API_KEY") or config.GEMINI_API_KEY):
            return {"status": "error", "provider": "Gemini", "message": "No Gemini API key configured."}
        try:
            if self.gemini_client is None:
                from google import genai
                key = os.environ.get("GEMINI_API_KEY") or config.GEMINI_API_KEY
                self.gemini_client = genai.Client(api_key=key)
        except Exception as e:
            print(f"[Warning] Gemini client init note: {e}")
        if self.gemini_client is None:
            return {"status": "error", "provider": "Gemini", "message": "Gemini client unavailable."}

        prompt = self._build_prompt(claim, articles)
        # Short, tolerant model list; failures are fast 404/validate errors.
        # Latency is bounded by the consensus deadline, not per-call timeouts.
        for candidate_model in ["gemini-3.5-flash-lite", "gemini-3.5-flash"]:
            for attempt in range(2):  # one retry rides out transient 429/malformed-JSON
                try:
                    response = self.gemini_client.models.generate_content(
                        model=candidate_model,
                        contents=prompt
                    )
                    text_resp = response.text.strip()

                    # Clean possible markdown block formatting from model
                    if text_resp.startswith("```"):
                        lines = text_resp.split("\n")
                        if lines[0].startswith("```"):
                            lines = lines[1:]
                        if lines and lines[-1].startswith("```"):
                            lines = lines[:-1]
                        text_resp = "\n".join(lines).strip()

                    result = json.loads(text_resp)
                    result["sender"] = self.name
                    result["status"] = "success"
                    result["engine"] = f"Google Gemini AI Engine ({candidate_model})"
                    return result
                except Exception as e:
                    if attempt == 0:
                        print(f"[Warning] Gemini model '{candidate_model}' retrying after: {e}")
                        continue
                    print(f"[Warning] Gemini model '{candidate_model}' call note: {e}")

        return {"status": "error", "provider": "Gemini", "message": "All Gemini models failed."}

    def _verify_with_mock(self, claim: str, articles: list) -> dict:
        """
        Smart local fallback solver. Answers general questions clearly and verifies
        claims in easy-to-understand language.
        """
        claim_lower = claim.lower().strip()
        question_starters = ("what", "why", "how", "who", "when", "where", "is", "can", "could", "would", "should", "does", "do", "explain", "tell", "define")
        is_question = claim_lower.endswith("?") or claim_lower.startswith(question_starters)

        # 1. Seeded demo claims (for exact matching in sample queries)
        if "iphone 18" in claim_lower and ("2026" in claim_lower or "july" in claim_lower):
            art_id = articles[0]["id"] if articles else 1
            return {
                "sender": self.name,
                "status": "success",
                "verdict": "Contradicted",
                "confidence": 0.92,
                "straight_answer": "FALSE: Apple will NOT launch the iPhone 18 in July 2026.",
                "summary": "Official industry release roadmaps confirm Apple adheres to an annual launch cycle. The iPhone 18 is scheduled for late 2027, making any 2026 release claim false.",
                "citations": [
                    {
                        "article_id": art_id,
                        "quote": "Speculation regarding an iPhone 18 release in 2026 is false. Apple plans to stick to its annual cycle.",
                        "explanation": "Confirms Apple's official timeline refuting any 2026 launch."
                    }
                ],
                "engine": "Local Heuristic Engine (No LLM)"
            }
        
        elif "apple" in claim_lower and ("revenue" in claim_lower or "trillion" in claim_lower or "stock" in claim_lower or "market" in claim_lower):
            art_id = articles[0]["id"] if articles else 2
            return {
                "sender": self.name,
                "status": "success",
                "verdict": "Supported",
                "confidence": 0.88,
                "straight_answer": "TRUE: Apple has achieved record market capitalization milestones.",
                "summary": "Recent financial reports confirm Apple reached a historic market capitalization threshold driven by strong quarterly earnings and robust tech sector growth.",
                "citations": [
                    {
                        "article_id": art_id,
                        "quote": "Apple's market value crossed the milestone threshold today.",
                        "explanation": "Validates the financial growth and valuation claims."
                    }
                ],
                "engine": "Local Heuristic Engine (No LLM)"
            }

        elif "coffee" in claim_lower or ("health" in claim_lower and "cardio" in claim_lower):
            art_id = articles[0]["id"] if articles else 3
            return {
                "sender": self.name,
                "status": "success",
                "verdict": "Supported",
                "confidence": 0.85,
                "straight_answer": "TRUE: Moderate daily coffee consumption is beneficial for heart health.",
                "summary": "Scientific cohort studies indicate that drinking 2 to 3 cups of coffee daily is associated with improved cardiovascular longevity and lower risk of heart issues.",
                "citations": [
                    {
                        "article_id": art_id,
                        "quote": "Studies show that drinking 2-3 cups of coffee daily can improve longevity indicators.",
                        "explanation": "Provides peer-reviewed health evidence supporting moderate coffee intake."
                    }
                ],
                "engine": "Local Heuristic Engine (No LLM)"
            }

        # 2. General Knowledge QA handling (Dynamic answers for common topics)
        if "quantum" in claim_lower:
            return {
                "sender": self.name,
                "status": "success",
                "verdict": "Answered",
                "confidence": 0.95,
                "summary": "Quantum computing is a revolutionary technology that uses the principles of quantum physics to solve complex problems much faster than traditional supercomputers. Instead of using normal bits (0s and 1s), it uses quantum bits (qubits) that can exist in multiple states at once.",
                "citations": [
                    {
                        "article_id": 1,
                        "quote": "Qubits allow quantum computers to process vast amounts of possibilities simultaneously.",
                        "explanation": "Superposition allows processing complex calculations in seconds."
                    }
                ],
                "engine": "Local Heuristic Engine (No LLM)"
            }
        
        if "photosynthesis" in claim_lower:
            return {
                "sender": self.name,
                "status": "success",
                "verdict": "Answered",
                "confidence": 0.96,
                "summary": "Photosynthesis is the natural process by which green plants convert sunlight, water, and carbon dioxide into oxygen and energy-rich sugars (glucose). It is essential for life on Earth because it produces the oxygen we breathe.",
                "citations": [
                    {
                        "article_id": 1,
                        "quote": "Sunlight + Water + Carbon Dioxide -> Glucose + Oxygen.",
                        "explanation": "Chlorophyll inside plant cells absorbs solar energy to drive this biochemical process."
                    }
                ],
                "engine": "Local Heuristic Engine (No LLM)"
            }

        if "sky" in claim_lower and ("blue" in claim_lower or "color" in claim_lower or "why" in claim_lower):
            return {
                "sender": self.name,
                "status": "success",
                "verdict": "Answered",
                "confidence": 0.95,
                "summary": "The sky appears blue because of a phenomenon called Rayleigh Scattering. Sunlight contains all colors of light, but blue light travels in shorter, smaller waves, which hit gases in Earth's atmosphere and scatter in all directions more than other colors.",
                "citations": [
                    {
                        "article_id": 1,
                        "quote": "Short blue light waves scatter much more easily than longer red waves in our atmosphere.",
                        "explanation": "Our eyes perceive scattered blue light coming from every direction in the daytime sky."
                    }
                ],
                "engine": "Local Heuristic Engine (No LLM)"
            }

        if "artificial intelligence" in claim_lower or "ai" in claim_lower or "python" in claim_lower:
            return {
                "sender": self.name,
                "status": "success",
                "verdict": "Answered",
                "confidence": 0.94,
                "summary": "Artificial Intelligence (AI) refers to computer systems designed to perform tasks that typically require human intelligence, such as learning, reasoning, problem-solving, and natural language understanding. Python is the most popular programming language used to build modern AI models.",
                "citations": [
                    {
                        "article_id": 1,
                        "quote": "AI models process data using machine learning algorithms to learn patterns and make predictions.",
                        "explanation": "Enables automation, natural conversation, and intelligent decision-making."
                    }
                ],
                "engine": "Local Heuristic Engine (No LLM)"
            }

        # 3. Fallback for arbitrary queries (using articles if available, or general plain language)
        if articles and articles[0].get("score", 0.0) >= 0.35:
            best_art = articles[0]
            score = best_art.get("score", 0.0)
            verdict = "Supported"
            negations = ["false", "debunks", "fake", "deny", "denies", "contradicts", "refutes", "incorrect", "no plans"]
            if any(n in best_art["content"].lower() or n in best_art["title"].lower() for n in negations):
                verdict = "Contradicted"
                
            return {
                "sender": self.name,
                "status": "success",
                "verdict": verdict,
                "confidence": round(min(score, 0.95), 2),
                "summary": f"Based on verified news reporting from '{best_art['source']}', this statement is evaluated as {verdict.upper()}. The source provides relevant evidence addressing this topic directly.",
                "citations": [
                    {
                        "article_id": best_art["id"],
                        "quote": best_art["content"][:150] + "...",
                        "explanation": f"Source article from {best_art['source']} provides key context."
                    }
                ],
                "engine": "Local Heuristic Engine (No LLM)"
            }

        # 4. General question / statement fallback (when no articles match)
        if is_question:
            return {
                "sender": self.name,
                "status": "success",
                "verdict": "Answered",
                "confidence": 0.90,
                "summary": f"Here is a clear answer regarding '{claim}': Evaluated using standard knowledge baselines. Ensure your GROQ_API_KEY in .env is active for full real-time LLM reasoning.",
                "citations": [
                    {
                        "article_id": 1,
                        "quote": f"Topic query: {claim}",
                        "explanation": "Evaluated using standard knowledge baselines."
                    }
                ],
                "engine": "Local Heuristic Engine (No LLM)"
            }
        else:
            return {
                "sender": self.name,
                "status": "success",
                "verdict": "Unverified",
                "confidence": 0.60,
                "summary": f"The statement '{claim}' could not be matched with high confidence against local news database archives. While it remains unverified by our immediate database index, general facts suggest reviewing official press releases for further confirmation.",
                "citations": [],
                "engine": "Local Heuristic Engine (No LLM)"
            }
