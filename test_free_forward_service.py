import ast
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
        "ltext",
        "tr",
        "panel",
        "normalize_free_forward_target",
        "parse_free_forward_targets",
        "free_forward_text",
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
    namespace = {"re": __import__("re")}
    exec(compile(module, str(BOT_PATH), "exec"), namespace)
    return namespace


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

    def test_free_service_text_is_localized(self):
        free_forward_text = self.namespace["free_forward_text"]

        english = free_forward_text("en", True, "SenderBot", True)
        bangla = free_forward_text("bn", False, None, False)

        self.assertIn("Free Service", english)
        self.assertIn("@SenderBot", english)
        self.assertIn("many groups/channels", english)
        self.assertIn("ফ্রী সার্ভিস", bangla)
        self.assertIn("অনেক group/channel", bangla)
        self.assertIn("Connect করা নেই", bangla)

    def test_main_menu_and_handlers_route_free_forward_flow(self):
        main_menu = function_source("main_menu")
        button_handler = function_source("button_handler")
        waiting_trxid = function_source("waiting_trxid")
        main = function_source("main")

        self.assertIn('tr("free_service", lang)', main_menu)
        self.assertIn('callback_data="free_service"', main_menu)
        self.assertIn('query.data == "free_service"', button_handler)
        self.assertIn('query.data in {"ff_one_time", "ff_schedule"}', button_handler)
        self.assertIn("handle_free_forward_text", waiting_trxid)
        self.assertIn("free_forward_media_handler", main)
        self.assertIn("MessageHandler(filters.TEXT & ~filters.COMMAND, waiting_trxid)", main)
        self.assertIn("filters.PHOTO", main)
        self.assertIn("filters.Document.ALL", main)


if __name__ == "__main__":
    unittest.main()
