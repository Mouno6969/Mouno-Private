# User seller / Stars withdrawal limits

Telegram Stars can be received by this bot, but the Bot API does not provide a normal method for this bot to transfer Stars to arbitrary Telegram users as withdrawable balances.

That means this exact idea is not fully possible:

```text
buyer pays Stars → bot receives Stars → bot automatically sends those Stars to another user on withdrawal
```

What is possible:

1. Users can connect their own wallet private keys and send their own crypto through `/send_wallet`.
2. Users can receive crypto from admin/bKash/Stars/gift-code flows.
3. The bot can keep an internal ledger saying user X earned N Stars.
4. Admin can manually settle that ledger outside the bot.
5. The bot can refund a specific Stars payment to the payer when supported, but that is not the same as paying another seller.

Recommended safe alternatives:

- Keep Stars selling only for the bot owner/admin.
- For user sellers, accept bKash/manual settlement and let admin pay them externally.
- If you need a marketplace, store seller earnings in DB and make admin approve/manual payout.

Do not promise automatic Stars withdrawal to users unless Telegram adds an official Bot API method for transferring Stars from a bot to arbitrary users.
