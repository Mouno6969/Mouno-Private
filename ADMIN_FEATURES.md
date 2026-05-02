# Admin and safety features

## Admin dashboard commands

```text
/stats
```

Shows total transactions, completed/failed counts, pending bKash count, retry queue count, completed BDT total, completed crypto total, and maintenance mode status.

```text
/balances
```

Shows admin wallet balances across supported networks.

## Order IDs

New transactions and pending bKash orders receive an internal order ID like:

```text
ORD-ABC123
```

TX log displays the order ID when available.

## Failed-send recovery

```text
/failed
```

Shows failed crypto sends with a `Retry Send` button. Retry uses the saved network, wallet, and crypto amount.

## Maintenance mode

Commands:

```text
/maintenance
/maintenance on
/maintenance off
```

Admin also has main-menu buttons:

```text
🛑 Maintenance ON
✅ Maintenance OFF
```

When maintenance is ON, normal users cannot start buy, Stars buy, or gift-code redeem flows. Admin can still use tools.

## Backup command

```text
/backup
```

Admin-only. Sends the current `mouno.db` database file to admin in Telegram.

## Terms and support

- Main menu includes `📞 Support` button.
- Main menu includes `📜 Terms` button.
- `/terms` sends risk warnings.

Set support username in `.env`:

```env
SUPPORT_USERNAME=MdMouno
```

## Gas/native token warning

Order summary screens now warn users/admin that native gas tokens are required for network sends, for example SOL/TRX/BNB/ETH/MATIC/AVAX depending on network.
