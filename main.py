import telebot
import yt_dlp
import os
import threading
from flask import Flask

app = Flask(__name__)
@app.route('/')
def hello(): return "Музыкальный бот активен!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

TOKEN = '8512698228:AAFgjxxCBY0hnYqtVFD-pter14gKL5nCGd4'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Бро, я готов! Кидай ссылку — пришлю и видео в топе, и музыку отдельно! 🎬🎵")

@bot.message_handler(func=lambda message: True)
def download_all(message):
    if 'tiktok.com' in message.text:
        msg = bot.reply_to(message, "Работаю... Забираю видео и музыку! 🚀")
        try:
            # 1. Качаем видео в макс. качестве
            ydl_opts_video = {'format': 'best', 'outtmpl': 'video.mp4', 'quiet': True}
            # 2. Качаем отдельно музыку (MP3)
            ydl_opts_audio = {
                'format': 'bestaudio/best',
                'outtmpl': 'music.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                }],
                'quiet': True
            }

            with yt_dlp.YoutubeDL(ydl_opts_video) as ydl:
                info = ydl.extract_info(message.text, download=True)
                artist = info.get('artist', 'Неизвестен')
                track = info.get('track', 'Трек из TikTok')

            with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
                ydl.download([message.text])

            # Отправляем видео
            with open('video.mp4', 'rb') as v:
                bot.send_video(message.chat.id, v, caption=f"🎬 Качество: Максимальное")

            # Отправляем аудио (как на твоем примере)
            with open('music.mp3', 'rb') as a:
                bot.send_audio(message.chat.id, a, title=track, performer=artist)

            # Чистим за собой
            os.remove('video.mp4')
            os.remove('music.mp3')
            bot.delete_message(message.chat.id, msg.message_id)

        except Exception as e:
            bot.reply_to(message, f"Ошибка, бро: {e}")
    else:
        bot.reply_to(message, "Это не ссылка на TikTok.")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.polling(none_stop=True)
