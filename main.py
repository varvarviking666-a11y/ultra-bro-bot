import telebot
import yt_dlp
import os
import threading
import asyncio
from shazamio import Shazam
from flask import Flask

app = Flask(__name__)
@app.route('/')
def hello(): return "Бот с Shazam активен!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# ТВОЙ ТОКЕН
TOKEN = '8512698228:AAFgjxxCBY0hnYqtVFD-pter14gKL5nCGd4'
bot = telebot.TeleBot(TOKEN)

async def recognize_track(path):
    shazam = Shazam()
    try:
        # Распознаем трек
        out = await shazam.recognize_song(path)
        if out and out.get('track'):
            return {
                'title': out['track']['title'],
                'artist': out['track']['subtitle']
            }
    except Exception as e:
        print(f"Ошибка Shazam: {e}")
    return None

@bot.message_handler(func=lambda message: 'tiktok.com' in message.text)
def handle_tiktok(message):
    msg = bot.reply_to(message, "🎬 Качаю и включаю Shazam... 🔎")
    try:
        # 1. Качаем видео
        ydl_opts = {'format': 'best', 'outtmpl': 'file.%(ext)s', 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(message.text, download=True)
            video_file = ydl.prepare_filename(info)

        # 2. Вырезаем звук для Shazam
        audio_file = "music.mp3"
        os.system(f"ffmpeg -i {video_file} -vn -ar 44100 -ac 2 -b:a 192k {audio_file} -y")

        # 3. Запускаем Shazam
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        found = loop.run_until_complete(recognize_track(audio_file))

        if found:
            artist = found['artist']
            track = found['title']
            caption_text = f"✅ Нашел трек: {artist} - {track}"
        else:
            artist = info.get('artist', 'TikTok')
            track = info.get('track', 'Оригинальный звук')
            caption_text = "⚠️ Оригинал в Shazam не найден, вырезал звук из видео"

        # 4. Отправляем видео и аудио (как на твоем примере)
        with open(video_file, 'rb') as v:
            bot.send_video(message.chat.id, v, caption=caption_text)

        with open(audio_file, 'rb') as a:
            bot.send_audio(message.chat.id, a, performer=artist, title=track)

        # Чистим файлы
        os.remove(video_file)
        os.remove(audio_file)
        bot.delete_message(message.chat.id, msg.message_id)

    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.polling(none_stop=True)
