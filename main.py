import os
from dotenv import load_dotenv
from pytube import YouTube
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")


# ✅ Channel Verification
async def is_subscriber(user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=f"@{CHANNEL_USERNAME}", user_id=user_id)
        return member.status in ["member", "creator", "administrator"]
    except:
        return False


# ✅ Menu
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📌 Title", callback_data='get_title')],
        [InlineKeyboardButton("🏷️ Tags", callback_data='get_tags')],
        [InlineKeyboardButton("🔖 Hashtags", callback_data='get_hashtags')],
        [InlineKeyboardButton("🎯 Topic Ideas", callback_data='get_topics')]
    ])


# ✅ Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_subscriber(user_id, context):
        btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔐 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME}")]
        ])
        await update.message.reply_text(
            "🔒 Access Denied!\n\nJoin our channel to use this premium bot.",
            reply_markup=btn
        )
        return

    await update.message.reply_text(
        "🥇 *Welcome to Premium YouTube Tool Bot!*\n\nChoose a feature below 👇",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )


# ✅ Button Handler
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['action'] = query.data
    if query.data == "get_topics":
        await query.message.reply_text("🧠 Send a keyword or phrase to get topic ideas...")
    else:
        await query.message.reply_text("📥 Send the YouTube link...")


# ✅ Handle Text
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_subscriber(user_id, context):
        await update.message.reply_text("🚫 Join our channel first: https://t.me/" + CHANNEL_USERNAME)
        return

    action = context.user_data.get('action')
    msg = update.message.text

    # Topic Ideas Section
    if action == 'get_topics':
        topics = [
            f"{msg} tutorial for beginners",
            f"{msg} explained in detail",
            f"{msg} tips and tricks",
            f"how to master {msg}",
            f"{msg} 2025 trending guide"
        ]
        await update.message.reply_text(
            "📊 *Topic Ideas:*\n" + "\n".join([f"• {t}" for t in topics]),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔁 Back to Menu", callback_data='menu')]
            ])
        )
        return

    # YouTube Link Result Section
    try:
        yt = YouTube(msg)
        if action == 'get_title':
            result = yt.title

        elif action == 'get_tags':
            tags = yt.keywords
            result = "\n".join([f"{i+1}. {tag}" for i, tag in enumerate(tags)])

        elif action == 'get_hashtags':
            result = " ".join([f"#{tag.replace(' ', '').lower()}" for tag in yt.keywords])

        else:
            await update.message.reply_text("❗ Please select an option using /start.")
            return

        await update.message.reply_text(
            f"✅ *Result:*\n```{result}```",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📋 Copy", switch_inline_query=result)],
                [InlineKeyboardButton("🔁 Back to Menu", callback_data='menu')]
            ])
        )

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")


# ✅ Back to Menu
async def handle_menu_return(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("🔘 *Choose an option below:*", parse_mode="Markdown", reply_markup=main_menu())


# ✅ Bot Setup
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle_menu_return, pattern='menu'))
app.add_handler(CallbackQueryHandler(handle_button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.run_polling()
