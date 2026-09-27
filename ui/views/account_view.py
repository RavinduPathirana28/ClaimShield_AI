"""
ClaimShield AI — User Account & Plan Management View.
"""

from __future__ import annotations

import time
import streamlit as st
from app import config
from app.utils.security import verify_password, hash_password, generate_jwt
from ui.views.common import (
    render_clean_html,
    render_html,
    icon_md,
    PAGE_ACCOUNT,
    PERSON,
    BAR_CHART,
    CHECK_CIRCLE,
    LOCK,
    BOLT,
    HOURGLASS_TOP,
    DIAMOND,
    STAR,
    CARD_MEMBERSHIP,
    GROUP,
    CONSTRUCTION,
    ARROW_FORWARD,
)


def render_account_page(db):
    """Renders user profile, token quotas, plan upgrade cards, and password change form."""
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
        <div class='{card_class}' style='border: 2px solid rgba(148, 163, 184, 0.35); overflow: visible;'>
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
        <div class='{card_class}' style='border: 2px solid #4F46E5; overflow: visible;'>
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
                st.session_state.checkout_plan = "pro"
                st.session_state.checkout_flow = "checkout"
                st.session_state.checkout_receipt = None
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

