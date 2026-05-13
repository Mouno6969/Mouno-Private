# bKash automation reliability

Your bot can now parse both bKash SMS text and bKash app notification text, as long as your Android forwarder can send that text to the server.

## Endpoints

If `FORWARDER_SECRET` is set in the bot `.env`, every forwarder request must include either:

```text
X-Forwarder-Token: YOUR_SECRET
```

or:

```text
Authorization: Bearer YOUR_SECRET
```

Forward SMS messages to:

```text
http://YOUR_SERVER:5000/sms
```

Forward app notifications to either:

```text
http://YOUR_SERVER:5000/notification
```

or:

```text
http://YOUR_SERVER:5000/bkash-notification
```

Both endpoints use the same parser and the same duplicate-protection logic.

Seller forwarder APKs post to `/seller/<seller_sms_token>/sms` and `/seller/<seller_sms_token>/notification`. Those seller routes use the seller SMS token as the seller-specific credential, so do not share the global `FORWARDER_SECRET` with sellers.

## Duplicate protection

The bot matches by TrxID.

- If SMS and app notification both arrive for the same TrxID, only the first one is saved/processed.
- If the transaction was already completed, later notices with the same TrxID are ignored.
- One TrxID cannot be used for more than one completed transaction because `transactions.trx_id` is the primary key and the bot checks `trx_exists()` before processing payment notices.

## Supported text examples

SMS-style:

```text
You have received Tk 500 from 01XXXXXXXXX. TrxID ABC123XYZ at 02/05/2026 12:30
```

App-notification-style examples the parser can understand:

```text
bKash Payment Received Tk 500 TrxID ABC123XYZ
```

```text
Receive Money ৳500 from 01XXXXXXXXX TxnID ABC123XYZ
```

```text
Cash In BDT 500 Transaction ID ABC123XYZ
```

The notification must include:

1. Amount, with `Tk`, `BDT`, or `৳`
2. Transaction ID, using `TrxID`, `TxnID`, or `Transaction ID`

Sender number and date/time are optional for app notifications.

## Normal flow

1. User places order.
2. User pays through bKash.
3. SMS or app notification reaches the server.
4. User submits TrxID in the bot.
5. Bot verifies the saved notice and sends crypto automatically.

## Delayed notification flow

If the user submits TrxID before SMS/notification arrives:

1. Bot stores the order as pending.
2. When SMS or app notification later arrives, bot finds the pending order by TrxID.
3. Bot verifies amount.
4. Bot sends crypto automatically.
5. Bot updates TX log and removes the pending order.

## If neither SMS nor notification reaches the server

No software can verify the payment automatically without receiving any payment event. Use:

```text
/pending
```

Then verify the TrxID in your bKash app manually and tap Approve/Reject.

## Recommended Android setup

Use the custom app in `android-forwarder/` or any forwarder that supports both:

- SMS forwarding
- Notification forwarding / notification listener

For notifications, forward the app name/title/body text together. JSON is fine; the webhook searches all JSON values.

Example JSON POST:

```json
{
  "app": "bKash",
  "title": "Payment Received",
  "text": "You have received Tk 500. TrxID ABC123XYZ"
}
```

## Best long-term option

For full reliability, use official bKash Merchant/Payment Gateway API access. SMS/app notifications are still phone-dependent, but forwarding both gives you redundancy.
