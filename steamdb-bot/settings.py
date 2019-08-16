import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
STEAM_API_TOKEN = os.getenv('STEAM_API_TOKEN')
BOT_ADMIN = os.getenv('BOT_ADMIN')
