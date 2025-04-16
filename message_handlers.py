from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from data_manager import DataManager
from menu_manager import MenuManager
from config import ADMINS
import re, datetime


class MessageHandlers:
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        user_id = str(update.message.from_user.id)
        data = DataManager.load()
        menu = context.user_data.get("menu", "main")

        # DEBUG: Show current user state
        print(f"DEBUG: Received text: {text}")
        print(f"DEBUG: context.user_data: {context.user_data}")

        # 🔥 Handle expected transaction submission first
        if context.user_data.get("expecting_tx"):
            return await MessageHandlers._handle_transaction_submission(update, context, data, user_id, text)

        # Back or Main Menu
        if text == "Back ↩️" or text == "🏠 Main Menu":
            return await MessageHandlers._go_to_main_menu(update, context, data)

        # Menu route dispatcher
        if menu == "main":
            return await MessageHandlers._handle_main_menu(update, context, data, text, user_id)
        elif menu == "giftcard":
            return await MessageHandlers._handle_giftcard(update, context, data, text)
        elif menu == "topups":
            return await MessageHandlers._handle_topups(update, context, data, text, user_id)
        elif menu == "referrals":
            return await MessageHandlers._handle_referrals(update, context)
        elif menu == "services":
            return await MessageHandlers._handle_services(update, context, data, text)


    # ---------- Menu Handlers ----------

    @staticmethod
    async def _go_to_main_menu(update, context, data):
        context.user_data['menu'] = 'main'
        return await update.message.reply_text("🏠 Back to main menu:", reply_markup=ReplyKeyboardMarkup(MenuManager.main_menu(data), resize_keyboard=True))

    @staticmethod
    async def _handle_main_menu(update, context, data, text, user_id):
        if text == "🎁 Gift Card":
            context.user_data['menu'] = 'giftcard'
            cards = [data['giftcards'][i:i + 2] for i in range(0, len(data['giftcards']), 2)]
            cards.append(["Back ↩️"])
            return await update.message.reply_text("🎁 Choose Gift Card:", reply_markup=ReplyKeyboardMarkup(cards, resize_keyboard=True))

        if text == "💸 Balance Top Ups":
            context.user_data['menu'] = 'topups'
            return await update.message.reply_text("💰 Choose top-up method:", reply_markup=ReplyKeyboardMarkup(MenuManager.topup_menu(data), resize_keyboard=True))

        if text == "👥 Referrals":
            context.user_data['menu'] = 'referrals'
            return await update.message.reply_text("👥 Referral menu (coming soon)", reply_markup=ReplyKeyboardMarkup([["Back ↩️"]], resize_keyboard=True))

        if text == "🎬 Streaming Service":
            context.user_data['menu'] = 'services'
            services = [data['services'][i:i + 2] for i in range(0, len(data['services']), 2)]
            services.append(["Back ↩️"])
            return await update.message.reply_text("🎬 Choose a streaming service:", reply_markup=ReplyKeyboardMarkup(services, resize_keyboard=True))

    @staticmethod
    async def _handle_giftcard(update, context, data, text):
        if text in data['giftcards']:
            await update.message.reply_text(f"✅ You selected {text}. Purchase flow coming soon!")

    @staticmethod
    async def _handle_services(update, context, data, text):
        if text in data['services']:
            await update.message.reply_text(f"🎬 You selected {text}. More features coming soon!")

    @staticmethod
    async def _handle_referrals(update, context):
        await update.message.reply_text("👥 Referral feature is under development.", reply_markup=ReplyKeyboardMarkup([["Back ↩️"]], resize_keyboard=True))

    @staticmethod
    async def _handle_topups(update, context, data, text, user_id):
        if "Deposit" in text:
            match = re.match(r"^(.*?)\s*(\(|Deposit)", text)
            coin = match.group(1).strip() if match else text.replace(" Deposit", "").strip()
            wallet_address = data.get("wallets", {}).get(coin, f"(dummy_wallet_address_for_{coin.lower()})")

            await update.message.reply_text(
                f"Send only {coin} to the address below and then send your transaction ID by typing it here.\n\n"
                f"💵 Minimum deposit: $100\n"
                f"🔗 Wallet Address: `{wallet_address}`\n\n"
                f"Once sent, click on Available Balance and then reply with your transaction hash/ID to submit.",
                parse_mode="Markdown"
            )
            context.user_data['expecting_tx'] = coin

        elif text == "Available balance":
            balance = data["balances"].get(user_id, {}).get("total_confirmed", 0)
            await update.message.reply_text(f"Balance: 💲{balance:.2f}")

        await update.message.reply_text(
            "🗒\nMade a Deposit? Enter transaction ID here.\n\n"
            "To obtain a <a href='https://youtu.be/yh6Oy-nkPd8?si=dhd_BSiE78-QIBsP'>transaction ID</a>, you can typically find it in your wallet or on the exchange platform.",
            parse_mode='HTML',
            disable_web_page_preview=True
        )

    @staticmethod
    async def _handle_transaction_submission(update, context, data, user_id, text):
        coin = context.user_data['expecting_tx']
        txid = text.strip()

        if not txid or len(txid) < 10:
            return await update.message.reply_text("⚠️ Invalid transaction ID format. Please check and try again.")

        for uid, info in data["balances"].items():
            for txn in info.get("transactions", []):
                if txn["txid"] == txid:
                    return await update.message.reply_text("⚠️ This transaction ID was already submitted.")

        if user_id not in data['balances']:
            data['balances'][user_id] = {"transactions": [], "total_confirmed": 0}

        transaction = {
            "crypto": coin,
            "txid": txid,
            "amount": 100,
            "status": "pending",
            "timestamp": datetime.datetime.now().isoformat()
        }

        data['balances'][user_id]['transactions'].append(transaction)
        DataManager.log_transaction("Transaction Submitted", user_id, txid, 100, "pending")
        DataManager.save(data)
        context.user_data['expecting_tx'] = None

        await update.message.reply_text(
            "📝 Transaction submitted for admin review. You'll be notified when processed.\n\n"
            "⚠️ Note: Processing may take up to 24 hours."
        )

        user = update.message.from_user
        username = f"@{user.username}" if user.username else "No username"
        msg = (
            f"🚨 *New Transaction Submitted!*\n\n"
            f"👤 User: {user.first_name} {user.last_name or ''} ({username})\n"
            f"🆔 User ID: `{user.id}`\n"
            f"🪙 Crypto: {coin}\n"
            f"🔗 TXID: `{txid}`\n"
            f"💵 Amount: $100\n"
            f"🕐 Submitted: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"📊 Status: Pending"
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve|{user.id}|{txid}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject|{user.id}|{txid}")
            ],
            [InlineKeyboardButton("📝 Add Note", callback_data=f"note|{user.id}|{txid}")]
        ])

        for admin_id in ADMINS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=msg,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
            except Exception as e:
                print(f"Failed to notify admin {admin_id}: {e}")
