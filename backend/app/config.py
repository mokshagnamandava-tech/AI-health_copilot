import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / "backend" / ".env")
APP_NAME = os.getenv("APP_NAME", "Wellnote Health Copilot")
DATABASE_PATH = os.getenv("DATABASE_PATH", str(ROOT / "backend" / "wellnote.db"))
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "12"))
ENABLE_GOOGLE_VISION = os.getenv("ENABLE_GOOGLE_VISION", "false").lower() == "true"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
CORS_ORIGINS = [x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if x.strip()]
CORS_ORIGINS = [
    x.strip()
    for x in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,https://wellnote-frontend.onrender.com"
    ).split(",")
    if x.strip()
]
