import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SYMBOLS_FILE = DATA_DIR / "symbols.json"
INITIAL_SYMBOLS_FILE = DATA_DIR / "initial_symbols.json"

PORT = int(os.environ.get("PORT", 8000))
HOST = os.environ.get("HOST", "0.0.0.0")

# Fiyat güncelleme periyodu (saniye) - Kullanıcı isteği doğrultusunda 10 saniye
UPDATE_INTERVAL_SECONDS = int(os.environ.get("UPDATE_INTERVAL_SECONDS", 10))

# Güvenlik API Anahtarı (Şifre)
API_KEY = os.environ.get("API_KEY", "8505050Cc.Mm")

