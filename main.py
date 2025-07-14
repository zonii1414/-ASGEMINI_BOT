import logging import json import requests from flask import Flask, request from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler

Tokens

TELEGRAM_TOKEN = "7865225217:AAFPf90LvkS26SielmfFPb2VhdYFapNNl24" GEMINI_API_KEY = "AIzaSyANNnLYicRZkbDCWrRc8EtkgvVBHPjDHaY"

Flask app for Render keep-alive

app = Flask(name)

@app.route('/') def home(): return "Bot is running."

Enable logging

logging.basicConfig( format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO ) logger = logging.getLogger(name)

Gemini API function

def ask_gemini(prompt): url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=" + GEMINI_API_KEY headers = {"Content-Type": "application/json"} payload = { "contents": [{"parts": [{"text": prompt}]}] } response = requests.post(url, headers=headers, json=payload) try: return response.json()['candidates'][0]['content']['parts'][0]['text'] except: return "⚠️ Gemini API error or limit reached."

/start command

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text( "👋 Welcome to ADNAN AI — your smart assistant!\n\nAsk me anything in English or Urdu.\nUse /help to view features.", parse_mode="Markdown")

/help command

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text( "🤖 Features of Adnan AI:\n\n" "1. Gemini AI Answering (English + Urdu)\n" "2. Inline Quiz Auto Answer (Experimental)\n" "3. Bollywood & Pakistani Songs 🎵 (Coming Soon)\n" "4. Works in Groups/Channels\n" "5. Welcome Messages\n\n" "Use /start to begin.", parse_mode="Markdown")

Handle messages (Gemini QA)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE): user_message = update.message.text response = ask_gemini(user_message) await update.message.reply_text(response)

Auto answer for inline quizzes

async def inline_answer(update: Update, context: ContextTypes.DEFAULT_TYPE): if update.message and update.message.text: text = update.message.text.lower() if 'answer' in text or 'solve' in text: messages = context.bot_data.get('inline_quiz', '') if messages: reply = ask_gemini(messages) await update.message.reply_text(reply)

Store forwarded quizzes in context

async def store_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE): if update.message and update.message.text and 'question' in update.message.text.lower(): context.bot_data['inline_quiz'] = update.message.text

Setup and run

async def main(): application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
application.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)(answer|solve)"), inline_answer))
application.add_handler(MessageHandler(filters.TEXT & filters.FORWARDED, store_quiz))

print("Bot started...")
await application.run_polling()

import asyncio if name == 'main': import threading threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start() asyncio.run(main())

