import logging import requests import json import threading from flask import Flask from telegram import Update, MessageEntity from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

Tokens

TELEGRAM_TOKEN = "7865225217:AAFPf90LvkS26SielmfFPb2VhdYFapNNl24" GEMINI_API_KEY = "AIzaSyANNnLYicRZkbDCWrRc8EtkgvVBHPjDHaY"

Keep Alive Flask App

app = Flask(name)

@app.route('/') def home(): return "ASGEMINI_BOT is running!"

Gemini API Call

def ask_gemini(prompt): url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}" headers = {"Content-Type": "application/json"} data = { "contents": [{"parts": [{"text": prompt}]}] } try: response = requests.post(url, headers=headers, data=json.dumps(data)) return response.json()["candidates"][0]["content"]["parts"][0]["text"] except Exception as e: return "⚠️ Gemini API error or limit reached."

Welcome command

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text( "✨ Welcome to ADNAN AI 🤖\n" "I'm your personal Gemini-powered assistant!\n\n" "📌 What I can do:\n" "- Ask me any question in English\n" "- Reply to a quiz with 'answer' and I’ll solve it\n" "- Send me a screenshot with a quiz\n" "- Use /help to learn more features", parse_mode="Markdown" )

Help command

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text( "📘 Help Menu\n" "1. Ask any question in English and get a Gemini AI response.\n" "2. Reply to a quiz message with '@ASGEMINI_BOT answer' to get the correct answer.\n" "3. Send a screenshot of a quiz; I’ll try to read and answer it.\n" "4. Use /about to know who created me.\n" "5. More updates coming soon!", parse_mode="Markdown" )

About command

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text( "ℹ️ About This Bot\n" "This bot is powered by Google Gemini Pro API.\n" "Created by Adnan.\n" "Built for fun and knowledge!", parse_mode="Markdown" )

Daily AI Tip command

async def tip_command(update: Update, context: ContextTypes.DEFAULT_TYPE): tips = [ "💡 AI Tip: Always double-check AI answers before using them in real work.", "💡 AI Tip: Use clear and specific prompts for better responses.", "💡 AI Tip: You can ask Gemini to summarize long texts or documents.", "💡 AI Tip: Combine AI with your creativity to build amazing projects.", ] import random await update.message.reply_text(random.choice(tips))

OCR function (text from image)

def extract_text_from_image(file_path): import pytesseract from PIL import Image try: img = Image.open(file_path) return pytesseract.image_to_string(img) except Exception as e: return "Unable to read image."

Message handler

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE): msg = update.message

# Case 1: Photo message (screenshot)
if msg.photo:
    photo_file = await msg.photo[-1].get_file()
    photo_path = "screenshot.jpg"
    await photo_file.download_to_drive(photo_path)
    text_from_image = extract_text_from_image(photo_path)
    reply = ask_gemini(text_from_image)
    await msg.reply_text(reply)
    return

# Case 2: Regular text
if msg.text and not msg.entities:
    reply = ask_gemini(msg.text)
    await msg.reply_text(reply)
    return

# Case 3: Quiz reply with "answer"
if msg.text and "answer" in msg.text.lower() and msg.reply_to_message:
    original = msg.reply_to_message.text
    if not original:
        await msg.reply_text("⚠️ Couldn't find quiz content.")
        return

    # Extract question and options
    question_part = original.split("📖 Question:")[-1].split("🔘")[0].strip()
    options = [line.strip() for line in original.split("🔘") if line.strip()]

    full_prompt = f"Question: {question_part}\nOptions:\n" + "\n".join(options) + "\nGive the correct option (A, B, C...) only."

    answer = ask_gemini(full_prompt)
    await msg.reply_text(f"✅ Gemini suggests: **{answer.strip()}**", parse_mode="Markdown")

Start Everything

if name == "main": def run_flask(): app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run_flask).start()

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("about", about_command))
app.add_handler(CommandHandler("tip", tip_command))
app.add_handler(MessageHandler(filters.ALL, handle_message))

app.run_polling()

