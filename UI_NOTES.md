# UI refresh notes

The main customer-facing bot screens were restyled for a cleaner Telegram interface:

- Home screen with polished panel header
- Cleaner rate table with network icons
- Improved live balance screen
- Improved TX log cards with source labels, order IDs, short wallets, and TrxID
- Improved buy network prompt
- Improved wallet saved screen
- Improved order summary screen
- Improved help center screen
- Improved wallet panel screen

Restart the bot after updating code:

```bash
cd ~/mouno
python3 -m compileall -q .
sudo systemctl restart mouno
```
