from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram_dialog import DialogManager, StartMode
from db.controller.ORM import ORMController
from bot.utils.statesform import RegistrationForm, MainMenuSG  # Ваши состояния
from bot.lexicon.lexicon import LEXICON_RU  # Импорт текстовых сообщений

orm_controller = ORMController()
router = Router()

@router.message(CommandStart())
async def start_handler(message: Message, dialog_manager: DialogManager):
    # Получаем сессию базы данных
    async with dialog_manager.middleware_data['session'] as session:
        # Проверяем, зарегистрирован ли пользователь
        is_registered = await orm_controller.is_user_registered(session, message.from_user.id)

        if is_registered:
            # Если пользователь уже зарегистрирован, переводим его в главное меню
            await message.answer(LEXICON_RU['welcome_back'])
            await dialog_manager.start(MainMenuSG.MAIN_PANEL, mode=StartMode.RESET_STACK)
        else:
            # Если пользователь не зарегистрирован, запускаем диалог регистрации
            await message.answer(LEXICON_RU['welcome_new'])
            await dialog_manager.start(RegistrationForm.username, mode=StartMode.RESET_STACK)