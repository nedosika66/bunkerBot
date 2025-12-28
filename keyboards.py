from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_main_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Створити гру"), KeyboardButton(text="Приєднатись до гри")]
        ], resize_keyboard=True
    )

def get_host_lobby_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 Почати гру"), KeyboardButton(text="❌ Скасувати гру")]
        ], resize_keyboard=True
    )

def get_player_lobby_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Вийти з лобі")]
        ], resize_keyboard=True
    )

def get_game_kb(is_admin=False):
    kb = [
        [KeyboardButton(text="👤 Моя картка"), KeyboardButton(text="📜 Стан бункера")],
        [KeyboardButton(text="👥 Гравці")]
    ]
    if is_admin:
        kb.append([KeyboardButton(text="🥾 Вигнати гравця"), KeyboardButton(text="🏁 Завершити гру")])
    
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_kick_kb(game):
    builder = InlineKeyboardBuilder()
    for uid, player in game.players.items():
        label = f"{player.name}"
        if uid == game.admin_id:
            label += " (Це ти)"
        builder.button(text=label, callback_data=f"kick_{uid}")
    
    builder.button(text="🔙 Скасувати", callback_data="cancel_kick")
    builder.adjust(1)
    return builder.as_markup()

def get_reveal_kb(player):
    builder = InlineKeyboardBuilder()
    
    mapping = {
        'bio': 'Біографія',
        'profession': 'Професія',
        'health': "Здоров'я",
        'hobby': 'Хобі',
        'luggage': 'Багаж',
        'phobia': 'Фобія',
        'fact_0': 'Факт 1',
        'fact_1': 'Факт 2'
    }

    for key, label in mapping.items():
        if key not in player.revealed_attributes:
            builder.button(text=label, callback_data=f"reveal_{key}")
            
    builder.adjust(2)
    return builder.as_markup()
