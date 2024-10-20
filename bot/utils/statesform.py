from aiogram.fsm.state import State, StatesGroup

# Состояния для регистрации пользователя
class RegistrationForm(StatesGroup):
    welcome = State()
    username = State()  # Ввод имени пользователя
    team_name = State()  # Ввод названия команды

# Состояния для основного меню
class MainMenuSG(StatesGroup):
    MAIN_PANEL = State()  # Главное меню пользователя
    VIEW_TEAM = State()
    NO_TEAM = State()

class TeamSelectionSG(StatesGroup):
    INSTRUCTION = State()
    GOALKEEPER = State()
    FIELD_PLAYERS = State()
    CONFIRMATION = State()
    CAPTAIN_SELECTION = State()