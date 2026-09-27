import sys
import os
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from io import BytesIO

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from fastapi import FastAPI, HTTPException, Header, Depends, status
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
from ui.payment_gateway import validate_card, process_payment, PLANS

app = FastAPI(
    title="ClaimShield AI — REST API",
    description="Backend API powering ClaimShield AI React SPA",
    version="1.0.0"
)

# Enable CORS for React dev servers and production builds
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared DB and Orchestrator instances
db = DBManager()
orchestrator = Orchestrator()

# Thread-safe pipeline execution helper
import threading
_API_PIPELINE_LOCK = threading.RLock()
_ORIGINAL_BASE_SEND = BaseAgent.send_message

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

class CheckoutRequest(BaseModel):
    cardholder_name: str
    card_number: str
    expiry: str
    cvv: str
    plan: str = "pro"

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
    
    success = db.create_user(username, pwd_hash, role)
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
        "resource_display_limit": 5 if is_pro else 2
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
@app.post("/api/verify")
def verify_claim(req: VerifyRequest, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    claim = req.claim.strip()
    if not claim:
        raise HTTPException(status_code=400, detail="Please enter a claim or question to verify.")
    
    username = current_user["username"] if current_user else "user"
    agent_logs = []

    def trace_agent_message(sender, recipient, action, data, response):
        agent_logs.append({
            "timestamp": time.strftime("%H:%M:%S", time.localtime()),
            "from": sender,
            "to": recipient,
            "action": action,
            "data_sent": data,
            "response_received": response
        })

    def custom_send(self, recipient, action, data):
        resp = _ORIGINAL_BASE_SEND(self, recipient, action, data)
        trace_agent_message(self.name, recipient.name, action, data, resp)
        return resp

    with _API_PIPELINE_LOCK:
        BaseAgent.send_message = custom_send
        try:
            result = orchestrator.handle_message({
                "action": "verify",
                "data": {
                    "claim": claim,
                    "username": username,
                    "engine_mode": req.engine_mode
                }
            })
        finally:
            BaseAgent.send_message = _ORIGINAL_BASE_SEND

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

    # Enforce display slicing based on plan:
    # Free users: 2 resources
    # Pro users: at least 3 (if available) up to 5 max
    is_pro = result.get("is_pro_plan", False)
    articles = result.get("articles", [])
    if is_pro:
        display_articles = articles[:5]
    else:
        display_articles = articles[:2]
    
    result["display_articles"] = display_articles
    result["total_resources_found"] = len(articles)

    return {
        "status": "success",
        "result": result,
        "agent_logs": agent_logs
    }

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
    logs = db.get_audit_logs(username=username, limit=50)
    formatted = []
    for row in logs:
        # Decrypt payload
        details_dec = decrypt_data(row.get("encrypted_details", ""))
        formatted.append({
            "id": row.get("id"),
            "timestamp": row.get("timestamp"),
            "claim": row.get("claim"),
            "verdict": row.get("verdict"),
            "confidence": row.get("confidence"),
            "details": details_dec
        })
    return {"logs": formatted}

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

