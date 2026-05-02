# Seller marketplace setup guide

This repository includes an admin-approved user-seller marketplace layer. Sellers are inactive until an admin approves them.

## Seller application

1. Open the bot and tap `🏪 Seller Center` or send `/seller`.
2. Submit display/shop name, seller bKash number, and support contact.
3. Wait for admin approval. Admin can use `/sellers` or the Seller Admin menu to approve/reject.

## Delivery wallet setup

After approval:

1. Open `🏪 Seller Center` → `🔐 Delivery Wallet`.
2. Select a supported delivery network: Solana, Polygon, BSC, Avalanche, Ethereum USDT/USDC, Base, or TRC20.
3. Send the private key for the seller delivery wallet only on that explicit setup screen.
4. The bot deletes the message after receipt, validates the public wallet address, and encrypts the key using `SELLER_WALLET_MASTER_KEY`.
5. Keep enough native gas token in that wallet: SOL, MATIC/POL, BNB, AVAX, ETH, or TRX.

`SELLER_WALLET_MASTER_KEY` must be set in `.env`. If it is missing, seller wallet setup fails and no key is stored.

## Seller rates

- Use `Seller Center` → `📈 Rates` to set BDT price per 1 USDC/USDT.
- Enter `0` to use the global/admin rate.
- Buyers see seller-specific rate when configured; otherwise global rate is used.

## bKash SMS/notification forwarder

Install an Android SMS/notification forwarder on the phone receiving the seller bKash messages.

Use seller-specific endpoints from Seller Center. Replace values as needed:

```text
http://YOUR_SERVER:5000/seller/<SMS_TOKEN>/sms
http://YOUR_SERVER:5000/seller/<SMS_TOKEN>/notification
```

Alternative query-token routes:

```text
http://YOUR_SERVER:5000/sms?seller_token=<SMS_TOKEN>
http://YOUR_SERVER:5000/notification?seller_token=<SMS_TOKEN>
```

The webhook also accepts JSON with `seller_token` or `token` fields.

Forward the raw SMS/app notification title/body/text. Example JSON:

```json
{
  "seller_token": "SELLER_SMS_TOKEN",
  "app": "bKash",
  "title": "Payment Received",
  "text": "You have received Tk 500 from 01XXXXXXXXX. TrxID ABC123XYZ"
}
```

The notice must include amount (`Tk`, `BDT`, or `৳`) and transaction ID (`TrxID`, `TxnID`, or `Transaction ID`).

## Buyer flow

1. Buyer taps `🛍️ Sellers`.
2. Buyer selects an approved seller.
3. Buyer selects `bKash` or `Telegram Stars`.
4. Buyer selects a seller-enabled network and enters destination wallet.
5. For bKash, buyer sends the exact BDT to the seller bKash number and submits TrxID.
6. If seller forwarder notice is already saved and amount matches, the bot sends crypto from the seller delivery wallet automatically.
7. If notice is missing or mismatched, order becomes manual review; seller/admin can approve/reject in-bot.

## Telegram Stars seller sales

Telegram Bot API cannot automatically transfer Stars from the bot to arbitrary sellers. Seller Stars earnings are recorded in `seller_star_ledger` as `pending_payout`.

Flow:

1. Buyer pays a bot Stars invoice for a seller order.
2. Bot records seller ledger entry.
3. Bot attempts crypto delivery from the seller delivery wallet.
4. Admin manually settles the seller outside Telegram Stars transfer and uses `/seller_payouts` to mark ledger entries paid.

Do not promise automatic Stars withdrawal to sellers.

## Test checklist

1. Apply as a seller.
2. Admin approves with `/sellers`.
3. Seller adds delivery wallet and rate.
4. Configure Android forwarder endpoint with seller token.
5. Create a small buyer bKash order.
6. Verify notice parsing and automatic delivery.
7. Test missing/mismatched notice and manual approve/reject.
8. Test seller Stars invoice and `/seller_payouts` ledger mark-paid.
