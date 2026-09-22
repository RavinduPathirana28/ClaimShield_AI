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
