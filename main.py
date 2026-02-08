import telebot
import yt_dlp
import os
import asyncio
from shazamio import Shazam
from flask import Flask
import threading

# Настройка веб-сервера для Render
app = Flask(__name__)
@app.route('/')
def home(): return "AI-Shazam Bot is Active!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

TOKEN = '8512698228:AAFgjxxCBY0hnYqtVFD-pter14gKL5nCGd4'
bot = telebot.TeleBot(TOKEN)

async def recognize_audio(path):
    shazam = Shazam()
    res = await shazam.recognize_song(path)
    if res and res.get('track'):
        return f"{res['track']['subtitle']} - {res['track']['title']}"
    return None

@bot.message_handler(func=lambda m: 'tiktok.com' in m.text)
def handle_tiktok(message):
    status = bot.reply_to(message, "⚙️ ИИ в деле: качаю видео и ищу трек...")
    
    try:
        # 1. Качаем видео и звук отдельно
        video_path = 'final_video.mp4'
        audio_path = 'check_audio.mp3'
        
        # Опции для видео
        ydl_v_opts = {'format': 'bestvideo+bestaudio/best', 'outtmpl': video_path, 'quiet': True}
        # Опции для поиска оригинала в SoundCloud (минуя YouTube)
        ydl_sc_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'full_track.mp3',
            'default_search': 'scsearch1:', 
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '320'}],
            'quiet': True
        }

        with yt_dlp.YoutubeDL(ydl_v_opts) as ydl:
            ydl.download([message.text])
        
        # Извлекаем быстрый кусок звука для Shazam
        os.system(f"ffmpeg -i {video_path} -vn -t 10 -ar 44100 -ac 2 {audio_path} -y")
        
        # 2. Узнаем название через Shazam
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        track_name = loop.run_until_complete(recognize_audio(audio_path))

        # 3. Отправляем видео
        with open(video_path, 'rb') as v:
            bot.send_video(message.chat.id, v, caption="✅ Видео готово")

        # 4. Если трек найден, ищем и шлем полную версию
        if track_name:
            bot.edit_message_text(f"🔍 Нашел трек: {track_name}\nДостаю полную версию...", message.chat.id, status.message_id)
            with yt_dlp.YoutubeDL(ydl_sc_opts) as ydl:
                ydl.download([f"scsearch1:{track_name}"])
            
            with open('full_track.mp3', 'rb') as a:
                bot.send_audio(message.chat.id, a, title=track_name, performer="AI Full Version")
            os.remove('full_track.mp3')
        else:
            bot.edit_message_text("🤷‍♂️ Оригинал в базе не найден, прислал только видео.", message.chat.id, status.message_id)

        # Чистим мусор
        for f in [video_path, audio_path]:
            if os.path.exists(f): os.remove(f)
            
    except Exception as e:
        bot.edit_message_text(f"❌ Сбой: {str(e)}", message.chat.id, status.message_id)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.polling(none_stop=True)
