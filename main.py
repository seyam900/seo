import logging
logging.basicConfig(level=logging.DEBUG)
import os
from dotenv import load_dotenv
import openai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")
openai.api_key = os.getenv("OPENAI_API_KEY")

def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_member = context.bot.get_chat_member(chat_id=f"@{CHANNEL_USERNAME}", user_id=user_id)
    if chat_member.status in ["member", "creator", "administrator"]:
        keyboard = [
            [InlineKeyboardButton("📥 Download Video", callback_data='download')],
            [InlineKeyboardButton("🎯 Topic Ideas", callback_data='topic')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="💎 *Welcome to Premium Downloader Bot!*\n\nSelect an option below ⬇️",
                                 parse_mode='Markdown', reply_markup=reply_markup)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="🔒 To use this bot, please join our channel first:\n👉 https://t.me/" + CHANNEL_USERNAME)

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    if query.data == 'download':
        query.edit_message_text("📥 Please send the video link (YouTube Shorts, TikTok, etc.)")
    elif query.data == 'topic':
        query.edit_message_text("🎯 Send me a topic or keyword, and I’ll suggest the most searched titles!")

def handle_message(update: Update, context: CallbackContext):
    user_input = update.message.text
    if "youtu" in user_input or "tiktok" in user_input:
        update.message.reply_text("🚀 Downloading your video... (Feature coming soon!)")
    else:
        update.message.reply_text("🤖 Generating topic ideas... Please wait...")
        prompt = f"""You are a YouTube SEO expert. Given the keyword: "{user_input}", suggest 5 highly searchable YouTube video title ideas. Format them as a list."""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300
            )
            ideas = response.choices[0].message.content
            update.message.reply_text(f"🎯 *Top Topic Ideas for:* `{user_input}`\n\n{ideas}",
                                      parse_mode='Markdown')
        except Exception as e:
            update.message.reply_text("❌ Something went wrong. Try again later.")

    # Show menu again
    keyboard = [
        [InlineKeyboardButton("📥 Download Video", callback_data='download')],
        [InlineKeyboardButton("🎯 Topic Ideas", callback_data='topic')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="📌 *Menu:* Choose an option below.",
                             parse_mode='Markdown', reply_markup=reply_markup)

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

