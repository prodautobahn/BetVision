# backend/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# ── Ruta del proyecto ────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# ── Carga .env ───────────────────────────────────────────────────────────────
load_dotenv(dotenv_path=BASE_DIR / ".env")

# ── Settings ──────────────────────────────────────────────────────────────────
class Settings:
    # API keys
    api_football_key: str = os.getenv("API_FOOTBALL_KEY", "")
    sportmonks_key: str   = os.getenv("SPORTMONKS_KEY", "")

    # BD
    db_url: str = os.getenv("DB_URL", "sqlite:///./data.db")

    # Scheduler
    update_interval_minutes: int = int(os.getenv("UPDATE_INTERVAL_MINUTES", 5))

settings = Settings()
