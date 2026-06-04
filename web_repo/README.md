# BGC Crypto Website

A modern, attractive, and user-friendly website for BGC Crypto services, built with React, Tailwind CSS, and Python (Flask).

## Features

- **Live Market Rates**: Real-time conversion rates for major crypto networks.
- **Buy Crypto**: Seamless bKash payment integration for purchasing USDC/USDT.
- **Swap & Bridge**: Cross-chain asset exchange powered by LI.FI.
- **Personal Wallet**: Secure, client-side private key storage for in-bot transactions.
- **Order History**: Track your current and past transactions.
- **Multilingual Support**: Fully bilingual in Bengali and English.
- **Telegram Sync**: Optionally link your web account with your Telegram bot profile.

## Tech Stack

- **Frontend**: React, TypeScript, Tailwind CSS, Framer Motion, i18next.
- **Backend**: Python (Flask), JWT Authentication, SQLite (shares data with the bot).

## Installation & Setup

1. **Prerequisites**:
   - Node.js (v18+)
   - Python 3.12+

2. **Frontend Build**:
   ```bash
   cd frontend
   npm install
   npm run build
   ```

3. **Backend Setup**:
   ```bash
   cd api
   pip install -r requirements.txt
   ```

4. **Configuration**:
   Ensure your `.env` file in the root directory (bot directory) contains:
   ```env
   WEB_SECRET_KEY=your_secret_key_here
   ```

5. **Run**:
   ```bash
   cd api
   PYTHONPATH=../../ python3 main.py
   ```
   The website will be available at `http://localhost:5001`.

## Security

Private keys are stored **only** in the user's browser (Local Storage) and are never sent to the server. The API uses JWT tokens for secure authentication.
