import telebot
import yt_dlp
import os
import asyncio
from shazamio import Shazam
from flask import Flask
import threading

# Веб-сервер для работы на Render без остановки
app = Flask(__name__)
@app.route('/')
def home(): return "AI Music Finder is Live!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

TOKEN = '8512698228:AAFgjxxCBY0hnYqtVFD-pter14gKL5nCGd4'
bot = telebot.TeleBot(TOKEN)

async def get_full_track_name(url):
    shazam = Shazam()
    # Качаем только маленький кусочек для распознавания
    ydl_opts = {'format': 'wa', 'outtmpl': 'short.mp3', 'quiet': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    res = await shazam.recognize_song('short.mp3')
    os.remove('short.mp3')
    
    if res and res.get('track'):
        return f"{res['track']['subtitle']} - {res['track']['title']}"
    return None

@bot.message_handler(func=lambda m: 'tiktok.com' in m.text)
def handle_music(message):
    status = bot.reply_to(message, "🎧 Распознаю трек и ищу полную версию...")
    
    try:
        # 1. Распознаем название
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        track_name = loop.run_until_complete(get_full_track_name(message.text))

        if not track_name:
            return bot.edit_message_text("❌ Не удалось распознать музыку.", message.chat.id, status.message_id)

        bot.edit_message_text(f"✅ Нашел: {track_name}\nЗагружаю полный файл...", message.chat.id, status.message_id)

        # 2. Качаем ПОЛНУЮ версию из SoundCloud (минуя YouTube и капчу)
        ydl_sc_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'full_music.mp3',
            'default_search': 'scsearch1:', 
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '320'}],
            'quiet': True
        }

        with yt_dlp.YoutubeDL(ydl_sc_opts) as ydl:
            ydl.download([f"scsearch1:{track_name}"])

        # 3. Отправляем файл
        with open('full_music.mp3', 'rb') as audio:
            bot.send_audio(message.chat.id, audio, title=track_name, performer="Full Track")
        
        os.remove('full_music.mp3')
        bot.delete_message(message.chat.id, status.message_id)

    except Exception as e:
        bot.edit_message_text(f"⚠ Ошибка: {str(e)}", message.chat.id, status.message_id)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.polling(none_stop=True)
