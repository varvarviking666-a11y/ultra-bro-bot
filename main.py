import telebot
import yt_dlp
import os
from flask import Flask
import threading

# Веб-сервер для поддержания жизни на Render
app = Flask(__name__)
@app.route('/')
def home(): return "AI Intelligence is Live"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

TOKEN = '8512698228:AAFgjxxCBY0hnYqtVFD-pter14gKL5nCGd4'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(func=lambda m: 'tiktok.com' in m.text)
def handle_tiktok(message):
    status = bot.reply_to(message, "🧠 ИИ извлекает информацию о треке...")
    
    try:
        url = message.text
        
        # 1. ИИ вытаскивает инфу напрямую из метаданных видео
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            # Берем название трека или автора из описания
            track_title = info.get('track') or info.get('alt_title') or info.get('title')
            artist = info.get('artist') or info.get('creator') or ""
            
            query = f"{artist} {track_title}".strip()
            
            if not query or "original sound" in query.lower():
                # Если в метаданных пусто, ИИ ищет по заголовку
                query = info.get('title').split('|')[0].replace('#', '').strip()

        bot.edit_message_text(f"🔍 Нашел информацию: **{query}**\n📥 Качаю полную версию...", message.chat.id, status.message_id, parse_mode="Markdown")

        # 2. Поиск и загрузка полной версии из облака (SoundCloud)
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'full_track.mp3',
            'default_search': 'scsearch1:',
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '320'}],
            'quiet': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"scsearch1:{query}"])
            
        # 3. Отправка файла
        with open('full_track.mp3', 'rb') as audio:
            bot.send_audio(message.chat.id, audio, title=query, performer="AI Intelligence")
            
        os.remove('full_track.mp3')
        bot.delete_message(message.chat.id, status.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ ИИ не смог вытащить инфу. Ошибка: {str(e)}", message.chat.id, status.message_id)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.polling(none_stop=True)
