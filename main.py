import os
import subprocess
import requests
from aiogram import Bot, Dispatcher, executor, types

# Твой токен вставлен напрямую
API_TOKEN = "8512698228:AAFgjxxCBY0hnYqtVFD-pter14gKL5nCGd4"
AUDD_API_KEY = os.getenv("AUDD_API_KEY") # ключ для аудио-распознавания

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply("Привет! Скинь ссылку на видео, я попробую найти музыку 🎵")

@dp.message_handler()
async def handle_video(message: types.Message):
    url = message.text.strip()
    await message.reply("Скачиваю видео...")

    # Скачиваем видео и аудио
    subprocess.run(["yt-dlp", "-f", "bestaudio", "-o", "audio.mp3", url])

    await message.reply("Ищу музыку...")

    # Отправляем аудио в Audd.io
    with open("audio.mp3", "rb") as f:
        response = requests.post("https://api.audd.io/", data={
            "api_token": AUDD_API_KEY,
            "return": "apple_music,spotify"
        }, files={"file": f})

    result = response.json()
    if result.get("result"):
        track = result["result"]["title"]
        artist = result["result"]["artist"]
        await message.reply(f"Нашёл: {artist} – {track}")
    else:
        await message.reply("Не удалось распознать трек 😔")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
