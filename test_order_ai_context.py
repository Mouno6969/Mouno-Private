import ast
import pathlib
import re
import unittest


BOT_PATH = pathlib.Path(__file__).with_name("bot.py")
BOT_SOURCE = BOT_PATH.read_text(encoding="utf-8")
BOT_TREE = ast.parse(BOT_SOURCE)


class InlineKeyboardButtonStub:
    def __init__(self, text, callback_data=None):
        self.text = text
        self.callback_data = callback_data


class InlineKeyboardMarkupStub:
    def __init__(self, inline_keyboard):
        self.inline_keyboard = inline_keyboard


def load_order_ai_namespace(context_line):
    names = {
        "AI_CONTEXT_LIMIT",
        "ORDER_AI_CALLBACK_PREFIX",
        "TRACK_ORDER_CALLBACK_PREFIX",
        "extract_support_identifiers",
        "normalize_order_context_identifier",
        "is_order_context_available",
        "ai_order_status_question",
        "build_ai_support_context",
        "order_status_ai_keyboard",
        "track_order_keyboard",
    }
    body = []
    for node in BOT_TREE.body:
        if isinstance(node, ast.Assign):
            targets = {target.id for target in node.targets if isinstance(target, ast.Name)}
            if targets & names:
                body.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name in names:
            body.append(node)
    module = ast.Module(body=body, type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {
        "re": re,
        "_order_context_line": lambda identifier, user_id, admin=False: context_line(identifier, user_id, admin),
        "find_order": lambda identifier: ("transaction", object()),
        "is_admin": lambda user_id: str(user_id) == "1",
        "ltext": lambda lang, en, bn: en if lang == "en" else bn,
        "InlineKeyboardButton": InlineKeyboardButtonStub,
        "InlineKeyboardMarkup": InlineKeyboardMarkupStub,
    }
    exec(compile(module, str(BOT_PATH), "exec"), namespace)
    return namespace


class OrderAIContextTests(unittest.TestCase):
    def test_ai_context_accepts_loaded_order_identifier_without_user_retyping_it(self):
        namespace = load_order_ai_namespace(lambda identifier, user_id, admin=False: f"CTX:{identifier}:{user_id}:{admin}")

        context = namespace["build_ai_support_context"]("এটার current অবস্থা কী?", "42", order_identifiers=["ORD-ABC123"])

        self.assertIn("Order/TrxID context:", context)
        self.assertIn("CTX:ORD-ABC123:42:False", context)

    def test_loaded_order_identifier_is_deduplicated_with_question_identifier(self):
        calls = []
        namespace = load_order_ai_namespace(lambda identifier, user_id, admin=False: calls.append(identifier) or f"CTX:{identifier}")

        namespace["build_ai_support_context"]("Please check ORD-ABC123", "42", order_identifiers=["ORD-ABC123"])

        self.assertEqual(calls, ["ORD-ABC123"])

    def test_order_status_ai_keyboard_uses_safe_callback_data(self):
        namespace = load_order_ai_namespace(lambda identifier, user_id, admin=False: f"CTX:{identifier}")

        markup = namespace["order_status_ai_keyboard"]("ORD-ABC123<script>" + "X" * 80, "42", "en")
        button = markup.inline_keyboard[0][0]

        self.assertEqual(button.text, "🤖 Ask AI about this order")
        self.assertTrue(button.callback_data.startswith(namespace["ORDER_AI_CALLBACK_PREFIX"]))
        self.assertLessEqual(len(button.callback_data), 64)
        self.assertRegex(button.callback_data, r"^aiorder_[A-Za-z0-9_-]+$")

    def test_order_status_ai_keyboard_is_hidden_without_accessible_context(self):
        for line in ("ORD-ABC123: permission denied; requester is not the order owner.", "ORD-ABC123: no matching order/TrxID found."):
            with self.subTest(line=line):
                namespace = load_order_ai_namespace(lambda identifier, user_id, admin=False, line=line: line)

                self.assertIsNone(namespace["order_status_ai_keyboard"]("ORD-ABC123", "42", "en"))

    def test_track_order_keyboard_opens_safe_order_status_callback(self):
        namespace = load_order_ai_namespace(lambda identifier, user_id, admin=False: f"CTX:{identifier}")

        markup = namespace["track_order_keyboard"]("ORD-ABC123<script>" + "X" * 80, "42", "bn")
        button = markup.inline_keyboard[0][0]

        self.assertEqual(button.text, "🔎 Order Track করুন")
        self.assertTrue(button.callback_data.startswith(namespace["TRACK_ORDER_CALLBACK_PREFIX"]))
        self.assertLessEqual(len(button.callback_data), 64)
        self.assertRegex(button.callback_data, r"^trackorder_[A-Za-z0-9_-]+$")

    def test_ai_order_status_question_is_localized_and_actionable(self):
        namespace = load_order_ai_namespace(lambda identifier, user_id, admin=False: f"CTX:{identifier}")

        bn = namespace["ai_order_status_question"]("ORD-ABC123<script>", "bn")
        en = namespace["ai_order_status_question"]("ORD-ABC123<script>", "en")

        self.assertIn("ORD-ABC123script", bn)
        self.assertIn("সহজ বাংলায়", bn)
        self.assertIn("সম্ভাব্য কারণ", bn)
        self.assertIn("simple English", en)
        self.assertIn("likely reason", en)
        self.assertIn("what the user should do next", en)


if __name__ == "__main__":
    unittest.main()
