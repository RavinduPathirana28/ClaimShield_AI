"""
ClaimShield AI — Dummy Payment Gateway (Demo Mode).

A purely simulated payment gateway for the Pro Plan checkout flow. No real
money is collected and no external service is ever contacted.

A payment is "approved" only when the submitted card matches the documented
test card (4242 4242 4242 4242). On approval the caller is expected to persist
the entitlement change (users.role) — the gateway itself never touches the DB.
"""

from __future__ import annotations

import re
import time
import uuid
from datetime import datetime

# Demo plan catalog. Mirrors the plan entitlements already enforced elsewhere
# (role "pro" bypasses rate limits, retrieves 3-5 resources, etc.).
PLANS = {
    "pro": {
        "id": "pro",
        "role": "pro",
        "name": "Pro Plan",
        "price": 19.00,
        "currency": "USD",
        "billing_period": "month",
        "description": "Unlimited claim checks · 3-5 resources displayed · Priority LLM queue.",
    },
}

# Demo-mode acceptance list: the ONLY card numbers that will be approved.
TEST_CARD_NUMBERS = {
    "4242424242424242": "Visa",
}

GATEWAY_NAME = "ClaimShield Pay (Demo)"
GATEWAY_CURRENCY = "USD"


def normalize_card_number(card_number: str) -> str:
    """Strip spaces/dashes and return only the digits."""
    return re.sub(r"[^\d]", "", card_number or "")


def validate_card(cardholder_name, card_number, expiry, cvv):
    """Validate the billing form against demo rules.

    Returns (ok: bool, message: str). Valid = the documented test card, a
    future MM/YY expiry, 3-4 digit CVV and a non-empty cardholder name.
    """
    holder = (cardholder_name or "").strip()
    if len(holder) < 3 or not any(ch.isalpha() for ch in holder):
        return False, "Please enter the cardholder name (at least 3 characters)."

    digits = normalize_card_number(card_number)
    if len(digits) != 16:
        return False, "Card number must contain exactly 16 digits."
    if digits not in TEST_CARD_NUMBERS:
        return False, (
            "Payment declined — this card is not recognized by the test gateway. "
            "Use 4242 4242 4242 4242 to simulate a successful payment."
        )

    expiry_str = (expiry or "").strip().replace(" ", "")
    match = re.fullmatch(r"(?P<month>0[1-9]|1[0-2])/(?P<year>\d{2})", expiry_str)
    if not match:
        return False, "Expiry must be in MM/YY format (e.g. 12/28)."
    month = int(match.group("month"))
    year = 2000 + int(match.group("year"))
    now = datetime.now()
    if (year, month) < (now.year, now.month):
        return False, "This card has expired. Please enter a future expiry date."

    cvv_digits = re.sub(r"[^\d]", "", cvv or "")
    if not (3 <= len(cvv_digits) <= 4):
        return False, "CVV must be 3 or 4 digits."

    return True, "Card is valid."


def process_payment(order):
    """Simulate authorizing a charge through the demo gateway.

    `order` is a dict containing at least {"username", "plan", "amount",
    "card_number"}. Returns a receipt dict; `approved` is always True here
    because an order only reaches this point after validate_card() succeeded
    (any decline is surfaced earlier by validate_card).
    """
    time.sleep(1.4)  # Realistic processing latency for the spinner.
    plan = PLANS.get(order.get("plan"), PLANS["pro"])
    amount = float(order.get("amount", plan["price"]))
    card_digits = normalize_card_number(order.get("card_number", ""))
    card_last4 = card_digits[-4:] if card_digits else "4242"
    brand = TEST_CARD_NUMBERS.get(card_digits, "Visa")
    now = datetime.now()
    return {
        "approved": True,
        "transaction_id": "CS-" + uuid.uuid4().hex[:10].upper(),
        "gateway": GATEWAY_NAME,
        "username": order.get("username"),
        "plan": plan["id"],
        "plan_name": plan["name"],
        "amount": round(amount, 2),
        "currency": GATEWAY_CURRENCY,
        "card_brand": brand,
        "card_last4": card_last4,
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
    }