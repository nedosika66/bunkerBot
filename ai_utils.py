# ai_utils.py
import google.generativeai as genai
import config
import asyncio

# Налаштування
genai.configure(api_key=config.GEMINI_API_KEY)

# Використовуємо швидку і безкоштовну модель
model = genai.GenerativeModel('gemini-2.5-flash')

async def generate_disaster():
    prompt = (
        "Ти ведучий настільної гри 'Бункер'. Твоя задача — придумати катастрофу. "
        "Вимоги:\n"
        "1. Опиши причину та наслідки апокаліпсису, скільки людей залишилось на світі (будь креативним).\n"
        "2. Опиши умови в бункері (що є, чого нема, на скільки часу провести в бункері і на скільки вистачить їжі).\n"
        "3. Відповідь має бути українською мовою.\n"
        "4. Обсяг: до 200 слів."
    )

    try:
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini Error: {e}")
        return (
            "⚠️ ШІ від Google втомився. \n"
            "Катастрофа: Навала гігантських равликів-вбивць. "
            "У бункері є лише сіль. Їжі на 2 дні."
        )