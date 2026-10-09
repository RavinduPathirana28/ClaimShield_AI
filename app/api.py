import sys
import os
import json
import time
import secrets
import queue
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from io import BytesIO

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

import httpx
from fastapi import FastAPI, HTTPException, Header, Depends, status, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field

from app.database.db_manager import DBManager
from app.utils.security import (
    verify_jwt,
    generate_jwt,
    hash_password,
    verify_password,
    decrypt_data,
)
from app.agents.orchestrator import Orchestrator
from app.agents.base_agent import BaseAgent
from app import config
from app.generate_pdf import build_verification_report
from app.payment_gateway import validate_card, process_payment, PLANS
import seed_database

# Shared DB and Orchestrator instances
db = DBManager()
orchestrator = Orchestrator()

# Thread-safe pipeline execution helper
_API_PIPELINE_LOCK = threading.RLock()
_ORIGINAL_BASE_SEND = BaseAgent.send_message


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Seed the demo database on first boot so the app works out of the box."""
    if not db.get_all_articles():
        print("[API] Database appears empty. Seeding sample articles and default accounts...")
        seed_database.seed()
    yield


app = FastAPI(
    title="ClaimShield AI — REST API",
    description="Backend API powering ClaimShield AI React SPA",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for React dev servers and production builds
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Pipeline step events (for live SSE progress)
# ---------------------------------------------------------------------------
PIPELINE_STEPS = [
    "Security Check",
    "Parse & Extract",
    "Vector Retrieval",
    "Context & Summaries",
    "Model Consensus",
    "Verdict & Audit",
]

PIPELINE_ACTION_STEPS = {
    "sanitize": 0,
    "check_rate_limit": 0,
    "process_claim": 1,
    "retrieve": 2,
    "summarize": 3,
    "verify_claim": 4,
    "log_audit": 5,
}

PIPELINE_ACTION_DETAIL = {
    "sanitize": "Sanitizing claim input",
    "check_rate_limit": "Token-bucket rate limit check",
    "process_claim": "spaCy NER extraction & query generation",
    "retrieve": "FAISS vector search over the corpus",
    "summarize": "Building extractive evidence summary",
    "verify_claim": "Collecting Groq & Gemini verdicts",
    "log_audit": "Persisting encrypted audit trail",
}

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "user"

class VerifyRequest(BaseModel):
    claim: str
    engine_mode: str = "Standard A2A Protocol"

class PlanChangeRequest(BaseModel):
    plan: str # "user" or "pro"

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

class AdminRoleChangeRequest(BaseModel):
    username: str
    role: str

class CheckoutRequest(BaseModel):
    cardholder_name: str
    card_number: str
    expiry: str
    cvv: str
    plan: str = "pro"

class GoogleAuthRequest(BaseModel):
    credential: str

# ---------------------------------------------------------------------------
# Auth Helper
# ---------------------------------------------------------------------------
def get_current_user(authorization: Optional[str] = Header(None)) -> Optional[Dict[str, Any]]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ")[1]
    payload = verify_jwt(token)
    if not isinstance(payload, dict) or "error" in payload:
        return None
    if "sub" in payload:
        payload["username"] = payload["sub"]
    return payload

def require_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    user = get_current_user(authorization)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid Bearer token required"
        )
    return user

# ---------------------------------------------------------------------------
# Authentication Endpoints
# ---------------------------------------------------------------------------
@app.post("/api/auth/login")
def login(req: LoginRequest):
    username = req.username.strip()
    user = db.get_user(username)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid username or password.")
    
    if not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Invalid username or password.")
    
    token = generate_jwt(username, user["role"])
    return {
        "status": "success",
        "token": token,
        "username": username,
        "role": user["role"],
        "message": f"Welcome back, {username}!"
    }

@app.post("/api/auth/register")
def register(req: RegisterRequest):
    username = req.username.strip()
    if len(username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters.")
    if len(req.password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters.")
    
    role = "pro" if req.role in ["pro", "premium"] else "user"
    pwd_hash = hash_password(req.password)

    try:
        success = db.create_user(username, pwd_hash, role)
    except ValueError:
        success = False
    if not success:
        raise HTTPException(status_code=400, detail="Username already exists. Please choose a different one.")
    
    token = generate_jwt(username, role)
    return {
        "status": "success",
        "token": token,
        "username": username,
        "role": role,
        "message": f"Account created successfully for {username}!"
    }

@app.post("/api/auth/google")
async def google_auth(req: GoogleAuthRequest):
    credential = (req.credential or "").strip()
    if not credential:
        raise HTTPException(status_code=400, detail="Google credential token is required.")

    payload = None

    # 1. Primary: Verify token via Google OAuth2 tokeninfo endpoint
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": credential}
            )
            if resp.status_code == 200:
                payload = resp.json()
    except Exception as e:
        print(f"[Google Auth] Network verification note: {e}")

    # 2. Check audience if Google Client ID is configured
    if payload and "email" in payload:
        if config.GOOGLE_CLIENT_ID and payload.get("aud") != config.GOOGLE_CLIENT_ID:
            raise HTTPException(status_code=400, detail="Google token client ID mismatch.")
    else:
        # Fallback for demo testing / simulated tokens or offline decoding
        try:
            if credential.startswith("demo_google_"):
                raw_email = credential.replace("demo_google_", "") or "demo.user@gmail.com"
                payload = {
                    "email": raw_email,
                    "name": raw_email.split("@")[0].replace(".", " ").title(),
                    "picture": "",
                    "sub": "demo_google_account_123"
                }
            else:
                import jwt as pyjwt
                decoded = pyjwt.decode(credential, options={"verify_signature": False})
                if "email" in decoded:
                    payload = decoded
        except Exception:
            pass

    if not payload or "email" not in payload:
        raise HTTPException(status_code=400, detail="Invalid Google token. Could not verify identity.")

    email = str(payload["email"]).lower().strip()
    name = str(payload.get("name") or email.split("@")[0])
    picture = str(payload.get("picture") or "")

    user = db.get_user(email)
    if not user:
        # Register new Google user with random strong password hash
        random_pass = secrets.token_urlsafe(32)
        pwd_hash = hash_password(random_pass)
        try:
            db.create_user(email, pwd_hash, role="user")
        except ValueError:
            pass
        user = db.get_user(email)

    if not user:
        raise HTTPException(status_code=500, detail="Failed to initialize user session for Google account.")

    token = generate_jwt(user["username"], user["role"])
    return {
        "status": "success",
        "token": token,
        "username": user["username"],
        "role": user["role"],
        "email": email,
        "name": name,
        "picture": picture,
        "message": f"Welcome, {name}!"
    }


# ---------------------------------------------------------------------------
# User Profile & Token Bucket Endpoints
# ---------------------------------------------------------------------------
@app.get("/api/user/profile")
def get_profile(user: Dict[str, Any] = Depends(require_current_user)):
    username = user.get("username") or user.get("sub")
    db_user = db.get_user(username)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    role = db_user["role"]
    is_pro = role in ["pro", "premium", "newsroom_admin"]
    
    # Calculate live token bucket balance
    now = time.time()
    last_time = db_user.get("last_request_time", 0.0)
    curr_tokens = db_user.get("tokens", float(config.RATE_LIMIT_CAPACITY))
    refill = (now - last_time) * (config.RATE_LIMIT_REFILL_AMOUNT / config.RATE_LIMIT_REFILL_PERIOD)
    tokens = min(float(config.RATE_LIMIT_CAPACITY), curr_tokens + refill)
    
    return {
        "username": username,
        "role": role,
        "is_pro": is_pro,
        "tokens": round(tokens, 2),
        "capacity": float(config.RATE_LIMIT_CAPACITY),
        "refill_rate": float(config.RATE_LIMIT_REFILL_AMOUNT),
        "refill_period_hours": 1.0,
        "resource_display_limit": 5 if is_pro else 2,
        "claims_verified": len(db.get_logs_by_user(username)),
    }

@app.post("/api/user/plan")
def change_plan(req: PlanChangeRequest, user: Dict[str, Any] = Depends(require_current_user)):
    username = user["username"]
    target_role = "pro" if req.plan.lower() in ["pro", "premium"] else "user"
    
    db.update_user_role(username, target_role)
    db.update_user_tokens(username, float(config.RATE_LIMIT_CAPACITY), time.time())
    new_token = generate_jwt(username, target_role)
    
    return {
        "status": "success",
        "role": target_role,
        "token": new_token,
        "message": f"Successfully updated plan to {target_role.capitalize()}!"
    }

@app.post("/api/user/password")
def change_password(req: PasswordChangeRequest, user: Dict[str, Any] = Depends(require_current_user)):
    username = user["username"]
    db_user = db.get_user(username)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found.")

    if not verify_password(req.current_password, db_user["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    if len(req.new_password) < 4:
        raise HTTPException(status_code=400, detail="New password must be at least 4 characters.")

    db.update_user_password(username, hash_password(req.new_password))
    return {"status": "success", "message": "Password updated successfully."}

# ---------------------------------------------------------------------------
# Admin: Member Directory & Access Management
# ---------------------------------------------------------------------------
ALLOWED_ROLES = ["user", "pro", "premium", "newsroom_admin"]

def require_admin(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    user = require_current_user(authorization)
    db_user = db.get_user(user.get("username") or user.get("sub"))
    if not db_user or db_user.get("role") != "newsroom_admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return db_user

@app.get("/api/admin/users")
def admin_list_users(_: Dict[str, Any] = Depends(require_admin)):
    users = db.get_all_users()
    return {
        "users": [
            {
                "id": u.get("id"),
                "username": u.get("username"),
                "role": u.get("role"),
                "tokens": u.get("tokens"),
            }
            for u in users
        ]
    }

@app.patch("/api/admin/users")
def admin_update_user_role(req: AdminRoleChangeRequest, _: Dict[str, Any] = Depends(require_admin)):
    if req.role not in ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail=f"Role must be one of: {', '.join(ALLOWED_ROLES)}.")
    target = db.get_user(req.username.strip())
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")

    db.update_user_role(target["username"], req.role)
    return {
        "status": "success",
        "username": target["username"],
        "role": req.role,
        "message": f"{target['username']} is now {req.role}.",
    }

# ---------------------------------------------------------------------------
# Payment Gateway Checkout
# ---------------------------------------------------------------------------
@app.post("/api/payment/checkout")
def checkout(req: CheckoutRequest, user: Dict[str, Any] = Depends(require_current_user)):
    username = user["username"]
    ok, msg = validate_card(req.cardholder_name, req.card_number, req.expiry, req.cvv)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    
    plan_info = PLANS.get(req.plan, PLANS["pro"])
    receipt = process_payment({
        "username": username,
        "plan": req.plan,
        "amount": plan_info["price"],
        "card_number": req.card_number
    })
    
    if receipt.get("approved"):
        db.update_user_role(username, "pro")
        db.update_user_tokens(username, float(config.RATE_LIMIT_CAPACITY), time.time())
        new_token = generate_jwt(username, "pro")
        return {
            "status": "success",
            "receipt": receipt,
            "token": new_token,
            "message": "Payment successful! Your Pro Plan is now active."
        }
    else:
        raise HTTPException(status_code=400, detail=receipt.get("status_reason", "Payment declined."))

# ---------------------------------------------------------------------------
# Verification Pipeline
# ---------------------------------------------------------------------------
def _attach_consensus_metadata(result: Dict[str, Any], submitted_claim: str) -> None:
    """Copy the verification agent's per-model consensus onto the final result.

    The orchestrator does not forward ``agreement_score``/``model_results``, so
    the Streamlit UI read them from ``verification_agent.last_result`` with a
    claim-matching guard — a stale run from a previous verification can never
    leak into this response.
    """
    try:
        last = getattr(orchestrator.verification_agent, "last_result", None) or {}
    except AttributeError:
        return
    last_claim = str(last.get("claim", "")).strip().lower()
    submitted = (submitted_claim or "").strip().lower()
    if not last_claim or (last_claim not in submitted and submitted not in last_claim):
        return
    if "agreement_score" in last:
        result["agreement_score"] = last.get("agreement_score")
    if "model_results" in last:
        result["model_results"] = last.get("model_results") or []


def _execute_verification(
    claim: str,
    username: str,
    engine_mode: str,
    on_step: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    """Run one verification through the orchestrator with A2A message tracing.

    Returns ``{"result": ..., "agent_logs": [...]}``. On success the article
    list is sliced to the caller's plan display limit. ``on_step(action)``
    fires before each inter-agent message so callers can surface live
    pipeline progress while the run is still in flight.
    """
    agent_logs: List[Dict[str, Any]] = []

    def custom_send(self, recipient, action, data):
        if on_step is not None:
            on_step(action)
        resp = _ORIGINAL_BASE_SEND(self, recipient, action, data)
        agent_logs.append({
            "timestamp": time.strftime("%H:%M:%S", time.localtime()),
            "from": self.name,
            "to": recipient.name,
            "action": action,
            "data_sent": data,
            "response_received": resp
        })
        return resp

    with _API_PIPELINE_LOCK:
        BaseAgent.send_message = custom_send
        try:
            result = orchestrator.handle_message({
                "action": "verify",
                "data": {
                    "claim": claim,
                    "username": username,
                    "engine_mode": engine_mode
                }
            })
        finally:
            BaseAgent.send_message = _ORIGINAL_BASE_SEND

    if result.get("status") not in ("rate_limited", "error"):
        _attach_consensus_metadata(result, claim)
        # Enforce display slicing based on plan:
        # Free users: 2 resources; Pro users: at least 3 (if available) up to 5 max
        articles = result.get("articles", [])
        result["display_articles"] = articles[:5] if result.get("is_pro_plan") else articles[:2]
        result["total_resources_found"] = len(articles)

    return {"result": result, "agent_logs": agent_logs}


def _validated_claim(raw_claim: str) -> str:
    claim = (raw_claim or "").strip()
    if not claim:
        raise HTTPException(status_code=400, detail="Please enter a claim or question to verify.")
    return claim


def _sse_event(payload: Dict[str, Any]) -> str:
    return f"data: {json.dumps(payload)}\n\n"


@app.post("/api/verify")
def verify_claim(req: VerifyRequest, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    claim = _validated_claim(req.claim)
    username = current_user["username"] if current_user else "user"

    payload = _execute_verification(claim, username, req.engine_mode)
    result = payload["result"]

    if result.get("status") == "rate_limited":
        raise HTTPException(
            status_code=429,
            detail=result.get("message", "Rate limit exceeded. Please wait or upgrade to Pro.")
        )
    if result.get("status") == "error":
        raise HTTPException(
            status_code=400,
            detail=result.get("message", "Verification failed.")
        )

    return {
        "status": "success",
        "result": result,
        "agent_logs": payload["agent_logs"]
    }


@app.post("/api/verify/stream")
def verify_claim_stream(req: VerifyRequest, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """Server-Sent Events variant of /api/verify.

    Emits ``{"type":"step",...}`` events as each agent message fires, followed
    by exactly one terminal ``result`` or ``error`` event.
    """
    claim = _validated_claim(req.claim)
    username = current_user["username"] if current_user else "user"

    step_queue: queue.Queue = queue.Queue()
    outcome: Dict[str, Any] = {}

    def on_step(action: str) -> None:
        step = PIPELINE_ACTION_STEPS.get(action)
        if step is None:
            return
        step_queue.put({
            "type": "step",
            "step": step,
            "label": PIPELINE_STEPS[step],
            "detail": PIPELINE_ACTION_DETAIL.get(action, "")
        })

    def worker() -> None:
        try:
            outcome.update(_execute_verification(claim, username, req.engine_mode, on_step))
        except Exception as exc:
            outcome["error"] = f"Verification failed: {exc}"
        finally:
            step_queue.put(None)

    def event_stream():
        threading.Thread(target=worker, daemon=True).start()
        while True:
            event = step_queue.get()
            if event is None:
                break
            yield _sse_event(event)

        result = outcome.get("result")
        if outcome.get("error"):
            yield _sse_event({"type": "error", "code": 400, "detail": outcome["error"]})
        elif not isinstance(result, dict):
            yield _sse_event({"type": "error", "code": 500, "detail": "Verification failed."})
        elif result.get("status") == "rate_limited":
            yield _sse_event({
                "type": "error",
                "code": 429,
                "detail": result.get("message", "Rate limit exceeded. Please wait or upgrade to Pro.")
            })
        elif result.get("status") == "error":
            yield _sse_event({
                "type": "error",
                "code": 400,
                "detail": result.get("message", "Verification failed.")
            })
        else:
            yield _sse_event({
                "type": "result",
                "result": result,
                "agent_logs": outcome.get("agent_logs", [])
            })

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

# ---------------------------------------------------------------------------
# PDF Report Export
# ---------------------------------------------------------------------------
@app.post("/api/export-pdf")
def export_pdf(payload: Dict[str, Any]):
    result_data = payload.get("result", payload)
    try:
        pdf_buffer: BytesIO = build_verification_report(result_data)
        pdf_buffer.seek(0)
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=claimshield_verification_report.pdf"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation error: {str(e)}")

# ---------------------------------------------------------------------------
# Audit Logs
# ---------------------------------------------------------------------------
@app.get("/api/audit-logs")
def get_audit_logs(user: Dict[str, Any] = Depends(require_current_user)):
    username = user["username"]
    formatted = []
    for row in db.get_logs_by_user(username):
        raw = row.get("details_json") or ""
        try:
            details = json.loads(decrypt_data(raw))
        except Exception:
            try:
                details = json.loads(raw)
            except Exception:
                details = {}
        formatted.append({
            "id": row.get("id"),
            "timestamp": row.get("timestamp"),
            "claim": row.get("claim"),
            "verdict": row.get("verdict"),
            "confidence": row.get("confidence"),
            "details": details
        })
    return {"logs": formatted}

# ---------------------------------------------------------------------------
# Voice Input: Speech-to-Text Transcription via Groq Whisper AI
# ---------------------------------------------------------------------------
@app.post("/api/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
):
    """
    Transcribe recorded user speech into text using Groq's high-speed Whisper model.
    Accepts webm, wav, mp4, mp3, ogg, or m4a audio files up to 25MB.
    """
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file provided.")
    if len(audio_bytes) > 25 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Audio file exceeds maximum size limit (25 MB).")

    groq_key = (os.environ.get("GROQ_API_KEY") or config.GROQ_API_KEY or "").strip().strip("'").strip('"')
    if not groq_key:
        raise HTTPException(
            status_code=500,
            detail="Groq API key is not configured on the server. Please check your .env configuration.",
        )

    filename = file.filename or "recording.webm"
    if "." not in filename:
        filename = f"{filename}.webm"
    content_type = file.content_type or "audio/webm"

    headers = {"Authorization": f"Bearer {groq_key}"}
    files = {"file": (filename, audio_bytes, content_type)}
    data = {
        "model": "whisper-large-v3-turbo",
        "response_format": "json",
        "temperature": "0.0",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers=headers,
                files=files,
                data=data,
            )
            # If turbo model encounters an issue, fallback to whisper-large-v3
            if resp.status_code != 200:
                fallback_data = dict(data)
                fallback_data["model"] = "whisper-large-v3"
                resp = await client.post(
                    "https://api.groq.com/openai/v1/audio/transcriptions",
                    headers=headers,
                    files={"file": (filename, audio_bytes, content_type)},
                    data=fallback_data,
                )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Network error communicating with Groq Whisper API: {str(exc)}",
        )

    if resp.status_code != 200:
        error_detail = "Voice transcription failed."
        try:
            err_json = resp.json()
            error_detail = err_json.get("error", {}).get("message") or error_detail
        except Exception:
            error_detail = resp.text[:200]
        raise HTTPException(status_code=resp.status_code, detail=error_detail)

    result_json = resp.json()
    transcribed_text = (result_json.get("text") or "").strip()

    return {
        "status": "success",
        "text": transcribed_text,
        "engine": "Groq Whisper (whisper-large-v3-turbo)",
    }

# ---------------------------------------------------------------------------
# Health Check / Status
# ---------------------------------------------------------------------------
@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "system": "ClaimShield AI",
        "version": "1.0.0",
        "active_models": ["Groq (Llama-3.3-70b)", "Google Gemini-2.5", "spaCy en_core_web_sm", "FAISS Index"]
    }

# ---------------------------------------------------------------------------
# Serve React Frontend SPA from frontend/dist
# ---------------------------------------------------------------------------
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

DIST_DIR = ROOT_DIR / "frontend" / "dist"
if DIST_DIR.exists():
    assets_dir = DIST_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
    
    @app.get("/{full_path:path}")
    def serve_frontend_spa(full_path: str):
        if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
            raise HTTPException(status_code=404, detail="Not found")
        target = DIST_DIR / full_path
        if target.is_file():
            return FileResponse(target)
        return FileResponse(DIST_DIR / "index.html")

