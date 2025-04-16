# command_handlers.py
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from data_manager import DataManager
from menu_manager import MenuManager
from config import ADMINS
from telegram import ReplyKeyboardMarkup



class CommandHandlers:
    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['menu'] = 'main'
        data = DataManager.load()
        await update.message.reply_text("👋 Welcome!", reply_markup=ReplyKeyboardMarkup(MenuManager.main_menu(data), resize_keyboard=True))

    @staticmethod
    async def add_giftcard(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message.from_user.id not in ADMINS:
            return await update.message.reply_text("⛔ Unauthorized")
        if context.args:
            data = DataManager.load()
            new_card = " ".join(context.args)
            data["giftcards"].append(new_card)
            DataManager.save(data)
            await update.message.reply_text(f"✅ Gift card '{new_card}' added!")

    @staticmethod
    async def add_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message.from_user.id not in ADMINS:
            return await update.message.reply_text("⛔ Unauthorized")
        if context.args:
            data = DataManager.load()
            new_service = " ".join(context.args)
            data["services"].append(new_service)
            DataManager.save(data)
            await update.message.reply_text(f"✅ Streaming service '{new_service}' added!")

    @staticmethod
    async def show_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message.from_user.id not in ADMINS:
            return await update.message.reply_text("⛔ Unauthorized")
        data = DataManager.load()
        msg = "📥 Pending Transactions:\n"
        for user_id, info in data["balances"].items():
            for txn in info.get("transactions", []):
                if txn["status"] == "pending":
                    msg += f"User: {user_id}\nCrypto: {txn['crypto']}\nTXID: {txn['txid']}\nAmount: ${txn['amount']}\n\n"
        await update.message.reply_text(msg or "✅ No pending transactions.")

    
    @staticmethod
    async def handle_admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        data = DataManager.load()
        parts = query.data.split("|")
        action = parts[0]
        user_id = parts[1]
        txid = parts[2]
        
        user_data = data["balances"].get(user_id, {})
        note = parts[3] if len(parts) > 3 else None

        for txn in user_data.get("transactions", []):
            if txn["txid"] == txid:
                if action == "approve":
                    txn["status"] = "approved"
                    user_data["total_confirmed"] += txn["amount"]
                    await query.edit_message_text(
                        f"✅ Approved TXID: `{txid}`\n"
                        f"📝 Note: {note or 'No note provided'}",
                        parse_mode="Markdown"
                    )
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"🎉 Your transaction has been approved!\n"
                            f"Amount: ${txn['amount']} added to your balance.\n"
                            f"Note: {note or 'No note provided'}"
                    )
                elif action == "reject":
                    txn["status"] = "rejected"
                    await query.edit_message_text(
                        f"❌ Rejected TXID: `{txid}`\n"
                        f"📝 Note: {note or 'No note provided'}",
                        parse_mode="Markdown"
                    )
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"⚠️ Your transaction was rejected.\n"
                            f"Reason: {note or 'No reason provided'}\n"
                            f"Please contact support if you have questions."
                    )
                break

        DataManager.save(data)

    @staticmethod
    async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in ADMINS:
            return await update.message.reply_text("⛔ You are not authorized to access the admin panel.")

        keyboard = [
            ["📥 View Orders", "✅ Approve", "❌ Reject"],
            ["🏠 Main Menu"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await update.message.reply_text("👮 Welcome to the Admin Panel:", reply_markup=reply_markup)
        context.user_data["menu"] = "admin"
       