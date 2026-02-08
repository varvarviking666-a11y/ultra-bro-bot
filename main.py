import telebot
from telebot import types
import yt_dlp
import os
import threading
import asyncio
from shazamio import Shazam
from flask import Flask

app = Flask(__name__)
@app.route('/')
def hello(): return "VK-Style Bot is Live!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

TOKEN = '8512698228:AAFgjxxCBY0hnYqtVFD-pter14gKL5nCGd4'
bot = telebot.TeleBot(TOKEN)

# Временное хранилище найденных треков
user_tracks = {}

async def get_shazam_info(path):
    shazam = Shazam()
    out = await shazam.recognize_song(path)
    if out and out.get('track'):
        return f"{out['track']['subtitle']} {out['track']['title']}"
    return None

@bot.message_handler(func=lambda message: 'tiktok.com' in message.text)
def handle_tiktok(message):
    msg = bot.reply_to(message, "🎬 Обрабатываю видео...")
    try:
        ydl_opts = {'format': 'best', 'outtmpl': 'v.mp4', 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(message.text, download=True)
            video_file = 'v.mp4'
            audio_file = 'temp_audio.mp3'
            os.system(f"ffmpeg -i {video_file} -vn -ar 44100 -ac 2 -b:a 192k {audio_file} -y")

        # Шазамим
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        query = loop.run_until_complete(get_shazam_info(audio_file)) or info.get('track', 'Популярная музыка')

        # Ищем 5 вариантов на YouTube Music
        search_opts = {'format': 'bestaudio', 'quiet': True, 'default_search': 'ytsearch5'}
        with yt_dlp.YoutubeDL(search_opts) as ydl:
            search_results = ydl.extract_info(f"ytsearch5:{query}", download=False)['entries']

        # Создаем кнопки
        markup = types.InlineKeyboardMarkup()
        text_msg = f"🔍 Нашел варианты для: **{query}**\n\n"
        user_tracks[message.chat.id] = []

        for i, entry in enumerate(search_results):
            title = entry.get('title')[:40]
            duration = entry.get('duration_string', '0:00')
            text_msg += f"{i+1}. {title} ({duration})\n"
            user_tracks[message.chat.id].append(entry['webpage_url'])
            markup.add(types.InlineKeyboardButton(text=f"Скачать {i+1}", callback_data=f"track_{i}"))

        with open(video_file, 'rb') as v:
            bot.send_video(message.chat.id, v, caption="✅ Видео готово. Выбери полную версию музыки ниже:")
        
        bot.send_message(message.chat.id, text_msg, reply_markup=markup, parse_mode="Markdown")
        
        os.remove(video_file)
        os.remove(audio_file)
        bot.delete_message(message.chat.id, msg.message_id)

    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('track_'))
def callback_download(call):
    index = int(call.data.split('_')[1])
    url = user_tracks[call.message.chat.id][index]
    bot.answer_callback_query(call.id, "Загружаю полную версию...")
    
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'full.mp3',
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '320'}],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            with open('full.mp3', 'rb') as a:
                bot.send_audio(call.message.chat.id, a, title=info.get('title'), performer="Full Version")
        os.remove('full.mp3')
    except Exception as e:
        bot.send_message(call.message.chat.id, f"Не удалось скачать: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.polling(none_stop=True)
