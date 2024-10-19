from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from configurations import get_config
config = get_config()


class Database:
    async_engine: AsyncEngine = create_async_engine(url=config.db_config.get_database_url(), echo=True)
    async_session_factory: async_sessionmaker = async_sessionmaker(async_engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass