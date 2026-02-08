import telebot
import yt_dlp
import os
import asyncio
from shazamio import Shazam
from flask import Flask
import threading

# Веб-сервер, чтобы бот не засыпал на Render
app = Flask(__name__)
@app.route('/')
def home(): return "AI Shazam is Live!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

TOKEN = '8512698228:AAFgjxxCBY0hnYqtVFD-pter14gKL5nCGd4'
bot = telebot.TeleBot(TOKEN)

async def shazam_it(url):
    shazam = Shazam()
    # Качаем только 10 сек звука для распознавания
    ydl_opts = {'format': 'wa', 'outtmpl': 'sample.mp3', 'quiet': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        res = await shazam.recognize_song('sample.mp3')
        if os.path.exists('sample.mp3'): os.remove('sample.mp3')
        if res and res.get('track'):
            return f"{res['track']['subtitle']} - {res['track']['title']}"
    except: return None
    return None

@bot.message_handler(func=lambda m: 'tiktok.com' in m.text)
def handle_link(message):
    status = bot.reply_to(message, "🧠 Шазамлю видео... Ищу полный трек.")
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        name = loop.run_until_complete(shazam_it(message.text))

        if not name:
            return bot.edit_message_text("❌ Не нашел такой трек в базе Shazam.", message.chat.id, status.message_id)

        bot.edit_message_text(f"✅ Нашел: {name}\n📥 Качаю полную версию...", message.chat.id, status.message_id)

        # Качаем полную версию из SoundCloud (там нет капчи YouTube)
        ydl_sc = {
            'format': 'bestaudio/best',
            'outtmpl': 'full.mp3',
            'default_search': 'scsearch1:', 
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '320'}],
            'quiet': True
        }

        with yt_dlp.YoutubeDL(ydl_sc) as ydl:
            ydl.download([f"scsearch1:{name}"])

        with open('full.mp3', 'rb') as a:
            bot.send_audio(message.chat.id, a, title=name, performer="Full Version")
        
        if os.path.exists('full.mp3'): os.remove('full.mp3')
        bot.delete_message(message.chat.id, status.message_id)

    except Exception as e:
        bot.edit_message_text(f"⚠ Ошибка: {str(e)}", message.chat.id, status.message_id)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.polling(none_stop=True)
