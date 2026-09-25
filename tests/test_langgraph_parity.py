import unittest
import sys
import os
import time
import shutil
import tempfile
from pathlib import Path

# Add root folder to sys.path to enable app module imports
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from app.database.db_manager import DBManager
from app.agents.orchestrator import Orchestrator
from app.agents.base_agent import BaseAgent
from app.utils import security
from app import config
import seed_database


class TestLangGraphParity(unittest.TestCase):
    """LanGraph mode must match the standard flow's guarantees: rate limiting
    (token spent), plan role threading, audit persistence, A2A tracing, and a
    fully-populated result payload."""

    @classmethod
    def setUpClass(cls):
        cls._tmpdir = tempfile.mkdtemp(prefix="claimshield_lg_")
        cls._orig_sqlite_path = config.SQLITE_DB_PATH
        cls._orig_faiss_path = config.FAISS_INDEX_PATH
        cls._orig_supabase_url = config.SUPABASE_URL
        cls._orig_supabase_key = config.SUPABASE_KEY
        config.SUPABASE_URL = ""
        config.SUPABASE_KEY = ""
        cls._orig_env_groq = os.environ.pop("GROQ_API_KEY", None)
        cls._orig_env_gemini = os.environ.pop("GEMINI_API_KEY", None)
        cls._orig_cfg_groq = config.GROQ_API_KEY
        cls._orig_cfg_gemini = config.GEMINI_API_KEY
        config.SQLITE_DB_PATH = os.path.join(cls._tmpdir, "test_news_verifier.db")
        config.FAISS_INDEX_PATH = os.path.join(cls._tmpdir, "test_faiss_index.bin")
        config.GROQ_API_KEY = ""
        config.GEMINI_API_KEY = ""
        seed_database.seed()
        cls.db = DBManager()
        cls.orchestrator = Orchestrator()
        cls.addClassCleanup(cls._restore_and_cleanup)

    @classmethod
    def _restore_and_cleanup(cls):
        config.SQLITE_DB_PATH = cls._orig_sqlite_path
        config.FAISS_INDEX_PATH = cls._orig_faiss_path
        config.SUPABASE_URL = cls._orig_supabase_url
        config.SUPABASE_KEY = cls._orig_supabase_key
        if cls._orig_env_groq is not None:
            os.environ["GROQ_API_KEY"] = cls._orig_env_groq
        config.GROQ_API_KEY = cls._orig_cfg_groq
        if cls._orig_env_gemini is not None:
            os.environ["GEMINI_API_KEY"] = cls._orig_env_gemini
        config.GEMINI_API_KEY = cls._orig_cfg_gemini
        shutil.rmtree(cls._tmpdir, ignore_errors=True)

    def _verify(self, claim, username, mode="LangGraph Stateful Workflow"):
        return self.orchestrator.handle_message({
            "action": "verify",
            "data": {
                "claim": claim,
                "username": username,
                "engine_mode": mode
            }
        })

    def test_01_langgraph_pro_role_parity(self):
        res = self._verify("Is drinking coffee good for heart health?", "premium")
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["is_pro_plan"])
        self.assertIn("LangGraph", res["engine"])
        # Pro tier must surface the full resource parity keys
        for key in ["straight_answer", "evidence_summary", "total_resources_found",
                    "is_pro_plan", "tokens_remaining", "ml_classification", "citations"]:
            self.assertIn(key, res, f"LangGraph result missing parity key '{key}'")
        self.assertLessEqual(len(res["articles"]), config.PRO_PLAN_MAX_RESOURCES)

    def test_02_langgraph_free_tier_deducts_token(self):
        self.db.create_user("lg_free_user", security.hash_password("pass"), role="user")
        before = self.db.get_user("lg_free_user")
        self.assertEqual(before["role"], "user")
        res = self._verify("Apple achieved record market capitalization.", "lg_free_user")
        self.assertEqual(res["status"], "success")
        after = self.db.get_user("lg_free_user")
        # Free tier spends exactly one token per verification
        self.assertAlmostEqual(before["tokens"] - after["tokens"], 1.0,
                               msg="LangGraph verification must consume a token")
        self.assertFalse(res["is_pro_plan"])
        # Free tier displays a maximum of 2 resources
        self.assertLessEqual(len(res["articles"]), config.FREE_PLAN_DISPLAY_RESOURCES)

    def test_03_langgraph_rate_limited_when_out_of_tokens(self):
        self.db.create_user("lg_dry_user", security.hash_password("pass"), role="user")
        self.db.update_user_tokens("lg_dry_user", 0.0, time.time())
        res = self._verify("Apple achieved record market capitalization.", "lg_dry_user")
        self.assertEqual(res["status"], "rate_limited")
        self.assertIn("Rate limit", res["message"])

    def test_04_langgraph_audit_log_persisted(self):
        self.db.create_user("lg_audit_user", security.hash_password("pass"), role="user")
        baseline = len(self.db.get_logs_by_user("lg_audit_user"))
        res = self._verify("Greenland's glaciers are melting 15% faster than the previous decade.", "lg_audit_user")
        self.assertEqual(res["status"], "success")
        logs = self.db.get_logs_by_user("lg_audit_user")
        self.assertEqual(len(logs), baseline + 1, "LangGraph verification must write an audit log")

    def test_05_langgraph_a2a_trace_via_send_message(self):
        captured = []
        original = BaseAgent.send_message

        def collector(self_, recipient, action, data):
            resp = original(self_, recipient, action, data)
            captured.append((self_.name, recipient.name, action))
            return resp

        BaseAgent.send_message = collector
        try:
            res = self._verify("Apple will launch the iPhone 18 in July 2026.", "premium")
        finally:
            BaseAgent.send_message = original
        self.assertEqual(res["status"], "success")
        actions = [a for _, _, a in captured]
        for expected in ["sanitize", "process_claim", "retrieve", "summarize", "verify_claim"]:
            self.assertIn(expected, actions,
                          f"A2A trace should include a '{expected}' edge from the graph")
        self.assertIn(("orchestrator", "security_agent", "log_audit"), captured)


if __name__ == '__main__':
    unittest.main()