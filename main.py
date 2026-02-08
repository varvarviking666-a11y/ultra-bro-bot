import telebot
import yt_dlp
import os
import threading
from flask import Flask

# --- СЕКЦИЯ ДЛЯ RENDER (ЧТОБЫ БОТ НЕ ВЫКЛЮЧАЛСЯ) ---
app = Flask(__name__)

@app.route('/')
def hello():
    return "Бот запущен и работает 24/7!"

def run_flask():
    # Render передает порт в переменные среды
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# --- ТВОЙ БОТ С ТВОИМ ТОКЕНОМ ---
TOKEN = '8512698228:AAFgjxxCBY0hnYqtVFD-pter14gKL5nCGd4'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Бро, я в сети на сервере! Кидай ссылку на TikTok — скачаю без проблем.")

@bot.message_handler(func=lambda message: True)
def download_video(message):
    if 'tiktok.com' in message.text:
        msg = bot.reply_to(message, "Принял! Качаю видео через сервер (это поможет обойти защиту)... 🚀")
        try:
            # Настройки для скачивания
            ydl_opts = {
                'format': 'best',
                'outtmpl': 'video.mp4',
                'quiet': True,
                'no_warnings': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([message.text])
            
            # Отправляем видео пользователю
            with open('video.mp4', 'rb') as video:
                bot.send_video(message.chat.id, video)
            
            # Удаляем файл после отправки
            os.remove('video.mp4')
            bot.delete_message(message.chat.id, msg.message_id)
            
        except Exception as e:
            bot.edit_message_text(f"Ошибка скачивания: {e}", message.chat.id, msg.message_id)
    else:
        bot.reply_to(message, "Это не похоже на ссылку TikTok, бро.")

# --- ЗАПУСК ---
if __name__ == "__main__":
    # 1. Запускаем веб-сервер в фоновом потоке для Render
    threading.Thread(target=run_flask).start()
    
    # 2. Запускаем самого бота
    print("Бот погнал!")
    bot.polling(none_stop=True)
