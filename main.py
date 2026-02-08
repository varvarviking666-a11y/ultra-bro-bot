import telebot
import yt_dlp
import os
import threading
from flask import Flask

app = Flask(__name__)
@app.route('/')
def hello(): return "Бот в топе и работает!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

TOKEN = '8512698228:AAFgjxxCBY0hnYqtVFD-pter14gKL5nCGd4'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Бро, я в сети! Теперь качаю в лучшем качестве и ищу музыку. Кидай ссылку!")

@bot.message_handler(func=lambda message: True)
def download_video(message):
    if 'tiktok.com' in message.text:
        msg = bot.reply_to(message, "Анализирую трек и качество... 🔎")
        try:
            # Настройки для МАКСИМАЛЬНОГО качества и извлечения инфо
            ydl_opts = {
                'format': 'bestvideo+bestaudio/best', # Ищем самый топ
                'outtmpl': 'video.mp4',
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(message.text, download=True)
                title = info.get('title', 'Без названия')
                # Пытаемся найти название трека в описании или метаданных
                track_info = info.get('track', info.get('alt_title', 'Не указан'))
                artist_info = info.get('artist', 'Неизвестен')

            caption = f"🎬 {title}\n🎵 Музыка: {artist_info} - {track_info}"
            
            with open('video.mp4', 'rb') as video:
                bot.send_video(message.chat.id, video, caption=caption)
            
            os.remove('video.mp4')
            bot.delete_message(message.chat.id, msg.message_id)
            
        except Exception as e:
            bot.reply_to(message, f"Бро, сорян, ошибка: {e}")
    else:
        bot.reply_to(message, "Это не TikTok, бро.")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    print("Бот погнал!")
    bot.polling(none_stop=True)
