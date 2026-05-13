import ast
import asyncio
import os
import pathlib
import tempfile
import unittest


BOT_PATH = pathlib.Path(__file__).with_name("bot.py")
BOT_SOURCE = BOT_PATH.read_text(encoding="utf-8")
BOT_TREE = ast.parse(BOT_SOURCE)


WELCOME_NAMES = {
    "WELCOME_VIDEO_PATH",
    "TELEGRAM_VIDEO_CAPTION_LIMIT",
    "welcome_video_available",
    "is_video_message",
    "fits_video_caption",
    "send_welcome_video_background",
    "send_first_time_language_selection",
    "complete_language_selection_message",
}


def load_welcome_namespace():
    body = []
    for node in BOT_TREE.body:
        if isinstance(node, ast.Assign):
            targets = [target.id for target in node.targets if isinstance(target, ast.Name)]
            if any(target in WELCOME_NAMES for target in targets):
                body.append(node)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in WELCOME_NAMES:
            body.append(node)
    module = ast.Module(body=body, type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {
        "__file__": str(BOT_PATH),
        "asyncio": asyncio,
        "os": os,
    }
    exec(compile(module, str(BOT_PATH), "exec"), namespace)
    return namespace


class WelcomeVideoTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.namespace = load_welcome_namespace()

    def test_welcome_video_path_points_to_assets_mp4(self):
        self.assertEqual(
            self.namespace["WELCOME_VIDEO_PATH"],
            str(BOT_PATH.with_name("assets") / "welcome_video.mp4"),
        )
        self.assertEqual(self.namespace["TELEGRAM_VIDEO_CAPTION_LIMIT"], 1024)

    def test_welcome_video_available_checks_regular_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "welcome_video.mp4")
            self.assertFalse(self.namespace["welcome_video_available"](path))
            with open(path, "wb") as file:
                file.write(b"video")
            self.assertTrue(self.namespace["welcome_video_available"](path))

    def test_video_message_and_caption_limit_helpers(self):
        class Message:
            video = object()

        self.assertTrue(self.namespace["is_video_message"](Message()))
        self.assertFalse(self.namespace["is_video_message"](object()))
        self.assertTrue(self.namespace["fits_video_caption"]("x" * 1024))
        self.assertFalse(self.namespace["fits_video_caption"]("x" * 1025))

    async def test_first_time_language_selection_falls_back_to_text_when_video_missing(self):
        calls = []

        class Message:
            async def reply_video(self, **kwargs):
                calls.append(("video", kwargs))

            async def reply_text(self, text, reply_markup=None):
                calls.append(("text", text, reply_markup))

        class Update:
            message = Message()

        self.namespace.update(
            {
                "tr": lambda key, lang: f"{key}:{lang}",
                "language_keyboard": lambda: "keyboard",
                "welcome_video_available": lambda: False,
            }
        )

        await self.namespace["send_first_time_language_selection"](Update())

        self.assertEqual(calls, [("text", "choose_language:bn", "keyboard")])

    async def test_first_time_language_selection_sends_text_before_background_video(self):
        calls = []

        class Message:
            async def reply_text(self, text, reply_markup=None):
                calls.append(("text", text, reply_markup))

        class Update:
            message = Message()

        async def fake_background(message):
            calls.append(("video", message))

        self.namespace.update(
            {
                "tr": lambda key, lang: f"{key}:{lang}",
                "language_keyboard": lambda: "keyboard",
                "welcome_video_available": lambda: True,
                "send_welcome_video_background": fake_background,
            }
        )

        await self.namespace["send_first_time_language_selection"](Update())
        await asyncio.sleep(0)

        self.assertEqual(calls[0], ("text", "choose_language:bn", "keyboard"))
        self.assertEqual(calls[1][0], "video")

    async def test_language_selection_from_video_sends_home_text_as_separate_text_menu(self):
        calls = []

        class User:
            first_name = "Ada"

        class Message:
            video = object()

            async def reply_text(self, text, reply_markup=None):
                calls.append(("reply_text", text, reply_markup))

        class Query:
            from_user = User()
            message = Message()

            async def edit_message_caption(self, **kwargs):
                calls.append(("edit_caption", kwargs))

            async def edit_message_text(self, *args, **kwargs):
                calls.append(("edit_text", args, kwargs))

        self.namespace.update(
            {
                "language_saved_home_text": lambda first_name, lang: "saved home text",
                "main_menu": lambda user_id, lang: "menu",
                "tr": lambda key, lang: f"{key}:{lang}",
                "home_text": lambda first_name, lang: f"home:{first_name}:{lang}",
            }
        )

        await self.namespace["complete_language_selection_message"](Query(), "123", "en")

        self.assertEqual(calls[0], ("edit_caption", {"caption": "language_saved:en"}))
        self.assertEqual(calls[1], ("reply_text", "home:Ada:en", "menu"))


if __name__ == "__main__":
    unittest.main()
