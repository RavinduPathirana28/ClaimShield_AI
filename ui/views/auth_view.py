"""
ClaimShield AI — Authentication & Access Portal View (Sidebar).
"""

from __future__ import annotations

import streamlit as st
from ui.views.common import (
    LOGO_SRC,
    PAGE_VERIFICATION,
    run_with_transition,
    icon_md,
    LOCK,
    ROCKET_LAUNCH,
    ARROW_FORWARD,
    CELEBRATION,
)


def render_auth_sidebar(orchestrator):
    """Renders the access portal (login, registration, demo accounts) in the sidebar."""
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

    # Plain session keys so landing "Choose Free/Pro" buttons can preselect the portal
    portal_mode_val = st.session_state.get("portal_mode", "Login")
    auth_mode = st.radio(
        "Access Portal",
        ["Login", "Register"],
        label_visibility="collapsed",
        horizontal=True,
        index=0 if portal_mode_val == "Login" else 1,
    )
    st.session_state.portal_mode = auth_mode

    username_in = st.text_input("Username", placeholder="Enter your username")
    password_in = st.text_input("Password", type="password", placeholder="Enter your password")

    role_select = "user"
    if auth_mode == "Register":
        portal_plan_val = st.session_state.get("portal_plan", "user")
        role_select = st.selectbox(
            "Subscription Plan",
            ["user", "pro"],
            index=0 if portal_plan_val == "user" else 1,
            format_func=lambda x: {
                "user": "Free Plan ($0) — 3 requests, 2 resources displayed",
                "pro": "Pro Plan ($19/mo) — Unlimited, 3–5 resources displayed"
            }[x]
        )
        st.session_state.portal_plan = role_select

    btn_label = "Sign In" if auth_mode == "Login" else "Create Account"
    btn_icon = f":material/{LOCK}:" if auth_mode == "Login" else f":material/{ROCKET_LAUNCH}:"
    if st.button(btn_label, icon=btn_icon, use_container_width=True, type="primary"):
        auth_action = "login" if auth_mode == "Login" else "register"
        pending_pro_checkout = (auth_action == "register" and role_select == "pro")
        auth_role = "user" if pending_pro_checkout else role_select
        auth_msg = {
            "action": "authenticate",
            "data": {
                "username": username_in,
                "password": password_in,
                "auth_action": auth_action,
                "role": auth_role
            }
        }

        def _do_auth() -> dict:
            return orchestrator.security_agent.handle_message(auth_msg)

        auth_overlay_title = "Signing In" if auth_action == "login" else "Creating Account"
        auth_overlay_sub = (
            "Verifying your credentials with the Security Agent…"
            if auth_action == "login"
            else "Registering your account securely…"
        )
        auth_resp, auth_ph = run_with_transition(
            auth_overlay_title, auth_overlay_sub, "key", _do_auth, min_seconds=0.7
        )

        if auth_resp.get("status") == "success":
            st.session_state.authenticated = True
            st.session_state.username = auth_resp["user"]["username"]
            st.session_state.role = auth_resp["user"]["role"]
            st.session_state.jwt_token = auth_resp["token"]
            st.session_state.current_page = PAGE_VERIFICATION
            st.session_state.nav_target = PAGE_VERIFICATION
            st.session_state.nav_radio = PAGE_VERIFICATION
            if pending_pro_checkout:
                st.session_state.checkout_plan = "pro"
                st.session_state.checkout_flow = "checkout"
                st.session_state.flash = f"Account created! Complete the Pro checkout to activate unlimited access. {icon_md(ARROW_FORWARD)}"
            else:
                st.session_state.checkout_flow = None
                st.session_state.checkout_receipt = None
                st.session_state.flash = f"Welcome, {st.session_state.username}! {icon_md(CELEBRATION)}"
            st.rerun()
        else:
            auth_ph.empty()
            st.error(auth_resp.get("message", "Authentication failed."))

    st.markdown("""
    <div class='demo-account-card'>
        <div class='demo-account-role'><span class="material-symbols-rounded">card_membership</span> Free Plan</div>
        <div class='demo-account-creds'>user / password (3 tokens, 2 resources displayed)</div>
    </div>
    <div class='demo-account-card'>
        <div class='demo-account-role'><span class="material-symbols-rounded">star</span> Pro Plan</div>
        <div class='demo-account-creds'>pro / password (Unlimited, 3–5 resources displayed)</div>
    </div>
    """, unsafe_allow_html=True)
