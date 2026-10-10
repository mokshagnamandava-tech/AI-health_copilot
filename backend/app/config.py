import os
from pathlib import Path

APP_NAME = "WellNote"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))

# Use the existing database in the backend folder
DATABASE_PATH = Path(
    os.getenv(
        "DATABASE_PATH",
        str(Path(__file__).resolve().parent.parent / "wellnote.db"),
    )
)

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,https://wellnote-frontend.onrender.com",
    ).split(",")
    if origin.strip()
]
