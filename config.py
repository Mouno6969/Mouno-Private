import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
BKASH_NUMBER = os.getenv("BKASH_NUMBER")
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "MdMouno")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
SOLANA_KEY = os.getenv("SOLANA_KEY")
RATE = float(os.getenv("RATE", "137"))
STAR_RATE = float(os.getenv("STAR_RATE", "100"))

POLYGON_RPC = os.getenv("POLYGON_RPC")
POLYGON_PRIVATE_KEY = os.getenv("POLYGON_PRIVATE_KEY")
BSC_RPC = os.getenv("BSC_RPC", "https://bsc-dataseed.binance.org/")
BSC_PRIVATE_KEY = os.getenv("BSC_PRIVATE_KEY")
AVALANCHE_RPC = os.getenv("AVALANCHE_RPC", "https://api.avax.network/ext/bc/C/rpc")
ETHEREUM_RPC = os.getenv("ETHEREUM_RPC")
BASE_RPC = os.getenv("BASE_RPC", "https://mainnet.base.org")
TRON_PRIVATE_KEY = os.getenv("TRON_PRIVATE_KEY")
TON_MNEMONIC = os.getenv("TON_MNEMONIC")
TON_API_KEY = os.getenv("TON_API_KEY")
TON_RPC = os.getenv("TON_RPC", "https://toncenter.com")
LOW_BALANCE_THRESHOLD = float(os.getenv("LOW_BALANCE_THRESHOLD", "1.0"))
WEBHOOK_STALE_MINUTES = int(os.getenv("WEBHOOK_STALE_MINUTES", "30"))
DASHBOARD_TOKEN = os.getenv("DASHBOARD_TOKEN") or os.getenv("ADMIN_WEB_TOKEN")
BACKUP_UPLOAD_URL = os.getenv("BACKUP_UPLOAD_URL")
