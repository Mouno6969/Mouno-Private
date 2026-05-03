import os
import tempfile
import unittest
from datetime import datetime, timedelta

import db


class GiveawayDbTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_path = db.DB_PATH
        db.DB_PATH = os.path.join(self.tmp.name, "test.db")
        db.init_db()

    def tearDown(self):
        db.DB_PATH = self.old_path
        self.tmp.cleanup()

    def test_claim_order_and_bonus_amounts_are_atomic(self):
        expires_at = (datetime.now() + timedelta(hours=1)).isoformat()
        db.create_giveaway_session("GIVE-TEST", "creator", "user_wallet", "solana", 1.0, 3, 2, 0.25, expires_at, "enc", "salt", "wallet")
        db.create_giveaway_codes("GIVE-TEST", ["AAA11111", "BBB22222", "CCC33333"])

        first = db.claim_giveaway_code("AAA11111", "u1")
        second = db.claim_giveaway_code("BBB22222", "u2")
        third = db.claim_giveaway_code("CCC33333", "u3")
        duplicate = db.claim_giveaway_code("AAA11111", "u4")

        self.assertTrue(first["ok"])
        self.assertEqual(first["claim_number"], 1)
        self.assertEqual(first["amount"], 1.25)
        self.assertEqual(second["claim_number"], 2)
        self.assertEqual(second["amount"], 1.25)
        self.assertEqual(third["claim_number"], 3)
        self.assertEqual(third["amount"], 1.0)
        self.assertFalse(duplicate["ok"])
        self.assertEqual(duplicate["reason"], "used")
        self.assertEqual(db.get_giveaway_session("GIVE-TEST")[8], 3)
        self.assertEqual(db.get_code("BBB22222")[9], 2)
        self.assertEqual(db.get_code("BBB22222")[10], 1.25)

    def test_existing_gift_code_shape_stays_compatible(self):
        expires_at = (datetime.now() + timedelta(hours=1)).isoformat()
        db.create_code("OLD12345", 2.0, expires_at, "trc20")
        row = db.get_code("OLD12345")

        self.assertEqual(row[0], "OLD12345")
        self.assertEqual(row[1], 2.0)
        self.assertEqual(row[6], "trc20")
        self.assertIsNone(row[7])
        used_row, error = db.use_code_if_available("OLD12345", "u1")
        self.assertIsNone(error)
        self.assertEqual(used_row[3], 1)
        self.assertEqual(used_row[4], "u1")


if __name__ == "__main__":
    unittest.main()
