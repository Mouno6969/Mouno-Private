# bKash automation reliability

Your current automation depends on bKash SMS being forwarded to `/sms`. If bKash never sends an SMS, the bot cannot know about that payment automatically from SMS alone. There are only two reliable paths:

1. Use the official bKash Merchant/Payment Gateway API, where bKash sends/queryable payment status through API instead of personal SMS.
2. Keep SMS automation as the fast path and use admin manual verification for orders where bKash does not send SMS.

This repo now supports option 2 more safely.

## What the bot now does

### 1. Normal case

1. User places order.
2. User sends bKash payment.
3. SMS Forwarder POSTs the bKash message to:

```text
http://YOUR_SERVER:5000/sms
```

4. User submits TrxID in the bot.
5. Bot verifies the saved SMS and sends crypto automatically.

### 2. Delayed SMS case

Sometimes the user submits TrxID before the forwarded SMS arrives.

The bot now stores that order as pending. When the delayed bKash SMS eventually arrives, the bot:

1. Finds the pending order by TrxID.
2. Verifies the amount matches the pending order.
3. Sends the crypto automatically.
4. Updates the transaction log.
5. Deletes the pending order.

No admin action is needed if the delayed SMS eventually arrives and the amount matches.

### 3. No SMS from bKash

If bKash never sends SMS, the bot cannot verify it automatically through SMS. Use:

```text
/pending
```

Only admin can use this command.

The bot shows all pending bKash orders with Approve/Reject buttons. Open your bKash app, verify the TrxID manually, then tap Approve. The bot sends the crypto and updates TX log.

## Recommended production setup

For full automation without SMS dependency, apply for official bKash Merchant/PGW API access and replace manual bKash send-money flow with a bKash checkout/payment flow. That gives you official payment status callbacks or query APIs. Personal bKash app transaction history is not a reliable automation API.

## SMS Forwarder format

The parser expects messages like:

```text
You have received Tk 500 from 01XXXXXXXXX. TrxID ABC123XYZ at 02/05/2026 12:30
```

Make sure your SMS forwarder sends the raw SMS text in the POST body or JSON values.
