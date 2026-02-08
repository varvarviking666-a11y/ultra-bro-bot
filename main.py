import telebot
import os
import subprocess
import requests
import random
from telebot import types

# --- НАСТРОЙКИ ---
TOKEN = '8512698228:AAFgjxxCBY0hnYqtVFD-pter14gKL5nCGd4'
AI_KEY = 'AIzaSyD4WqTDuqMGzs-NEB0kJy0kD5bX-uY4WNU'
bot = telebot.TeleBot(TOKEN)

chat_history = {}

def get_ai_answer(user_id, user_text):
    if user_id not in chat_history: chat_history[user_id] = []
    chat_history[user_id].append({"parts": [{"text": user_text}], "role": "user"})
    if len(chat_history[user_id]) > 10: chat_history[user_id] = chat_history[user_id][-10:]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={AI_KEY}"
    payload = {"contents": chat_history[user_id], "system_instruction": {"parts": [{"text": "Ты — крутой бро-помощник из Украины."}]}}
    try:
        r = requests.post(url, json=payload).json()
        ans = r['candidates'][0]['content']['parts'][0]['text']
        chat_history[user_id].append({"parts": [{"text": ans}], "role": "model"})
        return ans
    except: return "Бро, нейронка чет приуныла."

@bot.message_handler(func=lambda m: True)
def main_handler(m):
    text = m.text.lower() if m.text else ""
    if "стикер" in text:
        bot.reply_to(m, "Держи пачку! 🔥")
        packs = ['AnimeActions', 'MenheraChanAnimated', 'ChikaFujiwaraAni']
        for p in random.sample(packs, 2):
            try:
                s = bot.get_sticker_set(p)
                bot.send_sticker(m.chat.id, random.choice(s.stickers).file_id)
            except: continue
    elif 'tiktok.com' in text or 'douyin.com' in text:
        status = bot.reply_to(m, "📥 **Маскируюсь под человека и качаю...**")
        file = f"video_{m.chat.id}.mp4"
        try:
            # Улучшенный обход блокировок
            cmd = [
                'yt-dlp',
                '--no-check-certificate',
                '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                '-f', 'bv[ext=mp4]+ba[ext=m4a]/b[ext=mp4] / b',
                '-o', file,
                m.text
            ]
            subprocess.run(cmd, check=True)
            with open(file, 'rb') as v:
                bot.send_video(m.chat.id, v, caption="✅ Твой видос готов!")
            bot.delete_message(m.chat.id, status.message_id)
        except Exception as e:
            bot.reply_to(m, "❌ TikTok очень сильно защищается. Попробуй позже или скинь другую ссылку.")
        finally:
            if os.path.exists(file): os.remove(file)
    else:
        bot.reply_to(m, get_ai_answer(m.from_user.id, m.text))

if __name__ == '__main__':
    print("🚀 БОТ ЗАПУЩЕН! ЖДУ В ТЕЛЕГЕ")
    bot.polling(none_stop=True)
