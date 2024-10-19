from db.entities.core import Base, Database
from db.entities.models import User, Player, FantasyTeam, Transfer, Match, PlayerStats, FantasyPoints
import logging

from sqlalchemy import inspect

logger = logging.getLogger(__name__)

# Декоратор для автоматического управления сессией
def session_manager(func):
    async def wrapper(self, session, *args, **kwargs):
        try:
            logger.debug(f"Starting session for {func.__name__}")
            result = await func(self, session, *args, **kwargs)
            await session.commit()
            logger.debug(f"Session for {func.__name__} committed successfully")
            return result
        except Exception as e:
            await session.rollback()
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            raise e
        finally:
            logger.debug(f"Session for {func.__name__} closed")
    return wrapper


class ORMController:
    def __init__(self, db: Database = Database()):
        self.db = db
        logger.info("ORMController initialized")

    async def create_tables(self):
        async with self.db.async_engine.begin() as conn:
            def sync_inspect(connection):
                inspector = inspect(connection)
                return inspector.get_table_names()

            # Получаем существующие таблицы
            existing_tables = await conn.run_sync(sync_inspect)

            # Создаем таблицы в правильном порядке
            tables_in_order = [
                Base.metadata.tables['players'],   # Сначала создаем таблицу players
                Base.metadata.tables['users'],     # Затем таблицу users
                Base.metadata.tables['fantasy_teams'],
                Base.metadata.tables['transfers'],
                Base.metadata.tables['matches'],
                Base.metadata.tables['player_stats'],
                Base.metadata.tables['fantasy_points']
            ]

            # Проходим по каждой таблице и создаем её, если она не существует
            for table in tables_in_order:
                if table.name not in existing_tables:
                    logger.info(f"Creating '{table.name}' table")
                    await conn.run_sync(Base.metadata.create_all, tables=[table])
                else:
                    logger.info(f"Table '{table.name}' already exists")

            logger.info("Tables checked and created if necessary")

    # Проверка, зарегистрирован ли пользователь (через ORM)
    @session_manager
    async def is_user_registered(self, session, tg_id: int):
        user = await session.get(User, tg_id)  # Получаем пользователя по его id через ORM
        return user is not None  # Возвращаем True, если пользователь найден

    # Добавление нового пользователя (ORM)
    @session_manager
    async def add_user(self, session, tg_id: int, username: str, team_name: str):
        user = User(id=tg_id, username=username, team_name=team_name)  # Создаем объект пользователя
        session.add(user)  # Добавляем его в сессию