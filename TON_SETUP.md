# TON setup

The bot supports native TON transfers on the TON network.

## Environment variables

Add these to `.env`:

```env
TON_MNEMONIC=word1 word2 word3 ... word24
TON_API_KEY=
TON_RPC=https://toncenter.com
```

`TON_MNEMONIC` is the wallet seed phrase used for sending TON. Keep it private.

`TON_API_KEY` is optional but recommended because Toncenter rate-limits public requests.

## What is supported

- Native TON balance check
- Native TON send
- TON buy flow
- Telegram Stars flow for TON
- Gift code TON payout
- Admin Send for TON

## Address format

Users should submit a TON address that starts with:

```text
UQ...
```

or:

```text
EQ...
```

## Important

This is native TON, not TON USDT Jetton. Jetton support needs a separate smart-contract payload flow.
