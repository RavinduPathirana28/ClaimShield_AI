import unittest
import sys
from pathlib import Path

# Add root folder to sys.path to enable app module imports
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from ui.payment_gateway import (
    PLANS,
    TEST_CARD_NUMBERS,
    normalize_card_number,
    validate_card,
    process_payment,
)


class TestPaymentGateway(unittest.TestCase):
    TEST_CARD = "4242424242424242"

    def test_validate_card_accepts_test_card(self):
        ok, msg = validate_card("Jane Smith", "4242 4242 4242 4242", "12/28", "123")
        self.assertTrue(ok, msg)

    def test_validate_card_rejects_unknown_card(self):
        ok, msg = validate_card("Jane Smith", "5555555555554444", "12/28", "123")
        self.assertFalse(ok)
        self.assertIn("declined", msg.lower())

    def test_validate_card_rejects_bad_length(self):
        ok, _ = validate_card("Jane Smith", "4242", "12/28", "123")
        self.assertFalse(ok)

    def test_validate_card_rejects_expired_expiry(self):
        ok, msg = validate_card("Jane Smith", self.TEST_CARD, "01/20", "123")
        self.assertFalse(ok)
        self.assertIn("expired", msg.lower())

    def test_validate_card_rejects_invalid_expiry_format(self):
        ok, _ = validate_card("Jane Smith", self.TEST_CARD, "December 2028", "123")
        self.assertFalse(ok)

    def test_validate_card_rejects_bad_cvv(self):
        ok, _ = validate_card("Jane Smith", self.TEST_CARD, "12/28", "12")
        self.assertFalse(ok)

    def test_validate_card_rejects_blank_holder(self):
        ok, _ = validate_card("   ", self.TEST_CARD, "12/28", "123")
        self.assertFalse(ok)

    def test_normalize_card_number_strips_formatting(self):
        self.assertEqual(normalize_card_number("4242 4242 4242 4242"), self.TEST_CARD)
        self.assertEqual(normalize_card_number("4242-4242-4242-4242"), self.TEST_CARD)

    def test_process_payment_returns_receipt(self):
        order = {
            "username": "tester",
            "plan": "pro",
            "amount": PLANS["pro"]["price"],
            "card_number": self.TEST_CARD,
        }
        receipt = process_payment(order)
        self.assertTrue(receipt["approved"])
        self.assertEqual(receipt["username"], "tester")
        self.assertEqual(receipt["plan"], "pro")
        self.assertEqual(receipt["card_last4"], "4242")
        self.assertEqual(receipt["amount"], PLANS["pro"]["price"])
        self.assertTrue(receipt["transaction_id"].startswith("CS-"))

    def test_plans_reference_valid_role(self):
        self.assertEqual(PLANS["pro"]["role"], "pro")
        self.assertIn("4242424242424242", TEST_CARD_NUMBERS)


if __name__ == "__main__":
    unittest.main()