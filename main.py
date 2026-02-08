import telebot
import yt_dlp
import os
import threading
from flask import Flask

app = Flask(__name__)
@app.route('/')
def hello(): return "Музыкальный поиск активен!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

TOKEN = '8512698228:AAFgjxxCBY0hnYqtVFD-pter14gKL5nCGd4'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(func=lambda message: 'tiktok.com' in message.text)
def download_all(message):
    msg = bot.reply_to(message, "🎬 Качаю видео и ищу полный трек... Погоди секунду!")
    try:
        # 1. Получаем инфо и видео
        ydl_opts_video = {'format': 'best', 'outtmpl': 'video.mp4', 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts_video) as ydl:
            info = ydl.extract_info(message.text, download=True)
            search_query = f"{info.get('artist', '')} {info.get('track', 'original sound')}"
            
        # 2. Ищем ПОЛНЫЙ трек на YouTube Music по названию
        ydl_opts_audio = {
            'format': 'bestaudio/best',
            'outtmpl': 'full_track.mp3',
            'default_search': 'ytsearch1:', # Ищем первый попавшийся оригинал
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '320'}],
            'quiet': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
            ydl.download([f"ytsearch1:{search_query}"])

        # Отправляем результаты
        with open('video.mp4', 'rb') as v:
            bot.send_video(message.chat.id, v, caption="✅ Видео готово")
        
        with open('full_track.mp3', 'rb') as a:
            bot.send_audio(message.chat.id, a, title=search_query, performer="Найдено в поиске")

        os.remove('video.mp4')
        os.remove('full_track.mp3')
        bot.delete_message(message.chat.id, msg.message_id)

    except Exception as e:
        bot.reply_to(message, f"Бро, не вышло найти оригинал: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.polling(none_stop=True)
