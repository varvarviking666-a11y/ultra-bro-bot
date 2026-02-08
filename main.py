import telebot
import yt_dlp
import os
import threading
import asyncio
from shazamio import Shazam
from flask import Flask

app = Flask(__name__)
@app.route('/')
def hello(): return "Бот-Меломан на связи!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

TOKEN = '8512698228:AAFgjxxCBY0hnYqtVFD-pter14gKL5nCGd4'
bot = telebot.TeleBot(TOKEN)

async def get_track_query(path):
    shazam = Shazam()
    out = await shazam.recognize_song(path)
    if out and out.get('track'):
        return f"{out['track']['subtitle']} - {out['track']['title']}"
    return None

@bot.message_handler(func=lambda message: 'tiktok.com' in message.text)
def handle_tiktok(message):
    msg = bot.reply_to(message, "🧠 ИИ анализирует звук и ищет оригинал...")
    try:
        # 1. Качаем звук для анализа
        ydl_opts_info = {'format': 'bestaudio', 'outtmpl': 'check.mp3', 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            ydl.download([message.text])
        
        # 2. Shazam узнает название
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        query = loop.run_until_complete(get_track_query('check.mp3'))
        
        # 3. Ищем и качаем ПОЛНЫЙ трек (SoundCloud — чтобы не было капчи)
        # Если Shazam не нашел, используем просто "музыка из видео"
        search_query = query if query else "TikTok viral music"
        
        ydl_opts_full = {
            'format': 'bestaudio/best',
            'outtmpl': 'full_track.mp3',
            'default_search': 'scsearch1:', # Поиск строго в SoundCloud
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '320'}],
            'quiet': True
        }

        with yt_dlp.YoutubeDL(ydl_opts_full) as ydl:
            info = ydl.extract_info(f"scsearch1:{search_query}", download=True)
            track_title = info['entries'][0]['title'] if 'entries' in info else query

        # 4. Отправляем готовый файл
        with open('full_track.mp3', 'rb') as a:
            bot.send_audio(message.chat.id, a, title=track_title, performer="Найденный оригинал")

        # Чистка
        os.remove('check.mp3')
        os.remove('full_track.mp3')
        bot.delete_message(message.chat.id, msg.message_id)

    except Exception as e:
        bot.reply_to(message, f"Бро, даже ИИ припотел. Ошибка: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.polling(none_stop=True)
