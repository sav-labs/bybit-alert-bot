import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Bot settings
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_ADMINS = list(map(int, os.getenv("BOT_ADMINS", "").split(",")))

# Bybit API settings
POLLING_INTERVAL = int(os.getenv("POLLING_INTERVAL", 60))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = Path("logs/bot.log")

# Database
DATABASE_URL = f"sqlite:///{Path('data/database.sqlite3')}"

# Price alert settings
DEFAULT_PRICE_THRESHOLDS = {
    "BTC": 1000,  # $1000
    "ETH": 100,   # $100
    "SOL": 10,    # $10
    "XRP": 0.1,   # $0.1
    "DOGE": 0.01  # $0.01
}

# Default available price multipliers
AVAILABLE_PRICE_MULTIPLIERS = [0.001, 0.01, 0.1, 0.2, 0.5, 1, 10, 100, 1000, 10000] 