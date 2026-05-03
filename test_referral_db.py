import os
import tempfile
import unittest

import db


class ReferralDbTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_path = db.DB_PATH
        db.DB_PATH = os.path.join(self.tmp.name, "test.db")
        db.init_db()

    def tearDown(self):
        db.DB_PATH = self.old_path
        self.tmp.cleanup()

    def test_referral_code_is_stable_and_unique(self):
        c1 = db.get_or_create_referral_code("u1")
        c2 = db.get_or_create_referral_code("u1")
        c3 = db.get_or_create_referral_code("u2")

        self.assertEqual(c1, c2)
        self.assertNotEqual(c1, c3)
        self.assertGreaterEqual(len(c1), 6)

    def test_bind_rejects_self_and_does_not_overwrite(self):
        c1 = db.get_or_create_referral_code("ref1")
        c2 = db.get_or_create_referral_code("ref2")

        self.assertEqual(db.bind_referral("ref1", c1), "self")
        self.assertEqual(db.bind_referral("user", c1), "bound")
        self.assertEqual(db.bind_referral("user", c2), "exists")
        self.assertEqual(db.get_referrer_for_user("user"), "ref1")

    def test_credit_is_idempotent_and_balance_updates_with_debit(self):
        code = db.get_or_create_referral_code("ref")
        self.assertEqual(db.bind_referral("buyer", code), "bound")

        first = db.credit_referral_reward("buyer", "bkash", "trx1", 100, 5, "test")
        second = db.credit_referral_reward("buyer", "bkash", "trx1", 100, 5, "duplicate")

        self.assertIsNotNone(first)
        self.assertIsNone(second)
        self.assertAlmostEqual(db.referral_balance("ref"), 5.0)
        stats = db.referral_stats("ref")
        self.assertEqual(stats["referral_count"], 1)
        self.assertAlmostEqual(stats["total_earned"], 5.0)

        wd = db.create_referral_withdrawal("ref", 2, "solana", "wallet")
        self.assertTrue(db.debit_referral_withdrawal("ref", wd, 2, "solana", "wallet", "sig"))
        self.assertAlmostEqual(db.referral_balance("ref"), 3.0)
        stats = db.referral_stats("ref")
        self.assertAlmostEqual(stats["total_withdrawn"], 2.0)

    def test_withdrawal_reservation_blocks_over_reserve_and_failure_releases(self):
        code = db.get_or_create_referral_code("ref")
        self.assertEqual(db.bind_referral("buyer", code), "bound")
        db.credit_referral_reward("buyer", "bkash", "trx1", 100, 5, "test")

        wd1 = db.create_referral_withdrawal("ref", 3, "solana", "wallet1")
        self.assertTrue(db.reserve_referral_withdrawal("ref", wd1, 3, "solana", "wallet1"))
        self.assertAlmostEqual(db.referral_balance("ref"), 5.0)
        self.assertAlmostEqual(db.referral_available_balance("ref"), 2.0)

        wd2 = db.create_referral_withdrawal("ref", 3, "solana", "wallet2")
        self.assertFalse(db.reserve_referral_withdrawal("ref", wd2, 3, "solana", "wallet2"))

        db.fail_referral_withdrawal(wd1, "send failed")
        self.assertAlmostEqual(db.referral_balance("ref"), 5.0)
        self.assertAlmostEqual(db.referral_available_balance("ref"), 5.0)
        self.assertTrue(db.reserve_referral_withdrawal("ref", wd2, 3, "solana", "wallet2"))
        db.complete_referral_withdrawal(wd2, "sig")
        self.assertAlmostEqual(db.referral_balance("ref"), 2.0)
        self.assertAlmostEqual(db.referral_available_balance("ref"), 2.0)

    def test_default_settings_disabled(self):
        self.assertEqual(db.get_setting("referral_enabled"), "off")
        self.assertEqual(db.get_setting("referral_percent"), "0")
        self.assertEqual(db.get_setting("referral_min_withdraw_usd"), "1")


if __name__ == "__main__":
    unittest.main()
