from pathlib import Path
from urllib.parse import quote_plus
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
import os
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Use DATABASE_URL if set, else build from separate vars (password is URL-encoded for special chars)
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "123456")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    dbname = os.getenv("DB_NAME", "postgres")
    password_encoded = quote_plus(password)
    DATABASE_URL = f"postgresql+asyncpg://{user}:{password_encoded}@{host}:{port}/{dbname}"

engine = create_async_engine(DATABASE_URL)

async_session = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False
)

Base = declarative_base()


async def get_db():
    async with async_session() as session:
        yield session
