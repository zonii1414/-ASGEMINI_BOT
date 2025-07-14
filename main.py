
import logging
import requests
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Tokens
TELEGRAM_TOKEN = "7865225217:AAFPf90LvkS26SielmfFPb2VhdYFapNNl24"
GEMINI_API_KEY = "AIzaSyCxyrh9fR81wvoI0u476R-y0VX0zZuS-TM"

# Flask app for keep-alive
app = Flask('')

@app.route('/')
def home():
    return "Gemini Telegram Bot is running!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run_web).start()

# Gemini API
def ask_gemini(prompt):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    headers = {"Content-Type": "application/json"}
    payload = { "contents": [{"parts": [{"text": prompt}]}] }
    response = requests.post(f"{url}?key={GEMINI_API_KEY}", headers=headers, json=payload)
    try:
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return "⚠️ Gemini API error or limit reached."

# Telegram Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Welcome to Gemini AI Bot! Ask me anything.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    await update.message.chat.send_action(action="typing")
    reply = ask_gemini(user_message)
    await update.message.reply_text(reply)

app_bot = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app_bot.add_handler(CommandHandler("start", start))
app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app_bot.run_polling()
