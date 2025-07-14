import logging
import requests
import json
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Tokens
TELEGRAM_TOKEN = "7865225217:AAFPf90LvkS26SielmfFPb2VhdYFapNNl24"
GEMINI_API_KEY = AIzaSyANNnLYicRZkbDCWrRc8EtkgvVBHPjDHaY

# Flask for keep alive
app = Flask('')

@app.route('/')
def home():
    return "ASGEMINI_BOT is running!"

# Gemini call
def ask_gemini(prompt):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=" + GEMINI_API_KEY
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    try:
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except:
        return "⚠️ Gemini API error or limit reached."

# Telegram handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    reply = ask_gemini(user_text)
    await update.message.reply_text(reply)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Welcome to ASGEMINI_BOT!\nSend me any question or message and I’ll reply using Google Gemini AI.")

# Start bot app
if __name__ == '__main__':
    import threading
    def run_flask():
        app.run(host='0.0.0.0', port=8080)
    threading.Thread(target=run_flask).start()

    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()
