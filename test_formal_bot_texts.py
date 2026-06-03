import ast
import pathlib
import unittest


BOT_PATH = pathlib.Path(__file__).with_name("bot.py")
BOT_SOURCE = BOT_PATH.read_text(encoding="utf-8")
BOT_TREE = ast.parse(BOT_SOURCE)


def load_text_namespace():
    names = {"DIVIDER", "TEXT", "tr", "panel", "rates_text", "home_text"}
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
        "BKASH_NUMBER": "01346478492",
        "get_all_rates": lambda: {
            "solana": 137,
            "polygon": 137,
            "bsc": 130,
            "avalanche": 137,
            "ethereum": 137,
            "ethereum_usdc": 137,
            "base": 137,
            "trc20": 137,
            "ton": 137,
        },
    }
    exec(compile(module, str(BOT_PATH), "exec"), namespace)
    return namespace


class FormalBotTextTests(unittest.TestCase):
    def setUp(self):
        self.namespace = load_text_namespace()

    def test_panel_uses_plain_title_divider_body_layout(self):
        self.assertEqual(self.namespace["panel"]("Title", "Body"), "Title\n━━━━━━━━━━━━━━━━━━━━━\nBody")

    def test_home_text_is_formal_and_compact(self):
        text = self.namespace["home_text"]("Mandy", "en")

        self.assertTrue(text.startswith("Smart Crypto Buy\n━━━━━━━━━━━━━━━━━━━━━\n⚡ Welcome, Mandy."))
        self.assertIn("🔹 BSC USDT: 1 USDT = 130 BDT", text)
        self.assertIn("📡 Payment\n━━━━━━━━━━━━━━━━━━━━━\n🔹 bKash: `01346478492`", text)
        self.assertIn("Select an option from the menu.", text)

    def test_bangla_home_text_keeps_same_formal_structure(self):
        text = self.namespace["home_text"]("Mandy", "bn")

        self.assertIn("Smart Crypto Buy\n━━━━━━━━━━━━━━━━━━━━━", text)
        self.assertIn("বর্তমান রেট\n━━━━━━━━━━━━━━━━━━━━━", text)
        self.assertIn("Payment\n━━━━━━━━━━━━━━━━━━━━━", text)
        self.assertIn("নিচের মেনু থেকে একটি অপশন বেছে নিন।", text)


if __name__ == "__main__":
    unittest.main()
