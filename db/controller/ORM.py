from db.entities.core import Base, Database
from db.entities.models import User, Player, FantasyTeam, Transfer, Match, PlayerStats, FantasyPoints
from sqlalchemy import delete, update, select
from sqlalchemy.orm import joinedload

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

            tables_in_order = [
                Base.metadata.tables['players'],
                Base.metadata.tables['users'],
                Base.metadata.tables['fantasy_teams'],
                Base.metadata.tables['transfers'],
                Base.metadata.tables['matches'],
                Base.metadata.tables['player_stats'],
                Base.metadata.tables['fantasy_points']
            ]

            for table in tables_in_order:
                if table.name not in existing_tables:
                    logger.info(f"Creating '{table.name}' table")
                    await conn.run_sync(Base.metadata.create_all, tables=[table])
                else:
                    logger.info(f"Table '{table.name}' already exists")

    # Добавление функции очистки всех таблиц
    async def clear_tables(self):
        async with self.db.async_engine.begin() as conn:
            logger.info("Clearing all tables")
            for table in reversed(Base.metadata.sorted_tables):
                await conn.execute(delete(table))  # Используем SQLAlchemy delete для каждой таблицы
            logger.info("All tables have been cleared")

    @session_manager
    async def is_user_registered(self, session, tg_id: int):
        user = await session.get(User, tg_id)
        return user is not None

    @session_manager
    async def add_user(self, session, tg_id: int, username: str, team_name: str):
        user = User(id=tg_id, username=username, team_name=team_name)
        session.add(user)

        # Обновление имени пользователя

    @session_manager
    async def update_username(self, session, user_id: int, new_username: str):
        await session.execute(
            update(User).where(User.id == user_id).values(username=new_username)
        )
        logger.info(f"User {user_id} updated their username to {new_username}")

    # Обновление названия команды
    @session_manager
    async def update_team_name(self, session, user_id: int, new_team_name: str):
        await session.execute(
            update(User).where(User.id == user_id).values(team_name=new_team_name)
        )
        logger.info(f"User {user_id} updated their team name to {new_team_name}")

    @session_manager
    async def get_field_players(self, session):
        # Создаем запрос для выборки всех активных полевых игроков
        result = await session.execute(
            select(Player).where(Player.is_active == True, Player.position != 'goalkeeper')
        )
        field_players = result.scalars().all()
        return field_players

    @session_manager
    async def get_goalkeepers(self, session):
        # Создаем запрос для выборки всех активных вратарей
        result = await session.execute(
            select(Player).where(Player.is_active == True, Player.position == 'goalkeeper')
        )
        goalkeepers = result.scalars().all()
        return goalkeepers

    # ORM метод для добавления команды пользователя
    @session_manager
    async def add_fantasy_team(self, session, user_id: int, player_id: int, is_captain: bool):
        new_fantasy_team = FantasyTeam(
            user_id=user_id,
            player_id=player_id,
            is_captain=is_captain)
        session.add(new_fantasy_team)
        await session.commit()

    @session_manager
    async def get_players_by_ids(self, session, player_ids: list):
        # Преобразуем идентификаторы игроков в целые числа
        player_ids = [int(player_id) for player_id in player_ids]

        # Создаем запрос для выборки игроков по их идентификаторам
        result = await session.execute(
            select(Player).where(Player.id.in_(player_ids))
        )

        # Получаем список игроков как объекты Player
        players = result.scalars().all()

        # Возвращаем объекты Player без преобразования в словари
        return players

    @session_manager
    async def get_field_players_by_team(self, session, course: str):
        """
        Получение активных полевых игроков по курсу
        :param session: текущая сессия
        :param course: строка, обозначающая курс (например, '1 курс')
        :return: список игроков для указанного курса
        """
        logger.info(f"Запрос полевых игроков для курса: {course}")
        result = await session.execute(
            select(Player)
            .where(Player.team == course)  # Фильтр по курсу
            .where(Player.position != 'goalkeeper')  # Исключаем вратарей
            .where(Player.is_active == True)  # Только активные игроки
        )
        field_players = result.scalars().all()
        logger.info(f"Найдено {len(field_players)} игроков для курса {course}")
        return field_players

    @session_manager
    async def get_all_teams(self, session):
        # Получаем все уникальные названия команд (курсов)
        result = await session.execute(
            select(Player.team).distinct().where(Player.is_active == True)
        )
        teams = [row[0] for row in result.fetchall()]
        return teams

    @session_manager
    async def user_has_team(self, session, user_id: int) -> bool:
        # Запрашиваем наличие команды у пользователя
        result = await session.execute(select(FantasyTeam).where(FantasyTeam.user_id == user_id))
        return result.scalars().first() is not None

    @session_manager
    async def get_team_by_user_id(self, session, user_id: int):
        # Получаем объект пользователя вместе с его командой (связь через `FantasyTeam`)
        result = await session.execute(
            select(User)
            .options(joinedload(User.fantasy_teams))  # Загружаем связанные объекты FantasyTeam
            .where(User.id == user_id)
        )

        # Используем метод unique() для обработки связей с коллекциями
        user = result.unique().scalar_one_or_none()

        return user  # Возвращаем объект User
