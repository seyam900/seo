import os
import re
from urllib.parse import urlparse, parse_qs
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from yt_dlp import YoutubeDL
from dotenv import load_dotenv

# Load env vars
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = "SL_TooL_HuB"  # Without '@'

# 🔘 SEO Menu
def get_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 Get Title", callback_data='get_title')],
        [InlineKeyboardButton("🏷️ Get Tags", callback_data='get_tags')],
        [InlineKeyboardButton("#️⃣ Get Hashtags", callback_data='get_hashtags')]
    ])

# 🔐 Channel Check
async def is_subscriber(user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=f"@{CHANNEL_USERNAME}", user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        print(f"[DEBUG] Channel check failed: {e}")
        return False

# 🚀 Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await is_subscriber(user_id, context):
        join_btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔐 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME}")],
            [InlineKeyboardButton("✅ I've Joined", callback_data='check_join')]
        ])
        await update.message.reply_text("🚫 You must join our premium channel to use this bot:", reply_markup=join_btn)
        return

    await update.message.reply_text(
        "👋 Welcome to *YouTube SEO Bot!*\n\n🔍 Just send a video link and select an option below:",
        reply_markup=get_menu(),
        parse_mode='Markdown'
    )

# ✅ Re-check Channel Join
async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()

    if not await is_subscriber(user_id, context):
        await query.edit_message_text("🚫 You are still not a member. Please join first: https://t.me/" + CHANNEL_USERNAME)
    else:
        await query.edit_message_text("✅ You're verified!\n\nPlease send a YouTube video link:")
        context.user_data['joined'] = True

# 🔘 Button Press
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if not await is_subscriber(user_id, context):
        await query.edit_message_text("🚫 Please join our channel first: https://t.me/" + CHANNEL_USERNAME)
        return

    context.user_data['action'] = query.data
    await query.edit_message_text("📩 Please send the YouTube video link:")

# ইউটিউব URL পরিষ্কার করার ফাংশন
def clean_youtube_url(url):
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    video_id = qs.get('v')
    if video_id:
        return f"https://www.youtube.com/watch?v={video_id[0]}"
    if parsed.netloc == 'youtu.be':
        video_id = parsed.path.lstrip('/')
        if video_id:
            return f"https://www.youtube.com/watch?v={video_id}"
    return url

# 📩 Handle Link using yt-dlp
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_subscriber(user_id, context):
        await update.message.reply_text("🚫 Please join our channel first: https://t.me/" + CHANNEL_USERNAME)
        return

    link = update.message.text.strip()
    print(f"[DEBUG] Raw user link: {link}")

    link = clean_youtube_url(link)
    print(f"[DEBUG] Cleaned link: {link}")

    action = context.user_data.get('action')
    if not action:
        await update.message.reply_text("❗ প্রথমে /start দিয়ে অপশন সিলেক্ট করুন।")
        return

    try:
        ydl_opts = {"quiet": True}
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)

        if action == 'get_title':
            result = info.get("title", "Title not found.")

        elif action == 'get_tags':
            tags = info.get("tags", [])
            result = ', '.join(tags) if tags else "No tags found."

        elif action == 'get_hashtags':
            tags = info.get("tags", [])
            result = ' '.join([f"#{tag.replace(' ', '').lower()}" for tag in tags]) if tags else "No hashtags found."

        else:
            await update.message.reply_text("❗ Invalid action.")
            return

        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 Copy", switch_inline_query=result)],
            [InlineKeyboardButton("🔁 Back to Menu", callback_data='menu')]
        ])

        await update.message.reply_text(
            f"✅ *Result:*\n```{result}```",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    except Exception as e:
        print(f"[DEBUG] yt-dlp error: {e}")
        await update.message.reply_text(f"⚠️ Error while processing video: {e}")

# 🔁 Menu Again
async def handle_menu_reload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await query.edit_message_text("🔘 Please select an option:", reply_markup=get_menu())

# Run Bot
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler, pattern="^(get_title|get_tags|get_hashtags)$"))
app.add_handler(CallbackQueryHandler(handle_menu_reload, pattern="^menu$"))
app.add_handler(CallbackQueryHandler(check_join, pattern="^check_join$"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

print("🤖 Bot is running...")
app.run_polling()
