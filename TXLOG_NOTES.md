# TX log notes

The TX log now records every successful crypto send path:

- bKash auto/manual completed orders
- delayed bKash auto-completed pending orders
- Telegram Stars completed orders
- gift code redemptions
- admin `/send` transfers
- user wallet `/send_wallet` transfers

Use either:

```text
/start → TX Log button
```

or:

```text
/txlog
```

Runtime note: if the bot is already running, code changes only take effect after restart.

Safe restart command:

```bash
cd ~/mouno && python3 -m compileall -q . && sudo systemctl restart mouno
```

If using screen/tmux, stop and start `python3 bot.py` again.
