# Nigerian local payment automation

This bot supports a button-driven Nigerian local payment flow for OPay, PalmPay, Moniepoint, and bank-transfer alerts. Nigeria payments are matched by reference/session/transaction ID and stored internally with an `NGN-` prefix so they do not collide with bKash TrxIDs.

## 1. Admin setup inside Telegram

Open the bot as admin:

1. Tap `🇳🇬 Nigeria Pay Setup` from the main menu.
2. Tap `🏦 Provider` and choose one:
   - `OPay`
   - `PalmPay`
   - `Moniepoint`
   - `Bank Transfer`
   - `Other` then type the provider/channel name.
3. Tap `📱 Account/Phone` and send the receiving account number, wallet number, or phone number users should pay.
4. Tap `👤 Holder Name` and send the account holder/receiver name.
5. Tap `🏛️ Bank/Wallet` and send the bank name or wallet name shown to users.
6. Tap `🔐 Optional Secret` if your forwarder can send a shared key/token. Send the token or tap `⏭️ Skip / Clear`. The bot masks saved secrets in the setup view.
7. Tap `💱 NGN Rates`, choose each crypto network, and send the NGN price for 1 unit of that network asset. Example: if 1 USDC costs ₦1,500, send `1500` for Solana/Polygon/Base USDC.
8. Tap `👁️ View Config` to review saved values. Secret/token is masked.
9. Tap `✅ Enable` when provider details and needed network rates are set.

Use `⛔ Disable` anytime to hide the Nigeria payment option from users. If a user selects Nigeria payment while it is disabled or missing a rate/account field, the bot shows a clear unavailable message and lets them go back/cancel or choose bKash.

## 2. User payment flow

1. User taps `Buy`.
2. User selects a crypto network.
3. User sends wallet address.
4. User enters fiat amount.
5. User confirms the order summary.
6. Bot shows payment method buttons:
   - `📲 bKash`
   - `🇳🇬 Nigerian Local Payment`
7. If Nigeria is selected, the bot displays provider, bank/wallet name, account holder, account/phone, exact NGN amount, and asks for Reference/Session/Transaction ID.
8. User pays in the provider/bank app and sends the reference/session/transaction ID.

The bot stores Nigerian IDs internally as `NGN-REFERENCE`. Users can type just the visible reference.

## 3. Android SMS/notification forwarder setup

Use an Android forwarder app that supports both:

- SMS forwarding
- Notification listener forwarding for app alerts
- HTTP POST with raw text or JSON body
- Optional custom headers/body fields if you want to send a shared secret/token
- Retry on network failure

Recommended endpoints:

```text
http://YOUR_SERVER:5000/ng-sms
http://YOUR_SERVER:5000/ng-notification
http://YOUR_SERVER:5000/nigeria-notification
```

Suggested setup steps:

1. Install a trusted SMS/notification forwarder on the phone that receives bank/wallet alerts.
2. Grant SMS permission if using SMS alerts.
3. Grant notification-listener permission if using OPay/PalmPay/Moniepoint app notifications.
4. Create an HTTP POST rule for SMS alerts and set URL to `http://YOUR_SERVER:5000/ng-sms`.
5. Create an HTTP POST rule for app notifications and set URL to `http://YOUR_SERVER:5000/ng-notification` or `http://YOUR_SERVER:5000/nigeria-notification`.
6. Include the full message text. For app notifications, include app name, title, and body.
7. Test with a small transfer and confirm the admin receives a Nigeria payment notice.
8. Keep the phone online, charged, and exempted from battery optimization.

## 4. JSON payload examples

Raw text POST is accepted. JSON is also accepted; the webhook searches all JSON values.

SMS example:

```json
{
  "from": "OPay",
  "body": "OPay: You received ₦1,500.00 from JOHN DOE. Ref: 240502ABC123 on 02/05/2026 12:30"
}
```

Notification example:

```json
{
  "app": "PalmPay",
  "title": "Credit Alert",
  "text": "NGN 2,000 received. Transaction ID PPY987654321. Sender: Musa Ade"
}
```

Bank-transfer example:

```json
{
  "app": "Bank App",
  "title": "Credit transaction",
  "message": "Your account has been credited with NGN 10,000.00 by Bank Transfer. Ref 123ABC789"
}
```

Optional secret example if your forwarder supports it:

```json
{
  "secret": "YOUR_SHARED_SECRET",
  "app": "Moniepoint",
  "text": "Transfer received N3,500 from CHIKA. Session ID 100004260502123456789012"
}
```

Do not paste real production secrets into documentation or support chats.

## 5. Supported alert text examples

OPay:

```text
OPay: You received ₦1,500.00 from JOHN DOE. Ref: 240502ABC123 on 02/05/2026 12:30
```

PalmPay:

```text
PalmPay Credit Alert NGN 2,000 received. Transaction ID PPY987654321. Sender: Musa Ade
```

Moniepoint:

```text
Moniepoint transfer received N3500 from CHIKA. Session ID 100004260502123456789012
```

Bank transfer:

```text
Your account has been credited with NGN 10,000.00 by Bank Transfer. Ref 123ABC789
```

The parser requires Nigerian currency/payment words plus a recognizable `Ref`, `Reference`, `Txn ID`, `Transaction ID`, `Session ID`, `Trx ID`, `Receipt No`, or `RRN`. It rejects crypto-looking hashes as payment references.

## 6. Matching, delayed notices, and manual fallback

Normal automatic flow:

1. Forwarder sends payment notice to the webhook.
2. Bot saves it as `NGN-REFERENCE` in `sms_log`.
3. User submits the same reference in the bot.
4. Bot checks exact NGN amount, stock, sends crypto, marks the notice used, records the transaction, and removes any pending order.

Delayed notice flow:

1. User submits reference before the forwarder alert arrives.
2. Bot stores the order as pending with `NGN-REFERENCE`.
3. When the notice later arrives, the bot matches the pending order by prefixed ID.
4. If the amount matches exactly, it sends crypto automatically.
5. If the amount differs, admin receives approve/reject buttons.

Manual fallback:

```text
/pending
```

The pending cards show whether each order is bKash or Nigerian local payment. For Nigeria, verify the reference/session ID in the provider or bank app, then tap `Approve` or `Reject`.

## 7. Security warnings

- Do not expose bot token, wallet keys, bank credentials, or webhook secret/token.
- Use HTTPS or a trusted private tunnel in production instead of plain HTTP.
- Restrict the webhook port with firewall rules where possible.
- Keep the Android forwarder phone locked and physically secure.
- Never approve a Nigerian payment manually unless the amount, reference/session ID, and receiver account match.
- SMS/app-notification forwarding is phone-dependent. Official provider/bank APIs are more reliable when available.
