import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

# Імпортуємо налаштування та хендлери
import config
from handlers import router

# Налаштування логування (щоб бачити, що відбувається в консолі)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def main():
    # Перевірка наявності токена
    if not hasattr(config, 'BOT_TOKEN') or not config.BOT_TOKEN:
        print("❌ ПОМИЛКА: У файлі config.py не знайдено змінну BOT_TOKEN!")
        return

    # Ініціалізація бота
    # parse_mode="HTML" дозволяє писати жирним та курсивом без зайвих тегів у кожному повідомленні
    bot = Bot(
        token=config.BOT_TOKEN, 
        default=DefaultBotProperties(parse_mode="HTML")
    )
    
    dp = Dispatcher()
    
    # Підключаємо роутер (всі команди з handlers.py)
    dp.include_router(router)

    print("✅ Бот успішно запущено! Натисни Ctrl+C, щоб зупинити.")
    
    # Видаляємо старі оновлення, щоб бот не відповідав на спам, який прийшов, поки він спав
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запуск процесу опитування
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Бот вимкнено.")