import ast
import pathlib
import unittest


BOT_PATH = pathlib.Path(__file__).with_name("bot.py")
BOT_SOURCE = BOT_PATH.read_text(encoding="utf-8")
BOT_TREE = ast.parse(BOT_SOURCE)


def load_seller_guide_namespace():
    names = {"seller_guide_text", "seller_approval_text"}
    module = ast.Module(
        body=[node for node in BOT_TREE.body if isinstance(node, ast.FunctionDef) and node.name in names],
        type_ignores=[],
    )
    ast.fix_missing_locations(module)
    namespace = {
        "SCB_FORWARDER_APP_URL": "https://example.com/scb-forwarder.apk",
        "SCB_FORWARDER_SERVER_URL": "https://cryptobuybot6969.duckdns.org",
    }
    exec(compile(module, str(BOT_PATH), "exec"), namespace)
    return namespace


class SellerForwarderGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        namespace = load_seller_guide_namespace()
        cls.guide = staticmethod(namespace["seller_guide_text"])
        cls.approval = staticmethod(namespace["seller_approval_text"])

    def test_bengali_approval_includes_app_link_token_and_setup_steps(self):
        seller = ("42", "seller", "Seller", "017", "@support", "approved", "ST_TOKEN", "created", "updated")

        text = self.approval(seller, "bn")

        self.assertIn("আপনার seller account approved", text)
        self.assertIn("অ্যাপ লিংক: https://example.com/scb-forwarder.apk", text)
        self.assertIn("Seller token: ST_TOKEN", text)
        self.assertIn("Seller mode অন করুন", text)
        self.assertIn("Enable Notification Access", text)
        self.assertIn("Battery/autostart", text)

    def test_english_approval_includes_app_link_token_and_setup_steps(self):
        seller = ("42", "seller", "Seller", "017", "@support", "approved", "ST_TOKEN", "created", "updated")

        text = self.approval(seller, "en")

        self.assertIn("Your seller account has been approved", text)
        self.assertIn("App link: https://example.com/scb-forwarder.apk", text)
        self.assertIn("Seller token: ST_TOKEN", text)
        self.assertIn("Turn on Seller mode", text)
        self.assertIn("Enable Notification Access", text)
        self.assertIn("Battery/autostart", text)

    def test_seller_guide_defaults_to_placeholder_token(self):
        text = self.guide(None, "en")

        self.assertIn("Seller token: YOUR_SMS_TOKEN", text)
        self.assertIn("SCB-Forwarder", text)


if __name__ == "__main__":
    unittest.main()
