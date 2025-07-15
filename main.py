import logging
import requests
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler

# 🔐 API keys
DEEPSEEK_API_KEY = "sk-c2abdcaabd594f80bd90d37863c22472"
TELEGRAM_BOT_TOKEN = "8042316891:AAF42eRD-GZjyKQBDkheVHUm9wWx17yf0z4"

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 🎯 DeepSeek AI request
def call_deepseek(prompt):
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        raise Exception("DeepSeek API error")

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("💬 Ask AI", callback_data='ask')],
        [InlineKeyboardButton("📢 Add Me to Group", url=f"https://t.me/{context.bot.username}?startgroup=true")],
    ]
    await update.message.reply_text(
        f"👋 Hello {user.first_name}, welcome to DeepSeek AI Bot!\nAsk me anything!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Button press handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "ask":
        await query.edit_message_text("📝 Please type your question now:")

# Message text handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    try:
        reply = call_deepseek(user_message)
    except Exception:
        reply = "⚠️ DeepSeek API failed. Try again later."
    await update.message.reply_text(reply)

# Auto greet when added to group
async def added_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type in ["group", "supergroup"]:
        await context.bot.send_message(chat_id=chat.id, text="🤖 I'm ready to assist with DeepSeek AI! Just type your question.")

# Bot launch
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, added_to_group))
    app.run_polling()