import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from pytube import YouTube
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
    except:
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

# 📩 Handle Link
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_subscriber(user_id, context):
        await update.message.reply_text("🚫 Please join our channel first: https://t.me/" + CHANNEL_USERNAME)
        return

    link = update.message.text
    action = context.user_data.get('action')

    try:
        yt = YouTube(link)

        if action == 'get_title':
            result = f"{yt.title}"

        elif action == 'get_tags':
            result = ', '.join(yt.keywords)

        elif action == 'get_hashtags':
            result = ' '.join([f"#{tag.replace(' ', '').lower()}" for tag in yt.keywords])

        else:
            await update.message.reply_text("❗ Please select an option first using /start.")
            return

        # Result + Copy + Menu
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
        await update.message.reply_text(f"⚠️ Error: {e}")

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