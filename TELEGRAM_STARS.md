# Telegram Stars payments

The bot now supports Telegram Stars (`XTR`) as a separate automatic payment method.

## User flow

1. User taps `⭐ Telegram Stars`.
2. User selects network.
3. User sends wallet address.
4. User sends crypto amount.
5. Bot sends a Telegram Stars invoice.
6. Telegram sends a successful payment update after the user pays.
7. Bot verifies:
   - invoice payload/order ID
   - Telegram user ID
   - currency is `XTR`
   - exact Stars amount
8. Bot sends the requested crypto automatically.
9. Bot records the transaction and notifies admin.

## Configuration

Add this to `.env`:

```env
STAR_RATE=100
```

`STAR_RATE` means:

```text
1 USDC/USDT = 100 Telegram Stars
```

Optional per-network overrides:

```env
STAR_RATE_SOLANA=100
STAR_RATE_POLYGON=100
STAR_RATE_BSC=100
STAR_RATE_TRC20=100
```

## BotFather setup

Telegram Stars invoices use currency `XTR` and no normal payment provider token. Your bot must be allowed to accept Stars in Telegram/BotFather. If the invoice fails, check BotFather Stars/payment settings first.

## Duplicate protection

Every Stars invoice has a unique `order_id` payload stored in `star_orders`.

The bot rejects payment confirmation if:

- order does not exist
- order is not pending
- paying Telegram user is not the original user
- currency is not `XTR`
- Stars amount does not match the saved order

Completed/failed Stars payments are stored in `star_orders`, and completed transfers are also recorded in `transactions` using a transaction id like:

```text
STAR-<telegram_payment_charge_id>
```

## Failure case

If the user pays Stars but crypto sending fails, the bot marks the order as failed and notifies admin with the charge ID. You can then manually send crypto or refund through Telegram Stars tools if needed.
