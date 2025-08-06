import os
import logging
from dotenv import load_dotenv
import openai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def main_menu():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📥 Download Video", callback_data="download")],
            [InlineKeyboardButton("🎯 Topic Ideas", callback_data="topic")],
        ]
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(chat_id=f"@{CHANNEL_USERNAME}", user_id=user_id)
        if member.status not in ["member", "creator", "administrator"]:
            raise Exception("User not a member")
    except Exception:
        join_button = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔐 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME}")]]
        )
        await update.message.reply_text(
            "🔒 Please join our channel to use this bot.",
            reply_markup=join_button,
        )
        return

    await update.message.reply_text(
        "👋 Welcome to the Premium Bot!\n\nChoose an option below:",
        reply_markup=main_menu(),
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "download":
        await query.edit_message_text("📩 Send me a video link (YouTube Shorts, TikTok, Facebook)...")
    elif query.data == "topic":
        await query.edit_message_text("🧠 Send a keyword or phrase for topic suggestions...")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    try:
        member = await context.bot.get_chat_member(chat_id=f"@{CHANNEL_USERNAME}", user_id=user_id)
        if member.status not in ["member", "creator", "administrator"]:
            await update.message.reply_text(f"🔒 Please join our channel first: https://t.me/{CHANNEL_USERNAME}")
            return
    except Exception:
        await update.message.reply_text(f"🔒 Please join our channel first: https://t.me/{CHANNEL_USERNAME}")
        return

    # Check if text looks like URL for download
    if text.startswith("http"):
        await update.message.reply_text("🚧 Download feature coming soon!", reply_markup=main_menu())
        return

    # Otherwise assume topic suggestion
    await update.message.reply_text("⏳ Generating topic ideas... Please wait...")

    prompt = f"Generate 5 catchy and highly searchable YouTube video titles based on this keyword or phrase: '{text}'. List them with bullet points."

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250,
            timeout=10,
        )
        result = response.choices[0].message.content
        await update.message.reply_text(f"🎯 Topic Ideas:\n\n{result}", reply_markup=main_menu())
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        await update.message.reply_text(
            "⚠️ Sorry, there was an error fetching topic ideas. Please try again later.",
            reply_markup=main_menu(),
        )


if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running...")
    app.run_polling()
