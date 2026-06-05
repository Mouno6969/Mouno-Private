#!/bin/bash

echo "🚀 Starting BGC Crypto Website Setup..."

# 1. Install dependencies
echo "📦 Installing dependencies..."
pip install -r web_repo/api/requirements.txt

# 2. Check for .env and WEB_SECRET_KEY
if [ ! -f .env ]; then
    echo "⚠️ .env file not found! Creating a basic one..."
    touch .env
fi

if ! grep -q "WEB_SECRET_KEY" .env; then
    echo "🔑 Generating WEB_SECRET_KEY..."
    echo "WEB_SECRET_KEY=d8a010fc402981020c3fc714aba69297cb83de6c59c884309d92a08f1f4effc5" >> .env
fi

# 3. Navigate and run
echo "🌐 Starting server on port 5001..."
cd web_repo/api
export PYTHONPATH=$PYTHONPATH:/app/../../
python3 main.py
