import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
BKASH_NUMBER = os.getenv("BKASH_NUMBER")
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "MdMouno")
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
