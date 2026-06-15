import asyncio
import os
import logging
import uuid
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from utils import generate_card, get_sound, sync_to_ankiweb, parse_card, get_image_url

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("Критическая ошибка: BOT_TOKEN не найден в .env")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Временное хранилище для карточек
pending_cards = {}

async def process_sync(message: Message, card_text: str, audio_url: str):
    logger.info("--- [START SYNC PROCESS] ---")
    
    try:
        # Теперь sync_to_ankiweb сам превратит этот текст в красивый HTML!
        synced = await sync_to_ankiweb(card_text, audio_url)
        
        if synced:
            logger.info("Синхронизация успешна.")
            await message.answer("✅ Карточка добавлена в AnkiWeb — синхронизируй приложение")
        else:
            logger.error("Ошибка API AnkiWeb")
            await message.answer("❌ Ошибка при добавлении карточки в AnkiWeb.")
            
    except Exception as e:
        logger.exception(f"Исключение внутри process_sync: {e}")
        await message.answer("❌ Произошел сбой при обработке синхронизации.")
    
    logger.info("--- [END SYNC PROCESS] ---")

@dp.message(F.text)
async def handle_message(message: Message) -> None:
    word = message.text.strip()
    logger.info(f"=== [НОВОЕ СООБЩЕНИЕ] === Получено слово: '{word}'")

    # 1. Генерация текста карточки
    logger.info("Запуск генерации текста через LLM...")
    await bot.send_chat_action(message.chat.id, "typing")
    
    loop = asyncio.get_event_loop()
    try:
        card_text = await loop.run_in_executor(None, generate_card, word)
    except Exception as e:
        logger.error(f"Ошибка Groq API: {e}")
        await message.answer("❌ Ошибка при генерации текста. Проверьте VPN или API ключ.")
        return

    # 2. Формирование ссылки на аудио поток
    audio_url = await get_sound(word)

    # 3. Сохраняем данные во временный кэш для кнопки
    card_id = str(uuid.uuid4())[:8]
    pending_cards[card_id] = {
        "card_text": card_text,
        "audio_url": audio_url
    }

    # 4. Создаем inline-кнопки
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📥 Добавить в Anki", callback_data=f"add:{card_id}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel:{card_id}")
        ]
    ])

    # 5. Парсим карточку чисто для того, чтобы отправить превью-картинку пользователю в ТГ
    try:
        parsed_data = parse_card(card_text)
        image_url = await get_image_url(parsed_data["image_prompt"], parsed_data["front"])
        await bot.send_chat_action(message.chat.id, "upload_photo")
        await message.answer_photo(image_url, caption=card_text, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Не удалось отправить фото в ТГ: {e}")
        await message.answer(card_text, reply_markup=keyboard)

    # 6. Отправка аудио в телеграм
    try:
        await bot.send_chat_action(message.chat.id, "upload_voice")
        await message.answer_audio(audio_url, caption="🔊 Послушать произношение")
    except Exception as e:
        logger.error(f"Не удалось отправить аудио: {e}")

# =====================================================================
# ОБРАБОТЧИКИ НАЖАТИЯ НА КНОПКИ (CALLBACK QUERIES)
# =====================================================================

@dp.callback_query(F.data.startswith("add:"))
async def handle_add_callback(callback: CallbackQuery):
    card_id = callback.data.split(":")[1]
    card_data = pending_cards.get(card_id)

    if not card_data:
        await callback.answer("⚠️ Данные устарели.", show_alert=True)
        await callback.message.edit_reply_markup(reply_markup=None)
        return

    await callback.answer("Добавляю в Anki...")
    await callback.message.edit_reply_markup(reply_markup=None) 

    # Передаем оригинальный card_text - utils.py сам сделает из него HTML
    asyncio.create_task(process_sync(callback.message, card_data["card_text"], card_data["audio_url"]))

    if card_id in pending_cards:
        del pending_cards[card_id]

@dp.callback_query(F.data.startswith("cancel:"))
async def handle_cancel_callback(callback: CallbackQuery):
    card_id = callback.data.split(":")[1]
    
    if card_id in pending_cards:
        del pending_cards[card_id]
        
    await callback.answer("Отменено")
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.reply("❌ Добавление отменено.")

async def main():
    logger.info("Инициализация пуллинга бота...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logger.info("Запуск приложения...")
    asyncio.run(main())