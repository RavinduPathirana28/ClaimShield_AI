"""
Verification-Agent focused tests.

These tests exercise the multi-LLM consensus aggregator, the offline heuristic
fallback, the multi-agent debate bridge, and PDF report generation. They run
against the agent classes directly (no database writes, no destructive seeding,
no live network calls) so the shared test suite and team data are unaffected.
"""

import sys
import unittest
from pathlib import Path

# Add root folder to sys.path to enable app module imports
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from app.agents.autogen_bridge import AutoGenClaimBridge
from app.agents.verification_agent import VerificationAgent
import app.agents.verification_agent as verif_mod

ARTICLES = [
    {"id": 1, "title": "Apple market cap", "source": "Tech News",
     "date": "2026-01-01", "content": "Apple crossed a historic market cap.", "score": 0.92},
]

PROVIDER_OK = {
    "status": "success",
    "verdict": "Supported",
    "confidence": 0.88,
    "straight_answer": "TRUE.",
    "summary": "Evidence aligns with the claim.",
    "citations": [{"article_id": 1, "quote": "Milestone reached.", "explanation": "Supports claim."}],
    "engine": "Groq Free LLM (llama-3.3-70b-versatile)",
}


class _FakeOrchestrator:
    def __init__(self, verification_agent):
        self.verification_agent = verification_agent


class _ConfigIsolated(unittest.TestCase):
    """Snapshot and restore the GROQ/GEMINI keys mutated below so the
    module-global config is untouched for whichever suite runs next."""

    @classmethod
    def setUpClass(cls):
        cls._orig_groq = verif_mod.config.GROQ_API_KEY
        cls._orig_gemini = verif_mod.config.GEMINI_API_KEY

    @classmethod
    def tearDownClass(cls):
        verif_mod.config.GROQ_API_KEY = cls._orig_groq
        verif_mod.config.GEMINI_API_KEY = cls._orig_gemini


class TestConsensus(_ConfigIsolated):
    def _agent(self):
        import app.agents.verification_agent as mod
        mod.config.GROQ_API_KEY = "test-key"
        mod.config.GEMINI_API_KEY = "test-key"
        agent = VerificationAgent()
        agent._verify_with_ollama = lambda c, a: {"status": "error"}
        return agent

    def test_01_full_agreement_yields_verdict_and_metadata(self):
        agent = self._agent()
        agent._verify_with_groq = lambda c, a, api_key=None: PROVIDER_OK
        agent._verify_with_gemini = lambda c, a: {
            **PROVIDER_OK, "verdict": "TRUE", "confidence": 0.80,
            "engine": "Google Gemini AI Engine (gemini-flash-latest)"}
        res = agent.handle_message({
            "action": "verify_claim",
            "data": {"claim": "Apple reached record market cap.", "articles": ARTICLES},
        })
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["verdict"], "Supported")
        for key in ("verdict", "confidence", "straight_answer", "summary", "citations",
                    "engine", "agreement_score", "model_results"):
            self.assertIn(key, res)
        self.assertEqual(len(res["model_results"]), 2)
        self.assertAlmostEqual(res["agreement_score"], 1.0)
        self.assertIn("Multi-LLM Consensus", res["engine"])
        self.assertIn("Groq", res["engine"])
        self.assertIn("Gemini", res["engine"])

    def test_02_disagreement_reports_lower_agreement(self):
        agent = self._agent()
        agent._verify_with_groq = lambda c, a, api_key=None: PROVIDER_OK
        agent._verify_with_gemini = lambda c, a: {
            "status": "success", "verdict": "Contradicted", "confidence": 0.90,
            "straight_answer": "FALSE.", "summary": "Model disagrees.",
            "engine": "Google Gemini AI Engine (gemini-flash-latest)"}
        res = agent.handle_message({
            "action": "verify_claim",
            "data": {"claim": "Apple reached record market cap.", "articles": ARTICLES},
        })
        self.assertEqual(res["status"], "success")
        self.assertLess(res["agreement_score"], 0.6)
        self.assertIn("divergence", res["summary"].lower())

    def test_03_all_providers_fail_uses_offline_heuristic(self):
        agent = self._agent()
        agent._verify_with_groq = lambda c, a, api_key=None: {"status": "error"}
        agent._verify_with_gemini = lambda c, a: {"status": "error"}
        res = agent.handle_message({
            "action": "verify_claim",
            "data": {"claim": "What is quantum computing?", "articles": []},
        })
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["agreement_score"], None)
        self.assertEqual(res["model_results"], [])
        self.assertIn("Local Heuristic", res["engine"])

    def test_04_verdict_normalization(self):
        agent = self._agent()
        self.assertEqual(agent._normalize_verdict("TRUE"), "Supported")
        self.assertEqual(agent._normalize_verdict("Contradicted"), "Contradicted")
        self.assertEqual(agent._normalize_verdict("General Info"), "Answered")
        self.assertEqual(agent._normalize_verdict("nonsense"), "Unverified")


class TestDebateBridge(_ConfigIsolated):
    def test_05_debate_reuses_consensus_without_extra_calls(self):
        import app.agents.verification_agent as mod
        mod.config.GROQ_API_KEY = ""
        mod.config.GEMINI_API_KEY = ""
        agent = VerificationAgent()
        agent._verify_with_ollama = lambda c, a: {"status": "error"}
        agent._verify_with_groq = lambda c, a, api_key=None: PROVIDER_OK
        agent._verify_with_gemini = lambda c, a: {
            **PROVIDER_OK, "engine": "Google Gemini AI Engine (gemini-flash-latest)"}
        mod.config.GROQ_API_KEY = "test-key"
        mod.config.GEMINI_API_KEY = "test-key"

        claim = "Apple reached record market cap."
        agent.handle_message({"action": "verify_claim", "data": {"claim": claim, "articles": ARTICLES}})

        calls = []
        original = agent.handle_message

        def counting(msg):
            calls.append(msg)
            return original(msg)

        agent.handle_message = counting
        bridge = AutoGenClaimBridge(_FakeOrchestrator(agent))
        debate = bridge.run_debate(claim, ARTICLES)

        self.assertEqual(calls, [], "Debate must reuse cached consensus, not re-run verification.")
        self.assertEqual(debate["status"], "success")
        self.assertEqual(len(debate["debate_log"]), 4)  # 2 FactChecker + Critic + Consensus
        self.assertEqual(debate["engine"], "Multi-Agent Debate (2 models)")
        self.assertTrue(all("agent" in m and "message" in m for m in debate["debate_log"]))


class TestPdfReport(unittest.TestCase):
    def test_06_reportlab_generates_valid_pdf(self):
        try:
            import reportlab  # noqa: F401
        except ImportError:
            self.skipTest("reportlab not installed")
        from generate_pdf import build_verification_report_bytes
        result = {
            "claim": "Sample claim & <tag>.",
            "verdict": "Contradicted",
            "confidence": 0.92,
            "agreement_score": 0.71,
            "straight_answer": "FALSE.",
            "summary": "Models disagreed on the timeline.",
            "citations": [{"article_id": 1, "quote": "Quote.", "explanation": "Why."}],
            "engine": "Multi-LLM Consensus (Groq, Gemini)",
            "entities": [{"text": "Apple", "label": "ORG"}],
        }
        data = build_verification_report_bytes(result)
        self.assertTrue(data.startswith(b"%PDF"), "Output must be a valid PDF document.")
        self.assertGreater(len(data), 500)

    def test_07_reportlab_tolerates_minimal_result(self):
        try:
            import reportlab  # noqa: F401
        except ImportError:
            self.skipTest("reportlab not installed")
        from generate_pdf import build_verification_report_bytes
        data = build_verification_report_bytes({"claim": "", "verdict": "Unclear"})
        self.assertTrue(data.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()