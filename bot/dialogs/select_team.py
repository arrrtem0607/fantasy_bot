import operator
import logging

from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Button, Column, Multiselect, Select, Row, Group
from aiogram_dialog.widgets.text import Const, Format

from bot.utils.statesform import TeamSelectionSG, MainMenuSG
from bot.lexicon.lexicon import LEXICON_RU
from db.controller.ORM import ORMController
from bot.utils.validators import validate_team

# Логирование
logger = logging.getLogger(__name__)

# ORMController для работы с БД
orm_controller = ORMController()

# Геттер данных для списка вратарей
async def get_goalkeepers(
        dialog_manager: DialogManager,
        **kwargs):
    logger.info("Получение данных о вратарях")
    async with dialog_manager.middleware_data['session'] as session:
        goalkeepers = await orm_controller.get_goalkeepers(session)
        if not goalkeepers:
            logger.warning("Список вратарей пуст!")
            return {"goalkeepers": []}

    selected_goalkeeper = dialog_manager.dialog_data.get("goalkeeper")
    logger.info(f"Найдено вратарей: {len(goalkeepers)}")

    # Формируем список с символом мячика для выбранного вратаря
    goalkeepers_list = [
        (f"⚽️ {g.name} ({g.team}) ({g.price} баллов)" if str(g.id) == selected_goalkeeper
         else f"{g.name} ({g.team}) ({g.price} баллов)", str(g.id))
        for g in goalkeepers
    ]

    logger.info(f"Список вратарей для Select: {goalkeepers_list}")
    return {"goalkeepers": goalkeepers_list}

# Обработчик выбора вратаря
async def on_goalkeeper_selected(
        callback: CallbackQuery,
        button: Select,
        dialog_manager: DialogManager,
        item_id: str):
    dialog_manager.dialog_data["goalkeeper"] = item_id
    logger.info(f"Выбран вратарь с ID: {item_id}")

    await callback.answer(LEXICON_RU['goalkeeper_selected'])

# Обработчик изменения состояния выбора игроков
async def on_players_state_changed(
        event: CallbackQuery,
        widget: Multiselect,
        dialog_manager: DialogManager,
        item_id: str):
    selected_players = dialog_manager.dialog_data.get('selected_players', [])

    if item_id in selected_players:
        selected_players.remove(item_id)
    else:
        selected_players.append(item_id)

    dialog_manager.dialog_data['selected_players'] = selected_players
    logger.info(f"Обновленный список выбранных игроков: {selected_players}")

    await event.answer()  # Ответ пользователю для подтверждения

# Геттер данных для списка полевых игроков по командам
async def get_players_by_team(
        dialog_manager: DialogManager,
        **kwargs):
    logger.info("Получение данных о полевых игроках по командам")
    current_team_idx = dialog_manager.dialog_data.get('current_team_idx', 0)
    teams = dialog_manager.dialog_data.get('teams', [])

    if not teams:
        async with dialog_manager.middleware_data['session'] as session:
            teams = await orm_controller.get_all_teams(session)
            teams.sort()
            dialog_manager.dialog_data['teams'] = teams

    current_team = teams[current_team_idx] if teams else None
    if not current_team:
        return {"players": [], "current_team_idx": current_team_idx, "teams": teams}

    async with dialog_manager.middleware_data['session'] as session:
        players = await orm_controller.get_field_players_by_team(session, current_team)
        if not players:
            logger.warning("Список полевых игроков пуст!")
            return {"players": [], "current_team_idx": current_team_idx, "teams": teams}

    # Формируем список игроков
    players_data = [(f"{player.name} ({player.team}) ({player.price} баллов)", str(player.id), player.price) for player
                    in players]

    # Получаем ID выбранных игроков
    selected_player_ids = dialog_manager.dialog_data.get('selected_players', [])

    # Если выбраны игроки, запрашиваем их объекты по ID
    selected_players = []
    if selected_player_ids:
        selected_players = await orm_controller.get_players_by_ids(session, selected_player_ids)

    # Подсчитываем сумму стоимости выбранных игроков
    selected_players_price = sum(player.price for player in selected_players)

    # Проверяем, был ли выбран вратарь
    selected_goalkeeper_id = dialog_manager.dialog_data.get("goalkeeper")
    goalkeeper_price = 0
    if selected_goalkeeper_id:
        goalkeeper = await orm_controller.get_players_by_ids(session, [selected_goalkeeper_id])
        goalkeeper_price = goalkeeper[0].price if goalkeeper else 0

    # Всего должно быть 7 игроков (1 вратарь и 6 полевых)
    total_players = 7
    remaining_players = total_players - (len(selected_players) + (1 if selected_goalkeeper_id else 0))

    # Логируем и возвращаем данные для окна
    logger.info(
        f"Список полевых игроков (Команда: {current_team}), выбрано игроков: {len(selected_players)}, остаток баллов: {46 - (selected_players_price + goalkeeper_price)}, осталось выбрать: {remaining_players}")

    return {
        "players": players_data,
        "current_team_idx": current_team_idx,
        "teams": teams,
        "current_team": current_team,
        "remaining_points": 46 - (selected_players_price + goalkeeper_price),
        "remaining_players": remaining_players
    }

# Обработчик для переключения на следующую команду
async def set_next_team(
        dialog_manager: DialogManager):
    current_team_idx = dialog_manager.dialog_data.get('current_team_idx', 0)
    teams = dialog_manager.dialog_data.get('teams', [])
    if current_team_idx < len(teams) - 1:
        dialog_manager.dialog_data['current_team_idx'] = current_team_idx + 1
    await dialog_manager.switch_to(TeamSelectionSG.FIELD_PLAYERS)

# Обработчик для переключения на предыдущую команду
async def set_prev_team(
        dialog_manager: DialogManager):
    current_team_idx = dialog_manager.dialog_data.get('current_team_idx', 0)
    if current_team_idx > 0:
        dialog_manager.dialog_data['current_team_idx'] = current_team_idx - 1
    await dialog_manager.switch_to(TeamSelectionSG.FIELD_PLAYERS)

# Обработчик для сохранения команды после выбора капитана
async def process_confirm_team(
        callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager):
    # Получаем выбранных игроков из состояния
    selected_players = dialog_manager.current_context().dialog_data.get('selected_players', [])
    selected_players = [int(x) for x in selected_players]

    # Получаем ID голкипера и добавляем его к списку игроков
    selected_goalkeeper_id = dialog_manager.dialog_data.get('goalkeeper')
    if selected_goalkeeper_id:
        selected_players.append(int(selected_goalkeeper_id))  # Добавляем голкипера

    # Получаем объекты всех выбранных игроков
    async with dialog_manager.middleware_data['session'] as session:
        players = await orm_controller.get_players_by_ids(session, selected_players)

    # Получаем ID капитана
    captain_id = dialog_manager.dialog_data.get('captain')

    # Валидация команды
    is_valid, error_message = await validate_team(players)

    if not is_valid:
        await callback.answer(error_message, show_alert=True)
        return

    # Сохраняем каждого игрока в БД
    user_id = callback.from_user.id
    for player in players:
        is_captain = (player.id == captain_id)
        await orm_controller.add_fantasy_team(session, user_id, player.id, is_captain)

    await dialog_manager.switch_to(TeamSelectionSG.CONFIRMATION)

# Геттер данных для выбора капитана
async def get_captains(
        dialog_manager: DialogManager,
        **kwargs):
    logger.info("Получение данных для выбора капитана")
    selected_players = dialog_manager.dialog_data.get('selected_players', [])
    selected_goalkeeper_id = dialog_manager.dialog_data.get("goalkeeper")

    if not selected_players and not selected_goalkeeper_id:
        logger.warning("Нет выбранных игроков для выбора капитана")
        return {"players": []}

    async with dialog_manager.middleware_data['session'] as session:
        all_selected_players = await orm_controller.get_players_by_ids(
            session, selected_players + [selected_goalkeeper_id]
        )

    selected_captain = dialog_manager.dialog_data.get("captain")

    players_list = [
        (f"🃏 {player.name} ({player.team})" if str(player.id) == selected_captain
         else f"{player.name} ({player.team})", str(player.id))
        for player in all_selected_players
    ]

    logger.info(f"Список игроков для выбора капитана: {players_list}")
    return {"players": players_list}

# Обработчик выбора капитана
async def on_captain_selected(
        callback: CallbackQuery,
        button: Select,
        dialog_manager: DialogManager,
        item_id: str):
    dialog_manager.dialog_data["captain"] = item_id
    logger.info(f"Выбран капитан с ID: {item_id}")

    await callback.answer(LEXICON_RU['captain_selected'])

async def get_team_info(
        dialog_manager: DialogManager,
        **kwargs):
    # Получаем список ID игроков из данных диалога
    team_info = dialog_manager.dialog_data.get('team_info', [])
    logger.info(f"Получена информация о команде: {team_info}")  # Логируем полученные ID игроков

    # Если team_info пустой, загружаем команду из базы данных
    if not team_info:
        user_id = dialog_manager.event.from_user.id  # Получаем user_id
        session = dialog_manager.middleware_data['session']
        # Запрашиваем команду пользователя из базы данных
        team_info_db = await orm_controller.get_team_by_user_id(session, user_id)

        if not team_info_db or not team_info_db.fantasy_teams:
            logger.warning("Список игроков пустой!")
            return {"team_info": "Команда не выбрана."}  # Если список пустой, возвращаем текст

        # Сохраняем команду в dialog_data для повторного использования
        dialog_manager.dialog_data['team_info'] = [player.player_id for player in team_info_db.fantasy_teams]
        team_info = dialog_manager.dialog_data['team_info']

    # Получаем сессию и запрашиваем данные игроков по их ID
    session = dialog_manager.middleware_data['session']
    players_data = await orm_controller.get_players_by_ids(session, team_info)

    logger.info(f"Получены данные о игроках: {players_data}")  # Логируем полученные объекты Player

    # Формируем строку с информацией об игроках
    players_list = "\n".join([f"{player.name} ({player.team})" for player in players_data])

    # Возвращаем данные в формат, который будет использоваться в шаблоне
    return {"team_info": players_list}

# Виджет Select для выбора вратарей
goalkeepers_select = Select(
    Format("{item[0]}"),
    id="goalkeepers_select",
    item_id_getter=operator.itemgetter(1),
    items="goalkeepers",
    on_click=on_goalkeeper_selected
)

# Виджет Select для выбора капитана
captain_select = Select(
    Format("{item[0]}"),
    id="captain_select",
    item_id_getter=operator.itemgetter(1),
    items="players",
    on_click=on_captain_selected
)

# Окно для выбора капитана
captain_selection_window = Window(
    Const(LEXICON_RU['select_captain']),
    Column(
        captain_select,
        Button(Const(LEXICON_RU['confirm_captain']),
               id="confirm_captain",
               on_click=process_confirm_team),
        Button(Const(LEXICON_RU['return_to_field_players']),
               id="return_to_field_players",
               on_click=lambda c, b, d: d.switch_to(TeamSelectionSG.FIELD_PLAYERS))  # Возврат к выбору полевых игроков
    ),
    state=TeamSelectionSG.CAPTAIN_SELECTION,
    getter=get_captains
)

# Виджет Multiselect для выбора полевых игроков с правильным выводом баллов
players_multiselect = Multiselect(
    checked_text=Format('⚽️ {item[0]}'),
    unchecked_text=Format('{item[0]}'),
    id="players_multiselect",
    item_id_getter=operator.itemgetter(1),
    items="players",
    min_selected=0,
    max_selected=6,
    on_state_changed=on_players_state_changed
)

# Окна диалога
team_selection_dialog = Dialog(
    Window(
        Const(LEXICON_RU['rules']),
        Button(Const(LEXICON_RU['come']),
               id='switch_to_goalkeeper',
               on_click=lambda c, b, d: d.switch_to(TeamSelectionSG.GOALKEEPER)),
        Button(Const(LEXICON_RU['return_main_menu']),
               id="to_main_menu",
               on_click=lambda c, b, d: d.start(MainMenuSG.MAIN_PANEL)),
        state=TeamSelectionSG.INSTRUCTION
    ),
    Window(
        Const(LEXICON_RU['select_goalkeeper']),
        Column(
            goalkeepers_select,
            Button(Const(LEXICON_RU['confirm_goalkeeper']),
                   id="confirm_goalkeeper",
                   on_click=lambda c, b, d: d.switch_to(TeamSelectionSG.FIELD_PLAYERS)),
            Button(Const(LEXICON_RU['return_to_instructions']),
                   id="return_to_instructions",
                   on_click=lambda c, b, d: d.switch_to(TeamSelectionSG.INSTRUCTION))  # Возврат к правилам
        ),
        state=TeamSelectionSG.GOALKEEPER,
        getter=get_goalkeepers
    ),
    Window(
        Format(LEXICON_RU['select_field_players']),
        Group(
            Column(players_multiselect),
            Row(
                Button(Const(LEXICON_RU['prev_team']),
                       id="prev_team",
                       on_click=lambda c, b, d: set_prev_team(d)),
                Button(Const(LEXICON_RU['next_team']),
                       id="next_team",
                       on_click=lambda c, b, d: set_next_team(d)),
            ),
            Button(Const(LEXICON_RU['confirm_team']),
                   id="confirm_team",
                   on_click=lambda c, b, d: d.switch_to(TeamSelectionSG.CAPTAIN_SELECTION)),
            Button(Const(LEXICON_RU['return_to_goalkeeper']),
                   id="return_to_goalkeeper",
                   on_click=lambda c, b, d: d.switch_to(TeamSelectionSG.GOALKEEPER))  # Возврат к выбору вратаря
        ),
        state=TeamSelectionSG.FIELD_PLAYERS,
        getter=get_players_by_team
    ),
    captain_selection_window,
    Window(
        Format(LEXICON_RU['team_saved']),
        Button(Const(LEXICON_RU['return_main_menu']),
               id="to_main_menu",
               on_click=lambda c, b, d: d.start(MainMenuSG.MAIN_PANEL)),
        state=TeamSelectionSG.CONFIRMATION,
        getter=get_team_info
    )
)
