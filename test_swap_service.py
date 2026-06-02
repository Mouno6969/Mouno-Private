import unittest
from urllib.parse import parse_qs, urlparse

from swap_service import build_lifi_widget_url, decimal_amount_to_raw, find_chain, raw_amount_to_decimal, summarize_quote


class SwapServiceTest(unittest.TestCase):
    def test_decimal_amount_conversion_uses_token_decimals(self):
        self.assertEqual(decimal_amount_to_raw("100.25", 6), "100250000")
        self.assertEqual(raw_amount_to_decimal("99630000", 6), "99.63")

    def test_decimal_amount_rejects_precision_above_token_decimals(self):
        with self.assertRaises(ValueError):
            decimal_amount_to_raw("1.0000001", 6)

    def test_normalize_token_input_solana_native(self):
        from swap_service import normalize_token_input
        self.assertEqual(normalize_token_input("native", "1151111081099710"), "11111111111111111111111111111111")
        self.assertEqual(normalize_token_input("sol", "sol"), "11111111111111111111111111111111")
        self.assertEqual(normalize_token_input("native", "1"), "0x0000000000000000000000000000000000000000")

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

    def test_build_lifi_widget_url_prefills_wallet_connect_swap(self):
        intent = {
            "from_chain_id": 8453,
            "to_chain_id": 137,
            "from_token": "USDC",
            "to_token": "USDC",
            "amount": "10.5",
            "wallet": "0x1111111111111111111111111111111111111111",
        }
        quote = {
            "_fromTokenInfo": {"address": "0xfrom"},
            "_toTokenInfo": {"address": "0xto"},
        }
        url = build_lifi_widget_url(intent, quote, base_url="https://playground.li.fi/")
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        self.assertEqual(parsed.netloc, "playground.li.fi")
        self.assertEqual(params["fromChain"], ["8453"])
        self.assertEqual(params["toChain"], ["137"])
        self.assertEqual(params["fromToken"], ["0xfrom"])
        self.assertEqual(params["toToken"], ["0xto"])
        self.assertEqual(params["fromAmount"], ["10.5"])
        self.assertEqual(params["toAddress"], ["0x1111111111111111111111111111111111111111"])


if __name__ == "__main__":
    unittest.main()
