import asyncio
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from game_logic import games, games_by_invite, Game, Player
from keyboards import (
    get_main_menu_kb, get_player_lobby_kb, get_host_lobby_kb, 
    get_game_kb, get_kick_kb, get_reveal_kb
)

try:
    from ai_utils import generate_disaster, analyze_survival
except ImportError:
    async def generate_disaster(): return "🔥 Збій ШІ. Уявіть катастрофу самі."
    async def analyze_survival(d, s): return "🏁 Гра завершена (ШІ недоступний)."

router = Router()
game_lock = asyncio.Lock()

@router.message(Command("start"))
async def cmd_start(message: Message):
    args = message.text.split()
    if len(args) > 1:
        code = args[1]
        if code in games_by_invite:
            game = games_by_invite[code]
            if game.is_active: return await message.answer("🚫 Гра вже йде.")
            
            async with game_lock:
                if message.from_user.id not in game.players:
                    game.add_player(message.from_user.id, message.from_user.first_name)
                    await message.answer(f"✅ Ти в лобі {game.admin_name}!", reply_markup=get_player_lobby_kb())
                    try: await message.bot.send_message(game.chat_id, f"👋 {message.from_user.first_name} приєднався!")
                    except: pass
                else: 
                    await message.answer("Ти вже в лобі.", reply_markup=get_player_lobby_kb())
        else: await message.answer("Невірний код.")
    else: await message.answer("Вітаю в Бункері!", reply_markup=get_main_menu_kb())

@router.message(F.text == "Створити гру")
async def create_game(message: Message):
    chat_id = message.chat.id
    if chat_id in games: return await message.answer("⚠️ Тут вже є гра.")
    
    game = Game(chat_id, message.from_user.id, message.from_user.first_name)
    games[chat_id] = game
    games_by_invite[game.invite_code] = game
    game.add_player(message.from_user.id, message.from_user.first_name)
    
    bot_info = await message.bot.get_me()
    link = f"https://t.me/{bot_info.username}?start={game.invite_code}"
    
    await message.answer(
        f"☢️ <b>Лобі створено!</b>\nКод: `{game.invite_code}`\nПосилання: {link}", 
        parse_mode="HTML", 
        reply_markup=get_host_lobby_kb()
    )

@router.message(F.text == "Приєднатись до гри")
async def join_dialog(message: Message):
    await message.answer("Щоб приєднатися, натисніть на посилання, яке вам надіслав Хост.")

@router.message(F.text == "🚀 Почати гру")
async def start_game(message: Message):
    game = games.get(message.chat.id)
    if not game: return
    if message.from_user.id != game.admin_id: return await message.answer("Тільки хост може почати.")
    if game.is_active: return await message.answer("Гра вже йде.")
    
    wait_msg = await message.answer("🧠 <b>ШІ генерує катастрофу...</b>", parse_mode="HTML")
    game.is_active = True
    
    try: game.disaster_text = await generate_disaster()
    except: game.disaster_text = "Катастрофа невідома."
    try: await wait_msg.delete()
    except: pass
    
    for p in game.players.values(): p.generate_card()

    for pid in list(game.players.keys()):
        is_admin = (pid == game.admin_id)
        kb = get_game_kb(is_admin)
        try: 
            await message.bot.send_message(
                pid, 
                f"☢️ <b>ГРА ПОЧАЛАСЯ!</b>\n\n{game.disaster_text}", 
                reply_markup=kb, 
                parse_mode="HTML"
            )
        except: pass
    
    await message.answer("✅ Гру розпочато!", reply_markup=get_game_kb(True))

@router.message(F.text == "👤 Моя картка")
async def show_card(message: Message):
    uid = message.from_user.id
    game = None
    for g in games.values():
        if uid in g.players: 
            game = g
            break
            
    if not game: 
        if message.chat.id in games and games[message.chat.id].admin_id == uid:
            return await message.answer("👀 Ти Хост-спостерігач. Твоя картка анульована, але ти керуєш грою.")
        return await message.answer("Ти не в грі.")

    p = game.players[uid]
    
    def check(key, val):
        return f"{val} (✅)" if key in p.revealed_attributes else f"{val} (🔒)"

    text = (
        f"🪪 <b>ТВОЄ ДОСЬЄ:</b>\n"
        f"👤 {check('bio', f'{p.gender}, {p.age}, {p.childbearing}')}\n"
        f"🛠 {check('profession', f'{p.profession} ({p.profession_years} р.)')}\n"
        f"❤️ {check('health', f'{p.health} ({p.health_severity}%)')}\n"
        f"🎨 {check('hobby', f'{p.hobby} ({p.hobby_years} р.)')}\n"
        f"🎒 {check('luggage', p.luggage)}\n"
        f"😱 {check('phobia', p.phobia)}\n"
        f"💡 {check('fact_0', p.facts[0] if p.facts else '-')}\n"
        f"💡 {check('fact_1', p.facts[1] if len(p.facts)>1 else '-')}\n"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_reveal_kb(p))

@router.callback_query(F.data.startswith("reveal_"))
async def reveal_callback(call: CallbackQuery):
    attr = call.data.split("_", 1)[1]
    uid = call.from_user.id
    game = None
    for g in games.values():
        if uid in g.players: game = g; break
    
    if not game: return await call.answer("Помилка.")
    p = game.players[uid]
    
    if attr not in p.revealed_attributes:
        p.revealed_attributes.append(attr)
        val = "???"
        if attr == 'bio': val = f"{p.gender}, {p.age}, {p.childbearing}"
        elif attr == 'profession': val = f"{p.profession} ({p.profession_years} р.)"
        elif attr == 'health': val = f"{p.health} ({p.health_severity}%)"
        elif attr == 'hobby': val = f"{p.hobby} ({p.hobby_years} р.)"
        elif attr == 'luggage': val = p.luggage
        elif attr == 'phobia': val = p.phobia
        elif attr == 'fact_0': val = p.facts[0]
        elif attr == 'fact_1': val = p.facts[1]

        try: await call.bot.send_message(game.chat_id, f"🔓 <b>{p.name}</b> відкрив: {val}", parse_mode="HTML")
        except: pass
        
        await call.answer("Відкрито!")
        await call.message.edit_reply_markup(reply_markup=get_reveal_kb(p))
    else:
        await call.answer("Вже відкрито.")

@router.message(F.text == "📜 Стан бункера")
async def bunker_status(message: Message):
    game = games.get(message.chat.id)
    if not game:
        for g in games.values():
            if message.from_user.id in g.players: game = g; break
    
    if not game: return await message.answer("Гри немає.")
    
    await message.answer(
        f"☢️ <b>КАТАСТРОФА:</b>\n{game.disaster_text}\n\n"
        f"👥 Живих гравців: {len(game.players)}", 
        parse_mode="HTML"
    )

@router.message(F.text == "👥 Гравці")
async def show_players(message: Message):
    game = games.get(message.chat.id)
    if not game:
        for g in games.values():
            if message.from_user.id in g.players: game = g; break
            
    if not game: return await message.answer("Гри немає.")
    
    text = "<b>Список гравців у бункері:</b>\n"
    for p in game.players.values():
        text += f"- {p.name}\n"
    
    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "🥾 Вигнати гравця")
async def kick_menu(message: Message):
    game = games.get(message.chat.id)
    if not game: return
    if message.from_user.id != game.admin_id: return await message.answer("Тільки Хост може виганяти.")
    
    if not game.players:
        return await message.answer("Всі вже вигнані.")

    await message.answer("Кого вигнати з бункера?", reply_markup=get_kick_kb(game))

@router.callback_query(F.data.startswith("kick_"))
async def kick_callback(call: CallbackQuery):
    target_id = int(call.data.split("_")[1])
    game = games.get(call.message.chat.id)
    
    if not game or call.from_user.id != game.admin_id:
        return await call.answer("Немає прав.")

    if target_id not in game.players:
        return await call.answer("Цей гравець вже не в грі.")

    player_name = game.players[target_id].name
    
    del game.players[target_id]
    
    if target_id == game.admin_id:
        await call.message.edit_text(f"👀 <b>{player_name} (Хост)</b> залишив місце в бункері, але спостерігає за грою.", parse_mode="HTML")
    else:
        await call.message.edit_text(f"🚫 <b>{player_name}</b> був вигнаний з бункера рішенням Хоста!", parse_mode="HTML")
        try: await call.bot.send_message(target_id, "Тебе вигнали з гри.", reply_markup=get_main_menu_kb())
        except: pass

@router.callback_query(F.data == "cancel_kick")
async def cancel_kick(call: CallbackQuery):
    await call.message.delete()

@router.message(F.text == "🏁 Завершити гру")
async def end_game_confirm(message: Message):
    game = games.get(message.chat.id)
    if not game or message.from_user.id != game.admin_id: return
    
    processing_msg = await message.answer("⏳ <b>Збираю дані та аналізую шанси на виживання...</b>", parse_mode="HTML")
    
    survivors_text = ""
    for p in game.players.values():
        survivors_text += (
            f"\n👤 {p.name} ({p.gender}, {p.age}):\n"
            f"   Професія: {p.profession} ({p.profession_years} років)\n"
            f"   Здоров'я: {p.health} ({p.health_severity}%)\n"
            f"   Хобі: {p.hobby}\n"
            f"   Багаж: {p.luggage}\n"
            f"   Фобія: {p.phobia}\n"
            f"   Факти: {', '.join(p.facts)}\n"
        )
    
    if not survivors_text:
        survivors_text = "Ніхто не вижив. Бункер порожній."

    try:
        final_story = await analyze_survival(game.disaster_text, survivors_text)
    except Exception as e:
        final_story = f"Помилка аналізу: {e}"

    del games[message.chat.id]
    if game.invite_code in games_by_invite:
        del games_by_invite[game.invite_code]

    await processing_msg.delete()
    
    await message.answer(f"🏁 <b>ФІНАЛ:</b>\n\n{final_story}", parse_mode="Markdown", reply_markup=get_main_menu_kb())
    
    for pid in game.players:
        if pid != message.chat.id:
            try: await message.bot.send_message(pid, f"🏁 <b>ФІНАЛ:</b>\n\n{final_story}", parse_mode="Markdown", reply_markup=get_main_menu_kb())
            except: pass

@router.message(F.text == "❌ Скасувати гру")
async def cancel_lobby(message: Message):
    game = games.get(message.chat.id)
    if game and message.from_user.id == game.admin_id:
        del games[message.chat.id]
        if game.invite_code in games_by_invite: del games_by_invite[game.invite_code]
        await message.answer("Гру скасовано.", reply_markup=get_main_menu_kb())

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
