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
def hello(): return "VK-Style Full Music Bot is Live!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

TOKEN = '8512698228:AAFgjxxCBY0hnYqtVFD-pter14gKL5nCGd4'
bot = telebot.TeleBot(TOKEN)

# Хранилище ссылок на полные треки
user_data = {}

async def get_track_name(path):
    shazam = Shazam()
    out = await shazam.recognize_song(path)
    if out and out.get('track'):
        return f"{out['track']['subtitle']} {out['track']['title']}"
    return None

@bot.message_handler(func=lambda message: 'tiktok.com' in message.text)
def handle_tiktok(message):
    msg = bot.reply_to(message, "🔎 Ищу полную версию трека, подожди...")
    try:
        # 1. Качаем только звук из ТТ для распознавания
        ydl_opts_small = {'format': 'wa', 'outtmpl': 'short.mp3', 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts_small) as ydl:
            ydl.download([message.text])
        
        # 2. Узнаем название через Shazam
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        query = loop.run_until_complete(get_track_name('short.mp3'))
        os.remove('short.mp3')

        if not query:
            return bot.edit_message_text("❌ Не смог распознать музыку в этом видео.", message.chat.id, msg.message_id)

        # 3. Ищем 5 ПОЛНЫХ вариантов на YouTube Music
        search_opts = {'format': 'bestaudio', 'quiet': True, 'default_search': 'ytsearch5'}
        with yt_dlp.YoutubeDL(search_opts) as ydl:
            results = ydl.extract_info(f"ytsearch5:{query} full version", download=False)['entries']

        # 4. Меню выбора
        markup = types.InlineKeyboardMarkup()
        text_menu = f"🎵 **Результаты поиска для:**\n_{query}_\n\n"
        user_data[message.chat.id] = []

        for i, item in enumerate(results):
            title = item.get('title')[:45]
            duration = item.get('duration_string', '0:00')
            text_menu += f"{i+1}. {title} [{duration}]\n"
            user_data[message.chat.id].append({'url': item['webpage_url'], 'title': title})
            markup.add(types.InlineKeyboardButton(text=f"Скачать вариант {i+1}", callback_data=f"dl_{i}"))

        bot.delete_message(message.chat.id, msg.message_id)
        bot.send_message(message.chat.id, text_menu, reply_markup=markup, parse_mode="Markdown")

    except Exception as e:
        bot.reply_to(message, f"Ошибка поиска: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('dl_'))
def download_full_track(call):
    idx = int(call.data.split('_')[1])
    track_info = user_data[call.message.chat.id][idx]
    bot.answer_callback_query(call.id, "Начинаю загрузку полной версии...")
    
    try:
        ydl_opts_full = {
            'format': 'bestaudio/best',
            'outtmpl': 'full_music.mp3',
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '320'}],
        }
        with yt_dlp.YoutubeDL(ydl_opts_full) as ydl:
            ydl.download([track_info['url']])
            with open('full_music.mp3', 'rb') as a:
                bot.send_audio(call.message.chat.id, a, title=track_info['title'], performer="Full Track Found")
        os.remove('full_music.mp3')
    except Exception as e:
        bot.send_message(call.message.chat.id, f"Ошибка загрузки: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.polling(none_stop=True)
