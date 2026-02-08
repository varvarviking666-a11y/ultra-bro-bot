import os
import telebot
from flask import Flask, request
import subprocess
import asyncio
from shazamio import Shazam
import threading

# Токен вставлен напрямую
API_TOKEN = "8512698228:AAFgjxxCBY0hnYqtVFD-pter14gKL5nCGd4"
bot = telebot.TeleBot(API_TOKEN)

app = Flask(__name__)

# Маршрут для проверки Render
@app.route("/")
def index():
    return "Bot is running", 200

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Привет! Скинь ссылку на видео, я попробую найти музыку 🎵")

# Обработчик ссылок
@bot.message_handler(func=lambda m: 'http' in m.text)
def handle_video(message):
    url = message.text.strip()
    msg = bot.reply_to(message, "Скачиваю аудио...")

    try:
        # Скачиваем аудио из видео
        subprocess.run(["yt-dlp", "-f", "bestaudio", "-o", "full_track.mp3", url])

        bot.edit_message_text("Ищу музыку...", message.chat.id, msg.message_id)

        async def recognize():
            shazam = Shazam()
            out = await shazam.recognize_song("full_track.mp3")
            if out.get('matches'):
                track = out['track']['title']
                artist = out['track']['subtitle']
                bot.reply_to(message, f"Нашёл: {artist} – {track}")
            else:
                bot.reply_to(message, "Не удалось распознать трек 😔")
            
            if os.path.exists("full_track.mp3"):
                os.remove("full_track.mp3")

        asyncio.run(recognize())
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {str(e)}")

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # Запускаем Flask в отдельном потоке для Render
    threading.Thread(target=run_flask).start()
    print("Бот запущен через polling...")
    bot.infinity_polling()
