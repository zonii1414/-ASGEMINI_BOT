import os import logging import requests from telegram import Update from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

Gemini and ChatGPT API keys

GEMINI_API_KEYS = [ "AIzaSyANNnLYicRZkbDCWrRc8EtkgvVBHPjDHaY",  # More keys can be added here ] CHATGPT_API_KEY = "your_chatgpt_api_key_here" GEMINI_INDEX = 0

Welcome message handler

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text( "👋 Welcome to ADNAN AI!\n\n🤖 Ask questions in English or Urdu. I will reply smartly using Gemini or ChatGPT.", parse_mode="Markdown" )

Gemini fallback logic

async def query_gemini(prompt: str): global GEMINI_INDEX for _ in range(len(GEMINI_API_KEYS)): api_key = GEMINI_API_KEYS[GEMINI_INDEX] GEMINI_INDEX = (GEMINI_INDEX + 1) % len(GEMINI_API_KEYS) try: url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}" response = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}) if response.status_code == 200: return response.json()["candidates"][0]["content"]["parts"][0]["text"] except: continue return None

ChatGPT Fallback

async def query_chatgpt(prompt: str): try: url = "https://api.openai.com/v1/chat/completions" headers = { "Authorization": f"Bearer {CHATGPT_API_KEY}", "Content-Type": "application/json" } data = { "model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": prompt}] } response = requests.post(url, headers=headers, json=data) if response.status_code == 200: return response.json()['choices'][0]['message']['content'] except: return None

General message handler (includes Urdu/English)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE): prompt = update.message.text reply = await query_gemini(prompt) if not reply: reply = await query_chatgpt(prompt) if not reply: reply = "⚠️ AI services are currently busy. Try again shortly." await update.message.reply_text(reply)

Detect and store quiz-style questions in groups/channels

async def handle_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE): if update.message and update.message.text: text = update.message.text.lower() if any(x in text for x in ["quiz", "question", "options"]): context.chat_data['last_quiz'] = update.message.text

When someone says "answer" or "solve", reply with answer

async def answer_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE): text = context.chat_data.get('last_quiz') if text: response = await query_gemini(text) await update.message.reply_text(response) else: await update.message.reply_text("📌 Please forward or mention the quiz first.")

Bot main setup

if name == 'main': logging.basicConfig(level=logging.INFO) TOKEN = "your_telegram_bot_token_here" app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)(answer|solve)"), answer_quiz))
app.add_handler(MessageHandler(filters.TEXT & filters.FORWARDED, handle_quiz))

print("✅ ADNAN AI is now running!")
app.run_polling()

