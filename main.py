import os
import logging
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder, Redis
from aiogram_dialog import setup_dialogs

from configurations import get_config
# from db.controller.ORM import ORMController
# from bot import get_all_routers  # Добавьте реализацию всех маршрутизаторов бота
# from bot.middlewares.db_middleware import initialize_database  # Импортируем функцию для инициализации базы данных

# Логирование
current_directory = os.path.dirname(os.path.abspath(__file__))
log_file_path = os.path.join(current_directory, 'application.log')

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - [%(levelname)s] - %(name)s - "
                           "(%(filename)s).%(funcName)s(%(lineno)d) - %(message)s",
                    filename=log_file_path)

# orm_controller = ORMController()


async def run_bot():
    config = get_config()  # Чтение конфигурации из файла

    # Инициализируем Redis и хранилище для FSM
    redis = Redis(host='localhost')  # Настроить Redis при необходимости
    key_builder = DefaultKeyBuilder(with_destiny=True)
    storage = RedisStorage(redis=redis, key_builder=key_builder)

    # Настройки бота
    default = DefaultBotProperties(parse_mode="HTML")
    bot = Bot(token=config.bot_config.get_token(), default=default)
    dp = Dispatcher(storage=storage)

    # Включение маршрутизаторов
    # dp.include_router(await get_all_routers())

    # Настройка диалогов
    setup_dialogs(dp)

    # Инициализация базы данных
    # await initialize_database()  # Инициализация БД

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(run_bot())