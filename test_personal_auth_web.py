import unittest
import asyncio

from personal_auth import PERSONAL_AUTH_SESSIONS, create_personal_auth_session, send_personal_auth_code
from webhook import app


class PersonalAuthWebTests(unittest.TestCase):
    def setUp(self):
        PERSONAL_AUTH_SESSIONS.clear()
        self.client = app.test_client()

    def tearDown(self):
        PERSONAL_AUTH_SESSIONS.clear()

    def test_auth_page_prompts_for_web_only_login_code(self):
        token = create_personal_auth_session("123", "bn")

        response = self.client.get(f"/telegram-auth/{token}")

        self.assertEqual(response.status_code, 200)
        text = response.get_data(as_text=True)
        self.assertIn("Telegram personal account login", text)
        self.assertIn("never in Telegram chat", text)
        self.assertIn("/send-code", text)

    def test_expired_or_unknown_auth_link_is_safe(self):
        response = self.client.get("/telegram-auth/not-a-real-token")

        self.assertEqual(response.status_code, 200)
        self.assertIn("login link has expired", response.get_data(as_text=True))

    def test_send_code_requires_runtime(self):
        token = create_personal_auth_session("123", "en")

        response = self.client.post(
            f"/telegram-auth/{token}/send-code",
            data={"api_id": "1", "api_hash": "0" * 32, "phone": "+8801711111111"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("runtime is not ready", response.get_data(as_text=True))

    def test_connected_auth_link_cannot_start_new_login(self):
        token = create_personal_auth_session("123", "en")
        PERSONAL_AUTH_SESSIONS[token]["status"] = "connected"

        with self.assertRaisesRegex(RuntimeError, "already connected"):
            asyncio.run(send_personal_auth_code(token, "1", "0" * 32, "+8801711111111"))


if __name__ == "__main__":
    unittest.main()
