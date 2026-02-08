import telebot
import yt_dlp
import os
import threading
from flask import Flask

app = Flask(__name__)
@app.route('/')
def hello(): return "Бот-меломан активен!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

TOKEN = '8512698228:AAFgjxxCBY0hnYqtVFD-pter14gKL5nCGd4'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(func=lambda message: 'tiktok.com' in message.text)
def download_all(message):
    msg = bot.reply_to(message, "🎬 Готовлю видео и аудио-плеер...")
    try:
        # 1. Качаем лучшее видео
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'file.%(ext)s',
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(message.text, download=True)
            video_file = ydl.prepare_filename(info)
            # Достаем инфу о музыке
            artist = info.get('artist', 'TikTok')
            track = info.get('track', 'Оригинальный звук')

        # 2. Вырезаем звук в MP3 для плеера
        audio_file = "music.mp3"
        os.system(f"ffmpeg -i {video_file} -vn -ar 44100 -ac 2 -b:a 192k {audio_file}")

        # 3. Отправляем видео
        with open(video_file, 'rb') as v:
            bot.send_video(message.chat.id, v, caption="✅ Видео сохранено")

        # 4. Отправляем аудио (будет выглядеть как плеер!)
        with open(audio_file, 'rb') as a:
            bot.send_audio(
                message.chat.id, 
                a, 
                performer=artist, 
                title=track
            )

        # Удаляем временные файлы
        os.remove(video_file)
        os.remove(audio_file)
        bot.delete_message(message.chat.id, msg.message_id)

    except Exception as e:
        bot.reply_to(message, f"Ошибка, бро: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.polling(none_stop=True)
