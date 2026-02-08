import telebot
import yt_dlp
import os
from flask import Flask
import threading

app = Flask(__name__)
@app.route('/')
def home(): return "AI Music Bot is Running"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

TOKEN = '8512698228:AAFgjxxCBY0hnYqtVFD-pter14gKL5nCGd4'
bot = telebot.TeleBot(TOKEN)

def download_and_send(message):
    url = message.text
    msg = bot.reply_to(message, "⚡️ ИИ анализирует ссылку...")
    
    try:
        # 1. Получаем инфо о видео без скачивания самого видео
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            # Пытаемся достать название трека из метаданных TikTok
            track = info.get('track')
            artist = info.get('artist')
            
            if track and artist:
                query = f"{artist} - {track}"
            else:
                # Если метаданных нет, берем описание или название видео
                query = info.get('title', 'TikTok Music').split('|')[0].strip()

        bot.edit_message_text(f"🔍 Ищу полную версию: **{query}**", message.chat.id, msg.message_id, parse_mode="Markdown")

        # 2. Качаем ПОЛНЫЙ трек из SoundCloud (избегаем капчи YouTube)
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'song.mp3',
            'default_search': 'scsearch1:',
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '320'}],
            'quiet': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"scsearch1:{query}"])
            
        # 3. Отправляем файл
        with open('song.mp3', 'rb') as audio:
            bot.send_audio(message.chat.id, audio, title=query, performer="Full Track")
            
        os.remove('song.mp3')
        bot.delete_message(message.chat.id, msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ Не удалось найти чистый трек. Ошибка: {str(e)}", message.chat.id, msg.message_id)

@bot.message_handler(func=lambda m: 'tiktok.com' in m.text)
def handle_link(message):
    # Запускаем в отдельном потоке, чтобы бот не тупил
    threading.Thread(target=download_and_send, args=(message,)).start()

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.polling(none_stop=True)
