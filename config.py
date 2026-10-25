import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env si existe.
if os.path.exists(".env"):
    load_dotenv(".env")

class Config:
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    PORT: int = int(os.getenv("PORT", 8000))
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./assistant.db")
    WEBAPP_URL: str = os.getenv("WEBAPP_URL", f"http://localhost:{PORT}")

config = Config()
