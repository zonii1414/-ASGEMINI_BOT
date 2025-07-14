# Corrected imports and initial setup for your Gemini Telegram bot

import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Your Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyANNnLYicRZkbDCWrRc8EtkgvVBHPjDHaY")

# Define the start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to ADNAN AI! 🤖\nAsk me anything in English or Urdu!",
        parse_mode='Markdown'
    )

# Define the question handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    reply = ask_gemini(user_message)
    await update.message.reply_text(reply)

# Function to call Gemini API
def ask_gemini(message):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": message}]}],
        "generationConfig": {"temperature": 0.7}
    }
    try:
        response = requests.post(f"{url}?key={GEMINI_API_KEY}", json=data, headers=headers)
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return "⚠️ Gemini API error or limit reached."

# Main bot function
if __name__ == '__main__':
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()