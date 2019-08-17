import os

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
STEAM_API_TOKEN = os.getenv('STEAM_API_TOKEN')
BOT_ADMIN = os.getenv('BOT_ADMIN')
CACHE_SHORT_QUERY = os.getenv('CACHE_SHORT_QUERY', 300)
CACHE_USER_NOT_FOUND = os.getenv('CACHE_USER_NOT_FOUND', 300)
CACHE_USER_FOUND = os.getenv('CACHE_USER_FOUND', 300)
CACHE_DB = os.getenv('CACHE_DB', 3600)
LOG_CHANNEL = os.getenv('LOG_CHANNEL')
