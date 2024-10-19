from aiogram.fsm.state import State, StatesGroup

# Состояния для регистрации пользователя
class RegistrationForm(StatesGroup):
    username = State()  # Ввод имени пользователя
    team_name = State()  # Ввод названия команды

# Состояния для основного меню
class MainMenuSG(StatesGroup):
    MAIN_PANEL = State()  # Главное меню пользователя