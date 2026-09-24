import unittest
import sys
import os
import json
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
from app.utils import security
from app import config
import seed_database

class TestNewsClaimVerifier(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run the suite against an isolated temporary database so the real
        data/news_verifier.db (registered users + audit history) is never
        wiped, reseeded, or polluted by these tests."""
        print("[Test Setup] Creating isolated temporary database...")
        cls._tmpdir = tempfile.mkdtemp(prefix="claimshield_tests_")
        cls._orig_sqlite_path = config.SQLITE_DB_PATH
        cls._orig_faiss_path = config.FAISS_INDEX_PATH
        cls._orig_supabase_url = config.SUPABASE_URL
        cls._orig_supabase_key = config.SUPABASE_KEY
        config.SQLITE_DB_PATH = os.path.join(cls._tmpdir, "test_news_verifier.db")
        config.FAISS_INDEX_PATH = os.path.join(cls._tmpdir, "test_faiss_index.bin")
        # Keep the suite hermetic: never touch the configured (possibly cloud)
        # primary database. All reads/writes go to the isolated local SQLite.
        config.SUPABASE_URL = ""
        config.SUPABASE_KEY = ""
        # config now loads app/.env (which sets os.environ). Blank the provider
        # keys on BOTH sources so the verification tests keep running the
        # offline heuristic instead of firing live Groq/Gemini calls.
        cls._orig_env_groq = os.environ.pop("GROQ_API_KEY", None)
        cls._orig_env_gemini = os.environ.pop("GEMINI_API_KEY", None)
        cls._orig_cfg_groq = config.GROQ_API_KEY
        cls._orig_cfg_gemini = config.GEMINI_API_KEY
        config.GROQ_API_KEY = ""
        config.GEMINI_API_KEY = ""
        print(f"[Test Setup] Isolated DB: {config.SQLITE_DB_PATH}")

        seed_database.seed()
        cls.db = DBManager()
        cls.orchestrator = Orchestrator()
        cls.addClassCleanup(cls._restore_and_cleanup)

    @classmethod
    def _restore_and_cleanup(cls):
        """Restore the real DB paths, provider keys and remove the temporary test directory."""
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

    def test_01_password_hashing(self):
        """Test secure password hashing and verification helper functions."""
        password = "secret_password_123"
        hashed = security.hash_password(password)
        self.assertNotEqual(password, hashed)
        self.assertTrue(security.verify_password(password, hashed))
        self.assertFalse(security.verify_password("wrong_password", hashed))

    def test_02_jwt_token_generation_and_verification(self):
        """Test JWT signing, expiration settings, and claims verification."""
        username = "test_reporter"
        role = "premium"
        token = security.generate_jwt(username, role)
        
        # Verify
        payload = security.verify_jwt(token)
        self.assertEqual(payload["sub"], username)
        self.assertEqual(payload["role"], role)
        self.assertIn("exp", payload)

    def test_03_rate_limiting_bucket(self):
        """Test token-bucket rate limiting for standard user versus premium accounts."""
        username = "rate_limit_test_user"
        # Register a standard user
        hashed = security.hash_password("pass123")
        try:
            self.db.create_user(username, hashed, role="user")
        except Exception:
            pass
        
        sec_agent = self.orchestrator.security_agent
        res = sec_agent.handle_message({
            "action": "check_rate_limit",
            "data": {"username": username}
        })
        self.assertEqual(res["status"], "success")
        self.assertIn("allowed", res)

    def test_04_a2a_protocol_compliance(self):
        """Test A2A/1.0 protocol compliance on inter-agent messaging."""
        nlp_agent = self.orchestrator.nlp_agent
        captured_messages = []
        original_handle = nlp_agent.handle_message
        
        def capturing_handle(msg):
            captured_messages.append(msg)
            return original_handle(msg)
        
        nlp_agent.handle_message = capturing_handle
        
        # Send a test message
        self.orchestrator.send_message(
            recipient=nlp_agent,
            action="process_claim",
            data={"claim": "Test protocol fields"}
        )
        
        # Restore original handler
        nlp_agent.handle_message = original_handle
        
        # Verify the captured message has A2A/1.0 protocol fields
        self.assertTrue(len(captured_messages) > 0, "Should have captured at least one message.")
        msg = captured_messages[0]
        
        self.assertEqual(msg.get("protocol"), "A2A/1.0", 
                         "Message must include 'protocol': 'A2A/1.0'")
        self.assertIn("message_id", msg, 
                       "Message must include a 'message_id' field.")
        self.assertIn("timestamp", msg, 
                       "Message must include a 'timestamp' field.")
        self.assertIsInstance(msg["timestamp"], float, 
                              "Timestamp should be a float (Unix epoch).")
        # Validate UUID format
        import uuid
        try:
            uuid.UUID(msg["message_id"])
        except ValueError:
            self.fail(f"message_id '{msg['message_id']}' is not a valid UUID.")

    def test_05_nlp_entity_and_query_extraction(self):
        """Test spaCy Named Entity Recognition and keyword query extraction."""
        nlp_agent = self.orchestrator.nlp_agent
        res = nlp_agent.handle_message({
            "action": "process_claim",
            "data": {"claim": "Apple Inc. announced record revenue in California yesterday."}
        })
        self.assertEqual(res["status"], "success")
        self.assertIn("entities", res)
        self.assertIn("search_query", res)

    def test_06_nlp_extractive_summarization(self):
        """Test spaCy extractive summarization on long article texts."""
        nlp_agent = self.orchestrator.nlp_agent
        long_text = (
            "Artificial intelligence is transforming global industries. "
            "Machine learning algorithms analyze large volumes of complex data. "
            "Natural language processing allows computers to understand human language. "
            "Modern deep learning architectures power intelligent conversational agents."
        )
        res = nlp_agent.handle_message({
            "action": "summarize",
            "data": {"text": long_text, "max_sentences": 2}
        })
        self.assertEqual(res["status"], "success")
        self.assertIn("summary", res)

    def test_07_faiss_vector_retrieval(self):
        """Test FAISS vector store similarity retrieval."""
        ret_agent = self.orchestrator.retrieval_agent
        res = ret_agent.handle_message({
            "action": "retrieve",
            "data": {"query": "Apple stock revenue", "limit": 3}
        })
        self.assertEqual(res["status"], "success")
        self.assertIn("articles", res)

    def test_08_verification_claim_supported(self):
        """Test fact verification on supported claim."""
        res = self.orchestrator.handle_message({
            "action": "verify",
            "data": {
                "claim": "Apple achieved record market capitalization.",
                "username": "premium"
            }
        })
        self.assertEqual(res["status"], "success")
        self.assertIn("verdict", res)

    def test_09_verification_claim_contradicted(self):
        """Test fact verification on contradicted claim."""
        res = self.orchestrator.handle_message({
            "action": "verify",
            "data": {
                "claim": "Apple will launch the iPhone 18 in July 2026.",
                "username": "premium"
            }
        })
        self.assertEqual(res["status"], "success")
        self.assertIn("verdict", res)

    def test_10_scikit_learn_ml_classification(self):
        """Test Scikit-Learn ML classifier on NLPAgent."""
        nlp_agent = self.orchestrator.nlp_agent
        res = nlp_agent.handle_message({
            "action": "ml_classify",
            "data": {"text": "Official study proves vaccines reduce severe infection risk."}
        })
        self.assertEqual(res["status"], "success")
        self.assertIn("classification", res)
        self.assertIn("label", res["classification"])
        self.assertIn("confidence", res["classification"])

    def test_11_langgraph_workflow_execution(self):
        """Test LangGraph claim verification graph runner."""
        res = self.orchestrator.handle_message({
            "action": "verify",
            "data": {
                "claim": "Is coffee healthy for heart health?",
                "username": "premium",
                "engine_mode": "LangGraph Stateful Workflow"
            }
        })
        self.assertEqual(res["status"], "success")
        self.assertIn("verdict", res)

    def test_12_autogen_debate_bridge(self):
        """Test AutoGen multi-agent debate bridge execution."""
        res = self.orchestrator.handle_message({
            "action": "verify",
            "data": {
                "claim": "Apple will launch the iPhone 18 in July 2026.",
                "username": "premium",
                "engine_mode": "AutoGen Agent Debate"
            }
        })
        self.assertEqual(res["status"], "success")
        self.assertIn("verdict", res)

    def test_13_live_web_crawler(self):
        """Test live web crawler search and article scraping functionality."""
        from app.utils.web_crawler import WebCrawler
        crawler = WebCrawler()
        articles = crawler.search_and_crawl("James Webb Space Telescope discovery", limit=1)
        self.assertTrue(len(articles) > 0, "Web crawler should return at least 1 live article.")
        art = articles[0]
        self.assertIn("title", art)
        self.assertIn("content", art)
        self.assertIn("url", art)
        self.assertTrue(art["url"].startswith("http"), "Web article must contain a valid HTTP URL.")


if __name__ == '__main__':
    unittest.main()
