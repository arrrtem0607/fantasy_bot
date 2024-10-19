from aiogram import Router
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Start
from aiogram_dialog.widgets.text import Const
from bot.utils.statesform import MainMenuSG
from bot.lexicon.lexicon import LEXICON_RU  # Тексты

# Главное меню с кнопками
main_menu_dialog = Dialog(
    Window(
        Const(LEXICON_RU['main_menu_welcome']),
        Button(Const(LEXICON_RU['view_team']), id="view_team", on_click=lambda c, b, d: d.switch_to(MainMenuSG.VIEW_TEAM)),
        Button(Const(LEXICON_RU['select_team']), id="select_team", on_click=lambda c, b, d: d.switch_to(MainMenuSG.SELECT_TEAM)),
        Button(Const(LEXICON_RU['transfers']), id="transfers", on_click=lambda c, b, d: d.switch_to(MainMenuSG.TRANSFERS)),
        Button(Const(LEXICON_RU['choose_captain']), id="choose_captain", on_click=lambda c, b, d: d.switch_to(MainMenuSG.CHOOSE_CAPTAIN)),
        Button(Const(LEXICON_RU['view_stats']), id="view_stats", on_click=lambda c, b, d: d.switch_to(MainMenuSG.VIEW_STATS)),
        state=MainMenuSG.MAIN_PANEL
    )
)

def get_main_menu_router() -> Router:
    router = Router()
    return router