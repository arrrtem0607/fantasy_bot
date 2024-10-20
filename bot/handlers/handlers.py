from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from aiogram_dialog import DialogManager, StartMode
from db.entities.core import Base
from db.controller.ORM import ORMController
from bot.utils.statesform import RegistrationForm, MainMenuSG
from bot.lexicon.lexicon import LEXICON_RU

orm_controller = ORMController()
router = Router()

@router.message(CommandStart())
async def start_handler(message: Message, dialog_manager: DialogManager):
    async with dialog_manager.middleware_data['session'] as session:
        is_registered = await orm_controller.is_user_registered(session, message.from_user.id)

        if is_registered:
            await message.answer(LEXICON_RU['welcome_back'])
            await dialog_manager.start(MainMenuSG.MAIN_PANEL, mode=StartMode.RESET_STACK)
        else:
            await message.answer(LEXICON_RU['welcome_new'])
            await dialog_manager.start(RegistrationForm.username, mode=StartMode.RESET_STACK)

# Хендлер для команды /cancel
@router.message(Command(commands=["clear"]))
async def cancel_handler(message: Message):
    async with orm_controller.db.async_engine.begin() as conn:
        # Удаление всех таблиц
        await conn.run_sync(Base.metadata.drop_all)

    await message.answer("Все таблицы удалены.")