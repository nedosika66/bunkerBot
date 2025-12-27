import asyncio
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from collections import Counter

from game_logic import games, games_by_invite, Game, Player
from keyboards import (
    get_main_menu_kb, get_player_lobby_kb, get_host_lobby_kb, 
    get_game_keyboard, get_players_info_kb, get_vote_kb, 
    get_reveal_kb
)

try:
    from ai_utils import generate_disaster
except ImportError:
    async def generate_disaster(): return "🔥 Ядерна зима (ШІ недоступний)."

router = Router()

# --- СТАРТ, ЛОБІ, СТВОРЕННЯ (Без змін) ---
@router.message(Command("start"))
async def cmd_start(message: Message):
    args = message.text.split()
    if len(args) > 1:
        code = args[1]
        if code in games_by_invite:
            game = games_by_invite[code]
            if game.is_active: return await message.answer("🚫 Гра вже йде.")
            if message.from_user.id not in game.players:
                game.players[message.from_user.id] = Player(message.from_user.id, message.from_user.first_name)
                await message.answer(f"✅ Ти в лобі {game.admin_name}!", reply_markup=get_player_lobby_kb())
                try: await message.bot.send_message(game.chat_id, f"👋 {message.from_user.first_name} приєднався!")
                except: pass
            else: await message.answer("Ти вже в лобі.", reply_markup=get_player_lobby_kb())
        else: await message.answer("Невірний код.")
    else: await message.answer("Вітаю в Бункері!", reply_markup=get_main_menu_kb())

@router.message(F.text == "Створити гру")
async def create_game(message: Message):
    chat_id = message.chat.id
    if chat_id in games: return await message.answer("⚠️ Тут вже є гра.")
    game = Game(chat_id, message.from_user.id, message.from_user.first_name)
    games[chat_id] = game
    games_by_invite[game.invite_code] = game
    game.players[message.from_user.id] = Player(message.from_user.id, message.from_user.first_name)
    bot_info = await message.bot.get_me()
    link = f"https://t.me/{bot_info.username}?start={game.invite_code}"
    await message.answer(f"☢️ <b>Лобі створено!</b>\nКод: `{game.invite_code}`\nПосилання: {link}", parse_mode="HTML", reply_markup=get_host_lobby_kb())

@router.message(F.text == "🚀 Почати гру")
@router.message(Command("start_game"))
async def start_game(message: Message):
    game = None
    if message.chat.id in games: game = games[message.chat.id]
    if not game:
        for g in games.values():
            if g.admin_id == message.from_user.id: game = g; break
    if not game: return await message.answer("Гри не знайдено.")
    if message.from_user.id != game.admin_id: return await message.answer("Тільки хост може почати.")
    if game.is_active: return await message.answer("Гра вже йде.")
    
    wait_msg = await message.answer("🧠 <b>ШІ генерує катастрофу...</b>", parse_mode="HTML")
    game.is_active = True
    try: game.disaster_text = await generate_disaster()
    except: game.disaster_text = "Збій ШІ."
    try: await wait_msg.delete()
    except: pass
    
    for p in game.players.values(): p.generate_card()
    game.votes = {}

    for pid in game.players:
        try: await message.bot.send_message(pid, f"☢️ <b>ГРА ПОЧАЛАСЯ!</b>\n\n{game.disaster_text}", reply_markup=get_game_keyboard(), parse_mode="HTML")
        except: pass
    await message.answer("✅ Гру розпочато!")

# --- МОЯ КАРТКА ---
@router.message(F.text == "👤 Моя картка")
async def show_card(message: Message):
    uid = message.from_user.id
    game = None
    for g in games.values():
        if uid in g.players: game = g; break
    if not game: return await message.answer("Ти не в грі.")
    p = game.players[uid]
    
    def check_vis(attr_key, value):
        if attr_key in p.revealed_attributes: return f"{value} (✅)"
        return f"{value} (🔒)"

    bio_str = f"{p.gender}, {p.age} р., {p.childbearing}"
    prof_str = f"{p.profession} ({p.profession_years} р.)"
    hobby_str = f"{p.hobby} ({p.hobby_years} р.)"
    health_str = f"{p.health} ({p.health_severity}%)"
    fact1_txt = p.facts[0] if len(p.facts) > 0 else "-"
    fact2_txt = p.facts[1] if len(p.facts) > 1 else "-"

    text = (
        f"🪪 <b>ТВОЄ ДОСЬЄ:</b>\n"
        f"👤 <b>Біологія:</b> {check_vis('bio', bio_str)}\n"
        f"🛠 <b>Проф:</b> {check_vis('profession', prof_str)}\n"
        f"❤️ <b>Здор:</b> {check_vis('health', health_str)}\n"
        f"🎨 <b>Хобі:</b> {check_vis('hobby', hobby_str)}\n"
        f"🎒 <b>Багаж:</b> {check_vis('luggage', p.luggage)}\n"
        f"😱 <b>Фобія:</b> {check_vis('phobia', p.phobia)}\n"
        f"💡 <b>Факт 1:</b> {check_vis('fact_0', fact1_txt)}\n"
        f"💡 <b>Факт 2:</b> {check_vis('fact_1', fact2_txt)}\n\n"
        f"👇 <i>Натисни кнопку, щоб відкрити іншим:</i>"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_reveal_kb(p))

# --- ВІДКРИТТЯ ---
@router.callback_query(F.data.startswith("reveal_"))
async def reveal_attribute_callback(call: CallbackQuery):
    attr = call.data.split("_", 1)[1]
    uid = call.from_user.id
    game = None
    for g in games.values():
        if uid in g.players: game = g; break
    if not game: return await call.answer("Гра закінчилась.")
    player = game.players[uid]
    
    if attr not in player.revealed_attributes:
        player.revealed_attributes.append(attr)
        val = "???"
        msg_text = "щось"
        
        if attr == 'bio': val = f"{player.gender}, {player.age} р., {player.childbearing}"; msg_text = "свою Біологію"
        elif attr == 'profession': val = f"{player.profession} (Стаж: {player.profession_years} р.)"; msg_text = "свою Професію"
        elif attr == 'health': val = f"{player.health} (Ступінь: {player.health_severity}%)"; msg_text = "своє Здоров'я"
        elif attr == 'hobby': val = f"{player.hobby} (Стаж: {player.hobby_years} р.)"; msg_text = "своє Хобі"
        elif attr == 'luggage': val = player.luggage; msg_text = "свій Багаж"
        elif attr == 'phobia': val = player.phobia; msg_text = "свою Фобію"
        elif attr == 'fact_0': val = player.facts[0]; msg_text = "свій Факт №1"
        elif attr == 'fact_1': val = player.facts[1]; msg_text = "свій Факт №2"
            
        try: await call.bot.send_message(game.chat_id, f"🔓 <b>{player.name}</b> відкрив {msg_text}: <b>{val}</b>", parse_mode="HTML")
        except: pass
        await call.answer(f"Відкрито: {msg_text}")
        await call.message.edit_reply_markup(reply_markup=get_reveal_kb(player))
    else: await call.answer("Вже відкрито.")

# --- СПИСОК ГРАВЦІВ ---
@router.message(F.text == "👥 Гравці")
async def show_players_menu(message: Message):
    uid = message.from_user.id
    game = None
    for g in games.values():
        if uid in g.players: game = g; break
    if not game: return
    await message.answer("👇 <b>Обери гравця:</b>", reply_markup=get_players_info_kb(game), parse_mode="HTML")

@router.callback_query(F.data.startswith("info_"))
async def info_callback(call: CallbackQuery):
    target_id = int(call.data.split("_")[1])
    game = None
    for g in games.values():
        if call.from_user.id in g.players: game = g; break
    if not game or target_id not in game.players: return await call.answer("Гравець вийшов.")
    
    t = game.players[target_id]
    def show(attr_key, value):
        if attr_key in t.revealed_attributes: return f"<b>{value}</b>"
        return "🔒"

    bio_str = f"{t.gender}, {t.age} р., {t.childbearing}"
    prof_str = f"{t.profession} ({t.profession_years} р.)"
    hobby_str = f"{t.hobby} ({t.hobby_years} р.)"
    health_str = f"{t.health} ({t.health_severity}%)"

    text = (
        f"👤 <b>{t.name}</b>\n"
        f"👤 Біо: {show('bio', bio_str)}\n"
        f"🛠 Проф: {show('profession', prof_str)}\n"
        f"❤️ Здор: {show('health', health_str)}\n"
        f"🎨 Хобі: {show('hobby', hobby_str)}\n"
        f"🎒 Багаж: {show('luggage', t.luggage)}\n"
        f"😱 Фобія: {show('phobia', t.phobia)}\n"
        f"💡 Факт 1: {show('fact_0', t.facts[0] if len(t.facts) > 0 else '-')}\n"
        f"💡 Факт 2: {show('fact_1', t.facts[1] if len(t.facts) > 1 else '-')}"
    )
    try: await call.message.edit_text(text, reply_markup=get_players_info_kb(game), parse_mode="HTML")
    except: await call.answer()

# --- ГОЛОСУВАННЯ ---
@router.message(F.text == "📢 Голосувати")
async def vote_menu(message: Message):
    uid = message.from_user.id
    game = None
    for g in games.values():
        if uid in g.players: game = g; break
    if not game: return
    
    # Якщо гравець вже проголосував
    if uid in game.votes:
        target_id = game.votes[uid]
        target_name = game.players[target_id].name if target_id in game.players else "Невідомий"
        await message.answer(f"Ти вже проголосував проти <b>{target_name}</b>. Чекай інших.", parse_mode="HTML")
        return

    await message.answer("💀 <b>Хто має покинути бункер?</b>", reply_markup=get_vote_kb(game), parse_mode="HTML")

@router.callback_query(F.data.startswith("vote_"))
async def vote_callback(call: CallbackQuery):
    target_id = int(call.data.split("_")[1])
    voter_id = call.from_user.id
    game = None
    for g in games.values():
        if voter_id in g.players: game = g; break
    if not game: return await call.answer("Помилка.")
    if target_id not in game.players: return await call.answer("Гравець вже вибув.")
    
    game.votes[voter_id] = target_id
    target_name = game.players[target_id].name
    await call.answer(f"Прийнято: проти {target_name}")
    await call.message.edit_text(f"✅ Голос проти <b>{target_name}</b> прийнято.", parse_mode="HTML")
    
    # Перевіряємо, чи всі проголосували
    if len(game.votes) >= len(game.players):
        await finish_voting(game, call.bot)

async def finish_voting(game: Game, bot):
    """Підрахунок результатів голосування з нічиєю"""
    if not game.votes: return
    
    # Рахуємо голоси
    vote_counts = Counter(game.votes.values())
    
    # Отримуємо рейтинг: [(user_id, count), ...]
    ranking = vote_counts.most_common()
    
    # --- 1. ПЕРЕВІРКА НА НІЧИЮ ---
    # Якщо є хоча б 2 людини і у першого стільки ж голосів, скільки у другого
    if len(ranking) > 1 and ranking[0][1] == ranking[1][1]:
        max_votes = ranking[0][1]
        
        # Знаходимо імена тих, хто набрав макс. голосів
        tied_users = [uid for uid, count in ranking if count == max_votes]
        tied_names = [game.players[uid].name for uid in tied_users]
        names_str = ", ".join(tied_names)
        
        text = (
            f"⚖️ <b>НІЧИЯ!</b>\n\n"
            f"Гравці <b>{names_str}</b> набрали однакову кількість голосів ({max_votes}).\n"
            f"Ніхто не вибуває.\n\n"
            f"🔄 <b>ГОЛОСУВАННЯ ПОЧИНАЄТЬСЯ ЗАНОВО!</b>"
        )
        
        # Скидаємо голоси
        game.votes = {}
        
        try: await bot.send_message(game.chat_id, text, parse_mode="HTML")
        except: pass
        
        # Сповіщаємо гравців особисто
        for pid in game.players:
            try: await bot.send_message(pid, "🔄 Увага! Нічия. Голосуйте знову.")
            except: pass
            
        return # Важливо: виходимо з функції, нікого не видаляємо!

    # --- 2. ЯКЩО НІЧИЄЇ НЕМАЄ (ВИГНАННЯ) ---
    loser_id, count = ranking[0]
    loser_name = game.players[loser_id].name
    
    result_text = f"🗳 <b>ГОЛОСУВАННЯ ЗАВЕРШЕНО!</b>\n\n💀 Більшістю голосів ({count}) бункер покидає: <b>{loser_name}</b>."
    try: await bot.send_message(game.chat_id, result_text, parse_mode="HTML")
    except: pass
    
    try: await bot.send_message(loser_id, "🚫 Тебе вигнали.", reply_markup=get_main_menu_kb())
    except: pass
    
    del game.players[loser_id]
    game.votes = {} # Очищаємо для наступного раунду
    
    for pid in game.players:
        try: await bot.send_message(pid, f"У бункері залишилось {len(game.players)} гравців.")
        except: pass

# --- СТАН І ВИХІД ---
@router.message(F.text == "📜 Стан бункера")
async def bunker_status(message: Message):
    uid = message.from_user.id
    game = None
    for g in games.values():
        if uid in g.players: game = g; break
    if not game: return
    await message.answer(f"☢️ <b>КАТАСТРОФА:</b>\n{game.disaster_text}\n\nЖивих: {len(game.players)}", parse_mode="HTML")

@router.message(F.text == "❌ Скасувати гру")
async def cancel_game(message: Message):
    chat_id = message.chat.id
    if chat_id in games and games[chat_id].admin_id == message.from_user.id:
        del games[chat_id]
        await message.answer("🗑 Гру скасовано.", reply_markup=get_main_menu_kb())

@router.message(F.text == "❌ Вийти з лобі")
async def leave_lobby(message: Message):
    uid = message.from_user.id
    for g in games.values():
        if uid in g.players:
            del g.players[uid]
            await message.answer("Ви вийшли.", reply_markup=get_main_menu_kb())
            try: await message.bot.send_message(g.chat_id, f"🏃 {message.from_user.first_name} вийшов.")
            except: pass
            return
    await message.answer("Ти не в грі.", reply_markup=get_main_menu_kb())