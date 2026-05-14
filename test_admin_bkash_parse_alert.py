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
        self.old_get_seller_payment_notice_owner = bot.get_seller_payment_notice_owner
        self.old_get_completed_seller_order_by_trx = bot.get_completed_seller_order_by_trx
        self.old_get_seller_order = bot.get_seller_order
        self.old_get_seller = bot.get_seller
        self.old_update_seller_order = bot.update_seller_order

        bot.ADMIN_ID = "admin-1"
        bot.touch_webhook_notice = lambda *args, **kwargs: None
        bot.sms_exists = lambda trx_id: False
        bot.save_sms = lambda *args, **kwargs: True
        bot.get_pending_order = lambda trx_id: None
        bot.save_seller_payment_notice = lambda *args, **kwargs: False
        bot.find_waiting_seller_order_by_trx = lambda *args, **kwargs: None
        bot.get_seller_payment_notice_owner = lambda trx_id: None
        bot.get_completed_seller_order_by_trx = lambda trx_id: None

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
        bot.get_seller_payment_notice_owner = self.old_get_seller_payment_notice_owner
        bot.get_completed_seller_order_by_trx = self.old_get_completed_seller_order_by_trx
        bot.get_seller_order = self.old_get_seller_order
        bot.get_seller = self.old_get_seller
        bot.update_seller_order = self.old_update_seller_order

    async def test_alerts_admin_immediately_even_for_duplicate_transaction(self):
        app = FakeApp()
        bot.trx_exists = lambda trx_id: True

        outcome = await bot.process_bkash(app, "bKash Payment Received Tk 500 TrxID ABC123XYZ", "bkash_sms")

        self.assertEqual(len(app.bot.messages), 1)
        chat_id, text, _kwargs = app.bot.messages[0]
        self.assertEqual(chat_id, "admin-1")
        self.assertIn("bKash notice parsed", text)
        self.assertIn("ABC123XYZ", text)
        self.assertIn("500.0 BDT", text)
        self.assertIn("Scope: main", text)
        self.assertEqual(outcome["payment_status"], "duplicate")
        self.assertTrue(outcome["duplicate"])

    async def test_does_not_duplicate_webhook_sent_parse_alert(self):
        app = FakeApp()

        outcome = await bot.process_bkash(
            app,
            "bKash Payment Received Tk 500 TrxID ABC123XYZ",
            "bkash_sms",
            {"admin_parse_alert_sent": True},
        )

        self.assertEqual(app.bot.messages, [])
        self.assertEqual(outcome["payment_status"], "parsed")

    async def test_alerts_admin_for_seller_scoped_notice(self):
        app = FakeApp()
        bot.get_seller_by_sms_token = lambda token: ("seller-1", "user", "name", "bkash", "support", "approved")

        outcome = await bot.process_bkash(
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
        self.assertEqual(outcome["payment_status"], "duplicate")

    async def test_blocks_seller_notice_when_trx_belongs_to_another_seller(self):
        app = FakeApp()
        saved = []
        bot.get_seller_by_sms_token = lambda token: ("seller-2", "user", "name", "bkash", "support", "approved")
        bot.get_seller_payment_notice_owner = lambda trx_id: ("seller-1", trx_id, 700.0, "bkash_sms", "seller_bkash", "raw", 0, "now")
        bot.save_seller_payment_notice = lambda *args, **kwargs: saved.append(args) or True

        outcome = await bot.process_bkash(
            app,
            "bKash Payment Received Tk 700 TrxID SELLER123",
            "bkash_app_notification",
            {"seller_token": "seller-token"},
        )

        self.assertEqual(outcome["payment_status"], "duplicate")
        self.assertTrue(outcome["duplicate"])
        self.assertIn("another seller", outcome["message"])
        self.assertEqual(saved, [])
        self.assertEqual(app.bot.messages[0][0], "admin-1")
        self.assertIn("Cross-seller", app.bot.messages[0][1])

    async def test_manual_seller_approval_rejects_cross_seller_trx(self):
        updates = []
        bot.get_seller_order = lambda order_id: (
            order_id, "seller-2", "buyer-1", "buyer", "bkash", "SELLER123", "solana", "wallet", 700.0, 1.0, None, "pending_manual", None, "", "created", "updated"
        )
        bot.get_seller = lambda seller_id: (seller_id, "user", "name", "bkash", "support", "approved")
        bot.get_seller_payment_notice_owner = lambda trx_id: ("seller-1", trx_id, 700.0, "bkash_sms", "seller_bkash", "raw", 0, "now")
        bot.update_seller_order = lambda *args, **kwargs: updates.append((args, kwargs))

        ok, result = await bot.complete_seller_order(FakeTelegramBot(), "ORD-2", "seller-2")

        self.assertFalse(ok)
        self.assertIn("another seller", result)
        self.assertEqual(updates[0][0], ("ORD-2",))
        self.assertEqual(updates[0][1]["status"], "rejected")


if __name__ == "__main__":
    unittest.main()
