import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile
import yt_dlp

# 1. Налаштування (беремо з секретів Hugging Face)
TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

bot = Bot(token=TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

# Налаштування завантаження
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'outtmpl': 'downloads/%(id)s.%(ext)s', # Використовуємо ID відео для назви файлу
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Привіт! Я завантажувач музики. Скинь посилання, і я надішлю MP3 тобі та в канал. 🎵")

@dp.message(F.text.contains("youtube.com") | F.text.contains("youtu.be"))
async def download_audio(message: types.Message):
    url = message.text
    status_msg = await message.answer("⏳ Обробка посилання...")
    file_path = None # Змінна для шляху до файлу
    
    try:
        # Створюємо тимчасову папку
        if not os.path.exists('downloads'):
            os.makedirs('downloads')

        # Завантаження
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=True)
            # Отримуємо точний шлях до створеного mp3 файлу
            file_path = ydl.prepare_filename(info).replace(info['ext'], 'mp3')
            title = info.get('title', 'Audio')

        # Відправка тобі
        audio_to_user = FSInputFile(file_path)
        await message.answer_audio(audio_to_user, caption=f"✅ {title}")

        # Відправка в канал
        if CHANNEL_ID:
            audio_to_channel = FSInputFile(file_path)
            await bot.send_audio(
                chat_id=CHANNEL_ID, 
                audio=audio_to_channel, 
                caption=f"🎧 #Music: {title}\n👤 Замовив: {message.from_user.first_name}"
            )
        
        await status_msg.delete()

    except Exception as e:
        logging.error(f"Error: {e}")
        await message.answer("❌ Помилка завантаження. Спробуй інше посилання.")
    
    finally:
        # САМООЧИЩЕННЯ: Видаляємо файл, якщо він існує
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logging.info(f"Файл {file_path} видалено з сервера.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
