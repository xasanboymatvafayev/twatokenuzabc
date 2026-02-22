from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://casino:casino123@localhost/casino_db"
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    
    BOT_TOKEN: str = "YOUR_BOT_TOKEN_HERE"
    ADMIN_IDS: list = [123456789]  # Telegram admin IDs
    REQUIRED_CHANNEL: Optional[str] = None  # e.g. "@your_channel"
    
    HOUSE_EDGE: float = 0.05  # 5% house edge
    
    class Config:
        env_file = ".env"

settings = Settings()
