import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file automatically
load_dotenv()

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

SQLITE_DB_PATH = str(DATA_DIR / "news_verifier.db")
FAISS_INDEX_PATH = str(DATA_DIR / "faiss_index.bin")

# Supabase Configurations
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# LLM Configurations
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_KEY") or ""
GROQ_API_KEY = os.environ.get("GROQ_API_KEY") or ""
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY") or ""
HF_TOKEN = os.environ.get("HF_TOKEN") or ""
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", "")

# Security & JWT
JWT_SECRET = os.environ.get("JWT_SECRET", "super_secret_jwt_key_for_news_verifier_agentic_system_2026")
JWT_EXPIRY_MINUTES = int(os.environ.get("JWT_EXPIRY_MINUTES", "60"))

# Rate Limiting: Token Bucket settings
RATE_LIMIT_CAPACITY = 10  # Max requests
RATE_LIMIT_REFILL_PERIOD = 3600  # 1 hour in seconds
RATE_LIMIT_REFILL_AMOUNT = 5  # Refill 5 tokens per hour

# UI settings
UI_TITLE = "ClaimShield AI — Multi-Agent Fact Checker"
