from aiogram import Router
from aiogram_dialog import setup_dialogs

from bot.middlewares.db_middleware import DbSessionMiddleware
from bot.handlers.handlers import router as start_router
from bot.dialogs.user_registration import register_dialog
from bot.dialogs.main_menu import main_menu_dialog  # Импорт диалога главного меню
from db.entities.core import Database

async def get_all_routers() -> Router:
    # Создаем экземпляр базы данных и middleware для сессии
    db = Database()
    db_session_middleware = DbSessionMiddleware(db.async_session_factory)

    # Подключаем middleware для обработки сессий
    start_router.message.middleware(db_session_middleware)
    start_router.callback_query.middleware(db_session_middleware)

    register_dialog.message.middleware(db_session_middleware)
    register_dialog.callback_query.middleware(db_session_middleware)

    main_menu_dialog.message.middleware(db_session_middleware)  # Добавляем миддлварь для главного меню
    main_menu_dialog.callback_query.middleware(db_session_middleware)

    # Создаем основной маршрутизатор
    router = Router()

    # Включаем хендлеры и диалоги в маршрутизатор
    router.include_router(start_router)
    router.include_router(register_dialog)
    router.include_router(main_menu_dialog)  # Подключаем главный диалог

    # Настройка диалогов
    setup_dialogs(router)

    return router