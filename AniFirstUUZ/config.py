import os
from dotenv import load_dotenv

load_dotenv()

# Bot token
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Admin IDs (vergul bilan ajrating)
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "123456789").split(",")))

# Super admin
SUPER_ADMIN_ID = int(os.getenv("SUPER_ADMIN_ID", "123456789"))

# Database
DB_PATH = os.getenv("DB_PATH", "anime_bot.db")

# Kanal/Guruh ID lari (majburiy obuna uchun)
# Misol: -1001234567890
REQUIRED_CHANNELS = {
    "telegram": [],      # Telegram kanal ID lari
    "instagram": [],     # Instagram profil linki
    "youtube": [],       # YouTube kanal linki (max 2)
}

# Xabar matnlari
WELCOME_TEXT = """
🎌 <b>Anime Botga Xush Kelibsiz!</b>

Bu yerda siz eng yaxshi anime seriallarini tomosha qilishingiz mumkin.

📺 /anime - Barcha animalar ro'yxati
⚙️ /settings - Sozlamalar
"""

SUBSCRIPTION_REQUIRED_TEXT = """
⚠️ <b>Majburiy Obuna!</b>

Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:
"""
