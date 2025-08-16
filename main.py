import logging
import re
import uuid
from typing import Optional, List, Dict, Set

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    MessageEntity,
)
from telegram.constants import ChatMemberStatus
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)

# ============ CONFIG (filled with your details) ============
BOT_TOKEN = "7979451708:AAEnFsUpN1UEbUP8OOmf_ZjOiFLGj3FU17A"
ADMIN_USER_IDS = {6826147643, 8034801132}            # multiple admins supported
TARGET_CHANNEL = "-1002908737769"                     # post/edits will happen here (your group)

DELETE_AFTER = 300                                    # seconds (5 minutes)
LOG_CHAT_ID = None                                    # None => confirmations DM to first admin

# Mandatory Telegram joins (group/channel)
MANDATORY_TELEGRAM_CHATS = [
    {"title": "Join Our Group",  "chat_id": -1002908737769, "url": "https://t.me/LEGENDSTASK"},
]

# YouTube subscribe task
YOUTUBE_TASKS = [
    {"title": "Subscribe YouTube", "url": "https://www.youtube.com/@vampirelegendfamily"},
]

# What gets posted on approval (initial)
POST_TEMPLATE = (
    "RETWEET AND LIKE KRO JALDI SY 5 MINUTES KY ANDER ✅️🫆\n\n{link}"
)

# Edit after 5 minutes (remove link, show name)
EDIT_TEMPLATE = (
    "✅ TASK DONE — {name}\n"
    "DONE RETWEET AND LIKE TASK ✅️"
)
# ===========================================================

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("approval-bot")

# Conversation states
ASK_NAME, JOIN_TASKS, ASK_LINK = range(3)

URL_REGEX = re.compile(r"(https?://[^\s]+|www\.[^\s]+)", re.IGNORECASE)

# ---------- Helpers ----------
def extract_first_link(text: str, entities: Optional[List[MessageEntity]]) -> Optional[str]:
    if not text:
        return None
    if entities:
        for e in entities:
            if e.type == MessageEntity.TEXT_LINK and getattr(e, "url", None):
                return e.url
            if e.type == MessageEntity.URL:
                try:
                    return text[e.offset:e.offset + e.length]
                except Exception:
                    pass
    m = URL_REGEX.search(text)
    if m:
        link = m.group(0)
        if link.lower().startswith("www."):
            link = "https://" + link
        return link
    return None

def log_chat_id() -> int:
    # send confirmations either to LOG_CHAT_ID or first admin
    return LOG_CHAT_ID if LOG_CHAT_ID is not None else next(iter(ADMIN_USER_IDS))

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_USER_IDS

def get_tasks(context: ContextTypes.DEFAULT_TYPE) -> List[str]:
    return context.bot_data.get("task_links", [])

def set_tasks(context: ContextTypes.DEFAULT_TYPE, links: List[str]) -> None:
    context.bot_data["task_links"] = links[:5]

def add_task(context: ContextTypes.DEFAULT_TYPE, link: str) -> bool:
    links = get_tasks(context)
    if len(links) >= 5:
        return False
    links.append(link)
    set_tasks(context, links)
    return True

def clear_tasks(context: ContextTypes.DEFAULT_TYPE) -> None:
    context.bot_data["task_links"] = []

def kb_five_tasks(user_done: Set[int], links: List[str]) -> InlineKeyboardMarkup:
    rows = []
    for idx, link in enumerate(links):
        done = "✅ Done" if idx in user_done else "☑️ Mark Done"
        rows.append([
            InlineKeyboardButton(f"🔗 Open {idx+1}", url=link),
            InlineKeyboardButton(done, callback_data=f"taskdone:{idx}")
        ])
    return InlineKeyboardMarkup(rows)

def kb_join(join_done: Set[int], yt_done: Set[int]) -> InlineKeyboardMarkup:
    rows = []
    for idx, item in enumerate(MANDATORY_TELEGRAM_CHATS):
        jdone = "✅ Joined" if idx in join_done else "☑️ Check Join"
        rows.append([
            InlineKeyboardButton(f"➡️ {item['title']}", url=item["url"]),
            InlineKeyboardButton(jdone, callback_data=f"joinchk:{idx}")
        ])
    for idx, item in enumerate(YOUTUBE_TASKS):
        ydone = "✅ Subscribed" if idx in yt_done else "☑️ Mark Subscribed"
        rows.append([
            InlineKeyboardButton(f"▶️ {item['title']}", url=item["url"]),
            InlineKeyboardButton(ydone, callback_data=f"ytsub:{idx}")
        ])
    return InlineKeyboardMarkup(rows)

def joins_ok(context: ContextTypes.DEFAULT_TYPE) -> bool:
    return len(context.user_data.get("joins_done", set())) >= len(MANDATORY_TELEGRAM_CHATS)

def yt_ok(context: ContextTypes.DEFAULT_TYPE) -> bool:
    return len(context.user_data.get("yt_done", set())) >= len(YOUTUBE_TASKS)

# ---------- Start flow ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    submitted: Set[int] = context.bot_data.setdefault("submitted_users", set())
    if user.id in submitted:
        await update.message.reply_text("ALREADY YOU DO THIS TASK 🫆✅️")
        return ConversationHandler.END

    context.user_data.clear()
    context.user_data["tasks_done"] = set()
    context.user_data["joins_done"] = set()
    context.user_data["yt_done"] = set()

    await update.message.reply_text("👋 Welcome! Pehle apna **display name / username** bhejo (sirf text).")
    return ASK_NAME

async def got_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = (update.message.text or "").strip()
    if not name:
        await update.message.reply_text("❗️Naam sahi text me bhejo.")
        return ASK_NAME

    context.user_data["display_name"] = name
    await update.message.reply_text(
        f"✅ Name saved: **{name}**\n\n"
        "🔒 Pehle mandatory tasks complete karo:\n"
        "1) Telegram group/channel join\n"
        "2) YouTube channel subscribe (Mark Subscribed press karo)\n\n"
        "Phir main tumhe 5 task links dunga.",
        reply_markup=kb_join(set(), set()),
        disable_web_page_preview=True,
    )
    return JOIN_TASKS

# ---------- Join checks ----------
async def on_join_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    idx = int(q.data.split(":")[1])
    item = MANDATORY_TELEGRAM_CHATS[idx]

    try:
        member = await context.bot.get_chat_member(chat_id=item["chat_id"], user_id=q.from_user.id)
        joined = member.status in (
            ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR,
            ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED
        )
    except Exception as e:
        log.warning("get_chat_member failed: %s", e)
        joined = False

    if joined:
        context.user_data.setdefault("joins_done", set()).add(idx)

    try:
        await q.edit_message_reply_markup(
            reply_markup=kb_join(context.user_data.get("joins_done", set()),
                                 context.user_data.get("yt_done", set()))
        )
    except Exception:
        pass

    if joins_ok(context) and yt_ok(context):
        await show_five_tasks(q, context)

async def on_yt_sub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    idx = int(q.data.split(":")[1])
    context.user_data.setdefault("yt_done", set()).add(idx)

    try:
        await q.edit_message_reply_markup(
            reply_markup=kb_join(context.user_data.get("joins_done", set()),
                                 context.user_data.get("yt_done", set()))
        )
    except Exception:
        pass

    if joins_ok(context) and yt_ok(context):
        await show_five_tasks(q, context)

async def show_five_tasks(q_or_update, context: ContextTypes.DEFAULT_TYPE):
    links = get_tasks(context)
    if not links:
        txt = "⚠️ Admin ne abhi 5 tasks set nahi kiye. Admin: `/settasks` use karo."
        if hasattr(q_or_update, "message") and q_or_update.message:
            await q_or_update.message.reply_text(txt)
        return
    kb = kb_five_tasks(context.user_data.get("tasks_done", set()), links)
    if hasattr(q_or_update, "message") and q_or_update.message:
        await q_or_update.message.reply_text(
            "👇 Neeche 5 task links khol kar **Mark Done** karo. "
            "Sab khatam ho jaayen to apna link bhejna.",
            reply_markup=kb,
            disable_web_page_preview=True,
        )

# ---------- 5-link Tasks ----------
async def on_task_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    idx = int(q.data.split(":")[1])
    tasks = get_tasks(context)
    if idx < 0 or idx >= len(tasks):
        return

    done: Set[int] = context.user_data.setdefault("tasks_done", set())
    done.add(idx)

    try:
        await q.edit_message_reply_markup(reply_markup=kb_five_tasks(done, tasks))
    except Exception:
        pass

    if len(done) >= min(5, len(tasks)):
        await q.message.reply_text("🎉 All tasks completed! Ab apna **link** bhejo.")

# ---------- Link collection + approval ----------
async def got_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message

    if not (joins_ok(context) and yt_ok(context)):
        await msg.reply_text("🔒 Pehle mandatory join tasks complete karo.")
        return JOIN_TASKS

    tasks = get_tasks(context)
    done: Set[int] = context.user_data.get("tasks_done", set())
    if tasks and len(done) < min(5, len(tasks)):
        await msg.reply_text("⚠️ Pehle sab 5 tasks complete karo (Mark Done).")
        return ASK_LINK

    submitted: Set[int] = context.bot_data.setdefault("submitted_users", set())
    if update.effective_user.id in submitted:
        await msg.reply_text("ALREADY YOU DO THIS TASK 🫆✅️")
        return ConversationHandler.END

    text = msg.text or msg.caption or ""
    link = extract_first_link(text, msg.entities or msg.caption_entities)
    if not link:
        await msg.reply_text("❗️Koi valid link nahi mila. Sahi URL bhejo.")
        return ASK_LINK

    display_name = context.user_data.get("display_name", "Unknown")
    requester_id = update.effective_user.id

    req_id = str(uuid.uuid4())
    payload = {"req_id": req_id, "requester_id": requester_id, "display_name": display_name, "link": link}
    pending: Dict[str, dict] = context.bot_data.setdefault("pending_requests", {})
    pending[req_id] = payload

    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Approve", callback_data=f"approve:{req_id}"),
        InlineKeyboardButton("❌ Reject",  callback_data=f"reject:{req_id}"),
    ]])

    preview = (
        "📥 *New Link Request*\n"
        f"👤 From: `{display_name}` (ID: {requester_id})\n"
        f"🔗 Link: {link}\n\nApprove karun?"
    )
    # DM to all admins (first one is enough; sending to all is safer)
    for admin_id in ADMIN_USER_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id, text=preview, reply_markup=kb,
                disable_web_page_preview=False, parse_mode="Markdown",
            )
        except Exception as e:
            log.warning("Admin DM fail %s: %s", admin_id, e)

    await msg.reply_text("🕐 Link admin ko bhej diya gaya hai. Approval ka intezaar karein.")
    return ASK_LINK

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data or ""
    if data.startswith(("joinchk:", "ytsub:", "taskdone:")):
        return

    action, req_id = data.split(":", 1)
    pending = context.bot_data.get("pending_requests", {})
    payload = pending.get(req_id)
    if not payload:
        try: await q.edit_message_text("⏳ Ye request ab available nahi (maybe already processed).")
        except Exception: pass
        return

    requester_id = payload["requester_id"]
    display_name = payload["display_name"]
    link = payload["link"]
    log_chat = log_chat_id()

    if action == "reject":
        try:
            await context.bot.send_message(requester_id, "❌ Aapke link ko admin ne *reject* kar diya.", parse_mode="Markdown")
        except Exception: pass
        try: await q.edit_message_text("❌ Rejected.")
        except Exception: pass
        try:
            await context.bot.send_message(log_chat, f"❌ *REJECTED* — {display_name}\n🔗 {link}",
                                           parse_mode="Markdown", disable_web_page_preview=False)
        except Exception: pass
        pending.pop(req_id, None)
        return

    if action == "approve":
        try:
            post_text = POST_TEMPLATE.format(link=link)
            sent = await context.bot.send_message(chat_id=TARGET_CHANNEL, text=post_text, disable_web_page_preview=False)
            context.job_queue.run_once(
                edit_later, when=DELETE_AFTER,
                data=(str(TARGET_CHANNEL), sent.message_id, display_name),
                name=f"edit_{sent.chat.id}_{sent.message_id}",
            )
        except Exception as e:
            log.error("Post fail: %s", e)
            try: await q.edit_message_text("⚠️ Post fail ho gayi. Channel perms check karein.")
            except Exception: pass
            return

        try:
            await context.bot.send_message(requester_id,
                "✅ Aapka link *approve* ho gaya hai aur post ho chuka hai! "
                "(5 min baad message edit ho jayega — link remove ho jayega.)",
                parse_mode="Markdown")
        except Exception: pass

        try: await q.edit_message_text("✅ Approved & posted.")
        except Exception: pass

        try:
            await context.bot.send_message(
                chat_id=log_chat,
                text=f"✅ *ACCEPTED* — {display_name}\n🔗 {link}\nDONE RETWEET AND LIKE TASK ✅️",
                parse_mode="Markdown", disable_web_page_preview=False)
        except Exception: pass

        context.bot_data.setdefault("submitted_users", set()).add(requester_id)
        pending.pop(req_id, None)

# ---------- Jobs ----------
async def edit_later(context: ContextTypes.DEFAULT_TYPE):
    chat_id, message_id, display_name = context.job.data
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id, message_id=message_id,
            text=EDIT_TEMPLATE.format(name=display_name), disable_web_page_preview=True)
        log.info("Edited %s in %s", message_id, chat_id)
    except Exception as e:
        log.warning("Edit failed: %s", e)

# ---------- Admin commands ----------
async def settasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not update.message or not update.message.reply_to_message:
        await update.message.reply_text("Reply karo us message par jisme 1–5 links (har line me 1).")
        return
    text = update.message.reply_to_message.text or ""
    links = [ln.strip() for ln in text.splitlines() if ln.strip()]
    clean = []
    for ln in links:
        lnk = ln if ln.startswith("http") else ("https://" + ln if ln.startswith("www.") else ln)
        if URL_REGEX.search(lnk): clean.append(lnk)
    if not clean:
        await update.message.reply_text("Koi valid link nahi mila.")
        return
    set_tasks(context, clean[:5])
    await update.message.reply_text(f"✅ Tasks set. Count: {len(get_tasks(context))}")

async def addtask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("Use: /addtask <url>")
        return
    url = context.args[0].strip()
    if not URL_REGEX.search(url):
        await update.message.reply_text("Invalid URL.")
        return
    if url.lower().startswith("www."):
        url = "https://" + url
    if not add_task(context, url):
        await update.message.reply_text("Max 5 tasks allowed. Pehle /cleartasks karo.")
    else:
        await update.message.reply_text(f"✅ Added. Total: {len(get_tasks(context))}")

async def cleartasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    clear_tasks(context)
    await update.message.reply_text("🧹 Tasks cleared.")

async def showtasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    links = get_tasks(context)
    if not links:
        await update.message.reply_text("No tasks set.")
        return
    await update.message.reply_text("📋 Current tasks:\n" + "\n".join([f"{i+1}. {l}" for i, l in enumerate(links)]),
                                    disable_web_page_preview=False)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❎ Cancelled. `/start` se dobara shuru karein.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_name)],
            JOIN_TASKS: [],
            ASK_LINK: [MessageHandler((filters.TEXT | filters.Caption(True)) & ~filters.COMMAND, got_link)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(on_join_check, pattern=r"^joinchk:\d+$"))
    app.add_handler(CallbackQueryHandler(on_yt_sub,    pattern=r"^ytsub:\d+$"))
    app.add_handler(CallbackQueryHandler(on_task_done, pattern=r"^taskdone:\d+$"))
    app.add_handler(CallbackQueryHandler(on_callback,  pattern=r"^(approve|reject):"))

    app.add_handler(CommandHandler("settasks",   settasks))
    app.add_handler(CommandHandler("addtask",    addtask))
    app.add_handler(CommandHandler("cleartasks", cleartasks))
    app.add_handler(CommandHandler("showtasks",  showtasks))
    app.add_handler(CommandHandler("cancel",     cancel))

    log.info("Bot started.")
    app.run_polling(close_loop=False)

if __name__ == "__main__":
    main()