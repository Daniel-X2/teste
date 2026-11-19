from pathlib import Path

from dotenv import load_dotenv
import os

# Carrega o .env da raiz do projeto independente de onde o uvicorn foi chamado.
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ENV_PATH)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/api_db",
)
CRON_EXPRESSION = os.getenv("CRON_EXPRESSION", "0 * * * *")
