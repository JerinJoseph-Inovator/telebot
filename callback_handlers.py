# callback_handlers.py
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from data_manager import DataManager
from datetime import datetime
from config import ADMINS  # Import admin list for notifications
from enum import Enum
import logging

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

class TransactionStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class CallbackAction(Enum):
    APPROVE = "approve"
    REJECT = "reject"
    NOTE = "note"
    CANCEL_NOTE = "cancel_note"

class CallbackHandlers:
    @staticmethod
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        # Parse callback data
        callback_parts = query.data.split("_", 2)  # Split only on first two underscores
        
        if len(callback_parts) < 2:
            await query.edit_message_text("⚠️ Invalid callback data format")
            return
            
        action = callback_parts[0]
        
        # Handle cancel note action separately as it has a different format
        if action == CallbackAction.CANCEL_NOTE.value:
            return await CallbackHandlers._handle_cancel_note(query, context)
            
        if len(callback_parts) != 3:
            await query.edit_message_text("⚠️ Invalid callback data")
            return
            
        user_id = callback_parts[1]
        txid = callback_parts[2]  # Keep txid intact with any underscores it might contain
        
        # Load data
        try:
            data = DataManager.load()
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            await query.edit_message_text("⚠️ Error loading transaction data")
            return
            
        # Get transaction
        transaction = CallbackHandlers._get_transaction(data, user_id, txid)
        if not transaction:
            await query.edit_message_text("⚠️ Transaction not found!")
            return
            
        # Check transaction status
        if transaction["status"] != TransactionStatus.PENDING.value:
            await query.edit_message_text(f"⚠️ Transaction already {transaction['status']}")
            return
            
        # Handle different actions
        try:
            if action == CallbackAction.APPROVE.value:
                await CallbackHandlers._handle_approval(query, context, data, user_id, txid, transaction)
            elif action == CallbackAction.REJECT.value:
                await CallbackHandlers._handle_rejection(query, context, data, user_id, txid, transaction)
            elif action == CallbackAction.NOTE.value:
                await CallbackHandlers._handle_note_request(query, context, user_id, txid)
            else:
                await query.edit_message_text("⚠️ Unknown action")
        except Exception as e:
            logger.error(f"Error processing callback: {e}")
            await query.edit_message_text("⚠️ An error occurred while processing the request")

    @staticmethod
    def _get_transaction(data, user_id, txid):
        """Helper method to find a transaction by user_id and txid"""
        user_data = data['balances'].get(user_id, {"transactions": []})
        return next((t for t in user_data.get("transactions", []) if t["txid"] == txid), None)

    @staticmethod
    async def _handle_approval(query, context, data, user_id, txid, transaction):
        """Handle transaction approval"""
        # Update transaction
        transaction["status"] = TransactionStatus.APPROVED.value
        transaction["processed_at"] = datetime.now().isoformat()
        
        # Update user balance
        user_data = data['balances'].setdefault(user_id, {"transactions": [], "total_confirmed": 0})
        user_data["total_confirmed"] += transaction["amount"]
        
        # Save data
        DataManager.save(data)
        
        # Update admin message
        await query.edit_message_text(
            f"✅ Transaction approved!\n"
            f"• Amount: ${transaction['amount']}\n"
            f"• User: {user_id}\n"
            f"• TXID: {txid[:10]}...",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📝 Add Note", callback_data=f"note_{user_id}_{txid}")]
            ])
        )
        
        # Notify user
        await CallbackHandlers._notify_user(
            context, 
            user_id, 
            f"🎉 Your transaction has been approved!\n"
            f"• Amount: ${transaction['amount']}\n"
            f"• New balance: ${user_data['total_confirmed']:.2f}"
        )

    @staticmethod
    async def _handle_rejection(query, context, data, user_id, txid, transaction):
        """Handle transaction rejection"""
        # Update transaction
        transaction["status"] = TransactionStatus.REJECTED.value
        transaction["processed_at"] = datetime.now().isoformat()
        
        # Save data
        DataManager.save(data)
        
        # Update admin message
        await query.edit_message_text(
            f"❌ Transaction rejected!\n"
            f"• Amount: ${transaction['amount']}\n"
            f"• User: {user_id}\n"
            f"• TXID: {txid[:10]}...",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📝 Add Reason", callback_data=f"note_{user_id}_{txid}")]
            ])
        )
        
        # Notify user
        await CallbackHandlers._notify_user(
            context, 
            user_id,
            "⚠️ Your transaction was rejected.\n"
            "Please contact support if you believe this was a mistake."
        )

    @staticmethod
    async def _handle_note_request(query, context, user_id, txid):
        """Handle request to add a note to a transaction"""
        context.user_data['awaiting_note_for'] = f"{user_id}_{txid}"
        await query.edit_message_text(
            "✏️ Please reply with your note for this transaction:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Cancel", callback_data=f"cancel_note_{user_id}_{txid}")]
            ])
        )

    @staticmethod
    async def _handle_cancel_note(query, context):
        """Handle cancellation of note addition"""
        if 'awaiting_note_for' in context.user_data:
            del context.user_data['awaiting_note_for']
        await query.edit_message_text("📝 Note addition cancelled.")

    @staticmethod
    async def _notify_user(context, user_id, message):
        """Helper method to notify a user with error handling"""
        try:
            await context.bot.send_message(chat_id=user_id, text=message)
        except Exception as e:
            logger.error(f"Failed to notify user {user_id}: {e}")

    @staticmethod
    async def handle_note_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle admin reply with a note for a transaction"""
        if 'awaiting_note_for' not in context.user_data:
            return
            
        note_info = context.user_data['awaiting_note_for']
        if "_" not in note_info:
            await update.message.reply_text("⚠️ Invalid note format")
            del context.user_data['awaiting_note_for']
            return
            
        user_id, txid = note_info.split("_", 1)
        note = update.message.text
        
        try:
            # Load data
            data = DataManager.load()
            
            # Find transaction
            transaction = CallbackHandlers._get_transaction(data, user_id, txid)
            if not transaction:
                await update.message.reply_text("⚠️ Transaction not found")
                del context.user_data['awaiting_note_for']
                return
                
            # Add note
            transaction["admin_note"] = note
            DataManager.save(data)
            
            # Notify user if transaction was already processed
            if transaction["status"] in (TransactionStatus.APPROVED.value, TransactionStatus.REJECTED.value):
                await CallbackHandlers._notify_user(
                    context,
                    user_id,
                    f"📝 Admin note for your transaction:\n{note}"
                )
            
            # Confirm to admin
            await update.message.reply_text("📝 Note added to transaction!")
            
        except Exception as e:
            logger.error(f"Error adding note: {e}")
            await update.message.reply_text("⚠️ Error adding note")
        finally:
            del context.user_data['awaiting_note_for']