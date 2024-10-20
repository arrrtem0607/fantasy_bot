from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, Window, StartMode, DialogManager
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const, Format
from bot.utils.statesform import MainMenuSG, TeamSelectionSG
from bot.lexicon.lexicon import LEXICON_RU  # Тексты
from db.controller.ORM import ORMController

orm_controller = ORMController()

# Функция для проверки наличия команды и запуска процесса выбора команды
async def start_team_selection(
        callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager):
    user_id = callback.from_user.id

    # Проверяем через ORMController, есть ли у пользователя команда
    session = dialog_manager.middleware_data['session']
    user = await orm_controller.get_team_by_user_id(session, user_id)

    if user and user.fantasy_teams:
        # Если команда уже существует, загружаем информацию о команде
        fantasy_team = user.fantasy_teams  # Это список объектов FantasyTeam
        dialog_manager.dialog_data['team_info'] = [ft.player_id for ft in fantasy_team]

        # Переходим сразу к экрану подтверждения
        await dialog_manager.switch_to(MainMenuSG.VIEW_TEAM)
    else:
        # Если команды нет, переходим к выбору команды
        await dialog_manager.switch_to(MainMenuSG.NO_TEAM)

# Геттер данных для проверки, выбрал ли пользователь команду
async def has_selected_team(
        dialog_manager: DialogManager,
        **kwargs):
    user_id = dialog_manager.event.from_user.id  # Получаем user_id пользователя
    session = dialog_manager.middleware_data['session']  # Сессия с БД

    # Используем уже существующую функцию для получения пользователя и команды
    user = await orm_controller.get_team_by_user_id(session, user_id)

    # Если пользователь существует и у него есть хотя бы один игрок в команде
    return {"has_team": bool(user and user.fantasy_teams)}

# Геттер данных для информации о команде
async def get_team_or_message(dialog_manager: DialogManager, **kwargs):
    user_id = dialog_manager.event.from_user.id
    session = dialog_manager.middleware_data['session']

    # Проверяем наличие команды
    user = await orm_controller.get_team_by_user_id(session, user_id)
    if not user or not user.fantasy_teams:
        # Если у пользователя нет команды, переключаем на состояние без команды
        await dialog_manager.switch_to(MainMenuSG.NO_TEAM)
        return {}  # Возвращаем пустой словарь, так как команды нет

    # Если команда есть, выводим информацию о ней
    team_name = user.team_name
    fantasy_team = user.fantasy_teams  # Это список объектов FantasyTeam
    team_info = [ft.player_id for ft in fantasy_team]

    # Получаем информацию об игроках
    players_data = await orm_controller.get_players_by_ids(session, team_info)
    players_list = "\n".join([f"{player.name} ({player.team})" for player in players_data])

    # Возвращаем информацию о команде в шаблон
    return {"team_name": team_name, "team_info": players_list}

team_info_window = Window(
    Format(LEXICON_RU['team_info']),
    Button(Const(LEXICON_RU['return_main_menu']),
           id="return_main_menu",
           on_click=lambda c, b, d: d.start(MainMenuSG.MAIN_PANEL)),  # Возврат в главное меню
    state=MainMenuSG.VIEW_TEAM,
    getter=get_team_or_message
)

# Окно, которое оповещает пользователя, что команда не выбрана
no_team_window = Window(
    Const("Вы еще не выбрали свою команду.\n\n"
          "Для создания команды нажмите на кнопку ниже."),
    Button(Const(LEXICON_RU['create_team']),
           id="create_team",
           on_click=lambda c, b, d: d.start(TeamSelectionSG.INSTRUCTION, mode=StartMode.RESET_STACK)),  # Переход к созданию команды
    Button(Const(LEXICON_RU['return_main_menu']),
           id="return_main_menu",
           on_click=lambda c, b, d: d.start(MainMenuSG.MAIN_PANEL)),  # Возврат в главное меню
    state=MainMenuSG.NO_TEAM  # Состояние для окна, если команды нет
)

# Обновленный диалог с двумя окнами (если команда есть и если команды нет)
main_menu_dialog = Dialog(
    Window(
        Const(LEXICON_RU['main_menu_welcome']),
        Button(Const(LEXICON_RU['view_team']),
               id="view_team",
               on_click=start_team_selection),
        Button(Const(LEXICON_RU['select_team']),
               id="select_team",
               on_click=lambda c, b, d: d.start(TeamSelectionSG.INSTRUCTION, mode=StartMode.RESET_STACK),
               when=lambda data, widget, manager: not data.get("has_team")),  # Используем данные геттера
        Button(Const(LEXICON_RU['transfers']), id="transfers", on_click=lambda c, b, d: d.switch_to(MainMenuSG.TRANSFERS)),
        Button(Const(LEXICON_RU['view_stats']), id="view_stats", on_click=lambda c, b, d: d.switch_to(MainMenuSG.VIEW_STATS)),
        Button(Const(LEXICON_RU['change_username']), id="change_username", on_click=lambda c, b, d: d.switch_to(MainMenuSG.CHANGE_USERNAME)),
        Button(Const(LEXICON_RU['change_team_name']), id="change_team_name", on_click=lambda c, b, d: d.switch_to(MainMenuSG.CHANGE_TEAM_NAME)),
        state=MainMenuSG.MAIN_PANEL,
        getter=has_selected_team  # Здесь подключаем геттер
    ),
    team_info_window,  # Окно с командой, если команда есть
    no_team_window  # Окно, если команды нет
)