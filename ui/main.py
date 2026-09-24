import streamlit as st
import sys
import os
import json
import time
import datetime
import html
import textwrap
import importlib
import threading
from pathlib import Path

# Add root folder to sys.path to enable app module imports
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from app.database.db_manager import DBManager
from app.utils.security import verify_jwt, decrypt_data, hash_password, verify_password, generate_jwt

from app.agents.orchestrator import Orchestrator
from app.agents.base_agent import BaseAgent
from app import config
import seed_database
from ui.icons import (
    SHIELD, LOCK, KEY, TOKEN, BOLT, ASSIGNMENT, PUBLIC, PSYCHOLOGY,
    SMART_TOY, ALT_ROUTE, BAR_CHART, BIOTECH, SEARCH, BALANCE, LIGHTBULB,
    CHECK_CIRCLE, CANCEL, CHAT, HELP, TRACK_CHANGES, MENU_BOOK, HANDSHAKE,
    DESCRIPTION, EDIT_NOTE, RECORD_VOICE_OVER, SELL, PUSH_PIN, LINK,
    RECEIPT_LONG, NEWSPAPER, CALENDAR_TODAY, PERSON, GROUP, CONSTRUCTION,
    HISTORY_EDU, SETTINGS, SCHEDULE, OUTBOX, INBOX, DIAMOND, STAR,
    CARD_MEMBERSHIP, ROCKET_LAUNCH, SMARTPHONE, NIGHTLIGHT, COFFEE,
    HOURGLASS_TOP, EXPLORE, CELEBRATION, ARROW_FORWARD, CHECK, WARNING,
    CLOSE, FACT_CHECK, SECURITY, FINGERPRINT, HUB,
    icon_html, icon_md,
    ICON_SHIELD, ICON_LOCK, ICON_KEY, ICON_TOKEN, ICON_BOLT,
    ICON_ASSIGNMENT, ICON_PUBLIC, ICON_PSYCHOLOGY, ICON_SMART_TOY,
    ICON_ALT_ROUTE, ICON_BAR_CHART, ICON_BIOTECH, ICON_SEARCH,
    ICON_BALANCE, ICON_LIGHTBULB, ICON_CHECK_CIRCLE, ICON_CANCEL,
    ICON_CHAT, ICON_HELP, ICON_TRACK_CHANGES, ICON_MENU_BOOK,
    ICON_HANDSHAKE, ICON_DESCRIPTION, ICON_EDIT_NOTE,
    ICON_RECORD_VOICE_OVER, ICON_SELL, ICON_PUSH_PIN, ICON_LINK,
    ICON_RECEIPT_LONG, ICON_NEWSPAPER, ICON_CALENDAR_TODAY,
    ICON_PERSON, ICON_GROUP, ICON_CONSTRUCTION, ICON_HISTORY_EDU,
    ICON_SETTINGS, ICON_SCHEDULE, ICON_OUTBOX, ICON_INBOX,
    ICON_DIAMOND, ICON_STAR, ICON_CARD_MEMBERSHIP, ICON_ROCKET_LAUNCH,
    ICON_SMARTPHONE, ICON_NIGHTLIGHT, ICON_COFFEE, ICON_HOURGLASS_TOP,
    ICON_EXPLORE, ICON_CELEBRATION, ICON_ARROW_FORWARD, ICON_CHECK,
    ICON_WARNING, ICON_CLOSE, ICON_FACT_CHECK, ICON_SECURITY,
    ICON_FINGERPRINT, ICON_HUB
)

# Page Name Constants for consistent iconized navigation
PAGE_VERIFICATION = f"{icon_md(SHIELD)} Verification Dashboard"
PAGE_ACCOUNT = f"{icon_md(PERSON)} Account & Plan Management"
PAGE_AUDIT = f"{icon_md(HISTORY_EDU)} System Audit Logs"
PAGE_A2A = f"{icon_md(SETTINGS)} A2A Protocol Monitor"
PAGE_RESPONSIBLE_AI = f"{icon_md(SMART_TOY)} Responsible AI & Governance"


_ORIGINAL_BASE_SEND = BaseAgent.send_message
# Serialize pipeline runs so the class-level tracing monkeypatch below can never
# be observed mid-flight (or restored) by a concurrent Streamlit session.
_PIPELINE_LOCK = threading.RLock()

# Page Config
st.set_page_config(
    page_title="ClaimShield AI — Fact Checker & User Management",
    page_icon=":material/shield:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS Styles
def load_css():
    css_path = ROOT_DIR / "ui" / "style.css"
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

load_css()

# Logo path helper
LOGO_PATH = ROOT_DIR / "ui" / "assets" / "logo.jpg"

@st.cache_data
def get_logo_base64():
    """Returns base64 encoded logo for embedding in HTML."""
    import base64
    if LOGO_PATH.exists():
        with open(LOGO_PATH, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

LOGO_B64 = get_logo_base64()
LOGO_SRC = f"data:image/jpeg;base64,{LOGO_B64}" if LOGO_B64 else ""

def render_clean_html(html_str: str):
    """Renders HTML reliably via st.markdown without markdown code-block indentation or DOMPurify stripping."""
    clean = "\n".join(line.lstrip() for line in html_str.strip().splitlines())
    st.markdown(clean, unsafe_allow_html=True)


def get_typewriter_subtitle_html(text: str, base_delay: float = 0.25, letter_speed: float = 0.015) -> str:
    """Generates pure CSS hardware-accelerated letter-by-letter typewriter animation.
    Each character reveals sequentially with natural word wrapping and cursor fade.
    Includes embedded styles for 100% resilient cross-environment rendering.
    """
    words = text.split(" ")
    t = base_delay
    word_blocks = []
    for word in words:
        char_spans = []
        for ch in word:
            escaped_ch = html.escape(ch)
            char_spans.append(f"<span class='tw-char' style='animation-delay:{t:.3f}s;'>{escaped_ch}</span>")
            t += letter_speed
        word_blocks.append(f"<span class='tw-word'>{''.join(char_spans)}</span>")
        t += letter_speed * 1.3
    
    body = " ".join(word_blocks)
    cursor = "<span class='tw-cursor'>|</span>"
    total_duration = t + 0.5
    
    return f"""
<style>
.tw-word {{ display: inline-block; white-space: nowrap; }}
.tw-char {{
    display: inline-block;
    opacity: 0;
    animation: tw-char-reveal 0.12s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}}
@keyframes tw-char-reveal {{
    0% {{ opacity: 0; transform: translateY(2px); }}
    100% {{ opacity: 1; transform: translateY(0); }}
}}
.tw-cursor {{
    display: inline-block;
    color: #4338CA;
    font-weight: 500;
    margin-left: 2px;
    vertical-align: baseline;
    animation: tw-cursor-blink 0.75s ease-in-out infinite, tw-cursor-fade 0.5s ease forwards {total_duration:.2f}s;
}}
@keyframes tw-cursor-blink {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0; }}
}}
@keyframes tw-cursor-fade {{
    to {{ opacity: 0; visibility: hidden; }}
}}
@media (prefers-reduced-motion: reduce) {{
    .tw-char {{ opacity: 1 !important; transform: none !important; animation: none !important; }}
    .tw-cursor {{ display: none !important; }}
}}
</style>
<div class='hero-subtitle' id='hero-typewriter-wrap'>{body}{cursor}</div>
"""


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

@st.cache_resource
def get_db():
    db_inst = DBManager()
    # Auto-seed SQLite DB if empty to ensure instant out-of-the-box operation
    articles = db_inst.get_all_articles()
    if not articles:
        print("Streamlit: Database appears empty. Seeding sample articles and default accounts...")
        seed_database.seed()
        db_inst = DBManager()
        # The cached orchestrator holds an in-memory FAISS index built from the
        # old (empty) corpus; rebuild it so retrievals see the freshly seeded data.
        get_orchestrator.clear()
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
    st.session_state.current_page = PAGE_VERIFICATION
if "nav_radio" not in st.session_state:
    st.session_state.nav_radio = PAGE_VERIFICATION
if "flash" not in st.session_state:
    st.session_state.flash = None

# One-shot feedback surfaced across the st.rerun that set it (a success message
# printed right before st.rerun() would otherwise be discarded by the reload).
_flash_msg = st.session_state.get("flash")
if _flash_msg:
    st.session_state.flash = None
    st.success(_flash_msg)
if "show_access_portal" not in st.session_state:
    st.session_state.show_access_portal = False

# Header is rendered inside page sections, suppressed at top level

# Unauthenticated Landing Page: Access Portal Visibility & Apple VisionOS Slide Animation
if not st.session_state.authenticated:
    is_portal_open = st.session_state.get("show_access_portal", False)
    transform_val = "translateX(0)" if is_portal_open else "translateX(-105%)"
    opacity_val = "1" if is_portal_open else "0"
    pointer_val = "auto" if is_portal_open else "none"

    st.markdown(f"""
    <style>
    /* Ensure the landing page NEVER shifts, squeezes or jumps - ONLY portal slides */
    div[data-testid="stAppViewContainer"] {{
        display: block !important;
        margin-left: 0 !important;
        width: 100% !important;
    }}
    div[data-testid="stAppViewContainer"] > section.main {{
        display: block !important;
        width: 100% !important;
        max-width: 100% !important;
        margin-left: 0 !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }}

    /* Access Portal Panel: Smooth VisionOS Spatial Glass Drawer sliding LEFT to RIGHT */
    section[data-testid="stSidebar"] {{
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        bottom: 0 !important;
        height: 100vh !important;
        width: 380px !important;
        max-width: 88vw !important;
        z-index: 999999 !important;
        transform: {transform_val} !important;
        opacity: {opacity_val} !important;
        pointer-events: {pointer_val} !important;
        transition: transform 0.40s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.35s ease !important;
        will-change: transform, opacity !important;
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.82) 0%, rgba(246, 248, 252, 0.70) 100%) !important;
        backdrop-filter: blur(36px) saturate(190%) brightness(102%) !important;
        -webkit-backdrop-filter: blur(36px) saturate(190%) brightness(102%) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.85) !important;
        box-shadow:
            0 24px 60px -12px rgba(15, 23, 42, 0.18),
            8px 0 36px -6px rgba(67, 56, 202, 0.14),
            inset -1.5px 0 1.5px rgba(255, 255, 255, 0.95),
            inset 1.5px 0 1.5px rgba(255, 255, 255, 0.70) !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
    }}

    /* Hide default sidebar controls on landing page */
    div[data-testid="collapsedControl"],
    button[data-testid="stExpandSidebarButton"],
    button[data-testid="stSidebarCollapseButton"] {{
        display: none !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    # Client-side instantaneous smooth slide trigger on click
    st.markdown("""
    <script>
    (function() {
        function attachPortalTrigger() {
            function tagHeroBtn() {
                document.querySelectorAll('button').forEach(btn => {
                    const txt = (btn.innerText || btn.textContent || '').trim();
                    if (txt.includes('Start Verifying Claims') && !btn.classList.contains('hero-animated-wave-btn')) {
                        btn.classList.add('hero-animated-wave-btn');
                    }
                });
            }
            tagHeroBtn();
            setInterval(tagHeroBtn, 1200);

            document.addEventListener('click', function(e) {
                const btn = e.target.closest('button');
                if (!btn) return;
                const txt = (btn.innerText || btn.textContent || '').trim();
                if (txt.includes('Start Verifying Claims')) {
                    const sb = document.querySelector('section[data-testid="stSidebar"]');
                    if (sb) {
                        sb.style.setProperty('transform', 'translateX(0)', 'important');
                        sb.style.setProperty('opacity', '1', 'important');
                        sb.style.setProperty('pointer-events', 'auto', 'important');
                    }
                } else if (txt.toLowerCase().includes('close') || btn.getAttribute('key') === 'btn_close_access_portal') {
                    const sb = document.querySelector('section[data-testid="stSidebar"]');
                    if (sb) {
                        sb.style.setProperty('transform', 'translateX(-105%)', 'important');
                        sb.style.setProperty('opacity', '0', 'important');
                        sb.style.setProperty('pointer-events', 'none', 'important');
                    }
                }
            }, true);
        }
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', attachPortalTrigger);
        } else {
            attachPortalTrigger();
        }
    })();
    </script>
    """, unsafe_allow_html=True)

# ----------------- SIDEBAR: Auth, Navigation & Rate Limits -----------------
with st.sidebar:
    if not st.session_state.authenticated:
        # Dismiss button (top-right of Access Portal)
        col_portal_space, col_portal_close = st.columns([0.84, 0.16])
        with col_portal_close:
            if st.button("", icon=":material/close:", key="btn_close_access_portal", help="Close Access Portal"):
                st.session_state.show_access_portal = False
                st.rerun()

        # ---- Branded Login Header ----
        st.markdown(f"""
        <div class='login-header'>
            <div style='display:inline-flex; padding: 8px; border-radius: 24px; background: rgba(255,255,255,0.45); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.85); box-shadow: 0 10px 24px rgba(99,102,241,0.22), inset 0 1px 2px rgba(255,255,255,0.9); margin-bottom: 10px;'>
                <img src='{LOGO_SRC}' class='login-logo' style='margin:0;' alt='ClaimShield AI Logo'/>
            </div>
            <div class='login-brand-name'>ClaimShield AI</div>
            <div class='login-brand-sub'>Multi-Agent Fact Verification</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='login-divider'>Access Portal</div>", unsafe_allow_html=True)

        auth_mode = st.radio("Access Portal", ["Login", "Register"], label_visibility="collapsed",
                             horizontal=True)

        username_in = st.text_input("Username", placeholder="Enter your username")
        password_in = st.text_input("Password", type="password", placeholder="Enter your password")

        role_select = "user"
        if auth_mode == "Register":
            role_select = st.selectbox(
                "Subscription Plan",
                ["user", "pro"],
                format_func=lambda x: {"user": "Free Plan (3 requests, 2 resources displayed)",
                                       "pro": "Pro Plan (Unlimited, 3–5 resources displayed)"}[x]
            )

        btn_label = "Sign In" if auth_mode == "Login" else "Create Account"
        btn_icon = f":material/{LOCK}:" if auth_mode == "Login" else f":material/{ROCKET_LAUNCH}:"
        if st.button(btn_label, icon=btn_icon, use_container_width=True, type="primary"):
            auth_action = "login" if auth_mode == "Login" else "register"
            auth_msg = {
                "action": "authenticate",
                "data": {
                    "username": username_in,
                    "password": password_in,
                    "auth_action": auth_action,
                    "role": role_select
                }
            }
            auth_resp = orchestrator.security_agent.handle_message(auth_msg)

            if auth_resp.get("status") == "success":
                st.session_state.authenticated = True
                st.session_state.username = auth_resp["user"]["username"]
                st.session_state.role = auth_resp["user"]["role"]
                st.session_state.jwt_token = auth_resp["token"]
                st.session_state.current_page = PAGE_VERIFICATION
                st.session_state.nav_radio = PAGE_VERIFICATION
                st.session_state.flash = f"Welcome, {st.session_state.username}! {icon_md(CELEBRATION)}"
                st.rerun()
            else:
                st.error(auth_resp.get("message", "Authentication failed."))

        
        st.markdown(f"""
        <div class='demo-account-card'>
            <div class='demo-account-role'><span class="material-symbols-rounded">card_membership</span> Free Plan</div>
            <div class='demo-account-creds'>user / password (3 tokens, 2 resources displayed)</div>
        </div>
        <div class='demo-account-card'>
            <div class='demo-account-role'><span class="material-symbols-rounded">star</span> Pro Plan</div>
            <div class='demo-account-creds'>pro / password (Unlimited, 3–5 resources displayed)</div>
        </div>
        """, unsafe_allow_html=True)
        
    else:
        # User is authenticated
        user_info = db.get_user(st.session_state.username)
        current_role = user_info.get("role", st.session_state.role) if user_info else st.session_state.role
        initial_letter = (st.session_state.username[0].upper()) if st.session_state.username else "U"

        role_display = "Free Plan" if current_role == "user" else "Pro Plan"
        role_icon = ICON_CARD_MEMBERSHIP if current_role == "user" else ICON_STAR


        # Sidebar brand header (authenticated)
        st.markdown(f"""
        <div style='text-align:center; margin-bottom: 18px; padding-bottom: 14px; border-bottom: 1px solid rgba(255,255,255,0.45);'>
            <div style='display:inline-flex; padding: 6px; border-radius: 20px; background: rgba(255,255,255,0.45); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.85); box-shadow: 0 6px 18px rgba(15,23,42,0.04), inset 0 1px 2px rgba(255,255,255,0.9); margin-bottom: 6px;'>
                <img src='{LOGO_SRC}' style='width:44px; height:44px; border-radius:14px; object-fit:cover; display:block;'/>
            </div>
            <div style='font-family:"Outfit",sans-serif; font-weight:800; font-size:1.05em;
                background:linear-gradient(135deg,#1E1B4B,#4338CA); -webkit-background-clip:text;
                -webkit-text-fill-color:transparent; background-clip:text;'>ClaimShield AI</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class='glass-card' style='padding: 16px; margin-bottom: 15px;'>
            <div style='display: flex; align-items: center; gap: 12px;'>
                <div style='width: 44px; height: 44px; border-radius: 50%; background: linear-gradient(135deg, #4338CA, #2563EB);
                    display: flex; align-items: center; justify-content: center; font-weight: 700; color: white; font-size: 1.25em;
                    box-shadow: 0 4px 14px rgba(67,56,202,0.25); flex-shrink:0;'>
                    {initial_letter}
                </div>
                <div>
                    <div style='font-size: 1.05em; font-weight: 700; color: #0A0F1D;'>{st.session_state.username}</div>
                    <div style='font-size: 0.76em; color: #4338CA; font-weight: 600;'>{role_icon} {role_display}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"### {icon_md(EXPLORE)} Navigation Menu")

        nav_options = [
            PAGE_VERIFICATION,
            PAGE_ACCOUNT,
            PAGE_AUDIT,
            PAGE_A2A,
            PAGE_RESPONSIBLE_AI
        ]
        
        # Ensure session state radio key matches current page
        if "nav_radio" not in st.session_state or st.session_state.nav_radio not in nav_options:
            st.session_state.nav_radio = st.session_state.current_page if st.session_state.current_page in nav_options else PAGE_VERIFICATION

        def _on_nav_change():
            st.session_state.current_page = st.session_state.nav_radio

        # Keep track of active page with direct key binding for immediate single-click navigation
        selected_page = st.radio(
            "Go to Page",
            nav_options,
            label_visibility="collapsed",
            key="nav_radio",
            on_change=_on_nav_change
        )
        st.session_state.current_page = selected_page

        st.markdown("---")
        
        # Display current rate limit tokens (Quick Widget in Sidebar)
        if user_info:
            st.markdown(f"#### {icon_md(BOLT)} Plan Quota")
            if current_role in ["pro", "premium", "newsroom_admin"]:
                st.markdown("""
                <div style='background-color: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); padding: 8px 12px; border-radius: 8px; font-size: 0.82em; color: #047857; margin-bottom: 12px;'>
                    <span class="material-symbols-rounded">rocket_launch</span> Pro Plan: Unlimited Access Active
                </div>
                """, unsafe_allow_html=True)
            else:
                now = time.time()
                last_time = user_info.get("last_request_time", 0.0)
                curr_tokens = user_info.get("tokens", float(config.RATE_LIMIT_CAPACITY))
                refill = (now - last_time) * (config.RATE_LIMIT_REFILL_AMOUNT / config.RATE_LIMIT_REFILL_PERIOD)
                tokens = min(float(config.RATE_LIMIT_CAPACITY), curr_tokens + refill)
                
                progress_pct = tokens / config.RATE_LIMIT_CAPACITY
                st.progress(min(max(progress_pct, 0.0), 1.0))
                st.caption(f"Tokens: **{tokens:.1f} / {config.RATE_LIMIT_CAPACITY}** ({config.RATE_LIMIT_REFILL_AMOUNT}/hr) · Displays 2 resources")

        st.markdown("---")
        st.markdown(f"### {icon_md(SMART_TOY)} Multi-Agent Engine")
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
            st.session_state.current_page = PAGE_VERIFICATION
            st.session_state.nav_radio = PAGE_VERIFICATION
            st.session_state.show_access_portal = False
            st.rerun()

# ----------------- MAIN INTERFACE -----------------
if not st.session_state.authenticated:
    # =========================================================================
    # LANDING HOME PAGE — Unauthenticated Visitors
    # =========================================================================

    # ---- HERO SECTION ----
    subtitle_text = (
        "ClaimShield AI is an advanced agentic fact-verification platform powered by a collaborative "
        "network of 5 specialized AI agents, vector RAG retrieval, and multi-LLM consensus "
        "— delivering transparent, evidence-backed verdicts instantly."
    )
    subtitle_html = get_typewriter_subtitle_html(subtitle_text)

    hero_markup = f"""
    <div class='hero-section'>
        <div class='hero-logo-wrap'>
            <div style='display:inline-flex; padding: 10px; border-radius: 36px; background: linear-gradient(135deg, rgba(255,255,255,0.65) 0%, rgba(255,255,255,0.20) 100%); backdrop-filter: blur(24px); border: 1px solid rgba(255,255,255,0.85); box-shadow: 0 16px 40px -10px rgba(15,23,42,0.08), inset 0 2px 2px rgba(255,255,255,0.95);'>
                <img src='{LOGO_SRC}' class='hero-logo-img' style='margin:0;' alt='ClaimShield AI'/>
            </div>
        </div>
        <div class='hero-badge'>
            <span class='hero-badge-dot'></span>
            Now Live — Multi-Agent AI System
        </div>
        <div class='hero-title'>Truth Verified.<br/>In Real Time.</div>
        {subtitle_html}
    </div>
    """
    render_clean_html(hero_markup)

    # Hero CTA: Only [ Start Verifying Claims ]
    _, col_hero_btn, _ = st.columns([1.2, 1.6, 1.2])
    with col_hero_btn:
        render_clean_html("<div id='hero-btn-anchor' class='hero-btn-container'></div>")
        if st.button("Start Verifying Claims", icon=":material/shield:", key="btn_hero_start_verifying", type="primary", use_container_width=True):
            st.session_state.show_access_portal = True
            st.rerun()

    # ---- STATS ROW ----
    st.markdown("""
    <div class='stats-row'>
        <div class='stat-item'>
            <div class='stat-value'>5</div>
            <div class='stat-label'>Specialized Agents</div>
        </div>
        <div class='stat-item'>
            <div class='stat-value'>3</div>
            <div class='stat-label'>LLM Consensus Models</div>
        </div>
        <div class='stat-item'>
            <div class='stat-value'>A2A</div>
            <div class='stat-label'>Messaging Protocol</div>
        </div>
        <div class='stat-item'>
            <div class='stat-value'>FAISS</div>
            <div class='stat-label'>Vector Retrieval</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ---- TRUST BAR ----
    st.markdown("""
    <div class='trust-bar'>
        <div class='trust-item'><span class='trust-icon'><span class="material-symbols-rounded">key</span></span> PBKDF2-SHA256 Hashing</div>
        <div class='trust-item'><span class='trust-icon'><span class="material-symbols-rounded">generating_tokens</span></span> JWT Session Tokens</div>
        <div class='trust-item'><span class='trust-icon'><span class="material-symbols-rounded">bolt</span></span> Token-Bucket Rate Limiting</div>
        <div class='trust-item'><span class='trust-icon'><span class="material-symbols-rounded">assignment</span></span> Encrypted Audit Trails</div>
        <div class='trust-item'><span class='trust-icon'><span class="material-symbols-rounded">public</span></span> LangGraph Stateful Workflow</div>
    </div>
    """, unsafe_allow_html=True)

    # ---- FEATURE CARDS ----
    st.markdown("""
    <div class='section-eyebrow'>Platform Capabilities</div>
    <div class='section-title'>Everything you need to verify the truth</div>
    <div class='section-desc'>Six pillars of our multi-agent verification engine, built for journalists, researchers & news organizations.</div>
    """, unsafe_allow_html=True)

    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        st.markdown("""
        <div class='feature-card' style='--card-accent: linear-gradient(90deg, #4338CA, #2563EB);'>
            <div class='feature-icon-wrap' style='background: rgba(67,56,202,0.10);'><span class="material-symbols-rounded">psychology</span></div>
            <div class='feature-card-title'>Multi-Agent Orchestration</div>
            <div class='feature-card-desc'>
                Security, NLP, Retrieval, Verification, and Explainer agents collaborate
                via A2A/1.0 JSON protocol with full message tracing and live audit logs.
            </div>
        </div>
        """, unsafe_allow_html=True)
    with fc2:
        st.markdown("""
        <div class='feature-card' style='--card-accent: linear-gradient(90deg, #0284C7, #38BDF8);'>
            <div class='feature-icon-wrap' style='background: rgba(2,132,199,0.10);'><span class="material-symbols-rounded">bolt</span></div>
            <div class='feature-card-title'>Vector RAG & FAISS Index</div>
            <div class='feature-card-desc'>
                Semantic similarity retrieval over curated news repositories with cosine
                ranking, top-5 expansion, and direct inline source citations.
            </div>
        </div>
        """, unsafe_allow_html=True)
    with fc3:
        st.markdown("""
        <div class='feature-card' style='--card-accent: linear-gradient(90deg, #4F46E5, #6D28D9);'>
            <div class='feature-icon-wrap' style='background: rgba(79,70,229,0.10);'><span class="material-symbols-rounded">smart_toy</span></div>
            <div class='feature-card-title'>Multi-LLM Consensus</div>
            <div class='feature-card-desc'>
                Three independent LLMs independently evaluate claims, then vote on a consensus
                verdict — eliminating single-model hallucination bias.
            </div>
        </div>
        """, unsafe_allow_html=True)

    fc4, fc5, fc6 = st.columns(3)
    with fc4:
        st.markdown("""
        <div class='feature-card' style='--card-accent: linear-gradient(90deg, #059669, #10B981);'>
            <div class='feature-icon-wrap' style='background: rgba(5,150,105,0.10);'><span class="material-symbols-rounded">lock</span></div>
            <div class='feature-card-title'>Enterprise-Grade Security</div>
            <div class='feature-card-desc'>
                PBKDF2-SHA256 password hashing, signed JWT tokens, token-bucket
                rate limiting, and AES-encrypted audit trails at every layer.
            </div>
        </div>
        """, unsafe_allow_html=True)
    with fc5:
        st.markdown("""
        <div class='feature-card' style='--card-accent: linear-gradient(90deg, #D97706, #F59E0B);'>
            <div class='feature-icon-wrap' style='background: rgba(217,119,6,0.10);'><span class="material-symbols-rounded">alt_route</span></div>
            <div class='feature-card-title'>LangGraph Stateful Workflow</div>
            <div class='feature-card-desc'>
                Optional LangGraph execution mode provides a stateful graph-based pipeline
                for complex multi-step reasoning with full state persistence.
            </div>
        </div>
        """, unsafe_allow_html=True)
    with fc6:
        st.markdown("""
        <div class='feature-card' style='--card-accent: linear-gradient(90deg, #DC2626, #EF4444);'>
            <div class='feature-icon-wrap' style='background: rgba(220,38,38,0.10);'><span class="material-symbols-rounded">bar_chart</span></div>
            <div class='feature-card-title'>Explainability & Reports</div>
            <div class='feature-card-desc'>
                Every verdict comes with a cited evidence summary, confidence scores,
                source attribution, and downloadable PDF verification reports.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Ensure render_html is available throughout landing page components
    render_html = render_clean_html

    # ---- AGENT PIPELINE VISUALIZATION ----
    st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='section-eyebrow'>How it works</div>
    <div class='section-title'>The 5-Agent Verification Pipeline</div>
    <div class='section-desc'>Each claim flows through our sequential agent network — from authentication to final explanation.</div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class='glass-card'>
        <div class='pipeline-flow'>
            <div class='pipeline-agent'>
                <div class='pipeline-agent-icon' style='background: rgba(239,68,68,0.15); border-color: #EF4444; color: #EF4444;'><span class="material-symbols-rounded">key</span></div>
                <div class='pipeline-agent-label'>Security<br/>Agent</div>
            </div>
            <div class='pipeline-arrow'>→</div>
            <div class='pipeline-agent'>
                <div class='pipeline-agent-icon' style='background: rgba(56,189,248,0.15); border-color: #38BDF8; color: #38BDF8;'><span class="material-symbols-rounded">biotech</span></div>
                <div class='pipeline-agent-label'>NLP<br/>Agent</div>
            </div>
            <div class='pipeline-arrow'>→</div>
            <div class='pipeline-agent'>
                <div class='pipeline-agent-icon' style='background: rgba(245,158,11,0.15); border-color: #F59E0B; color: #F59E0B;'><span class="material-symbols-rounded">search</span></div>
                <div class='pipeline-agent-label'>Retrieval<br/>Agent</div>
            </div>
            <div class='pipeline-arrow'>→</div>
            <div class='pipeline-agent'>
                <div class='pipeline-agent-icon' style='background: rgba(168,85,247,0.15); border-color: #A855F7; color: #A855F7;'><span class="material-symbols-rounded">balance</span></div>
                <div class='pipeline-agent-label'>Verification<br/>Agent</div>
            </div>
            <div class='pipeline-arrow'>→</div>
            <div class='pipeline-agent'>
                <div class='pipeline-agent-icon' style='background: rgba(16,185,129,0.15); border-color: #10B981; color: #10B981;'><span class="material-symbols-rounded">lightbulb</span></div>
                <div class='pipeline-agent-label'>Explainer<br/>Agent</div>
            </div>
            <div class='pipeline-arrow'>→</div>
            <div class='pipeline-agent'>
                <div class='pipeline-agent-icon' style='background: rgba(99,102,241,0.2); border-color: #6366F1; color: #818CF8;'><span class="material-symbols-rounded">check_circle</span></div>
                <div class='pipeline-agent-label'>Verdict<br/>& Report</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ---- PRICING TABS ----
    st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
    landing_tabs = st.tabs([f"{icon_md(DIAMOND)} Subscription Plans", f"{icon_md(SMART_TOY)} Responsible AI & Ethics"])

    with landing_tabs[0]:
        st.markdown("""
        <div class='section-eyebrow'>Pricing</div>
        <div class='section-title'>Simple, Transparent Plans</div>
        <div class='section-desc'>Start with our Free plan or upgrade to Pro for expanded evidence depth.</div>
        """, unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            render_html("""
            <div class='plan-card' style='overflow: visible;'>
                <div>
                    <h4>Free Plan</h4>
                    <div class='plan-price-tag' style='color: #0F172A;'>&#36;0</div>
                    <p style='color: #64748B; font-size: 0.85em;'>Essential tools for individual fact-checking</p>
                    <ul class='plan-feature-list'>
                        <li><strong>3 requests</strong> token capacity</li>
                        <li><strong>Displays only 2 resources</strong> to user</li>
                        <li>Refills 3 tokens / hour</li>
                        <li>Standard NLP & FAISS vector search</li>
                        <li>Encrypted audit logging</li>
                    </ul>
                </div>
            </div>
            """)
        with col2:
            render_html("""
            <div class='plan-card' style='border: 2px solid #4F46E5; overflow: visible;'>
                <div class='plan-popular-tag'>Popular</div>
                <div>
                    <h4>Pro Plan</h4>
                    <div class='plan-price-tag' style='color: #4F46E5;'>&#36;19<span style='font-size: 0.45em; color: #64748B;'>/mo</span></div>
                    <p style='color: #64748B; font-size: 0.85em;'>For journalists, researchers & media professionals</p>
                    <ul class='plan-feature-list'>
                        <li><strong>Unlimited</strong> claim checks (Zero throttles)</li>
                        <li><strong>Displays at least 3 (if available) & up to 5 max</strong></li>
                        <li>Priority LLM reasoning queue</li>
                        <li>Multi-Agent Persona Debate & LangGraph</li>
                        <li>Verified live source citations</li>
                    </ul>
                </div>
            </div>
            """)

    with landing_tabs[1]:
        st.markdown(f"### {icon_md(SMART_TOY)} Responsible AI — Ethics & Governance")
        st.markdown("ClaimShield AI enforces fairness, explainability, transparency, and data protection across all tiers.")

else:
    # Ensure render_html is available throughout authenticated pages
    render_html = render_clean_html

    # =========================================================================
    # AUTHENTICATED USER PAGES
    # =========================================================================

    # -------------------------------------------------------------------------
    # PAGE 1: CLAIM VERIFICATION DASHBOARD
    # -------------------------------------------------------------------------
    if st.session_state.current_page == PAGE_VERIFICATION:
        st.markdown(f"### {icon_md(SEARCH)} Ask a Question or Verify a Claim")
        st.markdown("Type any general question or factual statement below. Our multi-agent AI system will evaluate it and provide a realistic, easy-to-understand explanation.")

        # Preset sample query buttons for quick testing
        st.markdown("**Sample Questions & Claims:**")
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        sample_query = None
        with col_s1:
            if st.button("What is AI?", icon=f":material/{SMART_TOY}:", use_container_width=True):
                sample_query = "What is Artificial Intelligence?"
        with col_s2:
            if st.button("iPhone 18 in 2026?", icon=f":material/{SMARTPHONE}:", use_container_width=True):
                sample_query = "Apple will launch the iPhone 18 in July 2026."
        with col_s3:
            if st.button("Why is sky blue?", icon=f":material/{NIGHTLIGHT}:", use_container_width=True):
                sample_query = "Why is the sky blue?"
        with col_s4:
            if st.button("Is coffee healthy?", icon=f":material/{COFFEE}:", use_container_width=True):
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
                    with _PIPELINE_LOCK:
                        try:
                            # Single-session tracing hook. Guarded by the lock so a
                            # concurrent rerun never sees a half-patched BaseAgent,
                            # and failures render cleanly instead of crashing the page.
                            BaseAgent.send_message = custom_send
                            pipeline_result = orchestrator.handle_message(orchestrator_req)
                        except Exception as e:
                            print(f"[UI] Pipeline raised an unexpected exception: {e}")
                            pipeline_result = {"status": "error", "message": f"Unexpected pipeline error: {e}"}
                        finally:
                            BaseAgent.send_message = _ORIGINAL_BASE_SEND
                    pipeline_end_time = time.time()
                    
                    if pipeline_result.get("status") == "rate_limited":
                        st.error(pipeline_result.get("message"))
                        st.info(f"Please wait {pipeline_result.get('retry_after_seconds')} seconds, or upgrade to the Pro Plan on the Account page.")
                    elif pipeline_result.get("status") == "success":
                        st.markdown(f"### {icon_md(BAR_CHART)} AI Analysis Report")
                        
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
                            verdict_display = f"{ICON_CHECK_CIRCLE} Verified True"
                        elif verdict in ["Contradicted", "False"]:
                            v_class = "verdict-contradicted"
                            verdict_display = f"{ICON_CANCEL} Debunked / False"
                        elif verdict in ["Answered", "General Info"]:
                            v_class = "verdict-answered"
                            verdict_display = f"{ICON_CHAT} Direct Answer"
                        elif verdict in ["Unverified", "Unclear"]:
                            v_class = "verdict-unclear"
                            verdict_display = f"{ICON_HELP} Unverified"

                        if not straight_ans:
                            straight_ans = summary.split(". ")[0] + "." if summary else verdict_display
                            
                        v_border = "#059669" if verdict in ["Supported", "True"] else "#DC2626" if verdict in ["Contradicted", "False"] else "#4F46E5" if verdict in ["Answered", "General Info"] else "#D97706"
                        v_bg = "var(--glass-surface-tint-success)" if verdict in ["Supported", "True"] else "linear-gradient(135deg, rgba(254, 242, 242, 0.75) 0%, rgba(255, 255, 255, 0.35) 100%)" if verdict in ["Contradicted", "False"] else "var(--glass-surface-tint-primary)" if verdict in ["Answered", "General Info"] else "linear-gradient(135deg, rgba(254, 243, 199, 0.70) 0%, rgba(255, 255, 255, 0.35) 100%)"

                        # 1. Straight Answer Section
                        render_html(f"""
                        <div class="glass-card" style="border-left: 6px solid {v_border}; background: {v_bg};">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
                                <div class="verdict-badge {v_class}">{verdict_display}</div>
                                <div style="display: inline-flex; align-items: center; gap: 8px; background: rgba(255, 255, 255, 0.75); padding: 5px 14px; border-radius: 9999px; border: 1px solid var(--glass-border); box-shadow: inset 0 1px 1px rgba(255,255,255,0.9);">
                                    <span style="font-size: 0.76em; color: #64748B; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em;">Confidence</span>
                                    <span style="font-size: 1.15em; font-weight: 800; color: #0F172A;">{int(confidence*100)}%</span>
                                </div>
                            </div>
                            <div style="font-size: 0.82em; color: {v_border}; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px;">
                                <span class="material-symbols-rounded">track_changes</span> Straight Answer
                            </div>
                            <h3 style="margin-top: 0; color: #0F172A; font-size: 1.35em; font-weight: 750; line-height: 1.4;">{straight_ans}</h3>
                        </div>
                        """)
                        
                        # 2. Detailed Explanation Section
                        st.markdown(f"""
                        <div class="glass-card">
                            <div style="font-size: 0.85em; color: #0284C7; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">
                                <span class="material-symbols-rounded">menu_book</span> Detailed Explanation
                            </div>
                            <p style="font-size: 1.05em; line-height: 1.6; color: #1E293B; margin-bottom: 15px;">{summary}</p>
                            <div style="font-size: 0.8em; color: #64748B;">
                                Processing Engine: <strong>{engine}</strong> | Execution Time: {pipeline_end_time - pipeline_start_time:.2f}s
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # 2b. Multi-Model Consensus & Explainability
                        verdict_icons = {"Supported": ICON_CHECK_CIRCLE, "Contradicted": ICON_CANCEL, "Answered": ICON_CHAT, "Unverified": ICON_HELP}
                        verdict_colors = {"Supported": "#059669", "Contradicted": "#DC2626", "Answered": "#4F46E5", "Unverified": "#D97706"}
                        provider_dots = {"Groq": "#F55036", "Gemini": "#4285F4", "Ollama": "#0D9488"}

                        def esc(s):
                            return html.escape(str(s or ""), quote=True)

                        consensus_body = ""
                        if model_breakdown:
                            row_html = []
                            for mr in model_breakdown:
                                eng = mr.get("engine", "LLM") or "LLM"
                                prov = next((p for p in ("Groq", "Gemini", "Ollama") if p in eng), "LLM")
                                dot = provider_dots.get(prov, "#64748B")
                                v = mr.get("verdict", "Unverified")
                                vcolor = verdict_colors.get(v, "#D97706")
                                conf = int(mr.get("confidence", 0) * 100)
                                snippet = (mr.get("straight_answer") or mr.get("summary") or "").strip()
                                if len(snippet) > 200:
                                    snippet = snippet[:200].rsplit(" ", 1)[0] + "…"
                                snippet_html = f'<div class="cs-model-snippet">“{esc(snippet)}”</div>' if snippet else ""
                                row_html.append(f"""
                                <div class="cs-model-row">
                                    <div class="cs-model-head">
                                        <div class="cs-model-name"><span class="cs-provider-dot" style="background:{dot}"></span>{esc(eng)}</div>
                                        <span class="cs-model-badge" style="color:{vcolor}; background:{vcolor}18; border:1px solid {vcolor}44;">{verdict_icons.get(v, ICON_HELP)} {v}</span>
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
                            fill_color = "linear-gradient(90deg,#059669,#0284C7)" if converged else "linear-gradient(90deg,#D97706,#DC2626)"
                            note_color = "#059669" if converged else "#D97706"
                            note_text = (f"{ICON_CHECK} The models converged on this verdict." if converged
                                         else f"{ICON_WARNING} The models diverged — treat this verdict with lower confidence.")
                            agreement_html = f"""
                            <div class="cs-agreement-box">
                                <div class="cs-agreement-label">
                                    <span style="font-size:0.85em; color:#64748B; font-weight:600; text-transform:uppercase; letter-spacing:0.04em;">Cross-Model Agreement</span>
                                    <span style="font-size:1.4em; font-weight:700; color:#0F172A;">{agr_pct}%</span>
                                </div>
                                <div class="cs-agreement-track"><div class="cs-conf-fill" style="width:{agr_pct}%; background:{fill_color};"></div></div>
                                <div class="cs-agreement-note" style="border-left:4px solid {note_color};">{note_text}</div>
                            </div>"""

                        render_html(f"""
                        <div class="glass-card" style="border-left: 4px solid #D97706;">
                            <div style="font-size: 0.85em; color: #D97706; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px;">
                                <span class="material-symbols-rounded">handshake</span> Multi-Model Consensus &amp; Explainability
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
                                    "Download Verification Report (PDF)",
                                    icon=f":material/{DESCRIPTION}:",
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
                            <div class="glass-card" style="border-left: 4px solid #4F46E5;">
                                <div style="font-size: 0.85em; color: #4F46E5; font-weight: 700; margin-bottom: 8px;"><span class="material-symbols-rounded">edit_note</span> Extractive Evidence Highlights</div>
                                <p style="font-size: 1.0em; line-height: 1.6; color: #1E293B;">{ev_summary}</p>
                            </div>
                            """, unsafe_allow_html=True)

                        # Scikit-Learn ML Stance
                        ml_info = pipeline_result.get("ml_classification", {})
                        if ml_info:
                            st.markdown(f"""
                            <div class="glass-card" style="border-left: 4px solid #059669;">
                                <div style="font-size: 0.85em; color: #059669; font-weight: 700; margin-bottom: 4px;"><span class="material-symbols-rounded">bolt</span> Scikit-Learn ML Credibility Analysis</div>
                                <div style="color: #1E293B;">Prediction Label: <strong>{ml_info.get('label', 'N/A')}</strong> | Confidence: <strong>{int(ml_info.get('confidence', 0)*100)}%</strong></div>
                                <div style="font-size: 0.8em; color: #64748B;">Engine: {ml_info.get('engine', 'TF-IDF Vectorizer')}</div>
                            </div>
                            """, unsafe_allow_html=True)

                        # Persona Debate Transcript
                        autogen_info = pipeline_result.get("autogen_debate", {})
                        if autogen_info:
                            stage_cfg = {
                                "FactCheckerAgent": {"icon": ICON_SEARCH, "label": "Fact Checker", "color": "#0284C7"},
                                "CriticAgent": {"icon": ICON_BALANCE, "label": "Critic", "color": "#D97706"},
                                "ConsensusAgent": {"icon": ICON_TRACK_CHANGES, "label": "Consensus", "color": "#059669"},
                            }
                            turn_html = []
                            for msg in autogen_info.get("debate_log", []):
                                agent = msg.get("agent", "")
                                cfg = stage_cfg.get(agent, {"icon": ICON_CHAT, "label": agent or "Agent", "color": "#64748B"})
                                color = cfg["color"]
                                model_badge = ""
                                if msg.get("model"):
                                    model_badge = (f'<span class="cs-debate-verdict" style="color:#1E293B; background:rgba(241,245,249,0.9); '
                                                   f'border:1px solid rgba(203,213,225,0.8);">{esc(msg["model"])}</span>')
                                verdict_badge = ""
                                if msg.get("verdict"):
                                    vcolor = verdict_colors.get(msg["verdict"], "#64748B")
                                    verdict_badge = (f'<span class="cs-debate-verdict" style="color:{vcolor}; background:{vcolor}18; '
                                                     f'border:1px solid {vcolor}44;">{verdict_icons.get(msg["verdict"], ICON_HELP)} {esc(msg["verdict"])}</span>')
                                conf_badge = ""
                                if msg.get("confidence") is not None:
                                    conf_badge = (f'<span style="font-size:0.75em; color:#64748B; font-weight:600;">{int(msg["confidence"])}% confidence</span>')
                                turn_html.append(f"""
                                <div class="cs-debate-turn" style="border-left: 4px solid {color};">
                                    <div class="cs-debate-head">
                                        <span class="cs-debate-stage" style="color:{color}; background:{color}18; border:1px solid {color}44;">{cfg["icon"]} {cfg["label"]}</span>
                                        {model_badge}
                                        {verdict_badge}
                                        {conf_badge}
                                    </div>
                                    <div class="cs-debate-message">{esc(msg.get("message", ""))}</div>
                                </div>""")

                            consensus_verdict = autogen_info.get("consensus") or autogen_info.get("message", "")
                            consensus_box = f"""
                            <div class="cs-consensus-box">
                                <div class="cs-consensus-title"><span class="material-symbols-rounded">track_changes</span> Final Consensus</div>
                                <div class="cs-consensus-text">{esc(consensus_verdict)}</div>
                            </div>"""

                            with st.expander(f"{icon_md(RECORD_VOICE_OVER)} Multi-Agent Debate Transcript", expanded=True):
                                render_html(f"""
                                <div style="font-size: 0.85em; color: #64748B; margin-bottom: 12px;">
                                    Fueled by <strong style="color: #4F46E5;">{esc(autogen_info.get("engine"))}</strong> — every statement is grounded in an actual model response, never fabricated.
                                </div>
                                """)
                                render_html("".join(turn_html) + consensus_box)

                        # Columns for concepts & quotes
                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown(f"#### {icon_md(SELL)} Key Extracted Concepts (spaCy NER)")
                            if entities:
                                for ent in entities:
                                    if not isinstance(ent, dict):
                                        continue
                                    ent_text = ent.get("text") or "Unknown"
                                    ent_label = ent.get("label") or "MISC"
                                    st.markdown(f"""
                                    <span class='verdict-badge badge-secondary' style='margin-right: 5px; margin-bottom: 5px;'>
                                        <strong>{ent_text}</strong> ({ent_label})
                                    </span>
                                    """, unsafe_allow_html=True)
                            else:
                                st.caption("No specific named entities extracted.")
                                
                        with c2:
                            st.markdown(f"#### {icon_md(PUSH_PIN)} Key Takeaways & Quotes")
                            if citations:
                                for cit in citations:
                                    if not isinstance(cit, dict):
                                        continue
                                    art_label = f"Article #{cit.get('article_id')}" if cit.get('article_id') else "General Evidence"
                                    cit_quote = cit.get("quote") or "No quote provided."
                                    cit_explanation = cit.get("explanation") or ""
                                    st.markdown(f"""
                                    <div class="citation-box">
                                        <div style="font-size: 0.85em; font-weight: 700; color: #7C3AED; margin-bottom: 5px;">
                                            {art_label}:
                                        </div>
                                        <div style="font-style: italic; font-size: 0.9em; margin-bottom: 8px; color: #1E293B;">
                                            "{cit_quote}"
                                        </div>
                                        <div style="font-size: 0.8em; color: #64748B;">
                                            <strong>Insight:</strong> {cit_explanation}
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                            else:
                                st.caption("No additional citations required for this response.")
                                
                        # Referenced Links
                        st.markdown("---")
                        st.markdown(f"### {icon_md(LINK)} Referenced Sources & Verified Article Links")
                        if ret_articles:
                            live_web_articles = [a for a in ret_articles if "Live Web" in a.get("source", "")]
                            db_articles = [a for a in ret_articles if "Live Web" not in a.get("source", "")]
                            article_dates = [a.get("date", "") for a in ret_articles if a.get("date")]
                            newest_date = max(article_dates) if article_dates else "unknown"
                            total_found = pipeline_result.get("total_resources_found", len(ret_articles))
                            is_pro = pipeline_result.get("is_pro_plan", current_role in ["pro", "premium", "newsroom_admin"])

                            if not is_pro:
                                render_html(f"""
                                <div style="font-size: 0.84em; background: rgba(79, 70, 229, 0.08); border: 1px solid rgba(79, 70, 229, 0.25); border-radius: 8px; padding: 10px 14px; margin-bottom: 12px; color: #334155;">
                                    <span class="material-symbols-rounded">lock</span> <strong style="color: #4F46E5;">Free Plan Display:</strong> Showing <strong>{len(ret_articles)}</strong> resources (Free plan displays maximum 2 of {total_found} retrieved). <span style="color: #64748B;">Upgrade to <strong>Pro Plan</strong> to view at least 3 (if available) and up to 5 maximum resources!</span>
                                </div>
                                """)
                            else:
                                render_html(f"""
                                <div style="font-size: 0.84em; background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 8px; padding: 10px 14px; margin-bottom: 12px; color: #334155;">
                                    <span class="material-symbols-rounded">star</span> <strong style="color: #059669;">Pro Plan Active:</strong> Displaying <strong>{len(ret_articles)}</strong> verified resources (Pro tier displays at least 3 if available, up to 5 maximum).
                                </div>
                                """)

                            render_html(f"""
                            <div style="font-size: 0.82em; color: #475569; background: rgba(241, 245, 249, 0.8); border: 1px solid rgba(226, 232, 240, 0.9); border-radius: 8px; padding: 8px 12px; margin-bottom: 12px;">
                                <span class="material-symbols-rounded">receipt_long</span> <strong style="color:#0F172A;">Evidence used for this verdict:</strong> {len(ret_articles)} source(s) — {len(db_articles)} from local knowledge base · {len(live_web_articles)} from live web · newest article: {newest_date}
                            </div>
                            """)
                            if live_web_articles:
                                st.markdown("The following live web sources were matched against the claim:")
                            else:
                                st.markdown("The following source articles were retrieved and cross-referenced by FAISS vector similarity:")
                            for idx, art in enumerate(ret_articles):
                                url_link = art.get('url', '#')
                                st.markdown(f"""
                                <div class="article-card" style="border-left: 4px solid #0284C7;">
                                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                                        <div class="article-title" style="font-size: 1.1em; font-weight: 700; color: #0F172A;">
                                            [{idx+1}] {art['title']}
                                        </div>
                                        <span class="badge-secondary" style="font-size: 0.8em; padding: 2px 8px; border-radius: 4px;">
                                            Score: {art['score']:.4f}
                                        </span>
                                    </div>
                                    <div class="article-meta" style="margin-top: 4px; margin-bottom: 8px; color: #64748B; font-size: 0.85em;">
                                        <span class="material-symbols-rounded">newspaper</span> <strong>Source:</strong> {art['source']} | <span class="material-symbols-rounded">calendar_today</span> <strong>Date:</strong> {art['date']}
                                    </div>
                                    <div style="font-size: 0.9em; color: #334155; line-height: 1.5; margin-bottom: 10px;">
                                        {art['content']}
                                    </div>
                                    <div style="background: rgba(241, 245, 249, 0.85); border: 1px solid rgba(226, 232, 240, 0.85); padding: 8px 12px; border-radius: 8px; font-size: 0.85em;">
                                        <span class="material-symbols-rounded">link</span> <strong>Verified Link:</strong> <a href="{url_link}" target="_blank" style="color: #0284C7; font-weight: 600; text-decoration: underline;">{url_link}</a>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.info(f"{icon_md(LIGHTBULB)} General knowledge query: No local database links were required. Answer generated using internal facts.")
                            
                    else:
                        st.error(f"Fact checking pipeline failed: {pipeline_result.get('message')}")

    # -------------------------------------------------------------------------
    # PAGE 2: USER ACCOUNT & PLAN MANAGEMENT (DEDICATED PAGE)
    # -------------------------------------------------------------------------
    elif st.session_state.current_page == PAGE_ACCOUNT:
        st.markdown(f"## {icon_md(PERSON)} User Account & Subscription Management")
        st.markdown("Manage your profile, monitor real-time token quotas, and switch subscription plans seamlessly.")

        # Fetch latest user data from DB
        user_info = db.get_user(st.session_state.username)
        current_role = user_info.get("role", st.session_state.role) if user_info else st.session_state.role
        user_logs = db.get_logs_by_user(st.session_state.username)
        total_checks = len(user_logs)
        initial_letter = (st.session_state.username[0].upper()) if st.session_state.username else "U"

        role_display = "Free Plan" if current_role == "user" else "Pro Plan"

        # 1. Profile Banner
        render_html(f"""
        <div class='user-profile-header'>
            <div class='avatar-badge'>
                {initial_letter}
            </div>
            <div style='flex-grow: 1;'>
                <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 4px;'>
                    <h2 style='margin: 0; font-size: 1.8em; color: #0F172A;'>{st.session_state.username}</h2>
                    <span class='user-status-pill status-active'>
                        <span class='status-indicator-dot'></span> Active Session
                    </span>
                </div>
                <div style='color: #64748B; font-size: 0.95em;'>
                    Subscription Plan: <strong style='color: #4F46E5;'>{role_display}</strong> | Authentication: <strong style='color: #059669;'>JWT Signed (HS256)</strong>
                </div>
            </div>
        </div>
        """)

        # 2. Key Metrics Row
        m1, m2, m3 = st.columns(3)
        with m1:
            render_html(f"""
            <div class='quota-card'>
                <div class='quota-metric-label'>Current Active Plan</div>
                <div class='quota-metric-value' style='color: #4F46E5;'>{role_display}</div>
                <div style='font-size: 0.82em; color: #64748B;'>{'Unlimited / Up to 5 resources' if current_role in ['pro', 'premium', 'newsroom_admin'] else '3 Tokens / 2 Resources displayed'}</div>
            </div>
            """)
            
        with m2:
            if current_role in ["pro", "premium", "newsroom_admin"]:
                render_html("""
                <div class='quota-card'>
                    <div class='quota-metric-label'>Verification Quota</div>
                    <div class='quota-metric-value' style='color: #059669;'>Unlimited ∞</div>
                    <div style='font-size: 0.82em; color: #059669;'>Rate Limit Bypassed · 3–5 Resources</div>
                </div>
                """)
            else:
                now = time.time()
                last_time = user_info.get("last_request_time", 0.0) if user_info else 0.0
                curr_tokens = user_info.get("tokens", float(config.RATE_LIMIT_CAPACITY)) if user_info else float(config.RATE_LIMIT_CAPACITY)
                refill = (now - last_time) * (config.RATE_LIMIT_REFILL_AMOUNT / config.RATE_LIMIT_REFILL_PERIOD)
                tokens = min(float(config.RATE_LIMIT_CAPACITY), curr_tokens + refill)
                
                render_html(f"""
                <div class='quota-card'>
                    <div class='quota-metric-label'>Remaining Tokens</div>
                    <div class='quota-metric-value' style='color: #0284C7;'>{tokens:.1f} <span style='font-size: 0.5em; color: #64748B;'>/ {config.RATE_LIMIT_CAPACITY}</span></div>
                    <div style='font-size: 0.82em; color: #64748B;'>Refills {config.RATE_LIMIT_REFILL_AMOUNT} / hour · Only 2 resources shown</div>
                </div>
                """)

        with m3:
            render_html(f"""
            <div class='quota-card'>
                <div class='quota-metric-label'>Lifetime Claims Verified</div>
                <div class='quota-metric-value' style='color: #7C3AED;'>{total_checks}</div>
                <div style='font-size: 0.82em; color: #64748B;'>Recorded in Encrypted Audit Trail</div>
            </div>
            """)

        st.markdown("---")

        # 3. Real-Time Token & Quota Management Section
        st.markdown(f"### {icon_md(BOLT)} Real-Time Plan Quotas & Token Bucket Status")
        st.markdown("ClaimShield AI enforces commercial plan quotas: **Free Plan** has a 3-token capacity with 2 displayed resources, while **Pro Plan** enjoys unlimited verification quota and up to 5 verified resources displayed.")

        if current_role in ["pro", "premium", "newsroom_admin"]:
            render_html(f"""
            <div class='glass-card' style='border-left: 6px solid #059669; background: var(--glass-surface-tint-success);'>
                <h4 style='color: #059669; margin-top: 0;'><span class="material-symbols-rounded">rocket_launch</span> Unlimited Pro Plan Active</h4>
                <p style='color: #334155; line-height: 1.6; margin-bottom: 0;'>
                    Your account is subscribed to the <strong>Pro Plan</strong>. You have zero request throttles, priority execution in the verification queue, and display of at least 3 (if available) and up to 5 maximum verified resources per query.
                </p>
            </div>
            """)
        else:
            # Free user live token simulation & progress bar
            now = time.time()
            last_time = user_info.get("last_request_time", 0.0) if user_info else 0.0
            curr_tokens = user_info.get("tokens", float(config.RATE_LIMIT_CAPACITY)) if user_info else float(config.RATE_LIMIT_CAPACITY)
            refill = (now - last_time) * (config.RATE_LIMIT_REFILL_AMOUNT / config.RATE_LIMIT_REFILL_PERIOD)
            tokens = min(float(config.RATE_LIMIT_CAPACITY), curr_tokens + refill)
            
            progress_val = min(max(tokens / config.RATE_LIMIT_CAPACITY, 0.0), 1.0)
            
            # Quota Box
            q_col1, q_col2 = st.columns([3, 2])
            with q_col1:
                st.markdown(f"**Token Capacity Utilization ({tokens:.1f} / {config.RATE_LIMIT_CAPACITY} available)**")
                st.progress(progress_val)
                st.caption(f"Refill rate: **{config.RATE_LIMIT_REFILL_AMOUNT} tokens per hour** ({config.RATE_LIMIT_REFILL_PERIOD/config.RATE_LIMIT_REFILL_AMOUNT:.0f} seconds per token) · Displays only 2 resources.")
            
            with q_col2:
                if tokens < config.RATE_LIMIT_CAPACITY:
                    needed = config.RATE_LIMIT_CAPACITY - tokens
                    seconds_to_full = needed * (config.RATE_LIMIT_REFILL_PERIOD / config.RATE_LIMIT_REFILL_AMOUNT)
                    mins_to_full = int(seconds_to_full / 60)
                    st.info(f"{icon_md(HOURGLASS_TOP)} Estimated time until 100% capacity: **~{mins_to_full} minutes**.")
                else:
                    st.success(f"{icon_md(CHECK_CIRCLE)} Your token bucket is currently at **100% full capacity (3 tokens)**.")

        st.markdown("---")

        # 4. Plan Changing & Subscription Switcher
        st.markdown(f"### {icon_md(DIAMOND)} Subscription Plan Switcher")
        st.markdown("Switch between plans instantly with real-time role updates and quota privileges.")

        p_col1, p_col2 = st.columns(2)

        # Plan 1: Free Plan
        with p_col1:
            is_active_free = (current_role == "user")
            card_class = "plan-card plan-card-active" if is_active_free else "plan-card"
            active_tag_html = "<div class='plan-active-tag'>Active Plan</div>" if is_active_free else ""
            
            render_html(f"""
            <div class='{card_class}' style='overflow: visible;'>
                {active_tag_html}
                <div>
                    <h4>Free Plan</h4>
                    <div class='plan-price-tag' style='color: #0F172A;'>&#36;0</div>
                    <p style='color: #64748B; font-size: 0.85em;'>Essential tools for individual fact-checkers</p>
                    <ul class='plan-feature-list'>
                        <li><strong>3 verification tokens</strong> capacity</li>
                        <li><strong>Displays only 2 resources</strong> per claim</li>
                        <li>Refills 3 tokens / hour</li>
                        <li>Standard NLP & spaCy extraction</li>
                        <li>FAISS vector similarity search</li>
                        <li>Encrypted audit logging</li>
                    </ul>
                </div>
            </div>
            """)
            
            if is_active_free:
                st.button("Current Active Plan", icon=f":material/{CHECK_CIRCLE}:", key="btn_free_active", disabled=True, use_container_width=True)
            else:
                if st.button("Downgrade to Free Plan", key="btn_free_downgrade", use_container_width=True):
                    db.update_user_tokens(st.session_state.username, float(config.RATE_LIMIT_CAPACITY), time.time())
                    db.update_user_role(st.session_state.username, "user")
                    st.session_state.role = "user"
                    st.session_state.jwt_token = generate_jwt(st.session_state.username, "user")
                    st.session_state.flash = "Successfully switched to Free Plan!"
                    st.rerun()

        # Plan 2: Pro Plan
        with p_col2:
            is_active_pro = (current_role in ["pro", "premium", "newsroom_admin"])
            card_class = "plan-card plan-card-active" if is_active_pro else "plan-card"
            active_tag_html = "<div class='plan-active-tag'>Active Plan</div>" if is_active_pro else "<div class='plan-popular-tag'>Popular</div>"
            
            render_html(f"""
            <div class='{card_class}' style='border-color: #4F46E5; overflow: visible;'>
                {active_tag_html}
                <div>
                    <h4>Pro Plan</h4>
                    <div class='plan-price-tag' style='color: #4F46E5;'>&#36;19<span style='font-size: 0.45em; color: #64748B;'>/mo</span></div>
                    <p style='color: #64748B; font-size: 0.85em;'>For freelance reporters, researchers and journalists</p>
                    <ul class='plan-feature-list'>
                        <li><strong>Unlimited</strong> verification checks</li>
                        <li><strong>Displays at least 3 (if available) & up to 5 max</strong></li>
                        <li>Bypassed token bucket rate limits</li>
                        <li>Priority LLM execution queue</li>
                        <li>Multi-Agent Persona Debate & LangGraph</li>
                    </ul>
                </div>
            </div>
            """)
            
            if is_active_pro:
                st.button("Current Active Plan", icon=f":material/{CHECK_CIRCLE}:", key="btn_pro_active", disabled=True, use_container_width=True)
            else:
                if st.button("Upgrade to Pro Plan", icon=f":material/{BOLT}:", key="btn_pro_upgrade", use_container_width=True):
                    db.update_user_role(st.session_state.username, "pro")
                    st.session_state.role = "pro"
                    st.session_state.jwt_token = generate_jwt(st.session_state.username, "pro")
                    st.session_state.flash = "Successfully upgraded to Pro Plan! Rate limits bypassed & full 3–5 resource display enabled."
                    st.rerun()

        st.markdown("---")

        # 5. Plan Comparison Matrix Table
        st.markdown(f"### {icon_md(BAR_CHART)} Subscription Plan Comparison Matrix")
        render_html("""
        <table class='matrix-table'>
            <thead>
                <tr>
                    <th>Feature / Capability</th>
                    <th>Free Plan (&#36;0)</th>
                    <th style='color: #4F46E5;'>Pro Plan (&#36;19/mo)</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>Verification Quota</strong></td>
                    <td>3 Checks / Bucket (3/hr refill)</td>
                    <td><strong style='color: #4F46E5;'>Unlimited</strong></td>
                </tr>
                <tr>
                    <td><strong>Resources Displayed</strong></td>
                    <td>Only 2 Resources</td>
                    <td><strong style='color: #4F46E5;'>At least 3 (if available) · 5 Maximum</strong></td>
                </tr>
                <tr>
                    <td><strong>Rate Limiter Status</strong></td>
                    <td>Token-Bucket Active (3 capacity)</td>
                    <td>Bypassed (Zero Throttles)</td>
                </tr>
                <tr>
                    <td><strong>LLM Verification Models</strong></td>
                    <td>Standard Heuristic + LLM</td>
                    <td>Priority Gemini / Groq Queue</td>
                </tr>
                <tr>
                    <td><strong>FAISS Vector Search & Retrieval</strong></td>
                    <td>Top 3 Articles retrieved (2 displayed)</td>
                    <td>Top 5 Articles retrieved (3–5 displayed)</td>
                </tr>
                <tr>
                    <td><strong>Persona Debate (FactChecker → Critic → Consensus)</strong></td>
                    <td>Standard Sequential</td>
                    <td><span class="material-symbols-rounded">check_circle</span> Full Consensus Debate</td>
                </tr>
                <tr>
                    <td><strong>LangGraph Stateful Graph</strong></td>
                    <td>Standard Graph</td>
                    <td><span class="material-symbols-rounded">check_circle</span> Full Graph Execution</td>
                </tr>
                <tr>
                    <td><strong>Audit Trail Encryption</strong></td>
                    <td>Fernet AES-128-CBC</td>
                    <td>Fernet AES-128-CBC + Telemetry</td>
                </tr>
            </tbody>
        </table>
        """)

        st.markdown("---")

        # 6. Security & Session Credentials Section
        st.markdown(f"### {icon_md(LOCK)} Security, Credentials & Session Management")
        
        sec_col1, sec_col2 = st.columns(2)

        with sec_col1:
            render_html("""
            <div class='glass-card'>
                <h4 style='color: #4F46E5; margin-top: 0;'><span class="material-symbols-rounded">shield</span> Session JWT Token Inspector</h4>
                <p style='font-size: 0.88em; color: #475569;'>
                    Your session is protected with JSON Web Tokens (JWT) signed via HMAC-SHA256 with 60-minute automated expiration.
                </p>
            </div>
            """)

            
        with sec_col2:
            render_html("""
            <div class='glass-card'>
                <h4 style='color: #059669; margin-top: 0;'><span class="material-symbols-rounded">key</span> Update Account Password</h4>
                <p style='font-size: 0.88em; color: #475569;'>
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

        # 7. Member Directory & Role Manager (Visible to newsroom_admin)
        if current_role == "newsroom_admin":
            st.markdown("---")
            st.markdown(f"### {icon_md(GROUP)} Member Directory & Access Management")
            st.markdown("Administrator console for reviewing registered member accounts and managing their subscription plan.")

            all_users = db.get_all_users()
            if all_users:
                st.markdown(f"**Total Registered Members:** `{len(all_users)}`")
                
                # Render clean user directory
                for u in all_users:
                    u_role = u.get("role", "user")
                    u_tokens = u.get("tokens", float(config.RATE_LIMIT_CAPACITY))
                    is_pro_member = u_role in ["pro", "premium", "newsroom_admin"]
                    
                    role_badge_class = "role-tag-premium" if is_pro_member else "role-tag-user"
                    display_role_label = "PRO PLAN" if is_pro_member else "FREE PLAN"
                    token_label = "Unlimited" if is_pro_member else f"{u_tokens:.1f} / {config.RATE_LIMIT_CAPACITY}"

                    render_html(f"""
                    <div class='admin-user-card'>
                        <div>
                            <strong style='font-size: 1.05em; color: #0F172A;'>{u['username']}</strong>
                            <span style='color: #64748B; font-size: 0.85em; margin-left: 10px;'>ID: #{u['id']}</span>
                        </div>
                        <div style='display: flex; align-items: center; gap: 15px;'>
                            <span style='color: #475569; font-size: 0.85em;'>Quota: <strong>{token_label}</strong></span>
                            <span class='{role_badge_class}'>{display_role_label}</span>
                        </div>
                    </div>
                    """)
                
                # Admin Fast Role Editor
                with st.expander(f"{icon_md(CONSTRUCTION)} Member Plan Modifier"):
                    usernames_list = [u["username"] for u in all_users]
                    selected_target_user = st.selectbox("Select User Account", usernames_list)
                    selected_new_role = st.selectbox(
                        "Assign Subscription Plan",
                        ["user", "pro"],
                        format_func=lambda x: "Free Plan (3 capacity, 2 resources displayed)" if x == "user" else "Pro Plan (Unlimited, 3–5 resources displayed)"
                    )
                    if st.button("Apply Plan Change", key="admin_apply_role"):
                        db.update_user_role(selected_target_user, selected_new_role)
                        st.session_state.flash = f"Updated user '{selected_target_user}' plan to '{'Pro Plan' if selected_new_role == 'pro' else 'Free Plan'}'."
                        st.rerun()

    # -------------------------------------------------------------------------
    # PAGE 3: SYSTEM AUDIT LOGS
    # -------------------------------------------------------------------------
    elif st.session_state.current_page == PAGE_AUDIT:
        render_html("""
        <div class='glass-card' style='border-left: 5px solid #10B981; margin-bottom: 22px; background: var(--glass-surface-tint-success);'>
            <div style='display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;'>
                <div>
                    <h3 style='margin: 0 0 4px 0; color: #065F46; font-size: 1.25em;'><span class="material-symbols-rounded">shield</span> Cryptographic Verification Ledger</h3>
                    <p style='color: #047857; margin: 0; font-size: 0.88em; line-height: 1.5;'>
                        Immutable audit trail. Every verified query, model reasoning trace, and citation is encrypted at rest using <strong>Fernet AES-128-CBC</strong>.
                    </p>
                </div>
                <div style='display: flex; gap: 8px; flex-wrap: wrap;'>
                    <span class='verdict-badge' style='background: rgba(16, 185, 129, 0.2); color: #047857; border: 1px solid rgba(16, 185, 129, 0.4); font-size: 0.74em;'>
                        <span class="material-symbols-rounded">lock</span> Fernet AES-128-CBC
                    </span>
                    <span class='verdict-badge' style='background: rgba(79, 70, 229, 0.15); color: #4338CA; border: 1px solid rgba(79, 70, 229, 0.35); font-size: 0.74em;'>
                        <span class="material-symbols-rounded">generating_tokens</span> PBKDF2 Salted
                    </span>
                </div>
            </div>
        </div>
        """)
        
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
                if verdict in ["Supported", "True"]:
                    v_class = "verdict-supported"
                elif verdict in ["Contradicted", "False"]:
                    v_class = "verdict-contradicted"
                elif verdict in ["Answered", "General Info"]:
                    v_class = "verdict-answered"
                
                expander_label = f"{icon_md(SCHEDULE)} {l['timestamp']} ── Claim: \"{l['claim'][:65]}...\""
                with st.expander(expander_label):
                    render_html(f"""
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; flex-wrap: wrap; gap: 8px; border-bottom: 1px solid rgba(226,232,240,0.8); padding-bottom: 10px;">
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <span class="verdict-badge {v_class}">{verdict}</span>
                            <span style="font-family:'JetBrains Mono',monospace; font-size: 0.78em; color: #64748B; background: rgba(241,245,249,0.85); padding: 4px 10px; border-radius: 9999px; border: 1px solid rgba(226,232,240,0.85);">
                                UTC: {l['timestamp']}
                            </span>
                        </div>
                        <div style="display: inline-flex; align-items: center; gap: 6px; background: rgba(255, 255, 255, 0.75); padding: 4px 12px; border-radius: 9999px; border: 1px solid var(--glass-border); font-size: 0.85em;">
                            <span style="color: #64748B; font-weight: 600;">Certainty:</span>
                            <strong style="color: #0F172A;">{int(l['confidence']*100)}%</strong>
                        </div>
                    </div>
                    <div style="background: rgba(255, 255, 255, 0.5); border-left: 4px solid #4F46E5; padding: 12px 16px; border-radius: 10px; margin-bottom: 14px;">
                        <div style="font-size: 0.78em; color: #4F46E5; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 4px;">Audited Model Rationale</div>
                        <div style="font-size: 0.94em; color: #1E293B; line-height: 1.6;">
                            {details.get('summary', 'No reasoning logged.')}
                        </div>
                    </div>
                    """)
                    
                    if details.get("entities"):
                        st.markdown(f"**{icon_md(SELL)} Extracted Named Entities:**")
                        ents_html = "<div style='display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px;'>"
                        for ent in details["entities"]:
                            if not isinstance(ent, dict):
                                continue
                            ents_html += f"<span class='verdict-badge badge-secondary' style='font-size: 0.78em;'>{ent.get('text','')} <span style='opacity: 0.7;'>({ent.get('label','MISC')})</span></span>"
                        ents_html += "</div>"
                        render_html(ents_html)

                    if details.get("articles_retrieved"):
                        st.markdown(f"**{icon_md(NEWSPAPER)} Referenced Source Articles (FAISS Cosine Similarity):**")
                        for s in details["articles_retrieved"]:
                            if not isinstance(s, dict):
                                continue
                            st.markdown(f"- **{s.get('source','Unknown')}**: {s.get('title','')} `(Score: {s.get('score', 0.0):.4f})`")

    # -------------------------------------------------------------------------
    # PAGE 4: A2A PROTOCOL MONITOR
    # -------------------------------------------------------------------------
    elif st.session_state.current_page == PAGE_A2A:
        st.markdown(f"### {icon_md(SETTINGS)} Multi-Agent A2A/1.0 Protocol Message Tracing")
        st.markdown("""
        Inspect the real-time JSON communications occurring between subagents using the **A2A/1.0 (Agent-to-Agent)** protocol.
        Each message includes a protocol version, unique message ID (UUID4), Unix timestamp, sender/recipient identifiers, action verb, and structured data payload.
        """)

        st.markdown("""
        <div class='glass-card' style='border-left: 4px solid #4F46E5;'>
            <h4 style='color: #4F46E5; margin-bottom: 10px;'><span class="material-symbols-rounded">assignment</span> A2A/1.0 Protocol Specification</h4>
            <table style='width: 100%; border-collapse: collapse; color: #1E293B; font-size: 0.9em;'>
                <tr style='border-bottom: 1px solid rgba(226,232,240,0.85);'>
                    <td style='padding: 8px; font-weight: 600; color: #4F46E5; width: 25%;'>Protocol</td>
                    <td style='padding: 8px;'>A2A/1.0 — Agent-to-Agent messaging over in-process Python function calls</td>
                </tr>
                <tr style='border-bottom: 1px solid rgba(226,232,240,0.85);'>
                    <td style='padding: 8px; font-weight: 600; color: #4F46E5;'>Serialization</td>
                    <td style='padding: 8px;'>JSON — validated via dumps/loads round-trip for strict compliance</td>
                </tr>
                <tr style='border-bottom: 1px solid rgba(226,232,240,0.85);'>
                    <td style='padding: 8px; font-weight: 600; color: #4F46E5;'>Message ID</td>
                    <td style='padding: 8px;'>UUID4 — unique identifier for every message for end-to-end traceability</td>
                </tr>
                <tr style='border-bottom: 1px solid rgba(226,232,240,0.85);'>
                    <td style='padding: 8px; font-weight: 600; color: #4F46E5;'>Timestamp</td>
                    <td style='padding: 8px;'>Unix epoch float — precise timing for performance profiling</td>
                </tr>
                <tr>
                    <td style='padding: 8px; font-weight: 600; color: #4F46E5;'>Transport</td>
                    <td style='padding: 8px;'>In-process function invocation — zero-latency delivery via BaseAgent.send_message()</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
        
        if not st.session_state.agent_logs:
            st.info("No query logs in buffer. Run a claim check from the Verification Dashboard to monitor agent communication flows.")
        else:
            for idx, log in enumerate(st.session_state.agent_logs):
                with st.expander(f"{icon_md(PUBLIC)} Trace #{idx+1} [{log['timestamp']}]: {log['from']} {icon_md(ARROW_FORWARD)} {log['to']} (Action: {log['action']})"):
                    col_sent, col_recv = st.columns(2)
                    with col_sent:
                        st.markdown(f"{icon_md(OUTBOX)} **Outgoing A2A/1.0 Message:**")
                        st.json({
                            "protocol": "A2A/1.0",
                            "sender": log["from"],
                            "recipient": log["to"],
                            "action": log["action"],
                            "data": log["data_sent"]
                        })
                    with col_recv:
                        st.markdown(f"{icon_md(INBOX)} **Received Response Payload:**")
                        st.json(log["response_received"])

    # -------------------------------------------------------------------------
    # PAGE 5: RESPONSIBLE AI & GOVERNANCE
    # -------------------------------------------------------------------------
    elif st.session_state.current_page == PAGE_RESPONSIBLE_AI:
        st.markdown(f"### {icon_md(SMART_TOY)} Responsible AI — Ethics, Transparency & Data Protection")
        st.markdown("ClaimShield AI is built with Responsible AI principles at its core. This section documents how our system addresses fairness, explainability, transparency, and user data protection.")

        rai1, rai2 = st.columns(2)

        with rai1:
            render_html("""
            <div class='glass-card' style='border-left: 5px solid #059669;'>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;'>
                    <h4 style='color: #059669; margin: 0; font-size: 1.15em;'><span class="material-symbols-rounded">search</span> Transparency & Auditability</h4>
                    <span class='verdict-badge' style='background: rgba(16, 185, 129, 0.15); color: #047857; border: 1px solid rgba(16, 185, 129, 0.35); font-size: 0.74em;'>
                        <span class="material-symbols-rounded">check_circle</span> Fully Traceable
                    </span>
                </div>
                <p style='color: #475569; font-size: 0.9em; line-height: 1.6; margin-bottom: 12px;'>
                    Every verification decision is completely auditable and end-to-end inspectable:
                </p>
                <ul style='color: #334155; line-height: 1.8; font-size: 0.9em; padding-left: 20px; margin-bottom: 0;'>
                    <li>Complete agent-to-agent communication logs (A2A/1.0 protocol)</li>
                    <li>Retrieved source articles with cosine similarity scores & URLs</li>
                    <li>The exact LLM prompt and processing engine used</li>
                    <li>NER entities and search queries derived from claims</li>
                    <li>Extractive evidence summaries generated by the NLP pipeline</li>
                </ul>
            </div>
            """)

            render_html("""
            <div class='glass-card' style='border-left: 5px solid #D97706;'>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;'>
                    <h4 style='color: #D97706; margin: 0; font-size: 1.15em;'><span class="material-symbols-rounded">balance</span> Algorithmic Fairness</h4>
                    <span class='verdict-badge' style='background: rgba(245, 158, 11, 0.15); color: #B45309; border: 1px solid rgba(245, 158, 11, 0.35); font-size: 0.74em;'>
                        <span class="material-symbols-rounded">balance</span> Uniform Verification
                    </span>
                </div>
                <p style='color: #334155; line-height: 1.65; font-size: 0.9em; margin-bottom: 0;'>
                    ClaimShield applies the <strong>same verification pipeline</strong> to all users regardless of subscription tier.
                    Commercial plans differ only by request capacity and display depth (Free: 3 capacity displaying 2 resources; Pro: unlimited displaying 3–5 resources), but the NLP analysis,
                    FAISS retrieval algorithm, and LLM verification logic are strictly identical for every query.
                    No user demographic data influences the fact-checking verdict.
                </p>
            </div>
            """)

            render_html("""
            <div class='glass-card' style='border-left: 5px solid #4F46E5;'>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;'>
                    <h4 style='color: #4F46E5; margin: 0; font-size: 1.15em;'><span class="material-symbols-rounded">psychology</span> Grounding & Bias Mitigation</h4>
                    <span class='verdict-badge' style='background: rgba(79, 70, 229, 0.15); color: #4338CA; border: 1px solid rgba(79, 70, 229, 0.35); font-size: 0.74em;'>
                        <span class="material-symbols-rounded">shield</span> Multi-LLM Consensus
                    </span>
                </div>
                <p style='color: #475569; font-size: 0.9em; line-height: 1.6; margin-bottom: 12px;'>
                    To systematically eliminate cognitive and model bias in verification outcomes:
                </p>
                <ul style='color: #334155; line-height: 1.8; font-size: 0.9em; padding-left: 20px; margin-bottom: 0;'>
                    <li>The LLM is <strong>grounded in retrieved evidence</strong> — verdicts must cite specific article quotes rather than unverified pre-trained memory</li>
                    <li>Multi-source retrieval ensures diverse, authoritative perspectives are considered</li>
                    <li>Confidence metrics mathematically quantify certainty, preventing overconfident claims</li>
                    <li>Categorical classification (Supported/Contradicted/Unclear) avoids binary bias</li>
                </ul>
            </div>
            """)

        with rai2:
            render_html("""
            <div class='glass-card' style='border-left: 5px solid #7C3AED;'>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;'>
                    <h4 style='color: #7C3AED; margin: 0; font-size: 1.15em;'><span class="material-symbols-rounded">lightbulb</span> Multi-Layer Explainability</h4>
                    <span class='verdict-badge' style='background: rgba(124, 58, 237, 0.15); color: #6D28D9; border: 1px solid rgba(124, 58, 237, 0.35); font-size: 0.74em;'>
                        <span class="material-symbols-rounded">menu_book</span> Transparent Rationale
                    </span>
                </div>
                <p style='color: #475569; font-size: 0.9em; line-height: 1.6; margin-bottom: 12px;'>
                    Every fact-check verdict generated by ClaimShield AI includes complete transparency attributes:
                </p>
                <ul style='color: #334155; line-height: 1.8; font-size: 0.9em; padding-left: 20px; margin-bottom: 0;'>
                    <li><strong>Categorical Verdict</strong> — Supported, Contradicted, Direct Answer, or Unclear</li>
                    <li><strong>Confidence Score</strong> — Quantified probabilistic certainty (0–100%)</li>
                    <li><strong>Summary Reasoning</strong> — Multi-sentence explanation of the verdict rationale</li>
                    <li><strong>Inline Citations</strong> — Exact verbatim quotes from verified source articles</li>
                    <li><strong>Named Entities</strong> — spaCy NER extractions showing concepts parsed by AI</li>
                    <li><strong>Extractive Evidence Highlights</strong> — Key supporting statements synthesized</li>
                </ul>
            </div>
            """)

            render_html("""
            <div class='glass-card' style='border-left: 5px solid #DC2626;'>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;'>
                    <h4 style='color: #DC2626; margin: 0; font-size: 1.15em;'><span class="material-symbols-rounded">lock</span> Cryptographic Security</h4>
                    <span class='verdict-badge' style='background: rgba(239, 68, 68, 0.15); color: #B91C1C; border: 1px solid rgba(239, 68, 68, 0.35); font-size: 0.74em;'>
                        <span class="material-symbols-rounded">shield</span> Defense in Depth
                    </span>
                </div>
                <p style='color: #475569; font-size: 0.9em; line-height: 1.6; margin-bottom: 12px;'>
                    User session and telemetry data are safeguarded through multi-layered defenses:
                </p>
                <ul style='color: #334155; line-height: 1.8; font-size: 0.9em; padding-left: 20px; margin-bottom: 0;'>
                    <li><strong>Password Hashing</strong> — PBKDF2-SHA256 with random salt (100,000 iterations)</li>
                    <li><strong>Session Tokens</strong> — Signed JWT (HS256) with 60-minute automated expiry</li>
                    <li><strong>Encryption at Rest</strong> — Fernet symmetric AES encryption for audit log payloads</li>
                    <li><strong>Input Sanitization</strong> — XSS, HTML, and script injection stripping with length bounds</li>
                    <li><strong>Rate Limiting</strong> — Token-bucket capacity enforcement prevents API denial-of-service</li>
                </ul>
            </div>
            """)

            render_html("""
            <div class='glass-card' style='border-left: 5px solid #0284C7;'>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;'>
                    <h4 style='color: #0284C7; margin: 0; font-size: 1.15em;'><span class="material-symbols-rounded">person</span> User Data Rights & Privacy</h4>
                    <span class='verdict-badge' style='background: rgba(2, 132, 199, 0.15); color: #0369A1; border: 1px solid rgba(2, 132, 199, 0.35); font-size: 0.74em;'>
                        <span class="material-symbols-rounded">assignment</span> Privacy Protected
                    </span>
                </div>
                <p style='color: #475569; font-size: 0.9em; line-height: 1.6; margin-bottom: 12px;'>
                    In strict alignment with ethical data governance principles:
                </p>
                <ul style='color: #334155; line-height: 1.8; font-size: 0.9em; padding-left: 20px; margin-bottom: 0;'>
                    <li>Users retain full visibility into their verification history via encrypted audit logs</li>
                    <li>All personal data is persisted in private storage (SQLite local / Supabase cloud)</li>
                    <li>Zero user telemetry is commercialized or sold to third-party data brokers</li>
                    <li>Users may update credentials or request purge of verification logs at any time</li>
                </ul>
            </div>
            """)

        render_html("""
        <div class='glass-card' style='border: 1px solid rgba(5, 150, 105, 0.40); background: var(--glass-surface-tint-success); text-align: center; padding: 28px 24px; margin-top: 10px;'>
            <div style='display: inline-flex; align-items: center; justify-content: center; width: 44px; height: 44px; border-radius: 50%; background: linear-gradient(135deg, #059669, #047857); color: white; font-size: 1.3em; margin-bottom: 10px; box-shadow: 0 4px 14px rgba(5,150,105,0.25);'>
                <span class="material-symbols-rounded">public</span>
            </div>
            <h3 style='color: #065F46; font-size: 1.3em; margin: 0 0 8px 0;'>Responsible AI Commitment</h3>
            <p style='color: #047857; font-size: 0.95em; line-height: 1.65; max-width: 780px; margin: 0 auto;'>
                ClaimShield AI is built from the ground up for ethical, evidence-based verification. We prioritize human editorial oversight,
                transparent provenance, and algorithmic integrity. Our multi-agent system empowers human judgment — it never supplants it.
            </p>
        </div>
        """)
