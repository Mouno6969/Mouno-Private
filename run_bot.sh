#!/usr/bin/env bash
set -euo pipefail
cd /home/ubuntu/mouno
echo "==== $(date -Is) starting mouno bot ====" >> /home/ubuntu/mouno/service.log
exec /home/ubuntu/mouno/.venv/bin/python /home/ubuntu/mouno/bot.py
