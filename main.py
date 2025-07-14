import os
import json
import logging
import requests
from flask import Flask
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

# ==== CONFIG ====
TELEGRAM_TOKEN = "7865225217:AAFTDl0uGBt7M3wziTFiX4FAvFEqekI0Wpw"
GEMINI_API_KEY = "AIzaSyANNnLYicRZkbDCWrRc8EtkgvVBHPjDHaY"

# ==== FLASK SETUP ====
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ ADNAN AI is running!"

# ==== GEMINI FUNCTION ====
def ask_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(url, headers=headers, data=json.dumps(data))

    try:
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except:
        return "⚠️ Gemini API error or limit reached."

# ==== TELEGRAM HANDLERS ====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Welcome to *ADNAN AI Bot*!\nAsk anything in English or Urdu.\n\n🌍 Powered by Google Gemini", parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    reply = ask_gemini(user_input)
    await update.message.reply_text(reply)

# ==== RUN BOT ====
if __name__ == '__main__':
    import threading

    def run_flask():
        app.run(host='0.0.0.0', port=8080)

    threading.Thread(target=run_flask).start()

    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()