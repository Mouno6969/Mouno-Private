import ast
import logging
import os
import pathlib
import unittest
import unicodedata
from datetime import datetime
from io import BytesIO


BOT_PATH = pathlib.Path(__file__).with_name("bot.py")
BOT_SOURCE = BOT_PATH.read_text(encoding="utf-8")
BOT_TREE = ast.parse(BOT_SOURCE)


RECEIPT_FUNCTIONS = {
    "short_wallet",
    "receipt_value",
    "receipt_amount",
    "receipt_explorer_url",
    "receipt_user_label",
    "load_receipt_font",
    "receipt_font",
    "receipt_bengali_font",
    "receipt_image_text",
    "draw_receipt_text",
    "paste_receipt_seal",
    "receipt_qr_payload",
    "build_receipt_qr",
    "paste_receipt_qr",
    "build_receipt_image",
}


def load_receipt_namespace():
    module = ast.Module(
        body=[node for node in BOT_TREE.body if isinstance(node, ast.FunctionDef) and node.name in RECEIPT_FUNCTIONS],
        type_ignores=[],
    )
    ast.fix_missing_locations(module)
    namespace = {
        "os": os,
        "unicodedata": unicodedata,
        "datetime": datetime,
        "BytesIO": BytesIO,
        "logger": logging.getLogger("receipt-test"),
        "RECEIPT_LOGO_PATH": str(BOT_PATH.with_name("assets") / "mouno_logo.jpg"),
        "RECEIPT_FONT_DIR": str(BOT_PATH.with_name("assets") / "fonts"),
        "ADMIN_ID": "1",
        "NETWORKS": {
            "solana": {"name": "Solana (SOL)", "symbol": "USDC", "explorer": "https://solscan.io/tx/"},
            "manual": {"name": "Manual", "symbol": "USDT", "explorer": ""},
        },
    }
    exec(compile(module, str(BOT_PATH), "exec"), namespace)
    return namespace


class ReceiptImageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipts = load_receipt_namespace()

    def sample_data(self, **overrides):
        data = {
            "title": "Smart Crypto Buy",
            "status": "SUCCESSFUL / COMPLETED",
            "order_id": "ORD-123",
            "payment_id": "PAY-456",
            "network": "solana",
            "network_name": "Solana (SOL)",
            "crypto_symbol": "USDC",
            "crypto_amount": "12.50000000",
            "bdt_amount": "1712.50",
            "buyer_id": "1001",
            "buyer_label": "buyer (1001)",
            "seller_id": "2002",
            "seller_label": "seller (2002)",
            "wallet": "So11111111111111111111111111111111111111112",
            "tx_hash": "5" * 88,
            "explorer_url": "https://solscan.io/tx/" + "5" * 88,
            "timestamp": "2026-05-04 12:34:56",
        }
        data.update(overrides)
        return data

    def test_qr_payload_prefers_explorer_url(self):
        payload, label = self.receipts["receipt_qr_payload"](self.sample_data())
        self.assertEqual(payload, "https://solscan.io/tx/" + "5" * 88)
        self.assertEqual(label, "Transaction proof link")

    def test_qr_payload_uses_compact_receipt_details_without_explorer_url(self):
        payload, label = self.receipts["receipt_qr_payload"](
            self.sample_data(network="manual", explorer_url="", tx_hash="a" * 64)
        )
        self.assertEqual(label, "Encoded receipt details")
        self.assertIn("order=ORD-123", payload)
        self.assertIn("payment=PAY-456", payload)
        self.assertIn("network=manual", payload)
        self.assertIn("amount=12.5 USDC", payload)
        self.assertIn("wallet=So111111...111112", payload)
        self.assertIn("tx=aaaaaaaa...aaaaaa", payload)
        self.assertIn("time=2026-05-04 12:34:56", payload)

    def test_build_receipt_image_returns_reasonable_png_bytes(self):
        image = self.receipts["build_receipt_image"](self.sample_data())
        content = image.getvalue()
        self.assertEqual(content[:8], b"\x89PNG\r\n\x1a\n")
        self.assertGreater(len(content), 20_000)
        self.assertEqual(image.name, "receipt-ORD-123.png")

    def test_transaction_receipt_photo_has_no_caption(self):
        function = next(node for node in BOT_TREE.body if isinstance(node, ast.AsyncFunctionDef) and node.name == "send_transaction_receipt")
        send_photo_calls = [node for node in ast.walk(function) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "send_photo"]
        self.assertTrue(send_photo_calls)
        for call in send_photo_calls:
            self.assertNotIn("caption", {keyword.arg for keyword in call.keywords})

    def test_transaction_receipt_image_is_built_before_recipient_loop(self):
        function = next(node for node in BOT_TREE.body if isinstance(node, ast.AsyncFunctionDef) and node.name == "send_transaction_receipt")
        build_calls = [node for node in ast.walk(function) if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "build_receipt_image"]
        self.assertEqual(len(build_calls), 1)
        for loop in [node for node in ast.walk(function) if isinstance(node, ast.For)]:
            self.assertFalse(any(call in ast.walk(loop) for call in build_calls))

    def test_transaction_receipt_image_generation_uses_executor(self):
        function = next(node for node in BOT_TREE.body if isinstance(node, ast.AsyncFunctionDef) and node.name == "send_transaction_receipt")
        executor_calls = [node for node in ast.walk(function) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "run_in_executor"]
        self.assertTrue(executor_calls)

    def test_bot_enables_concurrent_update_processing(self):
        self.assertIn("ChatScopedUpdateProcessor(8)", BOT_SOURCE)
        self.assertIn("asyncio.Lock()", BOT_SOURCE)
        self.assertIn('self._locks.pop(key, None)', BOT_SOURCE)
        self.assertNotIn("concurrent_updates(8)", BOT_SOURCE)

    def test_completed_receipt_summaries_are_not_sent_as_extra_text(self):
        blocked_snippets = [
            "Giveaway redeemed!",
            "🎁 গিফট কোড রিডিম!",
            "Telegram Stars order completed.",
            "Auto-completed delayed bKash order.",
            "Receipt:",
        ]
        for snippet in blocked_snippets:
            self.assertNotIn(snippet, BOT_SOURCE)


if __name__ == "__main__":
    unittest.main()
