import telebot
import yt_dlp
import os
import asyncio
from shazamio import Shazam
from flask import Flask
import threading

app = Flask(__name__)
@app.route('/')
def home(): return "Music AI is Active"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

TOKEN = '8512698228:AAFgjxxCBY0hnYqtVFD-pter14gKL5nCGd4'
bot = telebot.TeleBot(TOKEN)

async def get_track_info(url):
    shazam = Shazam()
    # Качаем только 10 секунд для распознавания
    ydl_opts = {'format': 'wa', 'outtmpl': 'sample.mp3', 'quiet': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    res = await shazam.recognize_song('sample.mp3')
    os.remove('sample.mp3')
    
    if res and res.get('track'):
        return f"{res['track']['subtitle']} - {res['track']['title']}"
    return None

@bot.message_handler(func=lambda m: 'tiktok.com' in m.text)
def handle_music(message):
    status = bot.reply_to(message, "🔍 Слушаю видео и ищу полную версию в сети...")
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        track_name = loop.run_until_complete(get_track_info(message.text))

        if not track_name:
            return bot.edit_message_text("❌ Shazam не узнал этот звук. Попробуй другое видео.", message.chat.id, status.message_id)

        bot.edit_message_text(f"✅ Нашел оригинал: {track_name}\n🚀 Качаю полную MP3 версию...", message.chat.id, status.message_id)

        # Качаем ТОЛЬКО полную версию из SoundCloud
        ydl_full_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'full.mp3',
            'default_search': 'scsearch1:', 
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '320'}],
            'quiet': True
        }

        with yt_dlp.YoutubeDL(ydl_full_opts) as ydl:
            ydl.download([f"scsearch1:{track_name}"])

        with open('full.mp3', 'rb') as audio:
            bot.send_audio(message.chat.id, audio, title=track_name, performer="Full Version Found")
        
        os.remove('full.mp3')
        bot.delete_message(message.chat.id, status.message_id)

    except Exception as e:
        bot.edit_message_text(f"⚠ Сбой поиска: {str(e)}", message.chat.id, status.message_id)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.polling(none_stop=True)
