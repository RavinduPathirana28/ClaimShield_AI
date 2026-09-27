"""
ClaimShield AI — Shared UI Constants, Helpers, and Resource Getters.
"""

from __future__ import annotations

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
import contextlib
import base64
from pathlib import Path

# Add root folder to sys.path to enable app module imports
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from app.database.db_manager import DBManager
from app.utils.security import verify_jwt, decrypt_data, hash_password, verify_password, generate_jwt
from app.agents.orchestrator import Orchestrator
from app.agents.base_agent import BaseAgent
from app import config
import seed_database
from ui.payment_gateway import (
    PLANS as BILLING_PLANS,
    TEST_CARD_NUMBERS as BILLING_TEST_CARDS,
    validate_card as billing_validate_card,
    process_payment as billing_process_payment,
)
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
_PIPELINE_LOCK = threading.RLock()

# Logo path helper
LOGO_PATH = ROOT_DIR / "ui" / "assets" / "logo.jpg"


@st.cache_data
def get_logo_base64():
    """Returns base64 encoded logo for embedding in HTML."""
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


# Backwards compatibility alias
render_html = render_clean_html


# ---------------------------------------------------------------------------
# Loading UX: boot splash + live step-by-step pipeline loader + transitions
# ---------------------------------------------------------------------------

_PIPELINE_STEPS = [
    ("shield", "Security Check"),
    ("biotech", "Parse & Extract"),
    ("search", "Vector Retrieval"),
    ("menu_book", "Context & Summaries"),
    ("handshake", "Model Consensus"),
    ("fact_check", "Verdict & Audit"),
]

_PIPELINE_ACTION_STEPS = {
    "sanitize": 0,
    "check_rate_limit": 0,
    "process_claim": 1,
    "retrieve": 2,
    "summarize": 3,
    "verify_claim": 4,
    "log_audit": 5,
}

_PIPELINE_ACTION_DETAIL = {
    "sanitize": "Sanitizing claim input",
    "check_rate_limit": "Token-bucket rate limit check",
    "process_claim": "spaCy NER extraction & query generation",
    "retrieve": "FAISS vector search over the corpus",
    "summarize": "Building extractive evidence summary",
    "verify_claim": "Collecting Groq & Gemini verdicts",
    "log_audit": "Persisting encrypted audit trail",
}


def build_pipeline_loader_html(active_step: int = -1, detail: str = "") -> str:
    """Renders the currently-executing step of the verification pipeline."""
    step_rows = []
    for i, (ic, title) in enumerate(_PIPELINE_STEPS):
        if active_step < 0 or i < active_step:
            state_cls, ico, status = "cs-st cs-st-done", "check", "Done"
        elif i == active_step:
            state_cls, ico, status = "cs-st cs-st-active", ic, "Running"
        else:
            state_cls, ico, status = "cs-st cs-st-pending", ic, "Queued"
        step_rows.append(f"""
        <div class="{state_cls}">
            <span class="cs-st-badge"><span class="material-symbols-rounded">{ico}</span></span>
            <span class="cs-st-label">{title}</span>
            <span class="cs-st-status">{status}</span>
        </div>""")
    pct = 0
    if active_step >= 0:
        pct = int(((active_step + 1) / len(_PIPELINE_STEPS)) * 100)
    return f"""
<div class="cs-run-loader">
    <div class="cs-run-head">
        <span class="cs-run-dot"></span>
        <span>Multi-Agent Verification Running</span>
        <span class="cs-run-tag">{pct}%</span>
    </div>
    <div class="cs-steps">{''.join(step_rows)}</div>
    <div class="cs-bar"><div class="cs-bar-fill" style="width:{pct}%;"></div></div>
    <div class="cs-run-detail">{detail}</div>
</div>
"""


def _pipeline_step_for(action: str) -> int:
    return _PIPELINE_ACTION_STEPS.get(action, -1)


_PIPELINE_RUNNER = {"render": None}


def _report_pipeline_step(action: str) -> None:
    render = _PIPELINE_RUNNER.get("render")
    if render is not None:
        render(action)


@contextlib.contextmanager
def _pipeline_loading():
    """Renders a live step-by-step loader for the duration of a synchronous run."""
    placeholder = st.empty()
    state = {"step": -1, "detail": ""}

    def render(action: str):
        step = _pipeline_step_for(action)
        if step >= 0:
            state["step"] = step
            state["detail"] = _PIPELINE_ACTION_DETAIL.get(action, "")
        placeholder.markdown(
            build_pipeline_loader_html(state["step"], state["detail"]),
            unsafe_allow_html=True,
        )

    _PIPELINE_RUNNER["render"] = render
    render("")
    try:
        yield state
    finally:
        placeholder.empty()
        _PIPELINE_RUNNER["render"] = None


def build_transition_overlay_html(title: str, subtitle: str, icon: str) -> str:
    """Branded full-screen overlay for async-looking transitions (login, logout)."""
    return f"""
<div class="cs-page-overlay">
    <div class="cs-overlay-card">
        <span class="material-symbols-rounded cs-overlay-ico">{icon}</span>
        <div class="cs-overlay-title">{title}</div>
        <div class="cs-overlay-sub">{subtitle}</div>
    </div>
</div>
"""


_TRANSITION_PH = None


def set_transition_ph(ph):
    global _TRANSITION_PH
    _TRANSITION_PH = ph


def get_transition_ph():
    global _TRANSITION_PH
    if _TRANSITION_PH is None:
        _TRANSITION_PH = st.empty()
    return _TRANSITION_PH


def run_with_transition(title: str, subtitle: str, icon: str, work, min_seconds: float = 0.7):
    """Executes work behind a branded overlay for at least min_seconds."""
    placeholder = get_transition_ph()
    placeholder.markdown(
        build_transition_overlay_html(title, subtitle, icon),
        unsafe_allow_html=True,
    )
    started = time.time()
    result = work()
    elapsed = time.time() - started
    if elapsed < min_seconds:
        time.sleep(min_seconds - elapsed)
    return result, placeholder


def build_boot_splash_html() -> str:
    """Full-screen branded splash rendered only on the very first script run."""
    return f"""
<div class="cs-boot-splash">
    <div class="cs-splash-orb">
        <div class="cs-splash-ring"></div>
        <img src='{LOGO_SRC}' alt='ClaimShield AI'/>
    </div>
    <div class="cs-splash-title">ClaimShield AI</div>
    <div class="cs-splash-sub">Multi-Agent Fact Verification Platform</div>
</div>
"""


def get_typewriter_subtitle_html(text: str, base_delay: float = 0.25, letter_speed: float = 0.015) -> str:
    """Generates pure CSS hardware-accelerated letter-by-letter typewriter animation."""
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
        from app.generate_pdf import build_verification_report_bytes
        return build_verification_report_bytes(pipeline_result)
    except Exception as e:
        print(f"[UI] PDF report generation unavailable: {e}")
        return None


# System Initializations
@st.cache_resource
def get_orchestrator():
    return Orchestrator(security_agent=None)


@st.cache_resource
def get_db():
    db_inst = DBManager()
    articles = db_inst.get_all_articles()
    if not articles:
        print("Streamlit: Database appears empty. Seeding sample articles and default accounts...")
        seed_database.seed()
        db_inst = DBManager()
        get_orchestrator.clear()
    return db_inst
