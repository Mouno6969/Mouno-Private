import ast
import pathlib
import unittest


BOT_PATH = pathlib.Path(__file__).with_name("bot.py")
BOT_SOURCE = BOT_PATH.read_text(encoding="utf-8")
BOT_TREE = ast.parse(BOT_SOURCE)


def load_bot_knowledge_base():
    for node in BOT_TREE.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "BOT_KNOWLEDGE_BASE" for target in node.targets):
            continue
        namespace = {}
        module = ast.Module(body=[node], type_ignores=[])
        ast.fix_missing_locations(module)
        exec(compile(module, str(BOT_PATH), "exec"), namespace)
        return namespace["BOT_KNOWLEDGE_BASE"]
    raise AssertionError("BOT_KNOWLEDGE_BASE not found")


class AISupportKnowledgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.knowledge = load_bot_knowledge_base()

    def test_forwarder_step_troubleshooting_is_in_ai_knowledge(self):
        for text in (
            "SCB-Forwarder setup troubleshooting by step",
            "Check server fails",
            "SMS permission fails",
            "Notification Access fails",
            "background service will not stay running",
        ):
            with self.subTest(text=text):
                self.assertIn(text, self.knowledge)

    def test_forwarder_error_handling_asks_for_details_first(self):
        for text in (
            "first ask for the exact screen/step",
            "phone brand/model",
            "Check server result",
            "Last error message",
            "Payment outcome",
        ):
            with self.subTest(text=text):
                self.assertIn(text, self.knowledge)

    def test_forwarder_error_outcomes_are_explained(self):
        for text in (
            "Token FAILED",
            "HTTP 404",
            "Queue count above 0",
            "ignored means",
            "parsed means",
            "duplicate means",
            "manual_review means",
            "matched_order means",
        ):
            with self.subTest(text=text):
                self.assertIn(text, self.knowledge)

    def test_broad_bot_feature_coverage_is_in_ai_knowledge(self):
        for text in (
            "Language, help, FAQ, terms",
            "Rates and buy amounts",
            "Gift Code and Giveaway",
            "Personal wallet",
            "Referral and payouts",
            "stock reservations",
            "TX Log, receipts, and failed sends",
            "Admin operations and health",
            "Maintenance, webhook, dashboard, AI admin",
        ):
            with self.subTest(text=text):
                self.assertIn(text, self.knowledge)

    def test_sensitive_user_wallet_boundaries_remain_in_ai_knowledge(self):
        for text in (
            "The bot cannot recover a forgotten password",
            "Never ask for or reveal private keys",
            "wrong networks, irreversible transfers, gas, and manual review",
        ):
            with self.subTest(text=text):
                self.assertIn(text, self.knowledge)

    def test_free_service_api_and_group_id_guidance_is_in_ai_knowledge(self):
        for text in (
            "https://my.telegram.org",
            "API development tools",
            "copy api_id and api_hash",
            "numeric chat ID",
            "supergroup/channel IDs usually start with -100",
            "where to get API ID/API hash and target group/chat ID",
        ):
            with self.subTest(text=text):
                self.assertIn(text, self.knowledge)

    def test_solana_ata_refund_guidance_is_in_ai_knowledge(self):
        for text in (
            "Free Service Solana ATA Refund",
            "empty Associated Token Accounts",
            "rent SOL is estimated to be refundable",
            "closes only empty ATA accounts",
            "ATAs with token balances must be skipped",
            "Solana ATA refund steps in Bengali for Bengali questions and English for English questions",
        ):
            with self.subTest(text=text):
                self.assertIn(text, self.knowledge)

    def test_telegram_id_finder_guidance_is_in_ai_knowledge(self):
        for text in (
            "Free Service Telegram ID Finder",
            "public @username",
            "public t.me/telegram.me link",
            "forwarded message from the target",
            "current chat ID",
            "privacy settings",
            "Telegram ID Finder steps in Bengali for Bengali questions and English for English questions",
        ):
            with self.subTest(text=text):
                self.assertIn(text, self.knowledge)


if __name__ == "__main__":
    unittest.main()
