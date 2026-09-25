"""
Claim Recommendations Engine.

After a claim is verified, surfaces 3-4 high-value, related claims the user can
verify next. The candidate pool is built from (1) a curated set of statements that
map directly onto the seeded news corpus (so every pick routes into a real,
evidence-backed verification) and (2) the user's own verification history.

Scoring uses semantic similarity from the shared SentenceTransformer embedding
model when available, with a token-overlap (Dice) fallback for offline/hermetic
environments. The currently verified claim is always excluded, candidates are
deduplicated on a normalized form, and the pool guarantees a minimum fill so the
user always sees actionable choices.
"""

import re

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
    def _candidate_pool(self, username):
        """(claim, source, recency) triples: curated topics then user history.

        History arrives newest-first from the DB, so ``recency`` (0 = freshest)
        lets scoring apply a small recency-decayed boost to prior checks.
        """
        pool = []
        seen = set()
        for claim in list(CURATED_CLAIMS) + list(CURATED_QUERIES):
            norm = _normalize(claim)
            if norm and norm not in seen:
                seen.add(norm)
                pool.append((claim, "Trending topic", None))
        if self.db is not None and username:
            try:
                for recency, log in enumerate(self.db.get_logs_by_user(username) or []):
                    claim = (log.get("claim") or "").strip()
                    norm = _normalize(claim)
                    if claim and norm and norm not in seen:
                        seen.add(norm)
                        pool.append((claim, "Previously verified", recency))
            except Exception:
                pass
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
        """Returns up to top_n varied recommendations, most related first."""
        if not claim or not claim.strip():
            return []
        n = top_n or self.top_n
        pool = self._candidate_pool(username)
        if not pool:
            return []
        norm_claim = _normalize(claim)
        pool_texts = [t for t, *_ in pool]

        emb = self._embed([claim] + pool_texts)
        semantic = {}
        if emb is not None and len(emb) == 1 + len(pool_texts):
            target = emb[0]
            scores = (emb[1:] * target).sum(axis=1)
            for i, s in enumerate(scores):
                semantic[i] = float(s)

        scored = []
        for i, (text, source, recency) in enumerate(pool):
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
            # Freshly verified claims are strong "verify next" candidates, so
            # nudge them with a small recency-decayed boost (newest first).
            if source == "Previously verified" and recency is not None:
                sim += max(0.0, 0.09 - 0.015 * recency)
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