import unittest

import bot


class FakeTelegramBot:
    def __init__(self):
        self.messages = []

    async def send_message(self, chat_id, text, **kwargs):
        self.messages.append((chat_id, text, kwargs))


class FakeApp:
    def __init__(self):
        self.bot = FakeTelegramBot()


class AdminBkashParseAlertTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.old_admin_id = bot.ADMIN_ID
        self.old_touch = bot.touch_webhook_notice
        self.old_trx_exists = bot.trx_exists
        self.old_sms_exists = bot.sms_exists
        self.old_save_sms = bot.save_sms
        self.old_get_pending_order = bot.get_pending_order
        self.old_get_seller_by_sms_token = bot.get_seller_by_sms_token
        self.old_save_seller_payment_notice = bot.save_seller_payment_notice
        self.old_find_waiting_seller_order_by_trx = bot.find_waiting_seller_order_by_trx

        bot.ADMIN_ID = "admin-1"
        bot.touch_webhook_notice = lambda *args, **kwargs: None
        bot.sms_exists = lambda trx_id: False
        bot.save_sms = lambda *args, **kwargs: True
        bot.get_pending_order = lambda trx_id: None
        bot.save_seller_payment_notice = lambda *args, **kwargs: False
        bot.find_waiting_seller_order_by_trx = lambda *args, **kwargs: None

    def tearDown(self):
        bot.ADMIN_ID = self.old_admin_id
        bot.touch_webhook_notice = self.old_touch
        bot.trx_exists = self.old_trx_exists
        bot.sms_exists = self.old_sms_exists
        bot.save_sms = self.old_save_sms
        bot.get_pending_order = self.old_get_pending_order
        bot.get_seller_by_sms_token = self.old_get_seller_by_sms_token
        bot.save_seller_payment_notice = self.old_save_seller_payment_notice
        bot.find_waiting_seller_order_by_trx = self.old_find_waiting_seller_order_by_trx

    async def test_alerts_admin_immediately_even_for_duplicate_transaction(self):
        app = FakeApp()
        bot.trx_exists = lambda trx_id: True

        await bot.process_bkash(app, "bKash Payment Received Tk 500 TrxID ABC123XYZ", "bkash_sms")

        self.assertEqual(len(app.bot.messages), 1)
        chat_id, text, _kwargs = app.bot.messages[0]
        self.assertEqual(chat_id, "admin-1")
        self.assertIn("bKash notice parsed", text)
        self.assertIn("ABC123XYZ", text)
        self.assertIn("500.0 BDT", text)
        self.assertIn("Scope: main", text)

    async def test_alerts_admin_for_seller_scoped_notice(self):
        app = FakeApp()
        bot.get_seller_by_sms_token = lambda token: ("seller-1", "user", "name", "bkash", "support", "approved")

        await bot.process_bkash(
            app,
            "bKash Payment Received Tk 700 TrxID SELLER123",
            "bkash_app_notification",
            {"seller_token": "seller-token"},
        )

        self.assertEqual(len(app.bot.messages), 1)
        chat_id, text, _kwargs = app.bot.messages[0]
        self.assertEqual(chat_id, "admin-1")
        self.assertIn("Scope: seller", text)
        self.assertIn("Seller: seller-1", text)
        self.assertIn("SELLER123", text)


if __name__ == "__main__":
    unittest.main()
