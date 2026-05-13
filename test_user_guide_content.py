import unittest

from user_guide import GUIDE, NETWORK_GUIDE


class UserGuideContentTests(unittest.TestCase):
    def test_guide_is_formal_detailed_and_telegram_safe(self):
        self.assertIn("ব্যবহার বিধি / User Guide\n────────────────", GUIDE)
        self.assertIn("১. Bot দিয়ে কী করা যাবে", GUIDE)
        self.assertIn("৩. প্রথমবার wallet setup", GUIDE)
        self.assertIn("৬. Gas fee / network fee", GUIDE)
        self.assertIn("৮. Security rules", GUIDE)
        self.assertIn("১০. Common problem", GUIDE)
        self.assertIn("/setup", GUIDE)
        self.assertIn("/send_wallet", GUIDE)
        self.assertIn("/order ORD-XXXXXX", GUIDE)
        self.assertLess(len(GUIDE), 4096)

        for decorative in ("╔", "╗", "║", "╝", "━━━━━━━━", "🔐", "💰", "💸", "⚠️", "✅", "🔴"):
            self.assertNotIn(decorative, GUIDE)

    def test_network_guides_cover_all_supported_networks_formally(self):
        self.assertEqual(
            set(NETWORK_GUIDE),
            {"solana", "polygon", "bsc", "avalanche", "ethereum", "ethereum_usdc", "base", "trc20", "ton"},
        )
        for network, text in NETWORK_GUIDE.items():
            with self.subTest(network=network):
                self.assertIn("network guide", text.lower())
                self.assertIn("Gas", text)
                self.assertIn("────────────────", text)
                self.assertLess(len(text), 500)
                self.assertNotIn("━━━━━━━━", text)


if __name__ == "__main__":
    unittest.main()
