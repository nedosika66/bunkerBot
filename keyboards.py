from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- СТАНДАРТНІ МЕНЮ ---
def get_main_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Створити гру"), KeyboardButton(text="Приєднатися до гри")]],
        resize_keyboard=True, input_field_placeholder="Меню"
    )

def get_player_lobby_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ Я готовий"), KeyboardButton(text="❌ Вийти з лобі")]],
        resize_keyboard=True, input_field_placeholder="Очікування..."
    )

def get_host_lobby_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🚀 Почати гру"), KeyboardButton(text="❌ Скасувати гру")]],
        resize_keyboard=True, input_field_placeholder="Ви - Адмін"
    )

def get_game_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Моя картка"), KeyboardButton(text="📜 Стан бункера")],
            [KeyboardButton(text="👥 Гравці"), KeyboardButton(text="📢 Голосувати")]
        ],
        resize_keyboard=True, input_field_placeholder="Твій хід..."
    )

# --- INLINE ---
def get_players_info_kb(game):
    builder = InlineKeyboardBuilder()
    for user_id, player in game.players.items():
        builder.button(text=f"👤 {player.name}", callback_data=f"info_{user_id}")
    builder.adjust(2) 
    return builder.as_markup()

def get_vote_kb(game):
    builder = InlineKeyboardBuilder()
    for user_id, player in game.players.items():
        builder.button(text=f"💀 {player.name}", callback_data=f"vote_{user_id}")
    builder.adjust(2)
    return builder.as_markup()

# --- ВІДКРИТТЯ (ОНОВЛЕНА НАЗВА КНОПКИ) ---
def get_reveal_kb(player):
    builder = InlineKeyboardBuilder()
    
    attributes = {
        'bio': '👤 Біологію',       # <--- Змінив назву
        'profession': '🛠 Професію',
        'health': '❤️ Здоров\'я',
        'hobby': '🎨 Хобі',
        'phobia': '😱 Фобію',
        'luggage': '🎒 Багаж'
    }
    
    for key, label in attributes.items():
        if key not in player.revealed_attributes:
            builder.button(text=f"👁 {label}", callback_data=f"reveal_{key}")
    
    if 'fact_0' not in player.revealed_attributes:
        builder.button(text="👁 Факт №1", callback_data="reveal_fact_0")
        
    if 'fact_1' not in player.revealed_attributes:
        builder.button(text="👁 Факт №2", callback_data="reveal_fact_1")
            
    builder.adjust(2)
    return builder.as_markup()