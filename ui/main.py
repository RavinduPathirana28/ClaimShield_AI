import streamlit as st
import sys
import os
import json
import time
import datetime
import html
import textwrap
import importlib
from pathlib import Path

# Add root folder to sys.path to enable app module imports
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

import app.database.db_manager
importlib.reload(app.database.db_manager)
from app.database.db_manager import DBManager

import app.utils.security
importlib.reload(app.utils.security)
from app.utils.security import verify_jwt, decrypt_data, hash_password, verify_password, generate_jwt

from app.agents.orchestrator import Orchestrator
from app.agents.base_agent import BaseAgent
from app import config
import seed_database

_ORIGINAL_BASE_SEND = BaseAgent.send_message

# Page Config
st.set_page_config(
    page_title="ClaimShield AI — Fact Checker & User Management",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS Styles
def load_css():
    css_path = ROOT_DIR / "ui" / "style.css"
    if css_path.exists():
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

def render_html(html_str: str):
    """Renders HTML reliably using st.html (or fallback) without markdown interference."""
    dedented = textwrap.dedent(html_str).strip()
    if hasattr(st, "html"):
        st.html(dedented)
    else:
        st.markdown(dedented, unsafe_allow_html=True)


def pdf_report_bytes(pipeline_result: dict):
    """Builds PDF report bytes for a pipeline result; returns None if reportlab is missing."""
    try:
        from generate_pdf import build_verification_report_bytes
        return build_verification_report_bytes(pipeline_result)
    except Exception as e:
        print(f"[UI] PDF report generation unavailable: {e}")
        return None

# System Initializations
@st.cache_resource
def get_orchestrator():
    return Orchestrator(security_agent=None)  # Uses default subagents

def get_db():
    db_inst = DBManager()
    # Auto-seed SQLite DB if empty to ensure instant out-of-the-box operation
    articles = db_inst.get_all_articles()
    if not articles:
        print("Streamlit: Database appears empty. Seeding sample articles and default accounts...")
        seed_database.seed()
        db_inst = DBManager()
    return db_inst

db = get_db()
orchestrator = get_orchestrator()

# Session State Initialization
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = "user"
if "jwt_token" not in st.session_state:
    st.session_state.jwt_token = None
if "agent_logs" not in st.session_state:
    st.session_state.agent_logs = []
if "current_page" not in st.session_state:
    st.session_state.current_page = "🛡️ Verification Dashboard"

# Header Branding
st.markdown("""
<div style='text-align: center; margin-bottom: 25px;'>
    <h1 style='font-size: 2.8em; margin-bottom: 5px;'>💬 ClaimShield AI</h1>
    <p style='color: #818CF8; font-size: 1.1em; font-weight: 500;'>Instant QA & Fact Verification Engine — Responds to any question in simple, realistic language</p>
</div>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR: Auth, Navigation & Rate Limits -----------------
with st.sidebar:
    if not st.session_state.authenticated:
        st.markdown("### 🔐 User Authentication")
        auth_mode = st.radio("Access Level", ["Login", "Register"], label_visibility="collapsed")
        
        username_in = st.text_input("Username", placeholder="e.g. user, premium, newsroom")
        password_in = st.text_input("Password", type="password", placeholder="password")
        
        role_select = "user"
        if auth_mode == "Register":
            role_select = st.selectbox("Select Subscription Tier", ["user", "premium", "newsroom_admin"])
            
        if st.button(auth_mode, use_container_width=True):
            auth_action = "login" if auth_mode == "Login" else "register"
            
            # Send message to Security Agent via Orchestrator's reference
            auth_msg = {
                "action": "authenticate",
                "data": {
                    "username": username_in,
                    "password": password_in,
                    "auth_action": auth_action,
                    "role": role_select
                }
            }
            
            # Intercept and directly query the security agent for auth
            auth_resp = orchestrator.security_agent.handle_message(auth_msg)
            
            if auth_resp.get("status") == "success":
                st.session_state.authenticated = True
                st.session_state.username = auth_resp["user"]["username"]
                st.session_state.role = auth_resp["user"]["role"]
                st.session_state.jwt_token = auth_resp["token"]
                st.success(f"Welcome back, {st.session_state.username}!")
                st.rerun()
            else:
                st.error(auth_resp.get("message", "Authentication failed."))
                
        st.markdown("---")
        st.info("💡 **Pre-seeded Demo Accounts:**\n- `user` / `password` (Free Reader)\n- `premium` / `premium` (Journalist)\n- `newsroom` / `newsroom` (Enterprise Admin)")
        
    else:
        # User is authenticated
        user_info = db.get_user(st.session_state.username)
        current_role = user_info.get("role", st.session_state.role) if user_info else st.session_state.role
        initial_letter = (st.session_state.username[0].upper()) if st.session_state.username else "U"
        
        role_display = {
            "user": "Free Reader",
            "premium": "Premium Journalist",
            "newsroom_admin": "Newsroom Enterprise"
        }.get(current_role, current_role.upper())

        st.markdown(f"""
        <div class='glass-card' style='padding: 16px; margin-bottom: 15px;'>
            <div style='display: flex; align-items: center; gap: 12px;'>
                <div style='width: 42px; height: 42px; border-radius: 50%; background: linear-gradient(135deg, #6366F1, #A855F7); display: flex; align-items: center; justify-content: center; font-weight: 700; color: white; font-size: 1.2em;'>
                    {initial_letter}
                </div>
                <div>
                    <div style='font-size: 1.1em; font-weight: 700; color: #FFFFFF;'>{st.session_state.username}</div>
                    <div style='font-size: 0.78em; color: #818CF8; font-weight: 600;'>{role_display}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 🧭 Navigation Menu")
        nav_options = [
            "🛡️ Verification Dashboard",
            "👤 Account & Plan Management",
            "📜 System Audit Logs",
            "⚙️ A2A Protocol Monitor",
            "🤖 Responsible AI & Governance"
        ]
        
        # Keep track of active page
        selected_page = st.radio(
            "Go to Page",
            nav_options,
            label_visibility="collapsed",
            index=nav_options.index(st.session_state.current_page) if st.session_state.current_page in nav_options else 0
        )
        st.session_state.current_page = selected_page

        st.markdown("---")
        
        # Display current rate limit tokens (Quick Widget in Sidebar)
        if user_info:
            st.markdown("#### ⚡ Plan Quota")
            if current_role in ["premium", "newsroom_admin"]:
                st.markdown("""
                <div style='background-color: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2); padding: 8px 12px; border-radius: 8px; font-size: 0.82em; color: #34D399; margin-bottom: 12px;'>
                    🚀 Unlimited Access Active
                </div>
                """, unsafe_allow_html=True)
            else:
                now = time.time()
                last_time = user_info.get("last_request_time", 0.0)
                curr_tokens = user_info.get("tokens", 10.0)
                refill = (now - last_time) * (config.RATE_LIMIT_REFILL_AMOUNT / config.RATE_LIMIT_REFILL_PERIOD)
                tokens = min(float(config.RATE_LIMIT_CAPACITY), curr_tokens + refill)
                
                progress_pct = tokens / config.RATE_LIMIT_CAPACITY
                st.progress(min(max(progress_pct, 0.0), 1.0))
                st.caption(f"Tokens: **{tokens:.1f} / {config.RATE_LIMIT_CAPACITY}** (5/hr)")

        st.markdown("---")
        st.markdown("### 🤖 Multi-Agent Engine")
        engine_mode = st.selectbox(
            "Engine Protocol",
            ["Standard A2A Protocol", "LangGraph Stateful Workflow", "AutoGen Agent Debate"],
            help="Choose between standard in-process A2A protocol, LangGraph stateful graph execution, or the multi-agent persona debate (FactChecker → Critic → Consensus)."
        )
        st.session_state.engine_mode = engine_mode

        if st.button("Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.role = "user"
            st.session_state.jwt_token = None
            st.session_state.agent_logs = []
            st.session_state.current_page = "🛡️ Verification Dashboard"
            st.rerun()

# ----------------- MAIN INTERFACE -----------------
if not st.session_state.authenticated:
    # Landing Page for unauthenticated visitors
    landing_tabs = st.tabs(["✨ Overview & Capabilities", "💎 Subscription Plans", "🤖 Responsible AI"])
    
    with landing_tabs[0]:
        st.markdown("""
        <div class='glass-card' style='text-align: center; padding: 40px;'>
            <h2 style='color: #818CF8;'>🛡️ Shield Your Journalism Today</h2>
            <p style='margin-bottom: 25px; color: #94A3B8; font-size: 1.1em;'>Create a secure account or login from the sidebar to access our real-time multi-agent claim verification system.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🌟 System Architecture Highlights")
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            st.markdown("""
            <div class='glass-card'>
                <h4 style='color: #818CF8;'>🧠 Multi-Agent Network</h4>
                <p style='color: #CBD5E1; font-size: 0.9em; line-height: 1.6;'>
                    Orchestrated collaboration between Security, NLP, Retrieval, Verification, and Explainer agents via A2A/1.0 protocol.
                </p>
            </div>
            """, unsafe_allow_html=True)
        with col_f2:
            st.markdown("""
            <div class='glass-card'>
                <h4 style='color: #38BDF8;'>⚡ Vector RAG & FAISS</h4>
                <p style='color: #CBD5E1; font-size: 0.9em; line-height: 1.6;'>
                    Semantic vector similarity retrieval over trusted news repositories with cosine ranking and direct source citations.
                </p>
            </div>
            """, unsafe_allow_html=True)
        with col_f3:
            st.markdown("""
            <div class='glass-card'>
                <h4 style='color: #10B981;'>🔒 Enterprise Security</h4>
                <p style='color: #CBD5E1; font-size: 0.9em; line-height: 1.6;'>
                    PBKDF2-SHA256 password hashing, signed JWT session tokens, token-bucket rate limiting, and encrypted audit trails.
                </p>
            </div>
            """, unsafe_allow_html=True)

    with landing_tabs[1]:
        st.markdown("### 💎 Subscription & Pricing Tiers")
        col1, col2, col3 = st.columns(3)
        with col1:
            render_html("""
            <div class='plan-card'>
                <div>
                    <h4>Standard Tier</h4>
                    <div class='plan-price-tag' style='color: #94A3B8;'>&#36;0</div>
                    <p style='color: #94A3B8; font-size: 0.85em;'>Ideal for individual researchers</p>
                    <ul class='plan-feature-list'>
                        <li>10 claim checks capacity</li>
                        <li>Refills 5 tokens / hour</li>
                        <li>Standard NLP & FAISS index</li>
                        <li>Encrypted audit logging</li>
                    </ul>
                </div>
            </div>
            """)
        with col2:
            render_html("""
            <div class='plan-card' style='border: 1px solid #6366F1;'>
                <div class='plan-popular-tag'>Popular</div>
                <div>
                    <h4>Premium Reader</h4>
                    <div class='plan-price-tag' style='color: #818CF8;'>&#36;19<span style='font-size: 0.45em; color: #94A3B8;'>/mo</span></div>
                    <p style='color: #94A3B8; font-size: 0.85em;'>Ideal for content writers & journalists</p>
                    <ul class='plan-feature-list'>
                        <li><strong>Unlimited</strong> claim checks</li>
                        <li>Priority LLM access queue</li>
                        <li>Retrieval expansion (Top 5)</li>
                        <li>Multi-Agent Persona Debate (FactChecker → Critic → Consensus)</li>
                    </ul>
                </div>
            </div>
            """)
        with col3:
            render_html("""
            <div class='plan-card'>
                <div>
                    <h4>Newsroom Enterprise</h4>
                    <div class='plan-price-tag' style='color: #10B981;'>&#36;49<span style='font-size: 0.45em; color: #94A3B8;'>/mo</span></div>
                    <p style='color: #94A3B8; font-size: 0.85em;'>For agencies & news outlets</p>
                    <ul class='plan-feature-list'>
                        <li><strong>Unlimited</strong> claim checks</li>
                        <li>Multi-seat team management</li>
                        <li>Advanced historical audit trails</li>
                        <li>LangGraph stateful workflow</li>
                    </ul>
                </div>
            </div>
            """)

    with landing_tabs[2]:
        st.markdown("### 🤖 Responsible AI — Ethics & Governance")
        st.markdown("ClaimShield AI enforces fairness, explainability, transparency, and data protection across all tiers.")

else:
    # =========================================================================
    # AUTHENTICATED USER PAGES
    # =========================================================================

    # -------------------------------------------------------------------------
    # PAGE 1: CLAIM VERIFICATION DASHBOARD
    # -------------------------------------------------------------------------
    if st.session_state.current_page == "🛡️ Verification Dashboard":
        st.markdown("### 🔍 Ask a Question or Verify a Claim")
        st.markdown("Type any general question or factual statement below. Our multi-agent AI system will evaluate it and provide a realistic, easy-to-understand explanation.")

        # Preset sample query buttons for quick testing
        st.markdown("**Sample Questions & Claims:**")
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        sample_query = None
        with col_s1:
            if st.button("🤖 What is AI?", use_container_width=True):
                sample_query = "What is Artificial Intelligence?"
        with col_s2:
            if st.button("📱 iPhone 18 in 2026?", use_container_width=True):
                sample_query = "Apple will launch the iPhone 18 in July 2026."
        with col_s3:
            if st.button("🌌 Why is sky blue?", use_container_width=True):
                sample_query = "Why is the sky blue?"
        with col_s4:
            if st.button("☕ Is coffee healthy?", use_container_width=True):
                sample_query = "Is drinking coffee good for heart health?"

        if "claim_text_val" not in st.session_state:
            st.session_state.claim_text_val = ""
        if sample_query:
            st.session_state.claim_text_val = sample_query

        claim_input = st.text_area(
            "Query or Claim Input", 
            value=st.session_state.claim_text_val,
            placeholder="e.g. 'What is quantum computing?', 'Why is the sky blue?', or 'Apple will launch iPhone 18 in July 2026'",
            label_visibility="collapsed",
            height=100
        )
        
        col_btn, col_info = st.columns([1, 4])
        with col_btn:
            submit_fact = st.button("Run ClaimShield AI")
        with col_info:
            st.caption("Supports general knowledge questions as well as factual news verification.")

        if submit_fact:
            if not claim_input.strip():
                st.warning("Please type a question or statement first.")
            else:
                with st.spinner("Multi-Agent Verification & QA Pipeline executing..."):
                    st.session_state.agent_logs = []
                    
                    def trace_agent_message(sender, recipient, action, data, response):
                        log_entry = {
                            "timestamp": time.strftime("%H:%M:%S", time.localtime()),
                            "from": sender,
                            "to": recipient,
                            "action": action,
                            "data_sent": data,
                            "response_received": response
                        }
                        st.session_state.agent_logs.append(log_entry)
                    
                    def custom_send(self, recipient, action, data):
                        resp = _ORIGINAL_BASE_SEND(self, recipient, action, data)
                        trace_agent_message(self.name, recipient.name, action, data, resp)
                        return resp
                    BaseAgent.send_message = custom_send
                    
                    selected_engine = st.session_state.get("engine_mode", "Standard A2A Protocol")
                    orchestrator_req = {
                        "action": "verify",
                        "data": {
                            "claim": claim_input,
                            "username": st.session_state.username,
                            "engine_mode": selected_engine
                        }
                    }
                    
                    pipeline_start_time = time.time()
                    try:
                        pipeline_result = orchestrator.handle_message(orchestrator_req)
                    finally:
                        BaseAgent.send_message = _ORIGINAL_BASE_SEND
                    pipeline_end_time = time.time()
                    
                    if pipeline_result.get("status") == "rate_limited":
                        st.error(pipeline_result.get("message"))
                        st.info(f"Please wait {pipeline_result.get('retry_after_seconds')} seconds, or upgrade to a Premium account on the Account page.")
                    elif pipeline_result.get("status") == "success":
                        st.markdown("### 📊 AI Analysis Report")
                        
                        verdict = pipeline_result["verdict"]
                        confidence = pipeline_result["confidence"]
                        straight_ans = pipeline_result.get("straight_answer", "")
                        summary = pipeline_result["summary"]
                        entities = pipeline_result.get("entities", [])
                        citations = pipeline_result.get("citations", [])
                        engine = pipeline_result.get("engine", "Unknown")
                        ret_articles = pipeline_result.get("articles", [])

                        # Per-model consensus metadata from the verification agent's latest run
                        agreement_score = None
                        model_breakdown = []
                        try:
                            last_result = getattr(orchestrator.verification_agent, "last_result", None)
                            lc = (last_result or {}).get("claim", "").strip().lower()
                            pc = pipeline_result.get("claim", "").strip().lower()
                            if lc and (lc == pc or lc in pc or pc in lc):
                                agreement_score = (last_result or {}).get("agreement_score")
                                model_breakdown = (last_result or {}).get("model_results", []) or []
                        except Exception:
                            pass
                        
                        v_class = "verdict-unclear"
                        verdict_display = verdict
                        if verdict in ["Supported", "True"]:
                            v_class = "verdict-supported"
                            verdict_display = "✅ Verified True"
                        elif verdict in ["Contradicted", "False"]:
                            v_class = "verdict-contradicted"
                            verdict_display = "❌ Debunked / False"
                        elif verdict in ["Answered", "General Info"]:
                            v_class = "verdict-answered"
                            verdict_display = "💬 Direct Answer"
                        elif verdict in ["Unverified", "Unclear"]:
                            v_class = "verdict-unclear"
                            verdict_display = "❓ Unverified"

                        if not straight_ans:
                            straight_ans = summary.split(". ")[0] + "." if summary else verdict_display
                            
                        # 1. Straight Answer Section
                        st.markdown(f"""
                        <div class="glass-card" style="border-left: 6px solid #6366F1; background: rgba(99, 102, 241, 0.1);">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                <div class="verdict-badge {v_class}">{verdict_display}</div>
                                <div>
                                    <span style="font-size: 0.85em; color: #94A3B8;">Confidence Metric:</span>
                                    <span style="font-size: 1.1em; font-weight: 700; color: #FFFFFF; margin-left: 5px;">{int(confidence*100)}%</span>
                                </div>
                            </div>
                            <div style="font-size: 0.85em; color: #818CF8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 5px;">
                                🎯 Straight Answer
                            </div>
                            <h3 style="margin-top: 0; color: #FFFFFF; font-size: 1.3em;">{straight_ans}</h3>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # 2. Detailed Explanation Section
                        st.markdown(f"""
                        <div class="glass-card">
                            <div style="font-size: 0.85em; color: #38BDF8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">
                                📖 Detailed Explanation
                            </div>
                            <p style="font-size: 1.05em; line-height: 1.6; color: #E2E8F0; margin-bottom: 15px;">{summary}</p>
                            <div style="font-size: 0.8em; color: #64748B;">
                                Processing Engine: <strong>{engine}</strong> | Execution Time: {pipeline_end_time - pipeline_start_time:.2f}s
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # 2b. Multi-Model Consensus & Explainability
                        verdict_icons = {"Supported": "✅", "Contradicted": "❌", "Answered": "💬", "Unverified": "❓"}
                        verdict_colors = {"Supported": "#10B981", "Contradicted": "#EF4444", "Answered": "#818CF8", "Unverified": "#F59E0B"}
                        provider_dots = {"Groq": "#F55036", "Gemini": "#4285F4", "Ollama": "#29BEB0"}

                        def esc(s):
                            return html.escape(str(s or ""), quote=True)

                        consensus_body = ""
                        if model_breakdown:
                            row_html = []
                            for mr in model_breakdown:
                                eng = mr.get("engine", "LLM") or "LLM"
                                prov = next((p for p in ("Groq", "Gemini", "Ollama") if p in eng), "LLM")
                                dot = provider_dots.get(prov, "#94A3B8")
                                v = mr.get("verdict", "Unverified")
                                vcolor = verdict_colors.get(v, "#F59E0B")
                                conf = int(mr.get("confidence", 0) * 100)
                                snippet = (mr.get("straight_answer") or mr.get("summary") or "").strip()
                                if len(snippet) > 200:
                                    snippet = snippet[:200].rsplit(" ", 1)[0] + "…"
                                snippet_html = f'<div class="cs-model-snippet">“{esc(snippet)}”</div>' if snippet else ""
                                row_html.append(f"""
                                <div class="cs-model-row">
                                    <div class="cs-model-head">
                                        <div class="cs-model-name"><span class="cs-provider-dot" style="background:{dot}"></span>{esc(eng)}</div>
                                        <span class="cs-model-badge" style="color:{vcolor}; background:{vcolor}1f; border:1px solid {vcolor}55;">{verdict_icons.get(v, "❓")} {v}</span>
                                    </div>
                                    <div class="cs-conf-track"><div class="cs-conf-fill" style="width:{min(max(conf, 4), 100)}%; background:linear-gradient(90deg,{vcolor},{dot});"></div></div>
                                    <div class="cs-conf-note">{conf}% confidence</div>
                                    {snippet_html}
                                </div>""")
                            consensus_body = "".join(row_html)
                        else:
                            consensus_body = """
                                <div class="cs-fallback-note">
                                    <strong>No live LLM models were available.</strong> This verdict was produced by the
                                    built-in Local Heuristic Engine. Add working Groq / Gemini API keys or start Ollama
                                    to see the per-model comparison below.
                                </div>"""

                        agreement_html = ""
                        if agreement_score is not None:
                            agr_pct = int(agreement_score * 100)
                            converged = agreement_score >= 0.7
                            fill_color = "linear-gradient(90deg,#10B981,#38BDF8)" if converged else "linear-gradient(90deg,#F59E0B,#EF4444)"
                            note_color = "#10B981" if converged else "#F59E0B"
                            note_text = ("✓ The models converged on this verdict." if converged
                                         else "⚠ The models diverged — treat this verdict with lower confidence.")
                            agreement_html = f"""
                            <div class="cs-agreement-box">
                                <div class="cs-agreement-label">
                                    <span style="font-size:0.85em; color:#94A3B8; font-weight:600; text-transform:uppercase; letter-spacing:0.04em;">Cross-Model Agreement</span>
                                    <span style="font-size:1.4em; font-weight:700; color:#FFFFFF;">{agr_pct}%</span>
                                </div>
                                <div class="cs-agreement-track"><div class="cs-conf-fill" style="width:{agr_pct}%; background:{fill_color};"></div></div>
                                <div class="cs-agreement-note" style="border-left:4px solid {note_color};">{note_text}</div>
                            </div>"""

                        render_html(f"""
                        <div class="glass-card" style="border-left: 4px solid #F59E0B;">
                            <div style="font-size: 0.85em; color: #F59E0B; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px;">
                                🤝 Multi-Model Consensus &amp; Explainability
                            </div>
                            {consensus_body}
                            {agreement_html}
                            <div style="font-size: 0.75em; color: #64748B; margin-top: 12px;">
                                Each model evaluates the same evidence independently; the verdict reflects their weighted consensus.
                            </div>
                        </div>
                        """)

                        # 2c. Downloadable PDF verification report
                        try:
                            report_bytes = pdf_report_bytes({**pipeline_result, "agreement_score": agreement_score})
                            if report_bytes:
                                st.download_button(
                                    "📄 Download Verification Report (PDF)",
                                    data=report_bytes,
                                    file_name=f"claimshield_report_{time.strftime('%Y%m%d_%H%M%S')}.pdf",
                                    mime="application/pdf",
                                )
                            else:
                                st.caption("PDF report unavailable — install 'reportlab' (pip install reportlab).")
                        except Exception as e:
                            st.caption(f"PDF report unavailable: {e}")

                        # Evidence Summary
                        ev_summary = pipeline_result.get("evidence_summary", "")
                        if ev_summary:
                            st.markdown(f"""
                            <div class="glass-card" style="border-left: 4px solid #818CF8;">
                                <div style="font-size: 0.85em; color: #818CF8; font-weight: 600; margin-bottom: 8px;">📝 Extractive Evidence Highlights</div>
                                <p style="font-size: 1.0em; line-height: 1.6; color: #E2E8F0;">{ev_summary}</p>
                            </div>
                            """, unsafe_allow_html=True)

                        # Scikit-Learn ML Stance
                        ml_info = pipeline_result.get("ml_classification", {})
                        if ml_info:
                            st.markdown(f"""
                            <div class="glass-card" style="border-left: 4px solid #10B981;">
                                <div style="font-size: 0.85em; color: #10B981; font-weight: 600; margin-bottom: 4px;">⚡ Scikit-Learn ML Credibility Analysis</div>
                                <div>Prediction Label: <strong>{ml_info.get('label', 'N/A')}</strong> | Confidence: <strong>{int(ml_info.get('confidence', 0)*100)}%</strong></div>
                                <div style="font-size: 0.8em; color: #64748B;">Engine: {ml_info.get('engine', 'TF-IDF Vectorizer')}</div>
                            </div>
                            """, unsafe_allow_html=True)

                        # Persona Debate Transcript
                        autogen_info = pipeline_result.get("autogen_debate", {})
                        if autogen_info:
                            stage_cfg = {
                                "FactCheckerAgent": {"icon": "🔍", "label": "Fact Checker", "color": "#38BDF8"},
                                "CriticAgent": {"icon": "⚖️", "label": "Critic", "color": "#F59E0B"},
                                "ConsensusAgent": {"icon": "🎯", "label": "Consensus", "color": "#10B981"},
                            }
                            turn_html = []
                            for msg in autogen_info.get("debate_log", []):
                                agent = msg.get("agent", "")
                                cfg = stage_cfg.get(agent, {"icon": "💬", "label": agent or "Agent", "color": "#94A3B8"})
                                color = cfg["color"]
                                model_badge = ""
                                if msg.get("model"):
                                    model_badge = (f'<span class="cs-debate-verdict" style="color:#E2E8F0; background:rgba(255,255,255,0.06); '
                                                   f'border:1px solid rgba(255,255,255,0.12);">{esc(msg["model"])}</span>')
                                verdict_badge = ""
                                if msg.get("verdict"):
                                    vcolor = verdict_colors.get(msg["verdict"], "#94A3B8")
                                    verdict_badge = (f'<span class="cs-debate-verdict" style="color:{vcolor}; background:{vcolor}1f; '
                                                     f'border:1px solid {vcolor}55;">{verdict_icons.get(msg["verdict"], "❓")} {esc(msg["verdict"])}</span>')
                                conf_badge = ""
                                if msg.get("confidence") is not None:
                                    conf_badge = (f'<span style="font-size:0.75em; color:#94A3B8; font-weight:600;">{int(msg["confidence"])}% confidence</span>')
                                turn_html.append(f"""
                                <div class="cs-debate-turn" style="border-left: 4px solid {color};">
                                    <div class="cs-debate-head">
                                        <span class="cs-debate-stage" style="color:{color}; background:{color}1f; border:1px solid {color}55;">{cfg["icon"]} {cfg["label"]}</span>
                                        {model_badge}
                                        {verdict_badge}
                                        {conf_badge}
                                    </div>
                                    <div class="cs-debate-message">{esc(msg.get("message", ""))}</div>
                                </div>""")

                            consensus_verdict = autogen_info.get("consensus") or autogen_info.get("message", "")
                            consensus_box = f"""
                            <div class="cs-consensus-box">
                                <div class="cs-consensus-title">🎯 Final Consensus</div>
                                <div class="cs-consensus-text">{esc(consensus_verdict)}</div>
                            </div>"""

                            with st.expander("🗣️ Multi-Agent Debate Transcript", expanded=True):
                                render_html(f"""
                                <div style="font-size: 0.85em; color: #64748B; margin-bottom: 12px;">
                                    Fueled by <strong style="color: #94A3B8;">{esc(autogen_info.get("engine"))}</strong> — every statement is grounded in an actual model response, never fabricated.
                                </div>
                                """)
                                render_html("".join(turn_html) + consensus_box)

                        # Columns for concepts & quotes
                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown("#### 🏷️ Key Extracted Concepts (spaCy NER)")
                            if entities:
                                for ent in entities:
                                    st.markdown(f"""
                                    <span class='verdict-badge badge-secondary' style='margin-right: 5px; margin-bottom: 5px;'>
                                        <strong>{ent['text']}</strong> ({ent['label']})
                                    </span>
                                    """, unsafe_allow_html=True)
                            else:
                                st.caption("No specific named entities extracted.")
                                
                        with c2:
                            st.markdown("#### 📌 Key Takeaways & Quotes")
                            if citations:
                                for cit in citations:
                                    art_label = f"Article #{cit['article_id']}" if 'article_id' in cit else "General Evidence"
                                    st.markdown(f"""
                                    <div class="citation-box">
                                        <div style="font-size: 0.85em; font-weight: 600; color: #C084FC; margin-bottom: 5px;">
                                            {art_label}:
                                        </div>
                                        <div style="font-style: italic; font-size: 0.9em; margin-bottom: 8px; color: #E2E8F0;">
                                            "{cit['quote']}"
                                        </div>
                                        <div style="font-size: 0.8em; color: #94A3B8;">
                                            <strong>Insight:</strong> {cit['explanation']}
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                            else:
                                st.caption("No additional citations required for this response.")
                                
                        # Referenced Links
                        st.markdown("---")
                        st.markdown("### 🔗 Referenced Sources & Verified Article Links")
                        if ret_articles:
                            live_web_articles = [a for a in ret_articles if "Live Web" in a.get("source", "")]
                            db_articles = [a for a in ret_articles if "Live Web" not in a.get("source", "")]
                            article_dates = [a.get("date", "") for a in ret_articles if a.get("date")]
                            newest_date = max(article_dates) if article_dates else "unknown"
                            render_html(f"""
                            <div style="font-size: 0.82em; color: #94A3B8; background: rgba(15, 23, 42, 0.5); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 8px; padding: 8px 12px; margin-bottom: 12px;">
                                🧾 <strong style="color:#CBD5E1;">Evidence used for this verdict:</strong> {len(ret_articles)} source(s) — {len(db_articles)} from local knowledge base · {len(live_web_articles)} from live web · newest article: {newest_date}
                            </div>
                            """)
                            if live_web_articles:
                                st.markdown("The following live web sources were matched against the claim:")
                            else:
                                st.markdown("The following source articles were retrieved and cross-referenced by FAISS vector similarity:")
                            for idx, art in enumerate(ret_articles):
                                url_link = art.get('url', '#')
                                st.markdown(f"""
                                <div class="article-card" style="border-left: 4px solid #38BDF8;">
                                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                                        <div class="article-title" style="font-size: 1.1em; font-weight: 700; color: #F8FAFC;">
                                            [{idx+1}] {art['title']}
                                        </div>
                                        <span class="badge-secondary" style="font-size: 0.8em; padding: 2px 8px; border-radius: 4px;">
                                            Score: {art['score']:.4f}
                                        </span>
                                    </div>
                                    <div class="article-meta" style="margin-top: 4px; margin-bottom: 8px; color: #94A3B8; font-size: 0.85em;">
                                        📰 <strong>Source:</strong> {art['source']} | 📅 <strong>Date:</strong> {art['date']}
                                    </div>
                                    <div style="font-size: 0.9em; color: #CBD5E1; line-height: 1.5; margin-bottom: 10px;">
                                        {art['content']}
                                    </div>
                                    <div style="background: rgba(15, 23, 42, 0.6); padding: 8px 12px; border-radius: 6px; font-size: 0.85em;">
                                        🔗 <strong>Verified Link:</strong> <a href="{url_link}" target="_blank" style="color: #38BDF8; font-weight: 600; text-decoration: underline;">{url_link}</a>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.info("💡 General knowledge query: No local database links were required. Answer generated using internal facts.")
                            
                    else:
                        st.error(f"Fact checking pipeline failed: {pipeline_result.get('message')}")

    # -------------------------------------------------------------------------
    # PAGE 2: USER ACCOUNT & PLAN MANAGEMENT (DEDICATED PAGE)
    # -------------------------------------------------------------------------
    elif st.session_state.current_page == "👤 Account & Plan Management":
        st.markdown("## 👤 User Account & Subscription Management")
        st.markdown("Manage your profile, monitor real-time token quotas, and switch subscription plans seamlessly.")

        # Fetch latest user data from DB
        user_info = db.get_user(st.session_state.username)
        current_role = user_info.get("role", st.session_state.role) if user_info else st.session_state.role
        user_logs = db.get_logs_by_user(st.session_state.username)
        total_checks = len(user_logs)
        initial_letter = (st.session_state.username[0].upper()) if st.session_state.username else "U"

        role_display = {
            "user": "Free Reader",
            "premium": "Premium Journalist",
            "newsroom_admin": "Newsroom Enterprise"
        }.get(current_role, current_role.upper())

        # 1. Profile Banner
        render_html(f"""
        <div class='user-profile-header'>
            <div class='avatar-badge'>
                {initial_letter}
            </div>
            <div style='flex-grow: 1;'>
                <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 4px;'>
                    <h2 style='margin: 0; font-size: 1.8em; color: #FFFFFF;'>{st.session_state.username}</h2>
                    <span class='user-status-pill status-active'>
                        <span class='status-indicator-dot'></span> Active Session
                    </span>
                </div>
                <div style='color: #94A3B8; font-size: 0.95em;'>
                    Subscription Tier: <strong style='color: #818CF8;'>{role_display}</strong> | Authentication: <strong style='color: #34D399;'>JWT Signed (HS256)</strong>
                </div>
            </div>
        </div>
        """)

        # 2. Key Metrics Row
        m1, m2, m3 = st.columns(3)
        with m1:
            render_html(f"""
            <div class='quota-card'>
                <div class='quota-metric-label'>Current Active Tier</div>
                <div class='quota-metric-value' style='color: #818CF8;'>{role_display}</div>
                <div style='font-size: 0.82em; color: #64748B;'>Unlimited / Standard Rate Limits</div>
            </div>
            """)
            
        with m2:
            if current_role in ["premium", "newsroom_admin"]:
                render_html("""
                <div class='quota-card'>
                    <div class='quota-metric-label'>Verification Quota</div>
                    <div class='quota-metric-value' style='color: #10B981;'>Unlimited ∞</div>
                    <div style='font-size: 0.82em; color: #10B981;'>Rate Limit Bypassed</div>
                </div>
                """)
            else:
                now = time.time()
                last_time = user_info.get("last_request_time", 0.0) if user_info else 0.0
                curr_tokens = user_info.get("tokens", 10.0) if user_info else 10.0
                refill = (now - last_time) * (config.RATE_LIMIT_REFILL_AMOUNT / config.RATE_LIMIT_REFILL_PERIOD)
                tokens = min(float(config.RATE_LIMIT_CAPACITY), curr_tokens + refill)
                
                render_html(f"""
                <div class='quota-card'>
                    <div class='quota-metric-label'>Remaining Tokens</div>
                    <div class='quota-metric-value' style='color: #38BDF8;'>{tokens:.1f} <span style='font-size: 0.5em; color: #94A3B8;'>/ 10</span></div>
                    <div style='font-size: 0.82em; color: #64748B;'>Refills 5 tokens / hour</div>
                </div>
                """)

        with m3:
            render_html(f"""
            <div class='quota-card'>
                <div class='quota-metric-label'>Lifetime Claims Verified</div>
                <div class='quota-metric-value' style='color: #C084FC;'>{total_checks}</div>
                <div style='font-size: 0.82em; color: #64748B;'>Recorded in Encrypted Audit Trail</div>
            </div>
            """)

        st.markdown("---")

        # 3. Real-Time Token & Quota Management Section
        st.markdown("### ⚡ Real-Time Plan Quotas & Token Bucket Status")
        st.markdown("ClaimShield AI enforces a token-bucket rate limiting algorithm. Standard users refill tokens gradually over time, while Premium and Newsroom tiers enjoy unlimited high-concurrency access.")

        if current_role in ["premium", "newsroom_admin"]:
            render_html(f"""
            <div class='glass-card' style='border-left: 6px solid #10B981; background: rgba(16, 185, 129, 0.08);'>
                <h4 style='color: #10B981; margin-top: 0;'>🚀 Unlimited Verification Quota Active</h4>
                <p style='color: #CBD5E1; line-height: 1.6; margin-bottom: 0;'>
                    Your account is subscribed to <strong>{role_display}</strong>. You have zero request throttles, priority execution in the verification queue, and direct access to multi-agent debate pipelines.
                </p>
            </div>
            """)
        else:
            # Free user live token simulation & progress bar
            now = time.time()
            last_time = user_info.get("last_request_time", 0.0) if user_info else 0.0
            curr_tokens = user_info.get("tokens", 10.0) if user_info else 10.0
            refill = (now - last_time) * (config.RATE_LIMIT_REFILL_AMOUNT / config.RATE_LIMIT_REFILL_PERIOD)
            tokens = min(float(config.RATE_LIMIT_CAPACITY), curr_tokens + refill)
            
            progress_val = min(max(tokens / config.RATE_LIMIT_CAPACITY, 0.0), 1.0)
            
            # Quota Box
            q_col1, q_col2 = st.columns([3, 2])
            with q_col1:
                st.markdown(f"**Token Capacity Utilization ({tokens:.1f} / {config.RATE_LIMIT_CAPACITY} available)**")
                st.progress(progress_val)
                st.caption(f"Refill rate: **{config.RATE_LIMIT_REFILL_AMOUNT} tokens per hour** ({config.RATE_LIMIT_REFILL_PERIOD/config.RATE_LIMIT_REFILL_AMOUNT:.0f} seconds per token).")
            
            with q_col2:
                if tokens < config.RATE_LIMIT_CAPACITY:
                    needed = config.RATE_LIMIT_CAPACITY - tokens
                    seconds_to_full = needed * (config.RATE_LIMIT_REFILL_PERIOD / config.RATE_LIMIT_REFILL_AMOUNT)
                    mins_to_full = int(seconds_to_full / 60)
                    st.info(f"⏳ Estimated time until 100% capacity: **~{mins_to_full} minutes**.")
                else:
                    st.success("✅ Your token bucket is currently at **100% full capacity**.")



        st.markdown("---")

        # 4. Plan Changing & Subscription Switcher
        st.markdown("### 💎 Subscription Tier & Plan Switcher")
        st.markdown("Switch between plans instantly with real-time role updates and quota privileges.")

        p_col1, p_col2, p_col3 = st.columns(3)

        # Plan 1: Free Reader
        with p_col1:
            is_active_free = (current_role == "user")
            card_class = "plan-card plan-card-active" if is_active_free else "plan-card"
            active_tag_html = "<div class='plan-active-tag'>Active Plan</div>" if is_active_free else ""
            
            render_html(f"""
            <div class='{card_class}'>
                {active_tag_html}
                <div>
                    <h4>Free Reader</h4>
                    <div class='plan-price-tag' style='color: #94A3B8;'>&#36;0</div>
                    <p style='color: #94A3B8; font-size: 0.85em;'>Essential tools for individual fact-checkers</p>
                    <ul class='plan-feature-list'>
                        <li>10 verification tokens capacity</li>
                        <li>Refills 5 tokens / hour</li>
                        <li>Standard NLP & spaCy extraction</li>
                        <li>FAISS vector similarity search</li>
                        <li>Encrypted audit logging</li>
                    </ul>
                </div>
            </div>
            """)
            
            if is_active_free:
                st.button("✅ Current Active Plan", key="btn_free_active", disabled=True, use_container_width=True)
            else:
                if st.button("Downgrade to Free Reader", key="btn_free_downgrade", use_container_width=True):
                    db.update_user_tokens(st.session_state.username, 10.0, time.time())
                    db.update_user_role(st.session_state.username, "user")
                    st.session_state.role = "user"
                    st.session_state.jwt_token = generate_jwt(st.session_state.username, "user")
                    st.success("Successfully switched to Free Reader tier!")
                    st.rerun()

        # Plan 2: Premium Journalist
        with p_col2:
            is_active_prem = (current_role == "premium")
            card_class = "plan-card plan-card-active" if is_active_prem else "plan-card"
            active_tag_html = "<div class='plan-active-tag'>Active Plan</div>" if is_active_prem else "<div class='plan-popular-tag'>Popular</div>"
            
            render_html(f"""
            <div class='{card_class}' style='border-color: #6366F1;'>
                {active_tag_html}
                <div>
                    <h4>Premium Journalist</h4>
                    <div class='plan-price-tag' style='color: #818CF8;'>&#36;19<span style='font-size: 0.45em; color: #94A3B8;'>/mo</span></div>
                    <p style='color: #94A3B8; font-size: 0.85em;'>For freelance reporters and content writers</p>
                    <ul class='plan-feature-list'>
                        <li><strong>Unlimited</strong> verification checks</li>
                        <li>Bypassed token bucket rate limits</li>
                        <li>Priority LLM execution queue</li>
                        <li>Expanded FAISS search (Top 5)</li>
                        <li>Multi-Agent Persona Debate (FactChecker → Critic → Consensus)</li>
                    </ul>
                </div>
            </div>
            """)
            
            if is_active_prem:
                st.button("✅ Current Active Plan", key="btn_prem_active", disabled=True, use_container_width=True)
            else:
                if st.button("⚡ Switch to Premium Journalist", key="btn_prem_upgrade", use_container_width=True):
                    db.update_user_role(st.session_state.username, "premium")
                    st.session_state.role = "premium"
                    st.session_state.jwt_token = generate_jwt(st.session_state.username, "premium")
                    st.success("Successfully upgraded to Premium Journalist! Rate limits bypassed.")
                    st.rerun()

        # Plan 3: Newsroom Enterprise
        with p_col3:
            is_active_news = (current_role == "newsroom_admin")
            card_class = "plan-card plan-card-active" if is_active_news else "plan-card"
            active_tag_html = "<div class='plan-active-tag'>Active Plan</div>" if is_active_news else ""
            
            render_html(f"""
            <div class='{card_class}'>
                {active_tag_html}
                <div>
                    <h4>Newsroom Enterprise</h4>
                    <div class='plan-price-tag' style='color: #10B981;'>&#36;49<span style='font-size: 0.45em; color: #94A3B8;'>/mo</span></div>
                    <p style='color: #94A3B8; font-size: 0.85em;'>For media agencies & editorial newsrooms</p>
                    <ul class='plan-feature-list'>
                        <li><strong>Unlimited</strong> verification checks</li>
                        <li>Multi-seat team user directory</li>
                        <li>Advanced audit trails & telemetry</li>
                        <li>LangGraph stateful workflow</li>
                        <li>Dedicated SLA & priority support</li>
                    </ul>
                </div>
            </div>
            """)
            
            if is_active_news:
                st.button("✅ Current Active Plan", key="btn_news_active", disabled=True, use_container_width=True)
            else:
                if st.button("🚀 Switch to Newsroom Enterprise", key="btn_news_upgrade", use_container_width=True):
                    db.update_user_role(st.session_state.username, "newsroom_admin")
                    st.session_state.role = "newsroom_admin"
                    st.session_state.jwt_token = generate_jwt(st.session_state.username, "newsroom_admin")
                    st.success("Successfully upgraded to Newsroom Enterprise tier! Admin tools unlocked.")
                    st.rerun()

        st.markdown("---")

        # 5. Plan Comparison Matrix Table
        st.markdown("### 📊 Subscription Tier Comparison Matrix")
        render_html("""
        <table class='matrix-table'>
            <thead>
                <tr>
                    <th>Feature / Capability</th>
                    <th>Free Reader (&#36;0)</th>
                    <th style='color: #818CF8;'>Premium Journalist (&#36;19/mo)</th>
                    <th style='color: #10B981;'>Newsroom Enterprise (&#36;49/mo)</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>Verification Quota</strong></td>
                    <td>10 Checks / Bucket (5/hr refill)</td>
                    <td><strong style='color: #818CF8;'>Unlimited</strong></td>
                    <td><strong style='color: #10B981;'>Unlimited</strong></td>
                </tr>
                <tr>
                    <td><strong>Rate Limiter Status</strong></td>
                    <td>Token-Bucket Active</td>
                    <td>Bypassed (Zero Throttles)</td>
                    <td>Bypassed (Zero Throttles)</td>
                </tr>
                <tr>
                    <td><strong>LLM Verification Models</strong></td>
                    <td>Standard Heuristic + LLM</td>
                    <td>Priority Gemini / Groq Queue</td>
                    <td>Custom Enterprise Endpoints</td>
                </tr>
                <tr>
                    <td><strong>FAISS Vector Search Depth</strong></td>
                    <td>Top 3 Articles</td>
                    <td>Top 5 Articles</td>
                    <td>Top 10 Articles + Live Crawler</td>
                </tr>
                <tr>
                    <td><strong>Persona Debate (FactChecker → Critic → Consensus)</strong></td>
                    <td>❌ Limited</td>
                    <td>✅ Full Consensus Debate</td>
                    <td>✅ Full Consensus Debate</td>
                </tr>
                <tr>
                    <td><strong>LangGraph Stateful Graph</strong></td>
                    <td>❌ Basic Sequential</td>
                    <td>✅ Enabled</td>
                    <td>✅ Advanced Branching</td>
                </tr>
                <tr>
                    <td><strong>Team & Multi-Seat Management</strong></td>
                    <td>❌ Single User</td>
                    <td>❌ Single User</td>
                    <td>✅ Newsroom Admin Console</td>
                </tr>
                <tr>
                    <td><strong>Audit Trail Encryption</strong></td>
                    <td>Fernet AES-128-CBC</td>
                    <td>Fernet AES-128-CBC</td>
                    <td>Fernet + Enterprise Telemetry</td>
                </tr>
            </tbody>
        </table>
        """)

        st.markdown("---")

        # 6. Security & Session Credentials Section
        st.markdown("### 🔒 Security, Credentials & Session Management")
        
        sec_col1, sec_col2 = st.columns(2)

        with sec_col1:
            render_html("""
            <div class='glass-card'>
                <h4 style='color: #818CF8; margin-top: 0;'>🛡️ Session JWT Token Inspector</h4>
                <p style='font-size: 0.88em; color: #CBD5E1;'>
                    Your session is protected with JSON Web Tokens (JWT) signed via HMAC-SHA256 with 60-minute automated expiration.
                </p>
            </div>
            """)

            
        with sec_col2:
            render_html("""
            <div class='glass-card'>
                <h4 style='color: #10B981; margin-top: 0;'>🔑 Update Account Password</h4>
                <p style='font-size: 0.88em; color: #CBD5E1;'>
                    Passwords are encrypted with PBKDF2-SHA256 with 100,000 salt iterations before storage.
                </p>
            </div>
            """)

            with st.form("pwd_change_form"):
                curr_pwd = st.text_input("Current Password", type="password")
                new_pwd = st.text_input("New Password", type="password")
                conf_pwd = st.text_input("Confirm New Password", type="password")
                pwd_submit = st.form_submit_button("Update Password", use_container_width=True)

                if pwd_submit:
                    if not curr_pwd or not new_pwd or not conf_pwd:
                        st.error("Please fill in all password fields.")
                    elif new_pwd != conf_pwd:
                        st.error("New password and confirmation do not match.")
                    elif len(new_pwd) < 4:
                        st.error("New password must be at least 4 characters long.")
                    else:
                        # Verify current password
                        user_rec = db.get_user(st.session_state.username)
                        if user_rec and verify_password(curr_pwd, user_rec["password_hash"]):
                            new_hash = hash_password(new_pwd)
                            db.update_user_password(st.session_state.username, new_hash)
                            st.success("Password successfully updated! It is secured with PBKDF2-SHA256.")
                        else:
                            st.error("Current password verification failed.")

        # 7. Newsroom Enterprise Admin Console (Visible to newsroom_admin)
        if current_role == "newsroom_admin":
            st.markdown("---")
            st.markdown("### 👥 Newsroom Enterprise User Directory")
            st.markdown("As a Newsroom Enterprise Administrator, you can view all member accounts across your organization and manage their access tiers.")

            all_users = db.get_all_users()
            if all_users:
                st.markdown(f"**Total Registered Members:** `{len(all_users)}`")
                
                # Render clean user directory
                for u in all_users:
                    u_role = u.get("role", "user")
                    u_tokens = u.get("tokens", 10.0)
                    
                    role_badge_class = "role-tag-user"
                    if u_role == "premium":
                        role_badge_class = "role-tag-premium"
                    elif u_role == "newsroom_admin":
                        role_badge_class = "role-tag-admin"

                    render_html(f"""
                    <div class='admin-user-card'>
                        <div>
                            <strong style='font-size: 1.05em; color: #FFFFFF;'>{u['username']}</strong>
                            <span style='color: #64748B; font-size: 0.85em; margin-left: 10px;'>ID: #{u['id']}</span>
                        </div>
                        <div style='display: flex; align-items: center; gap: 15px;'>
                            <span style='color: #94A3B8; font-size: 0.85em;'>Tokens: <strong>{u_tokens:.1f}</strong></span>
                            <span class='{role_badge_class}'>{u_role.upper()}</span>
                        </div>
                    </div>
                    """)
                
                # Admin Fast Role Editor
                with st.expander("🛠️ Admin Member Role Modifier"):
                    usernames_list = [u["username"] for u in all_users]
                    selected_target_user = st.selectbox("Select User Account", usernames_list)
                    selected_new_role = st.selectbox("Assign Subscription Role", ["user", "premium", "newsroom_admin"])
                    if st.button("Apply Role Change", key="admin_apply_role"):
                        db.update_user_role(selected_target_user, selected_new_role)
                        st.success(f"Updated user '{selected_target_user}' role to '{selected_new_role}'.")
                        st.rerun()

    # -------------------------------------------------------------------------
    # PAGE 3: SYSTEM AUDIT LOGS
    # -------------------------------------------------------------------------
    elif st.session_state.current_page == "📜 System Audit Logs":
        st.markdown("### 📜 System Verification Audit Trail")
        st.markdown("Responsible AI transparency log, auditing fact-check queries and verdict details. Audit data is **encrypted at rest** using Fernet symmetric encryption and decrypted on-the-fly for display.")
        
        user_logs = db.get_logs_by_user(st.session_state.username)
        
        if not user_logs:
            st.info("You haven't run any fact checks yet. Check a claim on the Verification Dashboard to populate this audit table.")
        else:
            for l in user_logs:
                details = {}
                try:
                    raw = l["details_json"]
                    decrypted_json = decrypt_data(raw)
                    details = json.loads(decrypted_json)
                except Exception:
                    try:
                        details = json.loads(l["details_json"])
                    except Exception:
                        pass
                
                verdict = l["verdict"]
                v_class = "verdict-unclear"
                if verdict == "Supported":
                    v_class = "verdict-supported"
                elif verdict == "Contradicted":
                    v_class = "verdict-contradicted"
                
                with st.expander(f"🕒 {l['timestamp']} — Claim: \"{l['claim'][:60]}...\""):
                    st.markdown(f"""
                    <div style="margin-bottom: 10px;">
                        <span class="verdict-badge {v_class}">{verdict}</span>
                        <span style="margin-left: 15px; font-size: 0.9em; color: #94A3B8;">Confidence: <strong>{int(l['confidence']*100)}%</strong></span>
                    </div>
                    <div style="font-size: 0.95em; color: #E2E8F0; line-height: 1.5; margin-bottom: 12px;">
                        <strong>Verdict Explanation:</strong><br>
                        {details.get('summary', 'No reasoning logged.')}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if details.get("entities"):
                        st.markdown("**Extracted Entities:**")
                        ents_html = ""
                        for ent in details["entities"]:
                            ents_html += f"<span class='verdict-badge badge-secondary' style='margin-right: 5px; font-size: 0.8em;'>{ent['text']} ({ent['label']})</span>"
                        st.markdown(ents_html, unsafe_allow_html=True)
                        
                    if details.get("articles_retrieved"):
                        st.markdown("**Retrieved Sources:**")
                        for s in details["articles_retrieved"]:
                            st.markdown(f"- **{s['source']}**: {s['title']} (Cosine Similarity: {s['score']:.4f})")

    # -------------------------------------------------------------------------
    # PAGE 4: A2A PROTOCOL MONITOR
    # -------------------------------------------------------------------------
    elif st.session_state.current_page == "⚙️ A2A Protocol Monitor":
        st.markdown("### ⚙️ Multi-Agent A2A/1.0 Protocol Message Tracing")
        st.markdown("""
        Inspect the real-time JSON communications occurring between subagents using the **A2A/1.0 (Agent-to-Agent)** protocol.
        Each message includes a protocol version, unique message ID (UUID4), Unix timestamp, sender/recipient identifiers, action verb, and structured data payload.
        """)

        st.markdown("""
        <div class='glass-card' style='border-left: 4px solid #6366F1;'>
            <h4 style='color: #818CF8; margin-bottom: 10px;'>📋 A2A/1.0 Protocol Specification</h4>
            <table style='width: 100%; border-collapse: collapse; color: #CBD5E1; font-size: 0.9em;'>
                <tr style='border-bottom: 1px solid rgba(255,255,255,0.1);'>
                    <td style='padding: 8px; font-weight: 600; color: #818CF8; width: 25%;'>Protocol</td>
                    <td style='padding: 8px;'>A2A/1.0 — Agent-to-Agent messaging over in-process Python function calls</td>
                </tr>
                <tr style='border-bottom: 1px solid rgba(255,255,255,0.1);'>
                    <td style='padding: 8px; font-weight: 600; color: #818CF8;'>Serialization</td>
                    <td style='padding: 8px;'>JSON — validated via dumps/loads round-trip for strict compliance</td>
                </tr>
                <tr style='border-bottom: 1px solid rgba(255,255,255,0.1);'>
                    <td style='padding: 8px; font-weight: 600; color: #818CF8;'>Message ID</td>
                    <td style='padding: 8px;'>UUID4 — unique identifier for every message for end-to-end traceability</td>
                </tr>
                <tr style='border-bottom: 1px solid rgba(255,255,255,0.1);'>
                    <td style='padding: 8px; font-weight: 600; color: #818CF8;'>Timestamp</td>
                    <td style='padding: 8px;'>Unix epoch float — precise timing for performance profiling</td>
                </tr>
                <tr>
                    <td style='padding: 8px; font-weight: 600; color: #818CF8;'>Transport</td>
                    <td style='padding: 8px;'>In-process function invocation — zero-latency delivery via BaseAgent.send_message()</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
        
        if not st.session_state.agent_logs:
            st.info("No query logs in buffer. Run a claim check from the Verification Dashboard to monitor agent communication flows.")
        else:
            for idx, log in enumerate(st.session_state.agent_logs):
                with st.expander(f"🌐 Trace #{idx+1} [{log['timestamp']}]: {log['from']} ➔ {log['to']} (Action: {log['action']})"):
                    col_sent, col_recv = st.columns(2)
                    with col_sent:
                        st.markdown("📤 **Outgoing A2A/1.0 Message:**")
                        st.json({
                            "protocol": "A2A/1.0",
                            "sender": log["from"],
                            "recipient": log["to"],
                            "action": log["action"],
                            "data": log["data_sent"]
                        })
                    with col_recv:
                        st.markdown("📥 **Received Response Payload:**")
                        st.json(log["response_received"])

    # -------------------------------------------------------------------------
    # PAGE 5: RESPONSIBLE AI & GOVERNANCE
    # -------------------------------------------------------------------------
    elif st.session_state.current_page == "🤖 Responsible AI & Governance":
        st.markdown("### 🤖 Responsible AI — Ethics, Transparency & Data Protection")
        st.markdown("ClaimShield AI is built with Responsible AI principles at its core. This section documents how our system addresses fairness, explainability, transparency, and user data protection.")

        rai1, rai2 = st.columns(2)

        with rai1:
            st.markdown("""
            <div class='glass-card'>
                <h4 style='color: #10B981;'>🔍 Transparency</h4>
                <p style='color: #CBD5E1; line-height: 1.7;'>
                    Every verification decision is fully traceable. The system exposes:
                </p>
                <ul style='color: #CBD5E1; line-height: 2;'>
                    <li>Complete agent-to-agent communication logs (A2A/1.0 protocol)</li>
                    <li>Retrieved source articles with cosine similarity scores</li>
                    <li>The exact LLM prompt and processing engine used</li>
                    <li>NER entities and search queries derived from claims</li>
                    <li>Extractive evidence summaries generated by the NLP pipeline</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class='glass-card'>
                <h4 style='color: #F59E0B;'>⚖️ Fairness</h4>
                <p style='color: #CBD5E1; line-height: 1.7;'>
                    ClaimShield applies the <strong>same verification pipeline</strong> to all users regardless of subscription tier.
                    Rate limits differ by tier (Free: 10/hr, Premium/Enterprise: unlimited), but the NLP analysis,
                    FAISS retrieval algorithm, and LLM verification logic are identical for every query.
                    No user demographic data influences the fact-checking verdict.
                </p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class='glass-card'>
                <h4 style='color: #818CF8;'>🧠 Bias Mitigation</h4>
                <p style='color: #CBD5E1; line-height: 1.7;'>
                    To minimize bias in verification outcomes:
                </p>
                <ul style='color: #CBD5E1; line-height: 2;'>
                    <li>The LLM is <strong>grounded in retrieved evidence</strong> — verdicts must cite specific article quotes rather than relying on pre-trained knowledge</li>
                    <li>Multi-source retrieval ensures diverse perspectives are considered</li>
                    <li>Confidence scores quantify certainty, preventing overstatement</li>
                    <li>Three-tier verdict system (Supported/Contradicted/Unclear) avoids binary bias</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        with rai2:
            st.markdown("""
            <div class='glass-card'>
                <h4 style='color: #C084FC;'>💡 Explainability</h4>
                <p style='color: #CBD5E1; line-height: 1.7;'>
                    Every fact-check verdict includes:
                </p>
                <ul style='color: #CBD5E1; line-height: 2;'>
                    <li><strong>Verdict</strong> — Supported, Contradicted, or Unclear</li>
                    <li><strong>Confidence Score</strong> — Quantified certainty (0–100%)</li>
                    <li><strong>Summary Reasoning</strong> — 2–3 sentence explanation of the verdict rationale</li>
                    <li><strong>Inline Citations</strong> — Exact quotes from source articles with article IDs</li>
                    <li><strong>Named Entities</strong> — spaCy NER extractions showing what the system identified</li>
                    <li><strong>Evidence Summary</strong> — Extractive summarization of retrieved documents</li>
                    <li><strong>Processing Engine</strong> — Whether Gemini API or local heuristic was used</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class='glass-card'>
                <h4 style='color: #EF4444;'>🔒 Data Protection & Security</h4>
                <p style='color: #CBD5E1; line-height: 1.7;'>
                    User data is safeguarded through multiple layers:
                </p>
                <ul style='color: #CBD5E1; line-height: 2;'>
                    <li><strong>Password Hashing</strong> — PBKDF2-SHA256 with random salt (100,000 iterations)</li>
                    <li><strong>Session Tokens</strong> — JWT (HS256) with configurable expiry</li>
                    <li><strong>Encryption at Rest</strong> — Fernet symmetric encryption for audit log details</li>
                    <li><strong>Input Sanitization</strong> — HTML/script injection stripping + length truncation</li>
                    <li><strong>Rate Limiting</strong> — Token-bucket algorithm prevents API abuse</li>
                    <li><strong>Audit Trail</strong> — Immutable, encrypted verification logs for accountability</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class='glass-card'>
                <h4 style='color: #34D399;'>👤 User Rights</h4>
                <p style='color: #CBD5E1; line-height: 1.7;'>
                    In compliance with data protection principles:
                </p>
                <ul style='color: #CBD5E1; line-height: 2;'>
                    <li>Users can view their complete verification history in the Audit Logs tab</li>
                    <li>All personal data is stored locally (SQLite) or in user-controlled cloud (Supabase)</li>
                    <li>No user data is shared with third parties beyond LLM API calls (claim text only)</li>
                    <li>Users can request account deletion by contacting the system administrator</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div class='glass-card' style='border: 1px solid rgba(16, 185, 129, 0.3); text-align: center;'>
            <p style='color: #34D399; font-size: 1.1em; font-weight: 600; margin-bottom: 5px;'>🌍 Responsible AI Commitment</p>
            <p style='color: #94A3B8; font-size: 0.95em;'>
                ClaimShield AI is committed to ethical AI development. We prioritize human oversight, evidence-based verdicts,
                and transparent decision-making. Our system augments — never replaces — human editorial judgment.
            </p>
        </div>
        """, unsafe_allow_html=True)
