"""
ClaimShield AI — Checkout Flow & Dummy Payment Gateway View.
"""

from __future__ import annotations

import time
import streamlit as st
from app import config
from app.utils.security import generate_jwt
from ui.payment_gateway import (
    PLANS as BILLING_PLANS,
    TEST_CARD_NUMBERS as BILLING_TEST_CARDS,
    validate_card as billing_validate_card,
    process_payment as billing_process_payment,
)
from ui.views.common import (
    render_clean_html,
    render_html,
    PAGE_ACCOUNT,
    PAGE_VERIFICATION,
    icon_md,
    CARD_MEMBERSHIP,
    LOCK,
    CANCEL,
    CHECK_CIRCLE,
    ARROW_FORWARD,
    PERSON,
)


def render_checkout_page(db):
    """Renders the checkout form or payment confirmation screen."""
    flow_state = st.session_state.get("checkout_flow")

    if flow_state == "checkout":
        checkout_plan = st.session_state.get("checkout_plan", "pro")
        plan_info = BILLING_PLANS.get(checkout_plan, BILLING_PLANS["pro"])
        price = plan_info["price"]
        checkout_user = st.session_state.username
        test_card_label = list(BILLING_TEST_CARDS.keys())[0]

        st.markdown(f"## {icon_md(CARD_MEMBERSHIP)} Secure Checkout")
        st.markdown(f"Complete this one-time **{plan_info['name']}** order to activate unlimited access for **{checkout_user}**.")

        col_order, col_billing = st.columns([1, 1])

        with col_order:
            render_html(f"""
            <div class='plan-card' style='border-color: #4F46E5; overflow: visible; text-align: left;'>
                <div class='plan-popular-tag'>Order Summary</div>
                <div>
                    <h4 style='text-align:center;'>{plan_info['name']}</h4>
                    <div class='plan-price-tag' style='text-align:center; color: #4F46E5;'>&#36;{price:.0f}<span style='font-size: 0.45em; color: #64748B;'>/mo</span></div>
                    <p style='color: #64748B; font-size: 0.85em; text-align:center;'>{plan_info['description']}</p>
                    <ul class='plan-feature-list'>
                        <li><strong>Unlimited</strong> verification checks</li>
                        <li><strong>Displays at least 3 (if available) &amp; up to 5 max</strong></li>
                        <li>Bypassed token bucket rate limits</li>
                        <li>Priority LLM execution queue</li>
                        <li>Multi-Agent Persona Debate &amp; LangGraph</li>
                    </ul>
                    <hr style='border:none; border-top:1px solid rgba(226,232,240,0.9); margin: 4px 0 12px;'>
                    <div style='font-size: 0.88em; color: #334155; line-height: 2;'>
                        <div style='display:flex; justify-content:space-between;'><span style='color:#64748B;'>Billing account</span><strong>{checkout_user}</strong></div>
                        <div style='display:flex; justify-content:space-between;'><span style='color:#64748B;'>Billing period</span><strong>Monthly</strong></div>
                        <div style='display:flex; justify-content:space-between;'><span style='color:#64748B;'>Plan price</span><strong>&#36;{price:.2f} USD</strong></div>
                        <div style='display:flex; justify-content:space-between;'><span style='color:#64748B;'>Tax</span><strong>&#36;0.00</strong></div>
                        <div style='display:flex; justify-content:space-between; border-top:1px solid rgba(226,232,240,0.9); padding-top:8px; margin-top:6px;'>
                            <span style='color:#0F172A; font-weight:700;'>Total due today</span>
                            <strong style='color:#4F46E5; font-size:1.05em;'>&#36;{price:.2f}</strong>
                        </div>
                    </div>
                </div>
            </div>
            """)

            render_html("""
            <div class='glass-card' style='padding: 14px 18px; margin-top: 12px; font-size: 0.84em; color: #64748B;'>
                <span class="material-symbols-rounded" style='vertical-align: middle; color: #059669;'>lock</span>
                Payments are processed by <strong style='color:#334155;'>ClaimShield Pay</strong>, a demo gateway.
                Your card details are validated locally and are never stored. No changes are made to your
                account unless the payment succeeds.
            </div>
            """)

        with col_billing:
            render_html("""
            <div class='section-eyebrow'>Payment Details</div>
            <div class='section-title' style='font-size: 1.35em;'>Card Information</div>
            """)
            with st.form(f"checkout_form_{checkout_plan}", clear_on_submit=False):
                holder_input = st.text_input("Cardholder Name", placeholder="e.g. Jane Smith")
                card_input = st.text_input(
                    "Card Number",
                    placeholder="4242 4242 4242 4242",
                    help=f"Demo gateway only accepts {test_card_label[:4]} {test_card_label[4:8]} {test_card_label[8:12]} {test_card_label[12:]}.",
                )
                exp_col, cvv_col = st.columns(2)
                expiry_input = exp_col.text_input("Expiry (MM/YY)", placeholder="12/28")
                cvv_input = cvv_col.text_input("CVV", type="password", placeholder="123")
                pay_submitted = st.form_submit_button(
                    f"Pay ${price:.2f} & Activate", type="primary",
                    icon=f":material/{LOCK}:", use_container_width=True,
                )

            if pay_submitted:
                ok, gate_msg = billing_validate_card(holder_input, card_input, expiry_input, cvv_input)
                if not ok:
                    st.error(icon_md(CANCEL) + " " + gate_msg)
                else:
                    with st.spinner("Encrypting details & contacting payment gateway..."):
                        receipt = billing_process_payment({
                            "username": checkout_user,
                            "plan": checkout_plan,
                            "amount": price,
                            "card_number": card_input,
                        })
                    if receipt["approved"]:
                        db.update_user_tokens(checkout_user, float(config.RATE_LIMIT_CAPACITY), time.time())
                        db.update_user_role(checkout_user, plan_info["role"])
                        st.session_state.role = plan_info["role"]
                        st.session_state.jwt_token = generate_jwt(checkout_user, plan_info["role"])
                        st.session_state.checkout_receipt = receipt
                        st.session_state.checkout_flow = "success"
                        st.session_state.flash = f"{icon_md(CHECK_CIRCLE)} Payment successful — {plan_info['name']} activated!"
                        st.rerun()
                    else:
                        st.error(icon_md(CANCEL) + " Payment declined. No changes were made to your account.")

            st.markdown("---")
            if st.button("Cancel & Keep Current Plan", use_container_width=True, key="btn_checkout_cancel"):
                st.session_state.checkout_flow = None
                st.session_state.checkout_receipt = None
                st.session_state.current_page = PAGE_ACCOUNT
                st.session_state.nav_target = PAGE_ACCOUNT
                st.session_state.nav_radio = PAGE_ACCOUNT
                st.rerun()

    elif flow_state == "success":
        receipt = st.session_state.get("checkout_receipt") or {}
        plan_name = receipt.get("plan_name", "Pro Plan")
        amount = float(receipt.get("amount", 19.00))

        render_html(f"""
        <div style='display: flex; flex-direction: column; align-items: center; text-align: center; padding: 34px 16px 8px;'>
            <div class='success-check'>
                <span class="material-symbols-rounded" style='font-size: 44px;'>check</span>
            </div>
            <div class='section-eyebrow' style='margin-top: 18px;'>Payment Successful</div>
            <div class='section-title' style='font-size: 1.7em;'>You're Now on {plan_name}</div>
            <p style='color: #64748B; max-width: 520px;'>Thank you, <strong style='color:#0F172A;'>{receipt.get('username', st.session_state.username)}</strong>.
            Unlimited claim checks, 3–5 resources per verdict and the priority LLM queue are now active for your account.</p>
        </div>
        """)

        receipt_col1, receipt_col2 = st.columns([1.4, 1])
        with receipt_col1:
            render_html(f"""
            <div class='receipt-card'>
                <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom: 6px;'>
                    <strong style='color:#0F172A;'>Order Confirmation</strong>
                    <span class='badge-secondary' style='background: rgba(16,185,129,0.12); color: #047857; border: 1px solid rgba(16,185,129,0.35);'>Paid</span>
                </div>
                <div class='receipt-row'><span class='receipt-label'>Receipt ID</span><span class='receipt-value'>{receipt.get('transaction_id', 'CS-XXXXXXXXXX')}</span></div>
                <div class='receipt-row'><span class='receipt-label'>Plan</span><span class='receipt-value'>{plan_name}</span></div>
                <div class='receipt-row'><span class='receipt-label'>Amount charged</span><span class='receipt-value' style='color:#047857;'>&#36;{amount:.2f} {receipt.get('currency', 'USD')}</span></div>
                <div class='receipt-row'><span class='receipt-label'>Payment method</span><span class='receipt-value'>{receipt.get('card_brand', 'Visa')} •••• {receipt.get('card_last4', '4242')}</span></div>
                <div class='receipt-row'><span class='receipt-label'>Transaction time</span><span class='receipt-value'>{receipt.get('timestamp', '-')}</span></div>
                <div class='receipt-row'><span class='receipt-label'>Gateway</span><span class='receipt-value'>{receipt.get('gateway', 'ClaimShield Pay (Demo)')}</span></div>
            </div>
            """)
        with receipt_col2:
            render_html("""
            <div class='glass-card' style='padding: 18px; font-size: 0.9em;'>
                <div style='font-weight:700; color:#0F172A; margin-bottom: 8px;'><span class="material-symbols-rounded" style='vertical-align: middle; color:#4F46E5;'>rocket_launch</span> What changed</div>
                <ul class='plan-feature-list' style='font-size: 0.9em; margin: 6px 0 0;'>
                    <li>Role upgraded to <strong style='color:#4F46E5;'>Pro</strong> in the database</li>
                    <li>Token bucket rate limits <strong>bypassed</strong></li>
                    <li>Up to <strong>5 resources</strong> displayed per verdict</li>
                    <li>JWT re-issued with the new role</li>
                </ul>
            </div>
            """)

        btn_c1, btn_c2 = st.columns(2)
        with btn_c1:
            if st.button("Continue to Verification Dashboard", type="primary", icon=f":material/{ARROW_FORWARD}:", use_container_width=True, key="btn_success_dashboard"):
                st.session_state.checkout_flow = None
                st.session_state.checkout_receipt = None
                st.session_state.current_page = PAGE_VERIFICATION
                st.session_state.nav_target = PAGE_VERIFICATION
                st.session_state.nav_radio = PAGE_VERIFICATION
                st.rerun()
        with btn_c2:
            if st.button("Go to Account & Plan", icon=f":material/{PERSON}:", use_container_width=True, key="btn_success_account"):
                st.session_state.checkout_flow = None
                st.session_state.checkout_receipt = None
                st.session_state.current_page = PAGE_ACCOUNT
                st.session_state.nav_target = PAGE_ACCOUNT
                st.session_state.nav_radio = PAGE_ACCOUNT
                st.rerun()
