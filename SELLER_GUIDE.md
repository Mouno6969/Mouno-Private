# Seller application and marketplace guide

## Seller setup

1. Open **🏪 Seller Center** or run `/seller_center`.
2. Tap **📝 Apply** and submit display name, seller bKash number, and support contact.
3. Admin approves from **🏪 Seller Apps** using the inline approve/reject buttons.
4. After approval, open **Seller Center → Delivery Wallet** and add a private key for each supported network. The key is encrypted with `SELLER_WALLET_MASTER_KEY`; the Telegram message is deleted best-effort.
5. Set a seller-specific BDT rate for each enabled network. Enter `0` to clear the override and use the global/admin rate.

Supported automated seller delivery networks: Solana USDC, Polygon USDC, BSC USDT, Avalanche USDT, Ethereum USDT/USDC, Base USDC, and TRC20 USDT. TON seller automated delivery is not supported.

## bKash forwarder endpoints

Use the seller SMS token shown in Seller Center:

- `/seller/<sms_token>/sms`
- `/seller/<sms_token>/notification`
- `/sms?seller_token=<sms_token>`
- `/notification?seller_token=<sms_token>`

Forward raw SMS/notification text or JSON containing the bKash notice. Seller-token notices are scoped by seller and do not enter the global admin `/sms` matcher.

## Seller orders

Buyers open **🛍️ Sellers**, choose an approved seller, choose bKash or Telegram Stars, select an enabled network, enter destination wallet and amount, then pay.

- bKash orders wait for a TrxID and the seller-specific webhook notice. Amount matches complete automatically from the seller delivery wallet. Mismatches go to seller/admin manual approval.
- Telegram Stars orders deliver crypto from the seller wallet when possible and create a seller Stars ledger entry for manual admin payout, because Stars cannot be transferred automatically to sellers.
