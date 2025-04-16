# main.py
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from command_handlers import CommandHandlers
from message_handlers import MessageHandlers
from telegram.ext import CallbackQueryHandler
from telegram.ext import CallbackQueryHandler
from callback_handlers import CallbackHandlers
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")


if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", CommandHandlers.start))
    app.add_handler(CommandHandler("addgift", CommandHandlers.add_giftcard))
    app.add_handler(CommandHandler("addservice", CommandHandlers.add_service))
    app.add_handler(CommandHandler("showpending", CommandHandlers.show_pending))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, MessageHandlers.handle))
    app.add_handler(CallbackQueryHandler(CommandHandlers.handle_admin_action))
    app.add_handler(CallbackQueryHandler(CallbackHandlers.handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, CallbackHandlers.handle_note_reply))
    app.add_handler(CommandHandler("admin", CommandHandlers.admin))


    print("🤖 Bot is running...")
    app.run_polling()