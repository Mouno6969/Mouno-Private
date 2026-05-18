import unittest

from swap_service import decimal_amount_to_raw, find_chain, raw_amount_to_decimal, summarize_quote


class SwapServiceTest(unittest.TestCase):
    def test_decimal_amount_conversion_uses_token_decimals(self):
        self.assertEqual(decimal_amount_to_raw("100.25", 6), "100250000")
        self.assertEqual(raw_amount_to_decimal("99630000", 6), "99.63")

    def test_decimal_amount_rejects_precision_above_token_decimals(self):
        with self.assertRaises(ValueError):
            decimal_amount_to_raw("1.0000001", 6)

    def test_find_chain_matches_id_key_name_and_partial_name(self):
        chains = [
            {"id": 1, "key": "eth", "name": "Ethereum", "coin": "ETH"},
            {"id": 8453, "key": "bas", "name": "Base", "coin": "ETH"},
        ]
        self.assertEqual(find_chain(chains, "8453")["name"], "Base")
        self.assertEqual(find_chain(chains, "eth")["name"], "Ethereum")
        self.assertEqual(find_chain(chains, "base")["id"], 8453)

    def test_summarize_quote_detects_token_approval_and_fees(self):
        quote = {
            "toolDetails": {"name": "Relay"},
            "_fromTokenInfo": {"symbol": "USDC", "decimals": 6, "address": "0xabc"},
            "_toTokenInfo": {"symbol": "USDC", "decimals": 6, "address": "0xdef"},
            "estimate": {
                "toAmount": "99630000",
                "toAmountMin": "99000000",
                "approvalAddress": "0xspender",
                "gasCosts": [{"amountUSD": "0.10"}],
                "feeCosts": [{"amountUSD": "0.27"}],
                "executionDuration": 90,
            },
            "transactionRequest": {"to": "0xroute", "value": "0x0", "data": "0x1234", "chainId": 8453},
        }
        summary = summarize_quote(quote)
        self.assertEqual(summary["tool"], "Relay")
        self.assertEqual(summary["to_amount"], "99.63")
        self.assertEqual(summary["fee_usd"], "0.27")
        self.assertEqual(summary["gas_usd"], "0.10")
        self.assertTrue(summary["approval_needed"])


if __name__ == "__main__":
    unittest.main()
