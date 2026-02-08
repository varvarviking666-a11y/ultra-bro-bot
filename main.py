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

TOKEN = '8512698228:AAFgjxxCBY0hnYqtVFD-pter14gKL5nCGd4'
bot = telebot.TeleBot(TOKEN)

async def recognize_track(path):
    shazam = Shazam()
    out = await shazam.recognize_song(path)
    if out.get('track'):
        return {
            'title': out['track']['title'],
            'artist': out['track']['subtitle']
        }
    return None

@bot.message_handler(func=lambda message: 'tiktok.com' in message.text)
def handle_tiktok(message):
    msg = bot.reply_to(message, "🎬 Качаю и включаю Shazam... 🔎")
    try:
        ydl_opts = {'format': 'best', 'outtmpl': 'file.%(ext)s', 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(message.text, download=True)
            video_file = ydl.prepare_filename(info)

        audio_file = "music.mp3"
        os.system(f"ffmpeg -i {video_file} -vn -ar 44100 -ac 2 -b:a 192k {audio_file}")

        # Запускаем Shazam
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        found = loop.run_until_complete(recognize_track(audio_file))

        artist = found['artist'] if found else info.get('artist', 'TikTok')
        track = found['title'] if found else info.get('track', 'Оригинальный звук')

        with open(video_file, 'rb') as v:
            bot.send_video(message.chat.id, v, caption="✅ Видео готово")

        with open(audio_file, 'rb') as a:
            bot.send_audio(message.chat.id, a, performer=artist, title=track)

        os.remove(video_file)
        os.remove(audio_file)
        bot.delete_message(message.chat.id, msg.message_id)

    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.polling(none_stop=True)
