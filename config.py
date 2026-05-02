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
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")
HF_API_KEY = os.getenv("HF_API_KEY")
HF_MODEL = os.getenv("HF_MODEL", "mistralai/Mistral-7B-Instruct-v0.3")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
TOGETHER_MODEL = os.getenv("TOGETHER_MODEL", "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "open-mistral-7b")
SOLANA_KEY = os.getenv("SOLANA_KEY")
RATE = float(os.getenv("RATE", "137"))
STAR_RATE = float(os.getenv("STAR_RATE", "100"))
SELLER_WALLET_MASTER_KEY = os.getenv("SELLER_WALLET_MASTER_KEY")

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
