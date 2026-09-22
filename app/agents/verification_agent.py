import os
import json
import httpx
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
        self.use_llm = False
        self.gemini_client = None
        
        # 1. Try Groq Free API key
        if config.GROQ_API_KEY:
            print("[Brain] Verification Agent: Groq Free API configured successfully.")
            self.use_llm = True
            
        # 2. Try Gemini Free API key
        elif config.GEMINI_API_KEY:
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=config.GEMINI_API_KEY)
                self.model_name = "gemini-2.5-flash"
                self.use_llm = True
                print(f"[Brain] Verification Agent: Gemini API configured successfully ({self.model_name}).")
            except Exception as e:
                print(f"[Warning] Verification Agent: Gemini API init note: {e}")

        # 3. Check if local Ollama server is running
        else:
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

    def _verify_claim(self, data: dict) -> dict:
        claim = data.get("claim", "").strip()
        articles = data.get("articles", [])

        # Priority 1: Groq Free API (Dynamic check)
        groq_key = os.environ.get("GROQ_API_KEY") or config.GROQ_API_KEY
        if groq_key:
            groq_res = self._verify_with_groq(claim, articles, api_key=groq_key)
            if groq_res.get("status") == "success":
                return groq_res

        # Priority 2: Gemini API (Dynamic check)
        gemini_key = os.environ.get("GEMINI_API_KEY") or config.GEMINI_API_KEY
        if gemini_key:
            if not self.gemini_client:
                try:
                    from google import genai
                    self.gemini_client = genai.Client(api_key=gemini_key)
                except Exception as e:
                    print(f"[Warning] Gemini client init note: {e}")
            if self.gemini_client:
                gem_res = self._verify_with_gemini(claim, articles)
                if gem_res.get("status") == "success":
                    return gem_res

        # Priority 3: Ollama Local Free LLM
        ollama_res = self._verify_with_ollama(claim, articles)
        if ollama_res.get("status") == "success":
            return ollama_res

        # Priority 4: Built-in Local Heuristic Solver
        return self._verify_with_mock(claim, articles)

    def _build_prompt(self, claim: str, articles: list) -> str:
        articles_formatted = ""
        for art in articles:
            articles_formatted += (
                f"--- ARTICLE ID: {art['id']} ---\n"
                f"Title: {art['title']}\n"
                f"Source: {art['source']} ({art['date']})\n"
                f"Content: {art['content']}\n\n"
            )

        return f"""
You are an intelligent, friendly AI assistant and expert fact verifier.
Your goal is to answer the user's input clearly, accurately, and in simple, plain language that ANYONE can easily understand.

User Input: "{claim}"

Retrieved Source Articles (if any):
{articles_formatted if articles_formatted else "No specific database articles found."}

Instructions:
1. Understand the intent of the input:
   - If it is a general question or informational query (e.g. "What is quantum computing?", "Why is the sky blue?"), answer it directly in plain, friendly language.
   - If it is a factual claim or news rumour (e.g. "iPhone 18 launch in 2026", "Drinking coffee is good for heart health"), evaluate whether it is true or false using the source articles and general factual knowledge.
2. Select a clear verdict:
   - "Answered" (for general questions, definitions, or conceptual explanations)
   - "Supported" (for true statements or verified factual claims)
   - "Contradicted" (for false claims, debunks, or refutations)
   - "Unverified" (only if a claim lacks sufficient evidence to confirm or deny)
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
