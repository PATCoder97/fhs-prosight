from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Get DATABASE_URL using the helper method
# This supports both direct DATABASE_URL or auto-constructed from POSTGRES_* vars
engine = create_async_engine(
    settings.get_database_url(),
    echo=False,
    future=True,
)

# Async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    async with AsyncSessionLocal() as db:
        yield db
