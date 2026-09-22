import streamlit as st
import sys
import os
import json
import time
from pathlib import Path

# Add root folder to sys.path to enable app module imports
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from app.database.db_manager import DBManager
from app.agents.orchestrator import Orchestrator
from app.agents.base_agent import BaseAgent
from app.utils.security import verify_jwt, decrypt_data
from app import config
import seed_database

_ORIGINAL_BASE_SEND = BaseAgent.send_message

# Page Config
st.set_page_config(
    page_title="ClaimShield AI — Fact Checker",
    page_icon="",
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

# Lazy Initializations
@st.cache_resource
def get_system_components():
    db = DBManager()
    
    # Auto-seed SQLite DB if empty to ensure instant out-of-the-box operation
    articles = db.get_all_articles()
    if not articles:
        print("Streamlit: Database appears empty. Seeding sample articles and default accounts...")
        seed_database.seed()
        db = DBManager()  # Refresh manager
        
    orchestrator = Orchestrator(security_agent=None)  # Uses default subagents
    return db, orchestrator

db, orchestrator = get_system_components()

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

# Header Branding
st.markdown("""
<div style='text-align: center; margin-bottom: 25px;'>
    <h1 style='font-size: 2.8em; margin-bottom: 5px;'>💬 ClaimShield AI</h1>
    <p style='color: #818CF8; font-size: 1.1em; font-weight: 500;'>Instant QA & Fact Verification Engine — Responds to any question in simple, realistic language</p>
</div>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR: Auth & Rate Limits -----------------
with st.sidebar:
    st.markdown("### [User] User Session Manager")
    
    if not st.session_state.authenticated:
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
        st.info("💡 Tip: Use pre-seeded credentials:\n- user / password\n- premium / premium\n- newsroom / newsroom")
        
    else:
        # User is authenticated
        st.markdown(f"""
        <div class='glass-card' style='padding: 15px; margin-bottom: 15px;'>
            <div style='font-size: 0.85em; color: #94A3B8;'>Logged in as</div>
            <div style='font-size: 1.25em; font-weight: 700; color: #FFFFFF;'>{st.session_state.username}</div>
            <div class='verdict-badge badge-secondary' style='margin-top: 5px; font-size: 0.75em;'>Tier: {st.session_state.role.upper()}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Display current rate limit tokens (Security Check)
        user_info = db.get_user(st.session_state.username)
        if user_info:
            role = user_info.get("role", "user")
            
            st.markdown("#### [Warning] API Rate Limiting")
            if role in ["premium", "newsroom_admin"]:
                st.markdown("""
                <div style='background-color: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2); padding: 10px; border-radius: 8px; font-size: 0.85em; color: #34D399; margin-bottom: 15px;'>
                    🚀 Unlimited Access Active for subscription tier.
                </div>
                """, unsafe_allow_html=True)
            else:
                # Standard user: Calculate tokens dynamically for UI
                now = time.time()
                last_time = user_info.get("last_request_time", 0.0)
                curr_tokens = user_info.get("tokens", 10.0)
                refill = (now - last_time) * (config.RATE_LIMIT_REFILL_AMOUNT / config.RATE_LIMIT_REFILL_PERIOD)
                tokens = min(float(config.RATE_LIMIT_CAPACITY), curr_tokens + refill)
                
                # Progress bar
                progress_pct = tokens / config.RATE_LIMIT_CAPACITY
                st.progress(min(max(progress_pct, 0.0), 1.0))
                st.caption(f"Remaining Tokens: **{tokens:.1f} / {config.RATE_LIMIT_CAPACITY}**")
                st.caption("Refills at 5 tokens / hour.")
        
        st.markdown("---")
        st.markdown("### 🤖 Multi-Agent Architecture Engine")
        engine_mode = st.selectbox(
            "Select Framework Engine",
            ["Standard A2A Protocol", "LangGraph Stateful Workflow", "AutoGen Agent Debate"],
            help="Choose between standard in-process A2A protocol, LangGraph stateful graph execution, or AutoGen multi-agent debate."
        )
        st.session_state.engine_mode = engine_mode

        if st.button("Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.role = "user"
            st.session_state.jwt_token = None
            st.session_state.agent_logs = []
            st.rerun()

# ----------------- MAIN INTERFACE -----------------
# 1. Main Fact Checker Module (Requires Auth)
if not st.session_state.authenticated:
    st.markdown("""
    <div class='glass-card' style='text-align: center; padding: 40px;'>
        <h2 style='color: #818CF8;'>🛡️ Shield Your Journalism Today</h2>
        <p style='margin-bottom: 25px; color: #94A3B8;'>Create a secure account or login to access our real-time multi-agent claim verification system.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Showcase Commercialization Tiers visually on the landing page
    st.markdown("### 💎 Subscription & Pricing Tiers")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class='glass-card' style='text-align: center;'>
            <h4>Standard Tier</h4>
            <h2 style='font-size: 2.2em; color: #94A3B8;'>Free</h2>
            <hr style='border-color: rgba(255,255,255,0.1);'>
            <p>10 claim checks capacity</p>
            <p>Refills 5 tokens / hour</p>
            <p>Standard NLP & FAISS index</p>
            <p style='color: #64748B;'>Ideal for individual researchers</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class='glass-card' style='text-align: center; border: 1px solid #6366F1;'>
            <div style='background-color: #6366F1; color: white; font-size: 0.7em; padding: 3px; border-radius: 5px; font-weight: 600; margin-bottom: 10px; text-transform: uppercase;'>Popular</div>
            <h4>Premium Reader</h4>
            <h2 style='font-size: 2.2em; color: #818CF8;'>$19<span style='font-size: 0.5em; color: #94A3B8;'>/mo</span></h2>
            <hr style='border-color: rgba(255,255,255,0.1);'>
            <p><strong>Unlimited</strong> claim checks</p>
            <p>Priority LLM access</p>
            <p>Retrieval expansion (Top 5)</p>
            <p style='color: #818CF8;'>Ideal for content writers</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class='glass-card' style='text-align: center;'>
            <h4>Newsroom Enterprise</h4>
            <h2 style='font-size: 2.2em; color: #10B981;'>$49<span style='font-size: 0.5em; color: #94A3B8;'>/mo</span></h2>
            <hr style='border-color: rgba(255,255,255,0.1);'>
            <p><strong>Unlimited</strong> claim checks</p>
            <p>Multi-seat logins</p>
            <p>Historical audit trails</p>
            <p style='color: #34D399;'>For agencies & news outlets</p>
        </div>
        """, unsafe_allow_html=True)

else:
    # Authenticated Dashboard
    tabs = st.tabs(["🛡️ Verify Claims", "💎 Subscription Pricing", "📜 Audit Logs", "⚙️ Developer Protocol Log", "🤖 Responsible AI"])
    
    # TAB 1: QA & FACT CHECKING ENGINE
    with tabs[0]:
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
                    # Build protocol monitoring queue
                    st.session_state.agent_logs = []
                    
                    # Log message tracing function for UI transparency
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
                    
                    # Override the base_agent send_message method temporarily to capture tracing logs
                    def custom_send(self, recipient, action, data):
                        resp = _ORIGINAL_BASE_SEND(self, recipient, action, data)
                        trace_agent_message(self.name, recipient.name, action, data, resp)
                        return resp
                    BaseAgent.send_message = custom_send
                    
                    # Execute flow
                    selected_engine = st.session_state.get("engine_mode", "Standard A2A Protocol")
                    orchestrator_req = {
                        "action": "verify",
                        "data": {
                            "claim": claim_input,
                            "username": st.session_state.username,
                            "engine_mode": selected_engine
                        }
                    }
                    
                    # Capture orchestrator request
                    pipeline_start_time = time.time()
                    try:
                        pipeline_result = orchestrator.handle_message(orchestrator_req)
                    finally:
                        BaseAgent.send_message = _ORIGINAL_BASE_SEND
                    pipeline_end_time = time.time()
                    
                    if pipeline_result.get("status") == "rate_limited":
                        st.error(pipeline_result.get("message"))
                        st.info(f"Please wait {pipeline_result.get('retry_after_seconds')} seconds, or upgrade to a premium account.")
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

                        # If straight_ans is empty, extract first sentence of summary
                        if not straight_ans:
                            straight_ans = summary.split(". ")[0] + "." if summary else verdict_display
                            
                        # ----------------- 1. STRAIGHT ANSWER SECTION -----------------
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
                        
                        # ----------------- 2. DETAILED EXPLANATION SECTION -----------------
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

                        # Evidence Summary (NLP Extractive Summarization output if relevant)
                        ev_summary = pipeline_result.get("evidence_summary", "")
                        if ev_summary:
                            st.markdown(f"""
                            <div class="glass-card" style="border-left: 4px solid #818CF8;">
                                <div style="font-size: 0.85em; color: #818CF8; font-weight: 600; margin-bottom: 8px;">📝 Extractive Evidence Highlights</div>
                                <p style="font-size: 1.0em; line-height: 1.6; color: #E2E8F0;">{ev_summary}</p>
                            </div>
                            """, unsafe_allow_html=True)

                        # Scikit-Learn ML Stance & Credibility Card
                        ml_info = pipeline_result.get("ml_classification", {})
                        if ml_info:
                            st.markdown(f"""
                            <div class="glass-card" style="border-left: 4px solid #10B981;">
                                <div style="font-size: 0.85em; color: #10B981; font-weight: 600; margin-bottom: 4px;">⚡ Scikit-Learn ML Credibility Analysis</div>
                                <div>Prediction Label: <strong>{ml_info.get('label', 'N/A')}</strong> | Confidence: <strong>{int(ml_info.get('confidence', 0)*100)}%</strong></div>
                                <div style="font-size: 0.8em; color: #64748B;">Engine: {ml_info.get('engine', 'TF-IDF Vectorizer')}</div>
                            </div>
                            """, unsafe_allow_html=True)

                        # AutoGen Debate Transcript Card
                        autogen_info = pipeline_result.get("autogen_debate", {})
                        if autogen_info:
                            with st.expander("🗣️ AutoGen Multi-Agent Debate Transcript", expanded=True):
                                st.markdown(f"**Engine:** {autogen_info.get('engine')}")
                                for msg in autogen_info.get("debate_log", []):
                                    st.markdown(f"**[{msg.get('agent')}]**: {msg.get('message')}")
                                st.info(f"**Consensus Verdict:** {autogen_info.get('consensus')}")

                        # Columns for entities and takeaways
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
                                
                        # ----------------- 3. SEPARATE SECTION FOR USED LINKS -----------------
                        st.markdown("---")
                        st.markdown("### 🔗 Referenced Sources & Verified Article Links")
                        if ret_articles:
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
                        
    # TAB 2: PRICING AND SIMULATED UPGRADE + COMMERCIALIZATION STRATEGY
    with tabs[1]:
        st.markdown("### 💎 Manage Newsroom Membership & Commercial Tiers")
        st.markdown("Explore and simulate upgrading your tier to verify and test rate limits dynamically.")
        
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.markdown("""
            <div class='glass-card' style='text-align: center; min-height: 380px;'>
                <h4>Free Reader</h4>
                <h2 style='color: #94A3B8;'>$0</h2>
                <p>Verify claims with rate limit caps</p>
                <p>10 requests/hour capacity</p>
                <p>Heuristic + spaCy pipeline</p>
            </div>
            """, unsafe_allow_html=True)
            if st.session_state.role == "user":
                st.button("Active Tier", key="act_free", disabled=True, use_container_width=True)
            else:
                if st.button("Downgrade to Free", key="dg_free", use_container_width=True):
                    db.update_user_tokens(st.session_state.username, 10.0, time.time())
                    db.update_user_role(st.session_state.username, "user")
                    st.session_state.role = "user"
                    st.success("Successfully downgraded to Free reader tier.")
                    st.rerun()

        with c2:
            st.markdown("""
            <div class='glass-card' style='text-align: center; border: 1px solid #6366F1; min-height: 380px;'>
                <h4>Premium Journalist</h4>
                <h2 style='color: #818CF8;'>$19<span style='font-size: 0.5em; color: #94A3B8;'>/mo</span></h2>
                <p>🎯 <strong>Unlimited</strong> requests (Bypassed rate limit)</p>
                <p>Priority LLM Verification Queue</p>
                <p>FAISS search limit expanded to Top 5 matches</p>
            </div>
            """, unsafe_allow_html=True)
            if st.session_state.role == "premium":
                st.button("Active Tier", key="act_prem", disabled=True, use_container_width=True)
            else:
                if st.button("Simulate Upgrade to Premium", key="up_prem", use_container_width=True):
                    db.update_user_role(st.session_state.username, "premium")
                    st.session_state.role = "premium"
                    st.success("Successfully upgraded to Premium Journalist tier! Rate limits bypassed.")
                    st.rerun()

        with c3:
            st.markdown("""
            <div class='glass-card' style='text-align: center; min-height: 380px;'>
                <h4>Newsroom Enterprise</h4>
                <h2 style='color: #10B981;'>$49<span style='font-size: 0.5em; color: #94A3B8;'>/mo</span></h2>
                <p>⚡ Unlimited requests + team logins</p>
                <p>Advanced detailed audit analytics</p>
                <p>Bulk claims verification API access</p>
            </div>
            """, unsafe_allow_html=True)
            if st.session_state.role == "newsroom_admin":
                st.button("Active Tier", key="act_nr", disabled=True, use_container_width=True)
            else:
                if st.button("Simulate Upgrade to Newsroom", key="up_nr", use_container_width=True):
                    db.update_user_role(st.session_state.username, "newsroom_admin")
                    st.session_state.role = "newsroom_admin"
                    st.success("Successfully upgraded to Newsroom Enterprise tier! Bypassed rate limits.")
                    st.rerun()

        # --- Commercialization Strategy Section ---
        st.markdown("---")
        st.markdown("### 🚀 Commercialization Strategy")

        strat1, strat2 = st.columns(2)
        with strat1:
            st.markdown("""
            <div class='glass-card'>
                <h4 style='color: #818CF8;'>🎯 Target Users & Market</h4>
                <ul style='line-height: 2; color: #CBD5E1;'>
                    <li><strong>Journalists & Reporters</strong> — Real-time claim verification before publication</li>
                    <li><strong>Newsroom Organizations</strong> — Enterprise-grade editorial fact-checking pipelines</li>
                    <li><strong>Fact-Checking NGOs</strong> — Scalable verification for misinformation monitoring</li>
                    <li><strong>Social Media Platforms</strong> — API integration for automated content moderation</li>
                    <li><strong>Academic Researchers</strong> — Citation-backed claim validation for papers</li>
                    <li><strong>Government & Policy Bodies</strong> — Public discourse monitoring tools</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        with strat2:
            st.markdown("""
            <div class='glass-card'>
                <h4 style='color: #10B981;'>☁️ Deployment Strategy</h4>
                <ul style='line-height: 2; color: #CBD5E1;'>
                    <li><strong>SaaS Cloud Deployment</strong> — Hosted on AWS/GCP with auto-scaling Kubernetes clusters</li>
                    <li><strong>API-First Architecture</strong> — RESTful API endpoints for third-party integration</li>
                    <li><strong>White-Label Licensing</strong> — Customizable branding for news agencies</li>
                    <li><strong>On-Premise Option</strong> — Air-gapped deployments for sensitive government clients</li>
                    <li><strong>Mobile SDK</strong> — Embeddable verification widget for mobile news apps</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div class='glass-card' style='border: 1px solid rgba(99, 102, 241, 0.2);'>
            <h4 style='color: #C084FC;'>💰 Revenue Model</h4>
            <table style='width: 100%; border-collapse: collapse; color: #CBD5E1;'>
                <tr style='border-bottom: 1px solid rgba(255,255,255,0.1);'>
                    <td style='padding: 10px;'><strong>Freemium SaaS</strong></td>
                    <td style='padding: 10px;'>Free tier drives adoption → Premium conversion at $19/mo → Enterprise at $49/mo</td>
                </tr>
                <tr style='border-bottom: 1px solid rgba(255,255,255,0.1);'>
                    <td style='padding: 10px;'><strong>API Usage Billing</strong></td>
                    <td style='padding: 10px;'>Pay-per-verification for high-volume integrators ($0.02/check after free tier)</td>
                </tr>
                <tr style='border-bottom: 1px solid rgba(255,255,255,0.1);'>
                    <td style='padding: 10px;'><strong>Annual Contracts</strong></td>
                    <td style='padding: 10px;'>Discounted annual plans for newsrooms (20% savings) with SLA guarantees</td>
                </tr>
                <tr>
                    <td style='padding: 10px;'><strong>White-Label Licensing</strong></td>
                    <td style='padding: 10px;'>Custom pricing for agencies embedding ClaimShield into their editorial workflows</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    # TAB 3: SYSTEM AUDIT LOG HISTORY
    with tabs[2]:
        st.markdown("### 📜 System Verification Audit Trail")
        st.markdown("Responsible AI transparency log, auditing fact-check queries and verdict details. Audit data is **encrypted at rest** using Fernet symmetric encryption and decrypted on-the-fly for display.")
        
        # Get logs from database
        user_logs = db.get_logs_by_user(st.session_state.username)
        
        if not user_logs:
            st.info("You haven't run any fact checks yet. Check a claim to populate this audit table.")
        else:
            for l in user_logs:
                details = {}
                try:
                    # Decrypt the encrypted audit log details
                    raw = l["details_json"]
                    decrypted_json = decrypt_data(raw)
                    details = json.loads(decrypted_json)
                except Exception:
                    # Fallback: try parsing as plain JSON (legacy unencrypted data)
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

    # TAB 4: A2A JSON MESSAGE MONITOR
    with tabs[3]:
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
            st.info("No query logs in buffer. Run a claim check to monitor agent communication flows.")
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

    # TAB 5: RESPONSIBLE AI
    with tabs[4]:
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
