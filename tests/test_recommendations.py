import unittest
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from app.recommendations import ClaimRecommender, _normalize, CURATED_CLAIMS


class _PlainVectorStore:
    """No real embedding model -> the recommender falls back to lexical scoring."""
    model = None


class _FuzzyDB:
    """Minimal double for db.get_logs_by_user history lookups."""

    def __init__(self, claims):
        self.claims = claims

    def get_logs_by_user(self, username):
        return [{"claim": c} for c in self.claims]


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

    def test_history_claims_enter_pool(self):
        prior = "ASML shipped its first 2nm High-NA EUV lithography system."
        db = _FuzzyDB([prior])
        rec = self.make_recommender(db=db, vector_store=_PlainVectorStore())
        out = rec.recommend("ASML began volume 2nm EUV lithography deliveries.", "user")
        labels = {r["claim"]: r["source"] for r in out}
        self.assertIn(prior, labels)
        self.assertEqual(labels[prior], "Previously verified")

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


if __name__ == '__main__':
    unittest.main()