import unittest
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from app.recommendations import (
    ClaimRecommender,
    _normalize,
    _parse_suggestions,
    _clean_suggestions,
    CURATED_CLAIMS,
)


class _PlainVectorStore:
    """No real embedding model -> the recommender falls back to lexical scoring."""
    model = None


class _IndexedVectorStore:
    """Minimal double exposing FAISS-style article search for corpus candidates."""

    def __init__(self, hits):
        self.hits = hits  # [(article_id, similarity), ...]
        self.model = None

    def search_index(self, query, limit=3):
        return self.hits[:limit]


class _FuzzyDB:
    """Minimal double for db.get_logs_by_user history lookups."""

    def __init__(self, claims):
        self.claims = claims

    def get_logs_by_user(self, username):
        return [{"claim": c} for c in self.claims]

    def get_all_articles(self):
        return []


class _ArticlesDB(_FuzzyDB):
    """DB double with a seeded corpus of articles."""

    def __init__(self, articles):
        self.articles = articles

    def get_all_articles(self):
        return self.articles


class TestClaimRecommender(unittest.TestCase):
    def make_recommender(self, db=None, vector_store=None, top_n=4, min_similarity=0.18):
        return ClaimRecommender(
            db=db, vector_store=vector_store,
            top_n=top_n, min_similarity=min_similarity
        )

    def test_empty_claim_returns_empty(self):
        rec = self.make_recommender(vector_store=_PlainVectorStore())
        self.assertEqual(rec.recommend("   "), [])

    def test_excludes_input_claim(self):
        rec = self.make_recommender(vector_store=_PlainVectorStore())
        claim = "Apple will launch the iPhone 18 in July 2026."
        out = rec.recommend(claim, "user")
        for r in out:
            self.assertNotEqual(_normalize(r["claim"]), _normalize(claim))
            self.assertIn("similarity", r)
            self.assertIn("source", r)
            self.assertIn("claim", r)

    def test_returns_at_most_top_n_and_sorted(self):
        rec = self.make_recommender(vector_store=_PlainVectorStore(), top_n=4)
        out = rec.recommend("Is drinking coffee good for heart health?", "user")
        self.assertGreaterEqual(len(out), 3)
        self.assertLessEqual(len(out), 4)
        sims = [r["similarity"] for r in out]
        self.assertEqual(sims, sorted(sims, reverse=True))
        claims = [r["claim"] for r in out]
        self.assertEqual(len(claims), len(set(claims)), "recommendations must be deduplicated")

    def test_related_ranks_above_unrelated(self):
        rec = self.make_recommender(vector_store=_PlainVectorStore())
        out = rec.recommend("Is drinking coffee good for heart health?", "user")
        claims = [r["claim"].lower() for r in out]
        coffee_idx = next((i for i, c in enumerate(claims)
                          if "coffee" in c or "heart" in c.lower()), None)
        glacier_idx = next((i for i, c in enumerate(claims)
                           if "glacier" in c), None)
        self.assertIsNotNone(coffee_idx, "a heart-health related claim should be recommended")
        if glacier_idx is not None:
            self.assertLess(coffee_idx, glacier_idx,
                            "clearly-related claim must rank above an unrelated one")

    def test_min_similarity_gate_with_fill(self):
        rec = self.make_recommender(vector_store=_PlainVectorStore(), top_n=4, min_similarity=0.99)
        out = rec.recommend("Apple will launch the iPhone 18 in July 2026.", "user")
        # Nothing passes the strict gate, but the panel is still filled to top_n.
        self.assertEqual(len(out), 4)

    def test_history_does_not_influence_recommendations(self):
        # A user's past checks must not surface in the panel: recommendations
        # follow the entered claim, never the user's prior preferences.
        prior = "Drinking 2-3 cups of coffee daily improves heart health."
        db = _FuzzyDB([prior])
        rec = self.make_recommender(db=db, vector_store=_PlainVectorStore())
        out = rec.recommend("Apple will launch the iPhone 18 in July 2026.", "user")
        self.assertTrue(out)
        self.assertNotIn("Previously verified", [r["source"] for r in out])
        self.assertTrue(any("apple" in r["claim"].lower() or "iphone" in r["claim"].lower()
                            for r in out),
                        "panel should lead with claims similar to what the user entered")

    def test_corpus_titles_rank_first_above_curated(self):
        # When the vector index retrieves articles, their titles are the primary
        # recommendation candidates: an Apple claim surfaces Apple articles first.
        db = _ArticlesDB([
            {"id": 1, "title": "Apple's Roadmap: No iPhone 18 planned until 2027",
             "source": "TechNews Daily"},
            {"id": 2, "title": "Greenland glaciers melting 15% faster than expected",
             "source": "Scientific Earth"},
        ])
        vs = _IndexedVectorStore([(1, 0.92), (2, 0.18)])
        rec = self.make_recommender(db=db, vector_store=vs)
        out = rec.recommend("Apple will launch the iPhone 18 in July 2026.", "user")
        self.assertGreaterEqual(len(out), 1)
        self.assertEqual(out[0]["source"], "TechNews Daily")
        self.assertIn("iphone", out[0]["claim"].lower())
        self.assertTrue(any("apple" in r["claim"].lower() or "iphone" in r["claim"].lower()
                            for r in out))

    def test_history_dedup_against_curated(self):
        db = _FuzzyDB(["Apple will launch the iPhone 18 in July 2026."])
        rec = self.make_recommender(db=db, vector_store=_PlainVectorStore())
        out = rec.recommend("Apple will launch the iPhone 18 in July 2026.", "user")
        claims = [r["claim"] for r in out]
        self.assertEqual(len(claims), len(set(claims)))
        # The history duplicate must not reappear as a separate entry.
        self.assertEqual(sum(1 for c in claims if "iphone 18" in c.lower()), 0)

    def test_embedded_similarity_ordering(self):
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception as e:  # model unavailable in hermetic env -> skip
            self.skipTest(f"Embedding model unavailable: {e}")

        class _VStore:
            pass

        _VStore.model = model

        rec = self.make_recommender(vector_store=_VStore())
        out = rec.recommend("Is drinking coffee good for heart health?", "user")
        claims = [r["claim"].lower() for r in out]
        coffee_idx = next((i for i, c in enumerate(claims)
                          if "coffee" in c or "heart" in c.lower()), None)
        self.assertIsNotNone(coffee_idx, "semantic scoring should rank coffee/heart claim first")
        self.assertTrue(any(r["similarity"] >= 0.5 for r in out),
                        "semantic similarity for related claims should be meaningful")


class TestLLMSuggestionLayer(unittest.TestCase):
    """The Groq/Gemini suggestion layer: parsing, validation and merging.

    Every test here is hermetic — the provider call is either bypassed by
    testing the pure helpers or stubbed on the instance, so no network traffic
    ever occurs regardless of which API keys the host machine has configured.
    """

    CLAIM = "The Great Wall of China is visible from space with the naked eye."

    def make_recommender(self, **kwargs):
        kwargs.setdefault("vector_store", _PlainVectorStore())
        return ClaimRecommender(**kwargs)

    # -- parsing -------------------------------------------------------------
    def test_parse_accepts_fenced_wrapper_and_bare_list(self):
        fenced = '```json\n{"suggestions": [{"claim": "A"}]}\n```'
        wrapped = '{"suggestions": [{"claim": "B"}]}'
        bare = '[{"claim": "C"}]'
        for payload, expected in ((fenced, "A"), (wrapped, "B"), (bare, "C")):
            parsed = _parse_suggestions(payload)
            self.assertEqual(len(parsed), 1, payload)
            self.assertEqual(parsed[0]["claim"], expected)

    def test_parse_rejects_garbage(self):
        for junk in ("", "   ", "not json at all", '{"suggestions": "oops"}'):
            self.assertEqual(_parse_suggestions(junk), [], junk)

    # -- validation ----------------------------------------------------------
    def test_clean_drops_short_items_and_input_paraphrases(self):
        paraphrase = "The Great Wall of China is visible from space without a telescope."
        items = [
            {"claim": "too short", "category": "x"},
            {"claim": paraphrase, "category": "Myth check", "reason": "restates input"},
            {"claim": "Astronauts have photographed the Great Wall from low Earth orbit using cameras.", "category": "Follow-up fact", "reason": "Tests the same visibility myth with the camera distinction."},
        ]
        cleaned = _clean_suggestions(items, "Groq", self.CLAIM)
        self.assertEqual(len(cleaned), 1, "only the valid, non-duplicate suggestion survives")
        got = cleaned[0]
        self.assertEqual(got["provider"], "Groq")
        self.assertEqual(got["source"], "Follow-up fact")
        self.assertIn("camera distinction", got["reason"])
        for key in ("claim", "source", "similarity"):
            self.assertIn(key, got)
        self.assertGreaterEqual(got["similarity"], 0.0)
        self.assertLessEqual(got["similarity"], 1.0)

    def test_clean_normalizes_whitespace_and_caps_fields(self):
        items = [{"claim": "  Renewables   supplied\n40% of global power in 2025 .  ",
                  "category": "Key Statistic " + "x" * 80,
                  "reason": "r" * 400}]
        cleaned = _clean_suggestions(items, "Gemini", self.CLAIM)
        self.assertEqual(len(cleaned), 1)
        self.assertNotIn("  ", cleaned[0]["claim"])
        self.assertLessEqual(len(cleaned[0]["source"]), 40)
        self.assertLessEqual(len(cleaned[0]["reason"]), 180)

    # -- merge / fallback ----------------------------------------------------
    def test_recommend_llm_matches_local_output_when_llm_unavailable(self):
        rec = self.make_recommender()
        rec._llm_suggestions = lambda *args, **kwargs: ([], [])
        claim = "Is drinking coffee good for heart health?"
        ai_out = rec.recommend_llm(claim, context={"verdict": "Answered"})
        local_out = rec.recommend(claim, "user")
        self.assertEqual([r["claim"] for r in ai_out], [r["claim"] for r in local_out])
        self.assertGreaterEqual(len(ai_out), 3)
        self.assertLessEqual(len(ai_out), 4)

    def test_recommend_llm_leads_with_ai_and_fills_from_local(self):
        ai_item = {
            "claim": "Greenland's glaciers are retreating about 15 percent faster than a decade ago.",
            "source": "Key statistic",
            "reason": "Quantifies the same climate-acceleration angle.",
            "provider": "Groq",
            "similarity": 0.42,
        }
        rec = self.make_recommender()
        rec._llm_suggestions = lambda *args, **kwargs: ([ai_item], ["Groq"])
        out = rec.recommend_llm("Greenland's glaciers are melting faster than before.")
        self.assertEqual(out[0]["claim"], ai_item["claim"])
        self.assertEqual(out[0]["provider"], "Groq")
        self.assertGreaterEqual(len(out), 3, "local engine tops the panel up to top_n")
        self.assertLessEqual(len(out), 4)
        claims = [r["claim"] for r in out]
        self.assertEqual(len(claims), len(set(claims)), "merged panel must be deduplicated")

    def test_recommend_llm_drops_input_and_near_duplicates(self):
        good = {
            "claim": "Astronauts have photographed the Great Wall from low Earth orbit using cameras.",
            "source": "Follow-up fact",
            "reason": "Same myth, camera distinction.",
            "provider": "Groq",
            "similarity": 0.5,
        }
        exact_dup = dict(good, claim=self.CLAIM)  # the entered claim itself
        restatement = dict(
            good,
            claim="The Great Wall of China is visible from space with the naked eye!",
            provider="Gemini",
        )  # normalized-equal to the entered claim (punctuation only)
        near_dup = dict(
            good,
            claim="Greenland's glaciers are melting 20 percent faster than in 2010.",
            provider="Gemini",
        )
        twin = dict(
            good,
            claim="Greenland glaciers are melting 20 percent faster than in 2010.",
            provider="Gemini",
        )  # near-duplicate of near_dup (one character apart)
        rec = self.make_recommender()
        rec._llm_suggestions = lambda *args, **kwargs: (
            [good, exact_dup, restatement, near_dup, twin],
            ["Groq", "Gemini"],
        )
        out = rec.recommend_llm(self.CLAIM, top_n=4)
        claims = [_normalize(r["claim"]) for r in out]
        self.assertEqual(len(claims), len(set(claims)), "no duplicates may reach the panel")
        self.assertNotIn(_normalize(self.CLAIM), claims, "the entered claim must be excluded")
        self.assertEqual(sum(1 for c in claims if "greenland" in c), 1,
                         "near-duplicate Greenland phrasings collapse to one entry")
        self.assertEqual(out[0]["claim"], good["claim"], "valid AI suggestions lead the panel")


if __name__ == '__main__':
    unittest.main()