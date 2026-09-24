"""
ClaimShield AI — Importable Icon Library & Semantic Components
Powered by Google Material Symbols (Rounded) for crisp, accessible, non-emoji vector UI iconography.
"""

from typing import Optional

# Material Symbol Name Constants (Tree-shakable references)
SHIELD = "shield"
LOCK = "lock"
KEY = "key"
VPN_KEY = "vpn_key"
TOKEN = "generating_tokens"
BOLT = "bolt"
ASSIGNMENT = "assignment"
PUBLIC = "public"
LANGUAGE = "language"
PSYCHOLOGY = "psychology"
SMART_TOY = "smart_toy"
ALT_ROUTE = "alt_route"
BAR_CHART = "bar_chart"
BIOTECH = "biotech"
SEARCH = "search"
BALANCE = "balance"
LIGHTBULB = "lightbulb"
CHECK_CIRCLE = "check_circle"
CANCEL = "cancel"
CHAT = "chat"
HELP = "help"
TRACK_CHANGES = "track_changes"
MENU_BOOK = "menu_book"
HANDSHAKE = "handshake"
DESCRIPTION = "description"
EDIT_NOTE = "edit_note"
RECORD_VOICE_OVER = "record_voice_over"
SELL = "sell"
PUSH_PIN = "push_pin"
LINK = "link"
RECEIPT_LONG = "receipt_long"
NEWSPAPER = "newspaper"
CALENDAR_TODAY = "calendar_today"
PERSON = "person"
GROUP = "group"
CONSTRUCTION = "construction"
HISTORY_EDU = "history_edu"
SETTINGS = "settings"
SCHEDULE = "schedule"
OUTBOX = "outbox"
INBOX = "inbox"
DIAMOND = "diamond"
STAR = "star"
CARD_MEMBERSHIP = "card_membership"
ROCKET_LAUNCH = "rocket_launch"
SMARTPHONE = "smartphone"
NIGHTLIGHT = "nightlight"
COFFEE = "coffee"
HOURGLASS_TOP = "hourglass_top"
EXPLORE = "explore"
CELEBRATION = "celebration"
ARROW_FORWARD = "arrow_forward"
CHECK = "check"
WARNING = "warning"
CLOSE = "close"
FACT_CHECK = "fact_check"
SECURITY = "security"
FINGERPRINT = "fingerprint"
HUB = "hub"


def icon_html(
    name: str,
    class_name: str = "",
    style: str = "",
    fill: bool = False
) -> str:
    """Generates an accessible Google Material Symbols Rounded inline HTML icon element."""
    extra_classes = f" {class_name}" if class_name else ""
    fill_style = "font-variation-settings: 'FILL' 1;" if fill else ""
    combined_style = f"{fill_style} {style}".strip()
    style_attr = f' style="{combined_style}"' if combined_style else ""
    return f'<span class="material-symbols-rounded{extra_classes}"{style_attr}>{name}</span>'


def icon_md(name: str) -> str:
    """Returns Streamlit native Material icon shortcode (:material/icon_name:)."""
    return f":material/{name}:"


# Pre-rendered HTML Icon Components for clean direct imports
ICON_SHIELD = icon_html(SHIELD)
ICON_LOCK = icon_html(LOCK)
ICON_KEY = icon_html(KEY)
ICON_TOKEN = icon_html(TOKEN)
ICON_BOLT = icon_html(BOLT)
ICON_ASSIGNMENT = icon_html(ASSIGNMENT)
ICON_PUBLIC = icon_html(PUBLIC)
ICON_PSYCHOLOGY = icon_html(PSYCHOLOGY)
ICON_SMART_TOY = icon_html(SMART_TOY)
ICON_ALT_ROUTE = icon_html(ALT_ROUTE)
ICON_BAR_CHART = icon_html(BAR_CHART)
ICON_BIOTECH = icon_html(BIOTECH)
ICON_SEARCH = icon_html(SEARCH)
ICON_BALANCE = icon_html(BALANCE)
ICON_LIGHTBULB = icon_html(LIGHTBULB)
ICON_CHECK_CIRCLE = icon_html(CHECK_CIRCLE)
ICON_CANCEL = icon_html(CANCEL)
ICON_CHAT = icon_html(CHAT)
ICON_HELP = icon_html(HELP)
ICON_TRACK_CHANGES = icon_html(TRACK_CHANGES)
ICON_MENU_BOOK = icon_html(MENU_BOOK)
ICON_HANDSHAKE = icon_html(HANDSHAKE)
ICON_DESCRIPTION = icon_html(DESCRIPTION)
ICON_EDIT_NOTE = icon_html(EDIT_NOTE)
ICON_RECORD_VOICE_OVER = icon_html(RECORD_VOICE_OVER)
ICON_SELL = icon_html(SELL)
ICON_PUSH_PIN = icon_html(PUSH_PIN)
ICON_LINK = icon_html(LINK)
ICON_RECEIPT_LONG = icon_html(RECEIPT_LONG)
ICON_NEWSPAPER = icon_html(NEWSPAPER)
ICON_CALENDAR_TODAY = icon_html(CALENDAR_TODAY)
ICON_PERSON = icon_html(PERSON)
ICON_GROUP = icon_html(GROUP)
ICON_CONSTRUCTION = icon_html(CONSTRUCTION)
ICON_HISTORY_EDU = icon_html(HISTORY_EDU)
ICON_SETTINGS = icon_html(SETTINGS)
ICON_SCHEDULE = icon_html(SCHEDULE)
ICON_OUTBOX = icon_html(OUTBOX)
ICON_INBOX = icon_html(INBOX)
ICON_DIAMOND = icon_html(DIAMOND)
ICON_STAR = icon_html(STAR)
ICON_CARD_MEMBERSHIP = icon_html(CARD_MEMBERSHIP)
ICON_ROCKET_LAUNCH = icon_html(ROCKET_LAUNCH)
ICON_SMARTPHONE = icon_html(SMARTPHONE)
ICON_NIGHTLIGHT = icon_html(NIGHTLIGHT)
ICON_COFFEE = icon_html(COFFEE)
ICON_HOURGLASS_TOP = icon_html(HOURGLASS_TOP)
ICON_EXPLORE = icon_html(EXPLORE)
ICON_CELEBRATION = icon_html(CELEBRATION)
ICON_ARROW_FORWARD = icon_html(ARROW_FORWARD)
ICON_CHECK = icon_html(CHECK)
ICON_WARNING = icon_html(WARNING)
ICON_CLOSE = icon_html(CLOSE)
ICON_FACT_CHECK = icon_html(FACT_CHECK)
ICON_SECURITY = icon_html(SECURITY)
ICON_FINGERPRINT = icon_html(FINGERPRINT)
ICON_HUB = icon_html(HUB)
