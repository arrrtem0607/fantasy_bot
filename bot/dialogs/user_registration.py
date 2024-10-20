from aiogram_dialog import Dialog, DialogManager, Window, StartMode, ShowMode
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const
from aiogram_dialog.widgets.input import TextInput, ManagedTextInput
from aiogram.types import Message

from bot.utils.statesform import RegistrationForm, MainMenuSG  # Добавим MainMenuSG для перевода в главное меню
from db.controller.ORM import ORMController
from bot.lexicon.lexicon import LEXICON_RU  # Импортируем текстовые сообщения

orm_controller = ORMController()

# Асинхронный обработчик успешного ввода имени
async def process_username_sync(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        input_value: str):
    dialog_manager.current_context().dialog_data.update(username=input_value)
    await dialog_manager.switch_to(RegistrationForm.team_name, show_mode=ShowMode.DELETE_AND_SEND)

# Асинхронный обработчик успешного ввода команды и завершение регистрации
async def process_team_name_sync(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        input_value: str):
    dialog_manager.current_context().dialog_data.update(team_name=input_value)
    dialog_manager.dialog_data.update(is_team_name_entered=True)

    # Выполняем регистрацию пользователя после ввода команды
    data = dialog_manager.current_context().dialog_data
    username = data['username']
    team_name = data['team_name']
    user_id = message.from_user.id

    async with dialog_manager.middleware_data['session'] as session:
        await orm_controller.add_user(session, tg_id=user_id, username=username, team_name=team_name)

    # await message.answer(LEXICON_RU['registration_complete'].format(username=username, team_name=team_name))

    # Переводим пользователя в главное меню
    await dialog_manager.start(MainMenuSG.MAIN_PANEL,
                               mode=StartMode.RESET_STACK,
                               show_mode=ShowMode.DELETE_AND_SEND)

# Обработчик ошибок
async def handle_error_sync(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        error: ValueError):
    await message.answer(LEXICON_RU['input_error'])

# Диалог
register_dialog = Dialog(
    Window(
        Const(LEXICON_RU['welcome_new']),
        Button(text=Const(LEXICON_RU['welcome_new_button']),
               id="go_to_username_input",
               on_click=lambda c, b, d: d.switch_to(RegistrationForm.username)  # Переключаем на ввод имени
               ),
        state=RegistrationForm.welcome  # Текущее состояние
    ),
    Window(
        Const(LEXICON_RU['enter_username']),
        TextInput(id="username",
                  on_success=process_username_sync,
                  on_error=handle_error_sync),
        state=RegistrationForm.username
    ),
    Window(
        Const(LEXICON_RU['enter_team_name']),
        TextInput(id="team_name",
                  on_success=process_team_name_sync,
                  on_error=handle_error_sync),
        state=RegistrationForm.team_name
    )
)
