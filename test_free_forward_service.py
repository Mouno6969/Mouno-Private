import ast
import asyncio
import pathlib
import unittest


BOT_PATH = pathlib.Path(__file__).with_name("bot.py")
BOT_SOURCE = BOT_PATH.read_text(encoding="utf-8")
BOT_TREE = ast.parse(BOT_SOURCE)


def load_free_forward_namespace():
    names = {
        "DIVIDER",
        "TEXT",
        "FREE_FORWARD_MAX_TARGETS",
        "FREE_FORWARD_MIN_INTERVAL_MINUTES",
        "PERSONAL_FORWARD_MAX_TARGETS",
        "PERSONAL_FORWARD_MIN_INTERVAL_MINUTES",
        "PERSONAL_FORWARD_DIALOG_PAGE_SIZE",
        "ltext",
        "tr",
        "panel",
        "free_service_text",
        "free_service_keyboard",
        "telegram_id_finder_text",
        "telegram_id_result_text",
        "normalize_telegram_lookup_target",
        "solana_refund_text",
        "normalize_free_forward_target",
        "parse_free_forward_targets",
        "free_forward_text",
        "personal_forward_picker_text",
        "send_personal_forward_message",
    }
    body = []
    for node in BOT_TREE.body:
        if isinstance(node, ast.Assign):
            targets = {target.id for target in node.targets if isinstance(target, ast.Name)}
            if targets & names:
                body.append(node)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in names:
            body.append(node)

    module = ast.Module(body=body, type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {"re": __import__("re"), "math": __import__("math")}
    exec(compile(module, str(BOT_PATH), "exec"), namespace)
    return namespace


class FakePersonalForwardClient:
    def __init__(self):
        self.entity_targets = []
        self.sent_messages = []

    async def get_entity(self, target):
        self.entity_targets.append(target)
        return {"entity": target}

    async def send_message(self, entity, text):
        self.sent_messages.append((entity, text))


def function_source(name):
    for node in BOT_TREE.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return ast.get_source_segment(BOT_SOURCE, node)
    raise AssertionError(f"Function not found: {name}")


class FreeForwardServiceTests(unittest.TestCase):
    def setUp(self):
        self.namespace = load_free_forward_namespace()

    def test_target_parser_accepts_ids_usernames_and_public_links(self):
        parse_targets = self.namespace["parse_free_forward_targets"]

        targets, invalid = parse_targets("-10012345 @publicgroup https://t.me/mychannel telegram.me/another_channel https://t.me/+private")

        self.assertEqual(targets, ["-10012345", "@publicgroup", "@mychannel", "@another_channel"])
        self.assertIn("https://t.me/+private", invalid)

    def test_target_parser_honors_personal_account_limit(self):
        parse_targets = self.namespace["parse_free_forward_targets"]
        max_targets = self.namespace["PERSONAL_FORWARD_MAX_TARGETS"]

        text = " ".join(f"@group{i:02d}" for i in range(max_targets + 3))
        targets, invalid = parse_targets(text, max_targets)

        self.assertEqual(len(targets), max_targets)
        self.assertEqual(invalid, [])

    def test_personal_forward_resolves_numeric_string_targets_as_ints(self):
        send_personal = self.namespace["send_personal_forward_message"]
        client = FakePersonalForwardClient()

        asyncio.run(send_personal(client, "-10012345", {"type": "text", "text": "hello"}))

        self.assertEqual(client.entity_targets, [-10012345])
        self.assertEqual(client.sent_messages, [({"entity": -10012345}, "hello")])

    def test_free_service_text_is_localized(self):
        free_service_text = self.namespace["free_service_text"]
        free_forward_text = self.namespace["free_forward_text"]

        self.assertIn("Telegram Message Forwarder", free_service_text("en"))
        self.assertIn("Telegram Message Forwarder", free_service_text("bn"))
        self.assertIn("Solana ATA Refund", free_service_text("en"))
        self.assertIn("Solana ATA Refund", free_service_text("bn"))
        self.assertIn("Telegram ID Finder", free_service_text("en"))
        self.assertIn("Telegram ID Finder", free_service_text("bn"))

        english = free_forward_text("en", True, "SenderBot", True)
        bangla = free_forward_text("bn", False, None, False)

        self.assertIn("Telegram Message Forwarder", english)
        self.assertIn("@SenderBot", english)
        self.assertIn("What is this?", english)
        self.assertIn("How to use", english)
        self.assertIn("Forward repeatedly", english)
        self.assertIn("Personal account", english)
        self.assertIn("personal-account maximum", english)
        self.assertIn("secure web login link", english)
        self.assertIn("Never send login codes in Telegram chat", english)
        self.assertIn("Where to get API ID/API hash", english)
        self.assertIn("https://my.telegram.org", english)
        self.assertIn("Where to get group/channel ID", english)
        self.assertIn("Telegram Message Forwarder", bangla)
        self.assertIn("এটা কী?", bangla)
        self.assertIn("কীভাবে ব্যবহার করবেন", bangla)
        self.assertIn("সুবিধাসমূহ", bangla)
        self.assertIn("API ID/API hash কোথা থেকে পাবেন", bangla)
        self.assertIn("Group/channel ID কোথা থেকে পাবেন", bangla)
        self.assertIn("নির্দিষ্ট সময় পরপর", bangla)
        self.assertIn("Connect করা নেই", bangla)
        self.assertIn("Personal account", bangla)
        self.assertIn("secure web login link", bangla)
        self.assertIn("Telegram chat-এ login code কখনো পাঠাবেন না", bangla)

    def test_personal_forward_picker_text_is_localized(self):
        picker_text = self.namespace["personal_forward_picker_text"]
        dialogs = [{"id": str(index), "title": f"Group {index}"} for index in range(12)]

        english = picker_text("en", 0, dialogs, ["1", "2"])
        bangla = picker_text("bn", 1, dialogs, ["1"])

        self.assertIn("Select target groups/channels", english)
        self.assertIn("Selected: 2/45", english)
        self.assertIn("Connected account থেকে target group/channel select করুন", bangla)
        self.assertIn("Selected: 1/45", bangla)

    def test_solana_refund_text_is_localized(self):
        solana_refund_text = self.namespace["solana_refund_text"]

        english = solana_refund_text("en")
        bangla = solana_refund_text("bn")

        self.assertIn("Solana ATA Refund", english)
        self.assertIn("Associated Token Accounts", english)
        self.assertIn("rent SOL", english)
        self.assertIn("ATAs with token balances will not be closed", english)
        self.assertIn("Solana ATA Refund", bangla)
        self.assertIn("empty Associated Token Account", bangla)
        self.assertIn("rent SOL", bangla)
        self.assertIn("Token balance থাকা ATA close করা হবে না", bangla)

    def test_telegram_id_finder_text_is_localized(self):
        telegram_id_finder_text = self.namespace["telegram_id_finder_text"]
        result_text = self.namespace["telegram_id_result_text"]

        english = telegram_id_finder_text("en")
        bangla = telegram_id_finder_text("bn")

        self.assertIn("Telegram ID Finder", english)
        self.assertIn("public @username", english)
        self.assertIn("forward a message", english)
        self.assertIn("current chat ID", english)
        self.assertIn("Telegram ID Finder", bangla)
        self.assertIn("Public @username", bangla)
        self.assertIn("message forward", bangla)
        self.assertIn("current chat ID", bangla)
        self.assertIn("ID: -100123", result_text("en", [{"label": "Current chat", "id": -100123, "type": "Supergroup"}]))

    def test_telegram_id_lookup_target_normalization(self):
        normalize = self.namespace["normalize_telegram_lookup_target"]

        self.assertEqual(normalize("@mychannel"), "@mychannel")
        self.assertEqual(normalize("https://t.me/mychannel/123"), "@mychannel")
        self.assertEqual(normalize("https://t.me/c/123456/7"), "-100123456")
        self.assertEqual(normalize("-100123456"), -100123456)
        self.assertIsNone(normalize("https://t.me/+privateinvite"))

    def test_ai_support_knowledge_includes_free_service_guidance(self):
        self.assertIn("Free Service forwarding", BOT_SOURCE)
        self.assertIn("Connect personal account", BOT_SOURCE)
        self.assertIn("must discourage spam", BOT_SOURCE)
        self.assertIn("AI Support must explain these steps in Bengali for Bengali questions and English for English questions", BOT_SOURCE)

    def test_main_menu_and_handlers_route_free_forward_flow(self):
        main_menu = function_source("main_menu")
        button_handler = function_source("button_handler")
        waiting_trxid = function_source("waiting_trxid")
        main = function_source("main")

        self.assertIn('tr("free_service", lang)', main_menu)
        self.assertIn('callback_data="free_service"', main_menu)
        self.assertIn('query.data == "free_service"', button_handler)
        self.assertIn('if query.data != "tid_start":', button_handler)
        self.assertIn('context.user_data.pop("telegram_id_finder", None)', button_handler)
        self.assertIn('callback_data="telegram_message_forwarder"', function_source("free_service_keyboard"))
        self.assertIn('callback_data="solana_ata_refund"', function_source("free_service_keyboard"))
        self.assertIn('callback_data="telegram_id_finder"', function_source("free_service_keyboard"))
        self.assertIn('query.data == "telegram_message_forwarder"', button_handler)
        self.assertIn('query.data == "solana_ata_refund"', button_handler)
        self.assertIn('query.data == "telegram_id_finder"', button_handler)
        self.assertIn('query.data == "tid_start"', button_handler)
        self.assertIn('query.data == "sr_connect"', button_handler)
        self.assertIn('query.data == "sr_refund_confirm"', button_handler)
        self.assertIn("handle_telegram_id_finder_message", function_source("waiting_trxid"))
        self.assertIn("handle_telegram_id_finder_message", function_source("free_forward_media_handler"))
        self.assertIn("handle_solana_refund_text", function_source("waiting_trxid"))
        self.assertIn('query.data in {"ff_one_time", "ff_schedule"}', button_handler)
        self.assertIn('query.data == "pf_connect_account"', button_handler)
        self.assertIn("create_personal_auth_session", button_handler)
        self.assertIn("personal_auth_link", button_handler)
        self.assertIn("Open secure web login", button_handler)
        self.assertIn('query.data in {"pf_one_time", "pf_schedule"}', button_handler)
        self.assertIn('query.data == "pf_pick_list"', button_handler)
        self.assertIn('query.data == "pf_manual_targets"', button_handler)
        self.assertIn('query.data.startswith("pf_pick_toggle_")', button_handler)
        self.assertIn('query.data == "pf_pick_done"', button_handler)
        self.assertIn("list_personal_forward_dialogs", button_handler)
        self.assertIn("personal_forward_target_source_keyboard", button_handler)
        self.assertIn("handle_free_forward_text", waiting_trxid)
        self.assertIn("personal_forward_send_to_targets", function_source("handle_free_forward_text"))
        self.assertIn("free_forward_media_handler", main)
        self.assertIn("MessageHandler(filters.TEXT & ~filters.COMMAND, waiting_trxid)", main)
        self.assertIn("filters.PHOTO", main)
        self.assertIn("filters.Document.ALL", main)


if __name__ == "__main__":
    unittest.main()
