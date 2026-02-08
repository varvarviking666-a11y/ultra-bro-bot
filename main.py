import telebot
import yt_dlp
import os
import threading
from flask import Flask

app = Flask(__name__)
@app.route('/')
def hello(): return "Бот работает стабильно!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

TOKEN = '8512698228:AAFgjxxCBY0hnYqtVFD-pter14gKL5nCGd4'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(func=lambda message: 'tiktok.com' in message.text)
def download_all(message):
    msg = bot.reply_to(message, "🚀 Загружаю видео и музыку...")
    try:
        # 1. Настройки для видео и аудио из ОДНОГО источника (TikTok)
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'file.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(message.text, download=True)
            video_filename = ydl.prepare_filename(info)
            # Вытаскиваем название трека из инфы ТикТока
            track_name = info.get('track', 'Музыка из TikTok')
            artist_name = info.get('artist', 'Автор неизвестен')

        # 2. Конвертируем видео в MP3 для отдельного файла
        audio_filename = "music.mp3"
        os.system(f"ffmpeg -i {video_filename} -q:a 0 -map a {audio_filename}")

        # 3. Отправляем видео
        with open(video_filename, 'rb') as v:
            bot.send_video(message.chat.id, v, caption="✅ Видео в макс. качестве")

        # 4. Отправляем аудио (как ты просил)
        with open(audio_filename, 'rb') as a:
            bot.send_audio(message.chat.id, a, title=track_name, performer=artist_name)

        # Чистим файлы
        os.remove(video_filename)
        os.remove(audio_filename)
        bot.delete_message(message.chat.id, msg.message_id)

    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.polling(none_stop=True)
