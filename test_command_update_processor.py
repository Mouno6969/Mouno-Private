import ast
import asyncio
import pathlib
import unittest


BOT_PATH = pathlib.Path(__file__).with_name("bot.py")
BOT_SOURCE = BOT_PATH.read_text(encoding="utf-8")
BOT_TREE = ast.parse(BOT_SOURCE)


def load_processor_namespace():
    body = []
    for node in BOT_TREE.body:
        if isinstance(node, ast.FunctionDef) and node.name == "is_command_update":
            body.append(node)
        elif isinstance(node, ast.ClassDef) and node.name == "ChatScopedUpdateProcessor":
            body.append(node)

    module = ast.Module(body=body, type_ignores=[])
    ast.fix_missing_locations(module)

    class BaseUpdateProcessor:
        def __init__(self, max_concurrent_updates):
            self.max_concurrent_updates = max_concurrent_updates

    namespace = {
        "asyncio": asyncio,
        "BaseUpdateProcessor": BaseUpdateProcessor,
    }
    exec(compile(module, str(BOT_PATH), "exec"), namespace)
    return namespace


class CommandUpdateProcessorTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.namespace = load_processor_namespace()

    def make_update(self, text=None):
        class Chat:
            id = 1

        class User:
            id = 2

        class Message:
            pass

        class Update:
            effective_chat = Chat()
            effective_user = User()
            effective_message = Message()

        Update.effective_message.text = text
        return Update()

    def test_is_command_update_accepts_slash_commands_only(self):
        is_command_update = self.namespace["is_command_update"]

        self.assertTrue(is_command_update(self.make_update("/start")))
        self.assertTrue(is_command_update(self.make_update("  /help")))
        self.assertFalse(is_command_update(self.make_update("start")))
        self.assertFalse(is_command_update(self.make_update(None)))

    async def test_commands_bypass_same_chat_lock_during_long_send(self):
        processor = self.namespace["ChatScopedUpdateProcessor"](8)
        long_started = asyncio.Event()
        release_long = asyncio.Event()
        events = []

        async def long_send_handler():
            events.append("long_started")
            long_started.set()
            await release_long.wait()
            events.append("long_finished")

        async def command_handler():
            events.append("command_handled")

        long_task = asyncio.create_task(processor.do_process_update(self.make_update("93ba"), long_send_handler()))
        await long_started.wait()

        command_task = asyncio.create_task(processor.do_process_update(self.make_update("/start"), command_handler()))
        await asyncio.wait_for(command_task, timeout=1)

        self.assertEqual(events, ["long_started", "command_handled"])

        release_long.set()
        await asyncio.wait_for(long_task, timeout=1)
        self.assertEqual(events, ["long_started", "command_handled", "long_finished"])


if __name__ == "__main__":
    unittest.main()
