
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# --- SQLite Configuration (Original) ---
DATABASE_URL = "sqlite+aiosqlite:///C:/Users/ADMIN/Desktop/proj1/rate_limited_api/rate_limit.db"

# --- PostgreSQL Configuration (Example) ---
# You need a running Postgres server.
# URL format: postgresql+asyncpg://user:password@host:port/dbname
# Example generic URL (replace with your credentials):
# DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/rate_limited_api")

try:
    engine = create_async_engine(DATABASE_URL, echo=False)
except Exception:
    # Fallback to SQLite if Postgres not configured/fails (for demo safety)
    print("Postgres URL not working or set. Falling back to SQLite.")
    DATABASE_URL = "sqlite+aiosqlite:///C:/Users/ADMIN/Desktop/proj1/rate_limited_api/rate_limit.db"
    engine = create_async_engine(DATABASE_URL, echo=False)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
