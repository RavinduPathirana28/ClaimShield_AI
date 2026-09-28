"""
Claim Recommendations Engine.

After a claim is verified, surfaces 3-4 high-value, related claims the user can
verify next. Every recommendation is driven by the claim the user just entered,
never by their past verification activity.

Two layers produce the panel:

1. **LLM suggestions (primary)** — Groq and Gemini are queried in parallel with
   a bounded latency budget to generate *fresh* follow-up claims: deeper facts,
   key statistics, counter-myths, recent developments and broader context that
   a reader would want verified next. Each suggestion carries a short category
   and a one-line reason tying it to the verified claim. Suggestions are
   validated (self-contained, non-duplicate, not a paraphrase of the input) and
   interleaved across providers so one model cannot dominate the panel.
2. **Local similarity engine (fallback + filler)** — the pre-existing FAISS /
   curated-candidate scorer: it fills any slots the LLM layer did not cover and
   keeps the panel fully functional offline or when no provider keys exist.

The user's own verification history is deliberately excluded at every layer so
the panel follows the current claim, not past preferences.

Scoring uses semantic similarity from the shared SentenceTransformer embedding
model when available, with a token-overlap (Dice) fallback for offline/hermetic
environments. The currently verified claim is always excluded, candidates are
deduplicated on a normalized form (plus a bigram near-duplicate gate), and the
pool guarantees a minimum fill so the user always sees actionable choices.
"""

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, wait

import httpx

import app.config as config

# Curated high-value claims tied to the seeded news corpus. Each statement is
# phrased as a checkable factual claim so selecting it runs a full verification
# with strong local vector evidence instead of a bare general-knowledge answer.
CURATED_CLAIMS = [
    "Apple will launch the iPhone 18 in July 2026.",
    "Drinking 2-3 cups of coffee daily improves heart and cardiovascular health.",
    "Apple's market valuation exceeded one trillion dollars after record Q2 earnings reports.",
    "The city council approved a $50 million smart city technology infrastructure package.",
    "Greenland's glaciers are melting 15% faster than in the previous decade.",
    "Donald Trump became the 47th United States President after winning the 2024 election.",
    "Semiconductor mega-foundries began mass production of 2nm and 3nm wafers in 2026.",
    "An mRNA cancer vaccine reduced melanoma recurrence by 49% in a Phase 3 clinical trial.",
    "The James Webb Space Telescope discovered a galaxy cluster from 320 million years after the Big Bang.",
    "The Federal Reserve cut interest rates by 25 basis points after inflation hit the 2% target.",
    "Researchers demonstrated over 100 fault-tolerant logical qubits for quantum error correction.",
    "Renewable electricity generated more than 33% of global power in 2025, surpassing coal.",
    "NASA will land astronauts on the Moon's South Pole under the Artemis III mission.",
    "The EU AI Act now requires mandatory watermarking for AI-generated synthetic media.",
    "Solid-state batteries enable 10-minute EV fast charging with an 800 kilometer range.",
    "A Mediterranean diet lowers dementia risk by 30% in older adults.",
    "NIST released its finalized post-quantum cryptography standards in 2026.",
    "Vertical farming grows fresh produce using 95% less water than conventional farming.",
    "A transatlantic flight was completed using 100% sustainable aviation biofuel.",
    "Deep-ocean hydrothermal vents host extremophile bacteria used in industrial enzymes.",
]

# Generic question-shaped entries that pair with the seeded knowledge base so the
# recommendation panel stays useful for general-knowledge queries as well.
CURATED_QUERIES = [
    "What is quantum computing?",
    "What is Artificial Intelligence?",
    "Why is the sky blue?",
]

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "but", "by", "for",
    "from", "had", "has", "have", "how", "in", "is", "it", "its", "not", "of",
    "on", "or", "the", "to", "was", "were", "what", "when", "where", "which",
    "who", "why", "will", "with",
}


def _normalize(text: str) -> str:
    """Lowercase, strip punctuation/cards and collapse whitespace."""
    cleaned = re.sub(r"[^a-z0-9 ]", "", (text or "").lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def _tokenize(text: str) -> set:
    """Token set with light stopword filtering for lexical similarity."""
    norm = _normalize(text)
    tokens = {t for t in norm.split() if t and len(t) > 1 and t not in STOPWORDS}
    if not tokens:
        return {t for t in norm.split() if t}
    return tokens


def _bigrams(text: str) -> set:
    """Character bigrams on the normalized text (robust to paraphrase)."""
    norm = _normalize(text)
    norm = norm.replace(" ", "")
    if len(norm) < 2:
        return {norm} if norm else set()
    return {norm[i:i + 2] for i in range(len(norm) - 1)}


def _dice(a: set, b: set) -> float:
    """Dice coefficient between two sets; 0 when both are empty."""
    if not a and not b:
        return 0.0
    return 2.0 * len(a & b) / (len(a) + len(b))


# ---------------------------------------------------------------------------
# LLM suggestion layer (Groq + Gemini, bounded latency, offline-safe)
# ---------------------------------------------------------------------------

# Hard wall-clock budget for the parallel provider window. Both providers get
# their own internal timeouts at or below this value, so the verify request can
# never stall on a slow straggler.
LLM_REC_DEADLINE = 7.0
GROQ_REC_MODELS = ["qwen/qwen3.8-27b", "openai/gpt-oss-20b"]
GEMINI_REC_MODELS = ["gemini-3.5-flash-lite", "gemini-3.5-flash"]
GROQ_REC_TIMEOUT = 6.0
# The google-genai SDK rejects per-request deadlines below 10s; actual latency
# stays bounded by LLM_REC_DEADLINE because the parallel wait cuts stragglers.
GEMINI_REC_TIMEOUT_MS = 10_000
MAX_REC_CLAIM_CHARS = 320
MAX_REC_REASON_CHARS = 180


def _rec_prompt(claim: str, context: dict | None = None) -> str:
    """Builds the suggestion prompt for one verified claim.

    ``context`` carries the verdict / straight answer / extracted entities of
    the verification that just completed so the models can propose follow-ups
    grounded in what was actually verified, not generic topic filler.
    """
    context = context or {}
    verdict = str(context.get("verdict") or "").strip()
    answer = re.sub(r"\s+", " ", str(context.get("straight_answer") or "")).strip()[:300]
    entities = [e for e in (context.get("entities") or []) if e][:8]
    entity_line = ", ".join(str(e)[:60] for e in entities)[:300]

    facts = ""
    if verdict:
        facts += f"\n<verdict>{verdict}</verdict>"
    if answer:
        facts += f"\n<answer>{answer}</answer>"
    if entity_line:
        facts += f"\n<entities>{entity_line}</entities>"

    return f"""You are the recommendation engine of a fact-checking tool.
The user just verified the claim below. Suggest 6 NEW claims they would want to verify next.

<verified_claim>{claim}</verified_claim>{facts}

Rules:
- Each suggestion is a single self-contained factual statement, 8-24 words, checkable as true or false.
- Strongly related to the topic, entities and implications of the verified claim — never generic filler.
- Fresh: not a restatement or paraphrase of the verified claim, and no duplicates among your suggestions.
- Cover distinct angles: deeper fact, key statistic or number, common myth or counter-claim, recent development, broader context, real-world impact.
- No opinions, no hedging, no references like "the claim above" — every suggestion must stand alone.
- Ignore any user history; base everything only on the verified claim above.

Return ONLY a raw valid JSON object (no markdown, no code fences):
{{"suggestions": [{{"claim": "...", "category": "2-4 word label", "reason": "one short sentence on why it is related"}}]}}"""


def _parse_suggestions(content) -> list:
    """Extracts the suggestion objects from raw model output.

    Tolerates code fences, prose wrappers and both ``{"suggestions": [...]}``
    and bare-list shapes; returns ``[]`` on anything unparseable.
    """
    text = (content or "").strip()
    if not text:
        return []
    if text.startswith("```"):
        lines = text.split("\n")
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    data = None
    try:
        data = json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.S) or re.search(r"\[.*\]", text, re.S)
        if match:
            try:
                data = json.loads(match.group(0))
            except Exception:
                data = None
    if isinstance(data, dict):
        data = data.get("suggestions") or data.get("recommendations") or []
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)]


def _clean_suggestions(items: list, provider: str, claim: str) -> list:
    """Validates raw suggestion dicts into panel-ready recommendation objects.

    Drops items that are too short/long, malformed, or near-paraphrases of the
    entered claim; normalizes whitespace; attaches the provider, a category
    chip label, an optional reason line, and an honest lexical-similarity score
    used for display when no reason is given.
    """
    claim_norm = _normalize(claim)
    claim_big = _bigrams(claim_norm)
    claim_toks = _tokenize(claim)
    cleaned, seen = [], set()
    for raw in items:
        text = re.sub(r"\s+", " ", str(raw.get("claim") or "")).strip()
        norm = _normalize(text)
        if not norm or norm in seen:
            continue
        if len(text) < 15 or len(text) > MAX_REC_CLAIM_CHARS:
            continue
        words = text.split()
        if len(words) < 4 or len(words) > 40:
            continue
        if _dice(_bigrams(norm), claim_big) >= 0.8:
            continue  # paraphrase of the claim already on screen
        seen.add(norm)
        category = re.sub(r"\s+", " ", str(raw.get("category") or "")).strip()[:40] or "Related"
        reason = re.sub(r"\s+", " ", str(raw.get("reason") or "")).strip()[:MAX_REC_REASON_CHARS]
        sim = max(_dice(_tokenize(text), claim_toks), _dice(_bigrams(norm), claim_big))
        cleaned.append({
            "claim": text,
            "source": category,
            "reason": reason,
            "provider": provider,
            "similarity": round(max(0.0, min(1.0, sim)), 3),
        })
    return cleaned


class ClaimRecommender:
    """Recommends related, verifiable claims for a just-verified claim."""

    def __init__(self, db=None, vector_store=None, top_n: int = 4,
                 min_similarity: float = 0.18, diversity: float = 0.60):
        self.db = db
        self.vector_store = vector_store
        self.top_n = max(1, int(top_n))
        self.min_similarity = min_similarity
        # Minimum pairwise similarity at which two recommendations are treated
        # as redundant. Keeps the panel topically varied instead of restating
        # the same claim in a few phrasings.
        self.diversity = max(0.0, min(1.0, diversity))
        self._embed_model = None
        self._model_checked = False
        self._titles = None
        self._gemini_client = None

    # -- embedding model -----------------------------------------------------
    def _ensure_model(self):
        if self._model_checked:
            return
        self._model_checked = True
        try:
            model = getattr(self.vector_store, "model", None)
            if model is not None and hasattr(model, "encode"):
                self._embed_model = model
        except Exception:
            self._embed_model = None

    def _embed(self, texts) -> "object | None":
        """Normalized embedding matrix or None (model missing / failure)."""
        self._ensure_model()
        if self._embed_model is None:
            return None
        try:
            return self._embed_model.encode(
                list(texts), show_progress_bar=False, normalize_embeddings=True
            )
        except Exception:
            return None

    # -- candidate construction ---------------------------------------------
    def _article_title_map(self):
        """``article_id -> (title, outlet)`` for the seeded corpus (cached)."""
        if self._titles is not None:
            return self._titles
        self._titles = {}
        if self.db is None:
            return self._titles
        try:
            for art in (self.db.get_all_articles() or []):
                self._titles[str(art.get("id"))] = (
                    (art.get("title") or "").strip(),
                    (art.get("source") or "").strip(),
                )
        except Exception:
            self._titles = {}
        return self._titles

    def _retrieve_corpus_titles(self, claim, limit):
        """Titles of the corpus articles the vector index deems closest."""
        search = getattr(self.vector_store, "search_index", None)
        if search is None:
            return []
        try:
            hits = search(claim, limit=limit)
        except Exception:
            hits = []
        if not hits:
            return []
        titles = self._article_title_map()
        out = []
        for article_id, _sim in hits or []:
            entry = titles.get(str(article_id))
            if entry and entry[0]:
                out.append(entry)
        return out

    def _candidate_pool(self, claim):
        """(claim, source) candidates similar to the entered claim.

        Led by the titles of the corpus articles retrieved for the claim -- they
        are the closest, verifyable "what next" items -- with the curated claim
        set as a fallback. The user's own history is deliberately excluded so
        the panel reflects the current claim, not past preferences.
        """
        pool = []
        seen = set()
        limit = max(self.top_n * 2, self.top_n + 2)

        for title, outlet in self._retrieve_corpus_titles(claim, limit):
            norm = _normalize(title)
            if norm and norm not in seen:
                seen.add(norm)
                pool.append((title, outlet or "Related article"))

        for claim_text in list(CURATED_CLAIMS) + list(CURATED_QUERIES):
            norm = _normalize(claim_text)
            if norm and norm not in seen:
                seen.add(norm)
                pool.append((claim_text, "Trending topic"))

        return pool

    # -- diversity ----------------------------------------------------------
    @staticmethod
    def _pair_similarity(a: dict, b: dict) -> float:
        """Similarity between two candidates (embedding cosine, else lexical)."""
        va, vb = a.get("_vec"), b.get("_vec")
        if va is not None and vb is not None:
            return float(va @ vb)
        return max(_dice(a["_bigs"], b["_bigs"]), _dice(a["_toks"], b["_toks"]))

    def _diverse_subset(self, items: list, n: int) -> list:
        """Greedy, relevance-first subset skipping redundant near-duplicates.

        Keeps the most relevant claim of each topic cluster so the panel reads
        as several distinct high-value claims instead of one claim restated.
        Output preserves relevance order.
        """
        kept = []
        for item in items:
            if len(kept) >= n:
                break
            if any(self._pair_similarity(item, k) >= self.diversity for k in kept):
                continue
            kept.append(item)
        return kept

    # -- scoring -------------------------------------------------------------
    def recommend(self, claim, username="guest", top_n=None):
        """Returns up to top_n varied recommendations, most related first.

        ``username`` is accepted for API compatibility but deliberately has no
        effect: recommendations are ranked purely by similarity to the entered
        claim, never by the user's past verification history.
        """
        if not claim or not claim.strip():
            return []
        n = top_n or self.top_n
        pool = self._candidate_pool(claim)
        if not pool:
            return []
        norm_claim = _normalize(claim)
        pool_texts = [t for t, _ in pool]

        emb = self._embed([claim] + pool_texts)
        semantic = {}
        if emb is not None and len(emb) == 1 + len(pool_texts):
            target = emb[0]
            scores = (emb[1:] * target).sum(axis=1)
            for i, s in enumerate(scores):
                semantic[i] = float(s)

        scored = []
        for i, (text, source) in enumerate(pool):
            if _normalize(text) == norm_claim:
                continue
            sem = semantic.get(i, 0.0)
            # Lexical signal combines word overlap with character-bigram overlap
            # so ranking stays claim-dependent even when no embedding model is
            # available (semantic-only ties otherwise collapse to a static list).
            tok = _dice(_tokenize(claim), _tokenize(text))
            big = _dice(_bigrams(claim), _bigrams(text))
            if self._embed_model is not None:
                sim = max(sem, max(tok, big) * 0.5)
            else:
                sim = max(tok, big, sem * 0.5)
            scored.append({
                "claim": text,
                "source": source,
                "similarity": round(max(0.0, min(1.0, sim)), 3),
                "_sim": sim,
                "_tok": tok,
                "_big": big,
                "_toks": _tokenize(text),
                "_bigs": _bigrams(text),
                "_vec": None if emb is None else emb[i + 1],
            })

        # Most related first. Near-ties resolve by lexical overlap with the
        # current claim (bigram, then tokens) instead of the static pool order,
        # so the panel produces fresh, query-specific recommendations every run.
        scored.sort(key=lambda r: (r["_sim"], r["_big"], r["_tok"]), reverse=True)

        # Prefer a topically varied set over several near-duplicate claims.
        chosen = self._diverse_subset(scored, n)
        if len(chosen) < n:
            # Top up with the next-best candidates when the pool cannot supply
            # enough distinct topics, so the panel never comes up short.
            seen = {id(c) for c in chosen}
            for c in scored:
                if len(chosen) >= n:
                    break
                if id(c) not in seen:
                    chosen.append(c)
                    seen.add(id(c))
        chosen = chosen[:n]
        chosen.sort(key=lambda r: r["_sim"], reverse=True)

        return [
            {"claim": r["claim"], "source": r["source"], "similarity": r["similarity"]}
            for r in chosen
        ]

    # -- LLM suggestion layer ------------------------------------------------
    def _groq_suggestions(self, claim: str, context: dict | None, api_key: str) -> list:
        """One bounded Groq pass; returns cleaned suggestions or []."""
        prompt = _rec_prompt(claim, context)
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        for model_name in GROQ_REC_MODELS:
            try:
                payload = {
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.4,
                    "response_format": {"type": "json_object"},
                }
                with httpx.Client(timeout=GROQ_REC_TIMEOUT) as client:
                    r = client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers=headers, json=payload,
                    )
                if r.status_code != 200:
                    print(f"[Recommendations] Groq HTTP {r.status_code} for {model_name}: {r.text[:100]}")
                    continue
                content = r.json()["choices"][0]["message"]["content"]
                items = _clean_suggestions(_parse_suggestions(content), "Groq", claim)
                if items:
                    return items
            except Exception as e:
                print(f"[Recommendations] Groq call note on {model_name}: {e}")
        return []

    def _gemini_suggestions(self, claim: str, context: dict | None, api_key: str) -> list:
        """One bounded Gemini pass; returns cleaned suggestions or []."""
        if self._gemini_client is None:
            try:
                from google import genai
                from google.genai import types
                self._gemini_client = genai.Client(
                    api_key=api_key,
                    http_options=types.HttpOptions(timeout=GEMINI_REC_TIMEOUT_MS),
                )
            except Exception as e:
                print(f"[Recommendations] Gemini client init note: {e}")
                return []
        prompt = _rec_prompt(claim, context)
        for model_name in GEMINI_REC_MODELS:
            for attempt in range(2):  # one retry rides out transient 429/malformed JSON
                try:
                    response = self._gemini_client.models.generate_content(
                        model=model_name, contents=prompt,
                    )
                    items = _clean_suggestions(
                        _parse_suggestions(response.text or ""), "Gemini", claim
                    )
                    if items:
                        return items
                    break  # parsed fine but empty -> next model
                except Exception as e:
                    if attempt == 0:
                        print(f"[Recommendations] Gemini '{model_name}' retrying after: {e}")
                        continue
                    print(f"[Recommendations] Gemini call note on {model_name}: {e}")
        return []

    def _llm_suggestions(self, claim: str, context: dict | None = None, need: int = 4):
        """Queries Groq and Gemini in parallel under one latency budget.

        Returns ``(items, providers)`` where ``items`` is a provider-interleaved
        list (so neither model dominates) and ``providers`` names the models
        that answered. Missing keys, timeouts and failures all yield ``([], [])``
        — callers degrade to the local engine silently.
        """
        groq_key = (os.environ.get("GROQ_API_KEY") or config.GROQ_API_KEY or "").strip()
        gemini_key = (os.environ.get("GEMINI_API_KEY") or config.GEMINI_API_KEY or "").strip()
        tasks = []
        if groq_key:
            tasks.append(("Groq", lambda: self._groq_suggestions(claim, context, groq_key)))
        if gemini_key:
            tasks.append(("Gemini", lambda: self._gemini_suggestions(claim, context, gemini_key)))
        if not tasks:
            return [], []

        executor = ThreadPoolExecutor(max_workers=len(tasks))
        futures = {executor.submit(fn): name for name, fn in tasks}
        done, pending = wait(set(futures), timeout=LLM_REC_DEADLINE)
        by_provider = {}
        for fut in done:
            try:
                items = fut.result()
            except Exception as e:
                print(f"[Recommendations] Provider '{futures[fut]}' raised: {e}")
                continue
            if items:
                by_provider[futures[fut]] = items
        for fut in pending:
            fut.cancel()
        # Never join stragglers; threads are bounded by their own timeouts.
        executor.shutdown(wait=False, cancel_futures=True)
        if not by_provider:
            return [], []

        ordered = [name for name in ("Groq", "Gemini") if name in by_provider]
        lists = [by_provider[name] for name in ordered]
        limit = max(need * 2, need + 2)
        merged, taken, idx = [], set(), 0
        while len(merged) < limit and any(idx < len(items) for items in lists):
            for items in lists:
                if idx >= len(items):
                    continue
                norm = _normalize(items[idx]["claim"])
                if norm in taken:
                    continue
                taken.add(norm)
                merged.append(items[idx])
            idx += 1
        return merged, ordered

    def recommend_llm(self, claim, username="guest", context=None, top_n=None):
        """Fresh LLM-generated follow-up claims, local engine as guarantee.

        Layer 1 (Groq + Gemini) supplies novel, context-aware suggestions in
        claim order; layer 2 tops the panel up with the local similarity
        ranking until ``top_n`` slots are filled. The entered claim — in any
        wording — and near-duplicate suggestions are always excluded.
        ``username`` is accepted for API compatibility and deliberately unused:
        recommendations follow the entered claim, never the user's history.
        """
        if not claim or not claim.strip():
            return []
        n = top_n or self.top_n
        try:
            local = self.recommend(claim, username, top_n=n)
        except Exception as e:
            print(f"[Recommendations] Local engine note: {e}")
            local = []
        try:
            ai_items, _providers = self._llm_suggestions(claim, context=context, need=n)
        except Exception as e:
            print(f"[Recommendations] LLM suggestions failed: {e}")
            ai_items = []

        # Merge: LLM suggestions first, then local fill. Near-duplicates
        # (including restatements of the entered claim) are skipped via
        # normalized equality plus a character-bigram gate.
        taken = {_normalize(claim)}
        taken_bigrams = [_bigrams(_normalize(claim))]
        merged = []
        for item in ai_items + local:
            norm = _normalize(item.get("claim") or "")
            if not norm or norm in taken:
                continue
            bigs = _bigrams(norm)
            if any(_dice(bigs, prior) >= 0.78 for prior in taken_bigrams):
                continue
            taken.add(norm)
            taken_bigrams.append(bigs)
            merged.append(item)
            if len(merged) >= n:
                break
        return merged[:n]