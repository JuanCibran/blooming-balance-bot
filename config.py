import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

TIENDANUBE_USER_ID = os.getenv("TIENDANUBE_USER_ID")
TIENDANUBE_ACCESS_TOKEN = os.getenv("TIENDANUBE_ACCESS_TOKEN")

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

# Opción A: path al JSON (uso local en tu Mac)
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Opción B: contenido del JSON como string (uso en Railway)
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")
