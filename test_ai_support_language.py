import ast
import pathlib
import unittest


BOT_PATH = pathlib.Path(__file__).with_name("bot.py")
BOT_SOURCE = BOT_PATH.read_text(encoding="utf-8")
BOT_TREE = ast.parse(BOT_SOURCE)


def load_functions(*names):
    module = ast.Module(
        body=[node for node in BOT_TREE.body if isinstance(node, ast.FunctionDef) and node.name in names],
        type_ignores=[],
    )
    ast.fix_missing_locations(module)
    namespace = {"AI_USER_MESSAGE_LIMIT": 6000}
    exec(compile(module, str(BOT_PATH), "exec"), namespace)
    return namespace


class AISupportLanguageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        namespace = load_functions("select_ai_response_language", "compose_ai_user_message")
        cls.select_language = staticmethod(namespace["select_ai_response_language"])
        cls.compose_message = staticmethod(namespace["compose_ai_user_message"])

    def test_bengali_question_returns_bengali(self):
        self.assertEqual(self.select_language("আমার অর্ডার pending কেন?", "en"), "Bengali")

    def test_english_question_returns_english(self):
        self.assertEqual(self.select_language("Why is my order pending?", "bn"), "English")

    def test_english_context_with_bengali_question_instructs_bengali(self):
        message = self.compose_message(
            "আমার পেমেন্ট আটকে আছে কেন?",
            "AI SUPPORT CONTEXT: Order is pending because webhook is delayed.",
            "en",
        )
        self.assertIn("[RESPONSE LANGUAGE]\nBengali", message)
        self.assertLess(message.index("[RESPONSE LANGUAGE]"), message.index("[BEGIN DIAGNOSTIC CONTEXT]"))
        self.assertLess(message.index("[BEGIN DIAGNOSTIC CONTEXT]"), message.index("[USER QUESTION]"))
        self.assertIn("Ignore diagnostic context language", message)

    def test_id_only_question_falls_back_to_saved_ui_language(self):
        self.assertEqual(self.select_language("ORD-123456", "en"), "English")
        self.assertEqual(self.select_language("ORD-123456", "bn"), "Bengali")
        self.assertIn("[RESPONSE LANGUAGE]\nBengali", self.compose_message("ORD-123456", None, "bn"))


if __name__ == "__main__":
    unittest.main()
