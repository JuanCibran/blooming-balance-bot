import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

BIGQUERY_PROJECT_ID = os.getenv("BIGQUERY_PROJECT_ID")
BIGQUERY_DATASET_ID = os.getenv("BIGQUERY_DATASET_ID", "blooming_essie")

# En Railway las credenciales van como JSON string en una env var
# En local apunta al path del archivo JSON
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")
