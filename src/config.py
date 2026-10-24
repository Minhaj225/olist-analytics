from pathlib import Path
import os

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def database_url():
    from sqlalchemy import URL

    password = os.getenv("POSTGRES_PASSWORD")
    if not password:
        raise ValueError("Set POSTGRES_PASSWORD in .env (copy .env.example and choose a password)")
    return URL.create(
        "postgresql+psycopg",
        username=os.getenv("POSTGRES_USER", "olist"),
        password=password,
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "olist"),
    )
