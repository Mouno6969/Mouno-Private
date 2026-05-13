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
        self.old_touch = webhook.touch_webhook_notice
        self.calls = []
        webhook.touch_webhook_notice = lambda *args, **kwargs: None
        webhook.set_callback(lambda text, source, meta=None: self.calls.append((text, source, meta)))

    def tearDown(self):
        webhook.FORWARDER_SECRET = self.old_secret
        webhook.touch_webhook_notice = self.old_touch
        webhook.set_callback(None)

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

    def test_accepts_legacy_notice_when_secret_is_not_configured(self):
        webhook.FORWARDER_SECRET = None

        response = webhook.app.test_client().post("/notification", json={"text": "bKash Payment Received Tk 500 TrxID ABC123XYZ"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(self.calls), 1)


if __name__ == "__main__":
    unittest.main()
