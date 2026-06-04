import ast
import pathlib
import re
import unittest


BOT_PATH = pathlib.Path(__file__).with_name("bot.py")
BOT_SOURCE = BOT_PATH.read_text(encoding="utf-8")
BOT_TREE = ast.parse(BOT_SOURCE)


def load_memory_namespace():
    names = {
        "AI_CONTEXT_LIMIT",
        "AI_SUPPORT_HISTORY_LIMIT",
        "AI_SUPPORT_HISTORY_TURNS",
        "append_ai_support_history",
        "combine_ai_support_context",
        "format_ai_support_history",
        "sanitize_diagnostic_text",
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
    namespace = {"re": re}
    exec(compile(module, str(BOT_PATH), "exec"), namespace)
    return namespace


class AISupportMemoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.namespace = load_memory_namespace()

    def test_history_context_includes_previous_user_and_ai_turns(self):
        text = self.namespace["format_ai_support_history"](
            [
                {"user": "আমার order pending", "assistant": "Order ID দিন।"},
                {"user": "ORD-ABC123", "assistant": "এটা webhook delay হতে পারে।"},
            ]
        )

        self.assertIn("Conversation memory for this AI Support session only", text)
        self.assertIn("Previous user: আমার order pending", text)
        self.assertIn("Previous AI: এটা webhook delay হতে পারে।", text)

    def test_history_context_redacts_sensitive_values(self):
        text = self.namespace["format_ai_support_history"](
            [{"user": "api_key=sk12345678901234567890", "assistant": "Do not share secrets."}]
        )

        self.assertIn("[REDACTED]", text)
        self.assertNotIn("sk12345678901234567890", text)

    def test_append_history_keeps_only_recent_session_turns(self):
        user_data = {"ai_support_history": []}
        turns = self.namespace["AI_SUPPORT_HISTORY_TURNS"]

        for index in range(turns + 2):
            self.namespace["append_ai_support_history"](user_data, f"q{index}", f"a{index}")

        self.assertEqual(len(user_data["ai_support_history"]), turns)
        self.assertEqual(user_data["ai_support_history"][0]["user"], "q2")
        self.assertEqual(user_data["ai_support_history"][-1]["assistant"], f"a{turns + 1}")

    def test_combined_context_preserves_memory_and_diagnostic_context(self):
        combined = self.namespace["combine_ai_support_context"]("Previous user: first question", "Order/TrxID context: pending")

        self.assertIn("Previous user: first question", combined)
        self.assertIn("Order/TrxID context: pending", combined)


if __name__ == "__main__":
    unittest.main()
