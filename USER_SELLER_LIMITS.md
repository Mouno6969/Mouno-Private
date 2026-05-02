# User seller / Stars withdrawal limits

Telegram Stars can be received by this bot, but the Bot API does not provide a normal method for this bot to transfer Stars to arbitrary Telegram users as withdrawable balances.

That means this exact idea is not fully possible:

```text
buyer pays Stars → bot receives Stars → bot automatically sends those Stars to another user on withdrawal
```

Implemented marketplace behavior:

1. Sellers apply in `🏪 Seller Center` and require admin approval.
2. Approved sellers can add encrypted delivery wallets for automated crypto delivery.
3. Buyers can buy from approved sellers with seller bKash or Telegram Stars.
4. Seller bKash notices route through seller-specific SMS tokens and can auto-complete matching orders.
5. Seller Stars sales create rows in `seller_star_ledger` with `pending_payout` status.
6. Admin manually settles seller Stars earnings outside Telegram and uses `/seller_payouts` to mark ledger entries `paid_out`.
7. The bot can refund a specific Stars payment to the payer when supported, but that is not the same as paying another seller.

Recommended safe alternatives:

- Keep seller Stars copy clear: payout is ledger/manual settlement only.
- Use `/seller_payouts` as the admin reconciliation queue.
- Keep seller bKash and crypto delivery wallet setup separate from the admin/global wallet flow.

Do not promise automatic Stars withdrawal to users unless Telegram adds an official Bot API method for transferring Stars from a bot to arbitrary users.
