import time
import json
from app.agents.base_agent import BaseAgent
from app.database.db_manager import DBManager
from app.utils import security
from app import config

class SecurityAgent(BaseAgent):
    """
    Security and Audit Agent. Governs access control, JWT session handling, 
    token-bucket rate limiting, sanitization, and compliance auditing.
    """
    def __init__(self, db: DBManager = None):
        super().__init__("security_agent")
        # Instantiate database manager if not provided
        self.db = db if db is not None else DBManager()

    def handle_message(self, message: dict) -> dict:
        action = message.get("action")
        data = message.get("data", {})
        
        if action == "authenticate":
            return self._authenticate(data)
        elif action == "check_rate_limit":
            return self._check_rate_limit(data)
        elif action == "sanitize":
            return self._sanitize(data)
        elif action == "log_audit":
            return self._log_audit(data)
        else:
            return {
                "sender": self.name,
                "status": "error",
                "message": f"Unknown action: {action}"
            }

    def _authenticate(self, data: dict) -> dict:
        username = data.get("username", "").strip()
        password = data.get("password", "")
        auth_action = data.get("auth_action", "login")  # 'login' or 'register'
        role = data.get("role", "user")

        if not username or not password:
            return {
                "sender": self.name,
                "status": "error",
                "message": "Username and password are required."
            }

        try:
            if auth_action == "register":
                hashed = security.hash_password(password)
                user = self.db.create_user(username, hashed, role)
                token = security.generate_jwt(user["username"], user["role"])
                return {
                    "sender": self.name,
                    "status": "success",
                    "token": token,
                    "user": {
                        "username": user["username"],
                        "role": user["role"]
                    }
                }
            elif auth_action == "login":
                user = self.db.get_user(username)
                if not user or not security.verify_password(password, user["password_hash"]):
                    return {
                        "sender": self.name,
                        "status": "error",
                        "message": "Invalid username or password."
                    }
                token = security.generate_jwt(user["username"], user["role"])
                return {
                    "sender": self.name,
                    "status": "success",
                    "token": token,
                    "user": {
                        "username": user["username"],
                        "role": user["role"]
                    }
                }
            else:
                return {
                    "sender": self.name,
                    "status": "error",
                    "message": f"Unsupported auth_action: {auth_action}"
                }
        except ValueError as e:
            return {
                "sender": self.name,
                "status": "error",
                "message": str(e)
            }
        except Exception as e:
            return {
                "sender": self.name,
                "status": "error",
                "message": f"Internal authentication error: {e}"
            }

    def _check_rate_limit(self, data: dict) -> dict:
        """Implements token-bucket rate limiting based on user subscription tiers."""
        username = data.get("username", "")
        if not username:
            return {
                "sender": self.name,
                "status": "error",
                "message": "Username missing from rate-limit check."
            }

        user = self.db.get_user(username)
        if not user:
            return {
                "sender": self.name,
                "status": "error",
                "message": "User not found."
            }

        # Subscriptions have unlimited limits or higher caps
        role = user.get("role", "user")
        if role in ["premium", "newsroom_admin"]:
            # Premium users are bypassed or have a massive bucket
            return {
                "sender": self.name,
                "status": "success",
                "allowed": True,
                "tokens": 999.0,
                "role": role
            }

        # Token Bucket Algorithm
        now = time.time()
        last_time = user.get("last_request_time", 0.0)
        curr_tokens = user.get("tokens", float(config.RATE_LIMIT_CAPACITY))

        # Refill tokens since last request
        elapsed = now - last_time
        refill = elapsed * (config.RATE_LIMIT_REFILL_AMOUNT / config.RATE_LIMIT_REFILL_PERIOD)
        new_tokens = min(float(config.RATE_LIMIT_CAPACITY), curr_tokens + refill)

        if new_tokens >= 1.0:
            updated_tokens = new_tokens - 1.0
            self.db.update_user_tokens(username, updated_tokens, now)
            return {
                "sender": self.name,
                "status": "success",
                "allowed": True,
                "tokens": updated_tokens,
                "role": role
            }
        else:
            # Not enough tokens
            # Calculate wait time in seconds to reach 1 token
            needed_refill = 1.0 - new_tokens
            wait_seconds = needed_refill / (config.RATE_LIMIT_REFILL_AMOUNT / config.RATE_LIMIT_REFILL_PERIOD)
            return {
                "sender": self.name,
                "status": "success",
                "allowed": False,
                "tokens": new_tokens,
                "retry_after_seconds": int(wait_seconds) + 1,
                "role": role
            }

    def _sanitize(self, data: dict) -> dict:
        text = data.get("text", "")
        clean_text = security.sanitize_input(text)
        return {
            "sender": self.name,
            "status": "success",
            "clean_text": clean_text
        }

    def _log_audit(self, data: dict) -> dict:
        user_id = data.get("user_id", "guest")
        claim = data.get("claim", "")
        verdict = data.get("verdict", "Unclear")
        confidence = data.get("confidence", 0.0)
        details = data.get("details", {})

        try:
            details_json = json.dumps(details)
            log = self.db.add_log(user_id, claim, verdict, confidence, details_json)
            return {
                "sender": self.name,
                "status": "success",
                "log_id": log["id"]
            }
        except Exception as e:
            return {
                "sender": self.name,
                "status": "error",
                "message": f"Audit logging failed: {e}"
            }
