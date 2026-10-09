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

from app import config


class TestApi(unittest.TestCase):
    """End-to-end tests for the FastAPI backend that powers the React SPA.

    The suite runs against an isolated temporary database with provider keys
    blanked so verification falls back to the offline heuristic and the real
    data/news_verifier.db is never touched.
    """

    @classmethod
    def setUpClass(cls):
        print("[Test Setup] Creating isolated API test database...")
        cls._tmpdir = tempfile.mkdtemp(prefix="claimshield_api_tests_")
        cls._orig = {
            "sqlite": config.SQLITE_DB_PATH,
            "faiss": config.FAISS_INDEX_PATH,
            "supabase_url": config.SUPABASE_URL,
            "supabase_key": config.SUPABASE_KEY,
            "groq": config.GROQ_API_KEY,
            "gemini": config.GEMINI_API_KEY,
            "env_groq": os.environ.pop("GROQ_API_KEY", None),
            "env_gemini": os.environ.pop("GEMINI_API_KEY", None),
        }
        config.SQLITE_DB_PATH = os.path.join(cls._tmpdir, "test_api.db")
        config.FAISS_INDEX_PATH = os.path.join(cls._tmpdir, "test_faiss_index.bin")
        config.SUPABASE_URL = ""
        config.SUPABASE_KEY = ""
        config.GROQ_API_KEY = ""
        config.GEMINI_API_KEY = ""

        # Import AFTER config isolation: app.api builds its DB/orchestrator
        # singletons at import time.
        import app.api as api
        cls.api = api

        from fastapi.testclient import TestClient
        cls._client_cm = TestClient(api.app)
        cls.client = cls._client_cm.__enter__()  # runs lifespan (auto-seed)
        cls.addClassCleanup(cls._restore_and_cleanup)

    @classmethod
    def _restore_and_cleanup(cls):
        try:
            cls._client_cm.__exit__(None, None, None)
        finally:
            config.SQLITE_DB_PATH = cls._orig["sqlite"]
            config.FAISS_INDEX_PATH = cls._orig["faiss"]
            config.SUPABASE_URL = cls._orig["supabase_url"]
            config.SUPABASE_KEY = cls._orig["supabase_key"]
            config.GROQ_API_KEY = cls._orig["groq"]
            config.GEMINI_API_KEY = cls._orig["gemini"]
            if cls._orig["env_groq"] is not None:
                os.environ["GROQ_API_KEY"] = cls._orig["env_groq"]
            if cls._orig["env_gemini"] is not None:
                os.environ["GEMINI_API_KEY"] = cls._orig["env_gemini"]
            shutil.rmtree(cls._tmpdir, ignore_errors=True)

    # ------------------------------------------------------------------ helpers
    @classmethod
    def _login(cls, username, password):
        res = cls.client.post("/api/auth/login", json={"username": username, "password": password})
        return res

    @classmethod
    def _register(cls, username, password="testpass123", role="user"):
        return cls.client.post(
            "/api/auth/register",
            json={"username": username, "password": password, "role": role},
        )

    @staticmethod
    def _auth(token):
        return {"Authorization": f"Bearer {token}"}

    @staticmethod
    def _unique(prefix):
        return f"{prefix}_{int(time.time() * 1000) % 100000000}"

    def _verify_user_token(self):
        return self._login("user", "password").json()["token"]

    def _refill_tokens(self, username="user"):
        self.api.db.update_user_tokens(username, float(config.RATE_LIMIT_CAPACITY), time.time())

    # ---------------------------------------------------------------- seeding
    def test_01_lifespan_seeds_demo_accounts(self):
        res = self._login("user", "password")
        self.assertEqual(res.status_code, 200, res.text)
        self.assertEqual(res.json()["role"], "user")

    def test_02_login_rejects_bad_password(self):
        res = self._login("user", "wrong-password")
        self.assertEqual(res.status_code, 400)
        self.assertIn("Invalid", res.json()["detail"])

    # ----------------------------------------------------------------- auth
    def test_03_register_and_duplicate(self):
        username = self._unique("apiuser")
        res = self._register(username)
        self.assertEqual(res.status_code, 200, res.text)
        body = res.json()
        self.assertEqual(body["status"], "success")
        self.assertTrue(body["token"])

        dup = self._register(username)
        self.assertEqual(dup.status_code, 400)
        self.assertIn("already exists", dup.json()["detail"])

    def test_04_register_validation(self):
        self.assertEqual(self._register("ab").status_code, 400)
        res = self.client.post(
            "/api/auth/register", json={"username": "validname", "password": "ab"}
        )
        self.assertEqual(res.status_code, 400)

    def test_04b_google_auth(self):
        # Empty credential returns 400
        res = self.client.post("/api/auth/google", json={"credential": ""})
        self.assertEqual(res.status_code, 400)

        # Demo google credential succeeds and creates account
        demo_email = self._unique("google_tester") + "@gmail.com"
        res = self.client.post("/api/auth/google", json={"credential": f"demo_google_{demo_email}"})
        self.assertEqual(res.status_code, 200, res.text)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["email"], demo_email)
        self.assertEqual(data["username"], demo_email)
        self.assertTrue(data["token"])

        # Signing in again with the same credential re-uses existing account
        res2 = self.client.post("/api/auth/google", json={"credential": f"demo_google_{demo_email}"})
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json()["username"], demo_email)

    # --------------------------------------------------------------- profile
    def test_05_profile_requires_auth(self):
        self.assertEqual(self.client.get("/api/user/profile").status_code, 401)

    def test_06_profile_shape(self):
        token = self._verify_user_token()
        res = self.client.get("/api/user/profile", headers=self._auth(token))
        self.assertEqual(res.status_code, 200, res.text)
        body = res.json()
        for key in (
            "username", "role", "is_pro", "tokens", "capacity",
            "refill_rate", "refill_period_hours", "resource_display_limit",
            "claims_verified",
        ):
            self.assertIn(key, body)
        self.assertEqual(body["username"], "user")
        self.assertIsInstance(body["claims_verified"], int)

    def test_07_plan_change(self):
        username = self._unique("planuser")
        token = self._register(username).json()["token"]

        res = self.client.post("/api/user/plan", json={"plan": "pro"}, headers=self._auth(token))
        self.assertEqual(res.status_code, 200, res.text)
        self.assertEqual(res.json()["role"], "pro")
        self.assertTrue(res.json()["token"])

        res = self.client.post("/api/user/plan", json={"plan": "user"}, headers=self._auth(token))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["role"], "user")

    # -------------------------------------------------------------- password
    def test_08_password_change(self):
        username = self._unique("pwduser")
        password = "initial-pass-1"
        token = self._register(username, password).json()["token"]

        wrong = self.client.post(
            "/api/user/password",
            json={"current_password": "nope", "new_password": "new-pass-1"},
            headers=self._auth(token),
        )
        self.assertEqual(wrong.status_code, 400)
        self.assertIn("Current password", wrong.json()["detail"])

        short = self.client.post(
            "/api/user/password",
            json={"current_password": password, "new_password": "ab"},
            headers=self._auth(token),
        )
        self.assertEqual(short.status_code, 400)

        ok = self.client.post(
            "/api/user/password",
            json={"current_password": password, "new_password": "new-pass-1"},
            headers=self._auth(token),
        )
        self.assertEqual(ok.status_code, 200, ok.text)
        self.assertEqual(ok.json()["status"], "success")

        self.assertEqual(self._login(username, password).status_code, 400)
        self.assertEqual(self._login(username, "new-pass-1").status_code, 200)

    # ----------------------------------------------------------------- admin
    def test_09_admin_requires_admin_role(self):
        token = self._verify_user_token()
        self.assertEqual(self.client.get("/api/admin/users", headers=self._auth(token)).status_code, 403)
        self.assertEqual(self.client.get("/api/admin/users").status_code, 401)

    def test_10_admin_member_directory(self):
        token = self._login("newsroom", "newsroom").json()["token"]

        res = self.client.get("/api/admin/users", headers=self._auth(token))
        self.assertEqual(res.status_code, 200, res.text)
        usernames = [u["username"] for u in res.json()["users"]]
        self.assertIn("user", usernames)

        target = self._unique("admuser")
        self._register(target)

        bad_role = self.client.patch(
            "/api/admin/users",
            json={"username": target, "role": "superadmin"},
            headers=self._auth(token),
        )
        self.assertEqual(bad_role.status_code, 400)

        missing = self.client.patch(
            "/api/admin/users",
            json={"username": "no_such_user", "role": "pro"},
            headers=self._auth(token),
        )
        self.assertEqual(missing.status_code, 404)

        ok = self.client.patch(
            "/api/admin/users",
            json={"username": target, "role": "pro"},
            headers=self._auth(token),
        )
        self.assertEqual(ok.status_code, 200, ok.text)
        self.assertEqual(ok.json()["role"], "pro")
        self.assertEqual(self.api.db.get_user(target)["role"], "pro")

    # ----------------------------------------------------------- audit logs
    def test_11_audit_logs_decrypt_details(self):
        token = self._verify_user_token()
        details = {"summary": "The claim is well supported by the evidence.", "entities": []}
        self.api.db.add_log(
            "user", "Sample claim for audit", "Supported", 0.91, json.dumps(details)
        )

        res = self.client.get("/api/audit-logs", headers=self._auth(token))
        self.assertEqual(res.status_code, 200, res.text)
        logs = res.json()["logs"]
        self.assertGreaterEqual(len(logs), 1)
        entry = next(l for l in logs if l["claim"] == "Sample claim for audit")
        self.assertEqual(entry["verdict"], "Supported")
        self.assertIsInstance(entry["details"], dict)
        self.assertIn("supported", entry["details"]["summary"])

    # --------------------------------------------------------------- checkout
    def test_12_checkout_flow(self):
        username = self._unique("buyer")
        token = self._register(username, "buypass123", role="user").json()["token"]

        declined = self.client.post(
            "/api/payment/checkout",
            json={
                "cardholder_name": "Test Buyer",
                "card_number": "5555555555554444",
                "expiry": "12/29",
                "cvv": "123",
                "plan": "pro",
            },
            headers=self._auth(token),
        )
        self.assertEqual(declined.status_code, 400)

        ok = self.client.post(
            "/api/payment/checkout",
            json={
                "cardholder_name": "Test Buyer",
                "card_number": "4242 4242 4242 4242",
                "expiry": "12/29",
                "cvv": "123",
                "plan": "pro",
            },
            headers=self._auth(token),
        )
        self.assertEqual(ok.status_code, 200, ok.text)
        body = ok.json()
        self.assertEqual(body["status"], "success")
        self.assertTrue(body["receipt"]["approved"])
        self.assertTrue(body["token"])
        self.assertEqual(self.api.db.get_user(username)["role"], "pro")

    # ------------------------------------------------------------ export pdf
    def test_13_export_pdf(self):
        res = self.client.post(
            "/api/export-pdf",
            json={"result": {"claim": "The sky is blue", "verdict": "Supported", "confidence": 0.9}},
        )
        self.assertEqual(res.status_code, 200, res.text)
        self.assertEqual(res.headers["content-type"], "application/pdf")
        self.assertTrue(res.content.startswith(b"%PDF"))

    # ----------------------------------------------------------------- verify
    def test_14_verify_returns_result_and_logs(self):
        self._refill_tokens()
        token = self._verify_user_token()

        res = self.client.post(
            "/api/verify",
            json={"claim": "The Great Wall of China is visible from space with the naked eye."},
            headers=self._auth(token),
        )
        self.assertEqual(res.status_code, 200, res.text)
        body = res.json()
        self.assertEqual(body["status"], "success")
        self.assertIn("verdict", body["result"])
        self.assertIn("display_articles", body["result"])
        self.assertIsInstance(body["agent_logs"], list)
        self.assertLessEqual(
            len(body["result"]["display_articles"]),
            body["result"].get("resource_display_limit", 2) or 2,
        )

    def test_15_verify_stream_emits_steps_then_result(self):
        self._refill_tokens()
        token = self._verify_user_token()

        res = self.client.post(
            "/api/verify/stream",
            json={"claim": "Water boils at 100 degrees Celsius at sea level."},
            headers=self._auth(token),
        )
        self.assertEqual(res.status_code, 200, res.text)
        self.assertTrue(res.headers["content-type"].startswith("text/event-stream"))

        events = self._parse_sse(res.text)
        types = [e["type"] for e in events]
        self.assertIn("step", types)
        self.assertEqual(types[-1], "result")
        for event in events:
            if event["type"] == "step":
                self.assertIn("step", event)
                self.assertIn("label", event)
                self.assertIn("detail", event)
        final = events[-1]
        self.assertIn("verdict", final["result"])
        self.assertIsInstance(final["agent_logs"], list)

    def test_16_verify_stream_reports_rate_limit(self):
        token = self._verify_user_token()
        self.api.db.update_user_tokens("user", 0.0, time.time())
        try:
            res = self.client.post(
                "/api/verify/stream",
                json={"claim": "Rate limit probe claim."},
                headers=self._auth(token),
            )
            self.assertEqual(res.status_code, 200, res.text)
            events = self._parse_sse(res.text)
            self.assertEqual(events[-1]["type"], "error")
            self.assertEqual(events[-1]["code"], 429)
        finally:
            self._refill_tokens()

    def test_17_verify_rejects_blank_claim(self):
        self.assertEqual(self.client.post("/api/verify", json={"claim": "   "}).status_code, 400)

    # ---------------------------------------------------------------- voice transcribe
    def test_19_transcribe_rejects_empty_file(self):
        res = self.client.post(
            "/api/transcribe",
            files={"file": ("empty.webm", b"", "audio/webm")}
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("Empty audio file", res.json()["detail"])

    def test_20_transcribe_groq_mocked(self):
        from unittest.mock import patch, AsyncMock
        fake_response = AsyncMock()
        fake_response.status_code = 200
        fake_response.json = lambda: {"text": "Artificial Intelligence is transforming medical science."}

        orig_key = config.GROQ_API_KEY
        config.GROQ_API_KEY = "gsk_test_mock_key"
        try:
            with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = fake_response
                res = self.client.post(
                    "/api/transcribe",
                    files={"file": ("test.webm", b"RIFF....fake_audio_bytes", "audio/webm")}
                )
                self.assertEqual(res.status_code, 200, res.text)
                data = res.json()
                self.assertEqual(data["status"], "success")
                self.assertEqual(data["text"], "Artificial Intelligence is transforming medical science.")
                self.assertIn("Groq Whisper", data["engine"])
        finally:
            config.GROQ_API_KEY = orig_key

    # ---------------------------------------------------------------- health
    def test_21_health(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "ok")

    # ---------------------------------------------------------------- helpers
    @staticmethod
    def _parse_sse(text):
        events = []
        for chunk in text.split("\n\n"):
            chunk = chunk.strip()
            if not chunk.startswith("data: "):
                continue
            payload = chunk[len("data: "):]
            try:
                events.append(json.loads(payload))
            except json.JSONDecodeError:
                raise AssertionError(f"Malformed SSE payload: {payload!r}")
        return events


if __name__ == "__main__":
    unittest.main()
