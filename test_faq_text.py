import ast
import pathlib
import unittest


BOT_PATH = pathlib.Path(__file__).with_name("bot.py")
BOT_SOURCE = BOT_PATH.read_text(encoding="utf-8")
BOT_TREE = ast.parse(BOT_SOURCE)


def load_faq_namespace():
    names = {"DIVIDER", "TEXT", "tr", "panel", "faq_text"}
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
    namespace = {"SUPPORT_USERNAME": "MdMouno"}
    exec(compile(module, str(BOT_PATH), "exec"), namespace)
    return namespace


def function_source(name):
    for node in BOT_TREE.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return ast.get_source_segment(BOT_SOURCE, node)
    raise AssertionError(f"Function not found: {name}")


class FAQTextTests(unittest.TestCase):
    def setUp(self):
        self.namespace = load_faq_namespace()

    def test_faq_text_is_available_in_bangla_and_english(self):
        faq_text = self.namespace["faq_text"]
        english = faq_text("en")
        bangla = faq_text("bn")

        self.assertIn("FAQ\n────────────────", english)
        self.assertIn("1. How do I buy crypto?", english)
        self.assertIn("Telegram Stars", english)
        self.assertIn("Never share private keys", english)
        self.assertIn("FAQ\n────────────────", bangla)
        self.assertIn("১. Crypto কীভাবে কিনব?", bangla)
        self.assertIn("Telegram Stars", bangla)
        self.assertIn("Private key", bangla)
        self.assertLess(len(english), 4096)
        self.assertLess(len(bangla), 4096)

    def test_main_menu_has_faq_button(self):
        source = function_source("main_menu")

        self.assertIn('tr("faq", lang)', source)
        self.assertIn('callback_data="faq"', source)

    def test_button_handler_routes_faq_callback(self):
        source = function_source("button_handler")

        self.assertIn('query.data == "faq"', source)
        self.assertIn("faq_text(lang)", source)


if __name__ == "__main__":
    unittest.main()
