from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite+aiosqlite:///./test.db"  # для простоти

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()
