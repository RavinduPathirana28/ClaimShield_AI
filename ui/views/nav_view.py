"""
ClaimShield AI — Authenticated User Sidebar & Navigation View.
"""

from __future__ import annotations

import time
import streamlit as st
from app import config
from ui.views.common import (
    LOGO_SRC,
    PAGE_VERIFICATION,
    PAGE_ACCOUNT,
    PAGE_AUDIT,
    PAGE_A2A,
    PAGE_RESPONSIBLE_AI,
    ICON_CARD_MEMBERSHIP,
    ICON_STAR,
    icon_md,
    EXPLORE,
    BOLT,
    SMART_TOY,
    build_transition_overlay_html,
    get_transition_ph,
)


def render_authenticated_sidebar(db):
    """Renders user profile info, page navigation radio, rate limit tokens, engine mode, and logout button."""
    # Re-Show Streamlit's native header/toolbar
    st.markdown("""
    <style>
    body header[data-testid="stHeader"],
    body div[data-testid="stToolbar"] {
        display: flex !important;
        visibility: visible !important;
    }
    </style>
    """, unsafe_allow_html=True)

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
    <div class='glass-card' style='padding: 12px; margin-bottom: 12px;'>
        <div style='display: flex; align-items: center; gap: 11px;'>
            <div style='width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, #4338CA, #2563EB);
                display: flex; align-items: center; justify-content: center; font-weight: 700; color: white; font-size: 1.15em;
                box-shadow: 0 4px 14px rgba(67,56,202,0.25); flex-shrink:0;'>
                {initial_letter}
            </div>
            <div style='min-width: 0;'>
                <div style='font-size: 1.0em; font-weight: 700; color: #0A0F1D; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'>{st.session_state.username}</div>
                <div style='font-size: 0.74em; color: #4338CA; font-weight: 600;'>{role_icon} {role_display}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"#### {icon_md(EXPLORE)} Navigation")

    nav_options = [
        PAGE_VERIFICATION,
        PAGE_ACCOUNT,
        PAGE_AUDIT,
        PAGE_A2A,
        PAGE_RESPONSIBLE_AI
    ]

    # Sync any external navigation request before radio widget instantiation
    if st.session_state.get("nav_target"):
        target_page = st.session_state.pop("nav_target")
        if target_page in nav_options:
            st.session_state.nav_selection = target_page
            st.session_state.current_page = target_page

    # Initialize nav_selection if needed
    if st.session_state.get("nav_selection") not in nav_options:
        curr = st.session_state.get("current_page")
        st.session_state.nav_selection = curr if curr in nav_options else PAGE_VERIFICATION

    def _on_nav_change():
        st.session_state.current_page = st.session_state.nav_selection
        st.session_state.nav_radio = st.session_state.nav_selection

    selected_page = st.radio(
        "Go to Page",
        nav_options,
        label_visibility="collapsed",
        key="nav_selection",
        on_change=_on_nav_change,
    )
    st.session_state.current_page = selected_page
    st.session_state.nav_radio = selected_page

    st.markdown("---")

    # Display current rate limit tokens
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
        logout_ph = get_transition_ph()
        logout_ph.markdown(
            build_transition_overlay_html("Signing Out", "Clearing your secure session…", "logout"),
            unsafe_allow_html=True,
        )
        time.sleep(0.5)
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.role = "user"
        st.session_state.jwt_token = None
        st.session_state.agent_logs = []
        st.session_state.current_page = PAGE_VERIFICATION
        st.session_state.nav_target = PAGE_VERIFICATION
        st.session_state.nav_selection = PAGE_VERIFICATION
        st.session_state.nav_radio = PAGE_VERIFICATION
        st.session_state.show_access_portal = False
        st.session_state.checkout_flow = None
        st.session_state.checkout_receipt = None
        st.rerun()
