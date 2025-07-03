import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
BUYER_ID = int(os.getenv("BUYER_ID", "0"))
DEFAULT_2FA_PASSWORD = os.getenv("DEFAULT_2FA_PASSWORD", "Bashir@111#")
DB_NAME = os.getenv("DB_NAME", "telegram_accounts.db")

# Validate required configuration
if not BOT_TOKEN or BOT_TOKEN == "TEST_TOKEN_REPLACE_WITH_ACTUAL":
    print("⚠️  WARNING: BOT_TOKEN not set. Please update .env file with actual values")
if not API_ID or API_ID == 0 or API_ID == 12345:
    print("⚠️  WARNING: API_ID not set. Please update .env file with actual values")
if not API_HASH or API_HASH == "test_api_hash_replace_with_actual":
    print("⚠️  WARNING: API_HASH not set. Please update .env file with actual values")
if not ADMIN_ID or ADMIN_ID == 0 or ADMIN_ID == 123456789:
    print("⚠️  WARNING: ADMIN_ID not set. Please update .env file with actual values")

# Operating hours (WAT timezone)
OPERATING_START_HOUR = 8  # 8 AM WAT
OPERATING_END_HOUR = 22   # 10 PM WAT

# Session directory
SESSION_DIR = "sessions"
os.makedirs(SESSION_DIR, exist_ok=True)
