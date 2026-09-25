"""
ClaimShield AI — Multi-Agent Fact Verification System.
Main UI Entry Point & Page Router.
"""

from __future__ import annotations

import sys
from pathlib import Path
import streamlit as st

# Add root folder to sys.path to enable app module imports
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from ui.views import (
    PAGE_VERIFICATION,
    PAGE_ACCOUNT,
    PAGE_AUDIT,
    PAGE_A2A,
    PAGE_RESPONSIBLE_AI,
    get_db,
    get_orchestrator,
    set_transition_ph,
    render_clean_html,
    build_boot_splash_html,
    render_landing_page,
    render_auth_sidebar,
    render_authenticated_sidebar,
    render_checkout_page,
    render_verification_page,
    render_account_page,
    render_audit_page,
    render_a2a_page,
    render_responsible_ai_page,
)

# -----------------------------------------------------------------------------
# Streamlit Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="ClaimShield AI — Fact Checker & User Management",
    page_icon=":material/shield:",
    layout="wide",
    initial_sidebar_state="expanded"
)


def load_css():
    """Injects custom application stylesheet."""
    css_path = ROOT_DIR / "ui" / "style.css"
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


load_css()

# Shared full-viewport placeholder for async transition overlays
TRANSITION_PH = st.empty()
set_transition_ph(TRANSITION_PH)

# -----------------------------------------------------------------------------
# Initial Boot Splash & Singletons
# -----------------------------------------------------------------------------
if "boot_splash_shown" not in st.session_state:
    st.session_state.boot_splash_shown = True
    render_clean_html(build_boot_splash_html())

db = get_db()
orchestrator = get_orchestrator()

# -----------------------------------------------------------------------------
# Session State Initialization
# -----------------------------------------------------------------------------
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
if "nav_selection" not in st.session_state:
    st.session_state.nav_selection = PAGE_VERIFICATION
if "nav_radio" not in st.session_state:
    st.session_state.nav_radio = PAGE_VERIFICATION
if "nav_target" not in st.session_state:
    st.session_state.nav_target = None
if "_prev_page" not in st.session_state:
    st.session_state._prev_page = PAGE_VERIFICATION
if "flash" not in st.session_state:
    st.session_state.flash = None
if "show_access_portal" not in st.session_state:
    st.session_state.show_access_portal = False

# Payment gateway flow state: None | "checkout" | "success"
if "checkout_flow" not in st.session_state:
    st.session_state.checkout_flow = None
if "checkout_plan" not in st.session_state:
    st.session_state.checkout_plan = "pro"
if "checkout_receipt" not in st.session_state:
    st.session_state.checkout_receipt = None

# Guest portal preselects
if "portal_mode" not in st.session_state:
    st.session_state.portal_mode = "Login"
if "portal_plan" not in st.session_state:
    st.session_state.portal_plan = "user"

# Flash message banner across reruns
_flash_msg = st.session_state.get("flash")
if _flash_msg:
    st.session_state.flash = None
    st.success(_flash_msg)

# -----------------------------------------------------------------------------
# Landing Page: Access Portal Drawer Styles & Client Script
# -----------------------------------------------------------------------------
if not st.session_state.authenticated:
    is_portal_open = st.session_state.get("show_access_portal", False)
    transform_val = "translateX(0)" if is_portal_open else "translateX(-105%)"
    opacity_val = "1" if is_portal_open else "0"
    pointer_val = "auto" if is_portal_open else "none"

    st.markdown(f"""
    <style>
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

    div[data-testid="collapsedControl"],
    button[data-testid="stExpandSidebarButton"],
    button[data-testid="stSidebarCollapseButton"] {{
        display: none !important;
    }}
    </style>
    """, unsafe_allow_html=True)

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

# -----------------------------------------------------------------------------
# Sidebar: Auth or Navigation
# -----------------------------------------------------------------------------
with st.sidebar:
    if not st.session_state.authenticated:
        render_auth_sidebar(orchestrator)
    else:
        render_authenticated_sidebar(db)

# -----------------------------------------------------------------------------
# Main Application Content Router
# -----------------------------------------------------------------------------
if not st.session_state.authenticated:
    render_landing_page(db)
else:
    # 1. Checkout Flow (overrides normal page dispatch)
    if st.session_state.get("checkout_flow") in ("checkout", "success"):
        render_checkout_page(db)
    else:
        # Subtle top progress sweep on page transitions
        if st.session_state.get("current_page") != st.session_state.get("_prev_page"):
            st.session_state._prev_page = st.session_state.get("current_page")
            render_clean_html('<div class="cs-nav-bar"><div class="cs-nav-fill"></div></div>')

        # 2. Page Router
        current_page = st.session_state.get("current_page", PAGE_VERIFICATION)
        if current_page == PAGE_VERIFICATION:
            render_verification_page(db, orchestrator)
        elif current_page == PAGE_ACCOUNT:
            render_account_page(db)
        elif current_page == PAGE_AUDIT:
            render_audit_page(db)
        elif current_page == PAGE_A2A:
            render_a2a_page(db)
        elif current_page == PAGE_RESPONSIBLE_AI:
            render_responsible_ai_page()
        else:
            render_verification_page(db, orchestrator)
