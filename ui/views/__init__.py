"""ClaimShield AI — UI Views and Modular Page Components."""

from ui.views.common import (
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
)
from ui.views.landing_view import render_landing_page
from ui.views.auth_view import render_auth_sidebar
from ui.views.nav_view import render_authenticated_sidebar
from ui.views.checkout_view import render_checkout_page
from ui.views.verification_view import render_verification_page
from ui.views.account_view import render_account_page
from ui.views.audit_view import render_audit_page
from ui.views.a2a_monitor_view import render_a2a_page
from ui.views.responsible_ai_view import render_responsible_ai_page

__all__ = [
    "PAGE_VERIFICATION",
    "PAGE_ACCOUNT",
    "PAGE_AUDIT",
    "PAGE_A2A",
    "PAGE_RESPONSIBLE_AI",
    "get_db",
    "get_orchestrator",
    "set_transition_ph",
    "render_clean_html",
    "build_boot_splash_html",
    "render_landing_page",
    "render_auth_sidebar",
    "render_authenticated_sidebar",
    "render_checkout_page",
    "render_verification_page",
    "render_account_page",
    "render_audit_page",
    "render_a2a_page",
    "render_responsible_ai_page",
]
