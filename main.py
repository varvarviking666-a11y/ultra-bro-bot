import telebot
import asyncio
from shazamio import Shazam
import os
from flask import Flask
import threading

# === НАСТРОЙКИ ===
# Твой токен вставлен сюда
TELEGRAM_TOKEN = "8512698228:AAFgjxxCBY0hnYqtVFD-pter14gKL5nCGd4"
MAX_FILE_SIZE_MB = 20

# Мини-сервер для поддержания жизни на Render
app = Flask(__name__)
@app.route('/')
def home(): return "AI Shazam Bot is Live"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

bot = telebot.TeleBot(TELEGRAM_TOKEN)

async def recognize_track(file_path: str):
    shazam = Shazam()
    try:
        # Прямое распознавание файла
        result = await shazam.recognize_song(file_path)
        if "track" in result and result["track"]:
            track = result["track"]
            title = track.get("title", "Неизвестно")
            subtitle = track.get("subtitle", "Неизвестно")
            url = track.get("share", {}).get("href", "Ссылка отсутствует")
            return f"🎵 Найдено: {title} — {subtitle}\n🔗 {url}"
        else:
            return "❌ Трек не найден."
    except Exception as e:
        return f"⚠ Ошибка при распознавании: {e}"

@bot.message_handler(content_types=['audio', 'voice'])
def handle_audio(message):
    try:
        file_id = message.audio.file_id if message.content_type == 'audio' else message.voice.file_id
        file_info = bot.get_file(file_id)
        file_size_mb = file_info.file_size / (1024 * 1024)

        if file_size_mb > MAX_FILE_SIZE_MB:
            bot.reply_to(message, f"⚠ Файл слишком большой (>{MAX_FILE_SIZE_MB} МБ).")
            return

        downloaded_file = bot.download_file(file_info.file_path)
        file_path = f"temp_{message.chat.id}.mp3"
        with open(file_path, 'wb') as f:
            f.write(downloaded_file)

        bot.reply_to(message, "🔍 ИИ анализирует звук...")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result_text = loop.run_until_complete(recognize_track(file_path))

        bot.send_message(message.chat.id, result_text)
        if os.path.exists(file_path): os.remove(file_path)

    except Exception as e:
        bot.reply_to(message, f"⚠ Ошибка: {e}")

if __name__ == "__main__":
    # Запуск сервера для Render
    threading.Thread(target=run_flask).start()
    print("Бот запущен...")
    bot.infinity_polling()
