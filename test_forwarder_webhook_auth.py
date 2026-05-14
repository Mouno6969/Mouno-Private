import unittest

try:
    import webhook
except ModuleNotFoundError as exc:
    webhook = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


class ForwarderWebhookAuthTests(unittest.TestCase):
    def setUp(self):
        if webhook is None:
            self.skipTest(f"webhook dependencies unavailable: {IMPORT_ERROR}")
        self.old_secret = webhook.FORWARDER_SECRET
        self.old_bot_token = webhook.BOT_TOKEN
        self.old_admin_id = webhook.ADMIN_ID
        self.old_touch = webhook.touch_webhook_notice
        self.old_get_seller = webhook.get_seller_by_sms_token
        self.old_requests_post = webhook.requests.post
        self.calls = []
        webhook.BOT_TOKEN = None
        webhook.ADMIN_ID = None
        webhook.touch_webhook_notice = lambda *args, **kwargs: None
        webhook.set_callback(lambda text, source, meta=None: self.calls.append((text, source, meta)))

    def tearDown(self):
        webhook.FORWARDER_SECRET = self.old_secret
        webhook.BOT_TOKEN = self.old_bot_token
        webhook.ADMIN_ID = self.old_admin_id
        webhook.touch_webhook_notice = self.old_touch
        webhook.get_seller_by_sms_token = self.old_get_seller
        webhook.requests.post = self.old_requests_post
        webhook.set_callback(None)

    def test_server_sends_admin_parse_alert_immediately(self):
        webhook.FORWARDER_SECRET = None
        webhook.BOT_TOKEN = "bot-token"
        webhook.ADMIN_ID = "admin-1"
        posts = []

        class Response:
            status_code = 200
            text = "ok"

        def fake_post(url, **kwargs):
            posts.append((url, kwargs))
            return Response()

        webhook.requests.post = fake_post

        response = webhook.app.test_client().post("/notification", json={"text": "bKash Payment Received Tk 500 TrxID ABC123XYZ"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(posts), 1)
        self.assertIn("botbot-token/sendMessage", posts[0][0])
        self.assertEqual(posts[0][1]["json"]["chat_id"], "admin-1")
        self.assertIn("bKash notice parsed", posts[0][1]["json"]["text"])
        self.assertIn("ABC123XYZ", posts[0][1]["json"]["text"])
        self.assertEqual(self.calls[0][2], {"admin_parse_alert_sent": True})

    def test_android_structured_parse_payload_triggers_admin_alert(self):
        webhook.FORWARDER_SECRET = None
        webhook.BOT_TOKEN = "bot-token"
        webhook.ADMIN_ID = "admin-1"
        posts = []

        class Response:
            status_code = 200
            text = "ok"

        def fake_post(url, **kwargs):
            posts.append((url, kwargs))
            return Response()

        webhook.requests.post = fake_post

        response = webhook.app.test_client().post(
            "/notification",
            json={
                "source": "sms_notification",
                "title": "bKash",
                "text": "Payment notification text was truncated by Android",
                "parsed_bkash": True,
                "amount_bdt": 2.0,
                "trx_id": "DEE987XNRV",
                "notice_sender": "01773076694",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json["parsed"])
        self.assertEqual(len(posts), 1)
        self.assertIn("DEE987XNRV", posts[0][1]["json"]["text"])
        self.assertIn("2.0 BDT", posts[0][1]["json"]["text"])
        self.assertEqual(self.calls[0][1], "bkash_app_notification")
        self.assertEqual(self.calls[0][2], {"admin_parse_alert_sent": True})
        self.assertIn("bKash Payment Received Tk 2.0 TrxID DEE987XNRV", self.calls[0][0])

    def test_structured_parse_callback_ignores_conflicting_trx_in_raw_text(self):
        webhook.FORWARDER_SECRET = None

        response = webhook.app.test_client().post(
            "/notification",
            json={
                "source": "sms_notification",
                "title": "bKash",
                "text": "Payment notification text was truncated TrxID WRONG123",
                "parsed_bkash": True,
                "amount_bdt": 2.0,
                "trx_id": "DEE987XNRV",
                "notice_sender": "01773076694",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json["parsed"])
        self.assertEqual(self.calls[0][0], "bKash Payment Received Tk 2.0 TrxID DEE987XNRV")
        self.assertEqual(webhook.parse_bkash_payment_notice(self.calls[0][0])["trx_id"], "DEE987XNRV")

    def test_rejects_forwarder_notice_without_secret_when_configured(self):
        webhook.FORWARDER_SECRET = "test-secret"

        response = webhook.app.test_client().post("/sms", data="bKash Payment Received Tk 500 TrxID ABC123XYZ")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.calls, [])

    def test_accepts_forwarder_notice_with_header_secret(self):
        webhook.FORWARDER_SECRET = "test-secret"

        response = webhook.app.test_client().post(
            "/sms",
            data="bKash Payment Received Tk 500 TrxID ABC123XYZ",
            headers={"X-Forwarder-Token": "test-secret"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.calls[0][1], "bkash_sms")

    def test_authorization_header_requires_bearer_scheme(self):
        webhook.FORWARDER_SECRET = "test-secret"

        bad_response = webhook.app.test_client().post(
            "/sms",
            data="bKash Payment Received Tk 500 TrxID ABC123XYZ",
            headers={"Authorization": "test-secret"},
        )
        good_response = webhook.app.test_client().post(
            "/sms",
            data="bKash Payment Received Tk 500 TrxID ABC123XYZ",
            headers={"Authorization": "Bearer test-secret"},
        )

        self.assertEqual(bad_response.status_code, 403)
        self.assertEqual(good_response.status_code, 200)
        self.assertEqual(len(self.calls), 1)

    def test_rejects_secret_in_query_or_body_when_configured(self):
        webhook.FORWARDER_SECRET = "test-secret"

        query_response = webhook.app.test_client().post(
            "/sms?forwarder_secret=test-secret",
            data="bKash Payment Received Tk 500 TrxID ABC123XYZ",
        )
        body_response = webhook.app.test_client().post(
            "/sms",
            json={"forwarder_secret": "test-secret", "text": "bKash Payment Received Tk 500 TrxID ABC123XYZ"},
        )

        self.assertEqual(query_response.status_code, 403)
        self.assertEqual(body_response.status_code, 403)
        self.assertEqual(self.calls, [])

    def test_accepts_seller_route_token_without_shared_secret_header(self):
        webhook.FORWARDER_SECRET = "test-secret"

        response = webhook.app.test_client().post(
            "/seller/SELLER123/sms",
            json={"text": "bKash Payment Received Tk 500 TrxID ABC123XYZ", "seller_token": "SELLER123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.calls[0][2], {"seller_token": "SELLER123"})
        self.assertNotIn("SELLER123", self.calls[0][0])

    def test_accepts_legacy_notice_when_secret_is_not_configured(self):
        webhook.FORWARDER_SECRET = None

        response = webhook.app.test_client().post("/notification", json={"text": "bKash Payment Received Tk 500 TrxID ABC123XYZ"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["payment_status"], "parsed")
        self.assertFalse(response.json["matched_order"])
        self.assertFalse(response.json["duplicate"])
        self.assertFalse(response.json["manual_review"])
        self.assertEqual(len(self.calls), 1)

    def test_accepts_real_bkash_received_sms_wording(self):
        webhook.FORWARDER_SECRET = None

        response = webhook.app.test_client().post(
            "/sms",
            data="You have received Tk 1.00 from 01773076694. Ref 1234. Fee Tk 0.00. Balance Tk 94.69. TrxID DEF88BZRY8 at 15/05/2026 03:05",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json["parsed"])
        self.assertEqual(response.json["payment_status"], "parsed")
        self.assertEqual(response.json["trx_id"], "DEF88BZRY8")
        self.assertEqual(response.json["amount_bdt"], 1.0)
        self.assertEqual(len(self.calls), 1)

    def test_ack_includes_callback_payment_outcome(self):
        webhook.FORWARDER_SECRET = None
        webhook.set_callback(lambda text, source, meta=None: {
            "payment_status": "matched_order",
            "matched_order": True,
            "order_id": "ORD-123",
            "message": "Payment matched an order and crypto delivery completed.",
        })

        response = webhook.app.test_client().post("/notification", json={"text": "bKash Payment Received Tk 500 TrxID ABC123XYZ"})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json["parsed"])
        self.assertEqual(response.json["payment_status"], "matched_order")
        self.assertTrue(response.json["matched_order"])
        self.assertEqual(response.json["order_id"], "ORD-123")

    def test_ack_marks_unsupported_notice_ignored(self):
        webhook.FORWARDER_SECRET = None

        response = webhook.app.test_client().post("/notification", json={"text": "hello"})

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json["parsed"])
        self.assertEqual(response.json["payment_status"], "ignored")

    def test_forwarder_health_reports_bad_secret(self):
        webhook.FORWARDER_SECRET = "test-secret"

        response = webhook.app.test_client().get("/forwarder-health", headers={"X-Forwarder-Token": "wrong"})

        self.assertEqual(response.status_code, 403)
        self.assertTrue(response.json["server_reachable"])
        self.assertFalse(response.json["auth_ok"])

    def test_forwarder_health_accepts_secret(self):
        webhook.FORWARDER_SECRET = "test-secret"

        response = webhook.app.test_client().get("/forwarder-health", headers={"X-Forwarder-Token": "test-secret"})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json["server_reachable"])
        self.assertTrue(response.json["auth_ok"])

    def test_seller_health_validates_approved_token(self):
        webhook.get_seller_by_sms_token = lambda token: ("seller-id", "user", "name", "bkash", "support", "approved") if token == "SELLER123" else None

        good_response = webhook.app.test_client().get("/seller/SELLER123/health")
        bad_response = webhook.app.test_client().get("/seller/BAD/health")

        self.assertEqual(good_response.status_code, 200)
        self.assertTrue(good_response.json["auth_ok"])
        self.assertEqual(bad_response.status_code, 403)
        self.assertFalse(bad_response.json["auth_ok"])


if __name__ == "__main__":
    unittest.main()
