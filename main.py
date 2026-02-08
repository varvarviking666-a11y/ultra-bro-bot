import telebot
import yt_dlp
import os
import asyncio
from shazamio import Shazam
from flask import Flask
import threading

# Мини-сервер для Render, чтобы бот не засыпал
app = Flask(__name__)
@app.route('/')
def home(): return "AI-Bot is Online!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

TOKEN = '8512698228:AAFgjxxCBY0hnYqtVFD-pter14gKL5nCGd4'
bot = telebot.TeleBot(TOKEN)

async def ai_recognize(path):
    shazam = Shazam()
    res = await shazam.recognize_song(path)
    if res and res.get('track'):
        return f"{res['track']['subtitle']} - {res['track']['title']}"
    return None

@bot.message_handler(func=lambda m: 'tiktok.com' in m.text)
def ai_handler(message):
    status = bot.reply_to(message, "🤖 Мозги ИИ включены: обрабатываю твою ссылку...")
    
    try:
        video_file = 'video.mp4'
        audio_check = 'check.mp3'
        
        # 1. Качаем видео (лучшее качество)
        ydl_v_opts = {'format': 'best', 'outtmpl': video_file, 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_v_opts) as ydl:
            ydl.download([message.text])
        
        # 2. Быстро вырезаем 10 секунд для Shazam
        os.system(f"ffmpeg -i {video_file} -vn -t 10 -ar 44100 -ac 2 {audio_check} -y")
        
        # 3. Распознаем трек
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        track_name = loop.run_until_complete(ai_recognize(audio_check))

        # 4. Отправляем видео
        with open(video_file, 'rb') as v:
            bot.send_video(message.chat.id, v, caption="✅ Видео скачано через ИИ")

        # 5. Ищем и шлем ПОЛНЫЙ трек (SoundCloud)
        if track_name:
            bot.edit_message_text(f"🎵 ИИ нашел трек: {track_name}\nКачаю полную версию...", message.chat.id, status.message_id)
            ydl_sc_opts = {
                'format': 'bestaudio/best',
                'outtmpl': 'full.mp3',
                'default_search': 'scsearch1:', 
                'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '320'}],
                'quiet': True
            }
            with yt_dlp.YoutubeDL(ydl_sc_opts) as ydl:
                ydl.download([f"scsearch1:{track_name}"])
            
            with open('full.mp3', 'rb') as a:
                bot.send_audio(message.chat.id, a, title=track_name, performer="AI Full Music")
            os.remove('full.mp3')
        else:
            bot.edit_message_text("ℹ️ Видео готово. Полный трек в базе не найден.", message.chat.id, status.message_id)

        # Удаляем временные файлы
        for f in [video_file, audio_check]:
            if os.path.exists(f): os.remove(f)
            
    except Exception as e:
        bot.edit_message_text(f"❌ Ошибка ИИ: {str(e)}", message.chat.id, status.message_id)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.polling(none_stop=True)
