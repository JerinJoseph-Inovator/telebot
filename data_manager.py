import logging
import os
import json

DATA_DIRECTORY = "user_data"  # Directory to store user-specific JSON files
LOG_FILE = "transaction_audit.log"

# Set up logging configuration
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Ensure the user data directory exists
if not os.path.exists(DATA_DIRECTORY):
    os.makedirs(DATA_DIRECTORY)

class DataManager:
    @staticmethod
    def load(user_id):
        user_file = os.path.join(DATA_DIRECTORY, f"user_{user_id}.json")

        # If the user's file doesn't exist, create default data
        if not os.path.exists(user_file):
            data = {
                "giftcards": ["Amazon", "Google"],
                "services": ["Netflix", "Prime Video"],
                "balances": {},
                "topups": [
                    "Bitcoin (BTC) Deposit",
                    "Ethereum (ETH) Deposit",
                    "USDT (TRC20) Deposit",
                    "Litecoin (LTC) Deposit",
                    "Tron (TRX) Deposit",
                    "Cash App Deposit"
                ],
                "main_menu": [
                    ["🎁 Gift Card", "🏷️ Apply Coupon"],
                    ["💸 Balance Top Ups", "👥 Referrals"],
                    ["🎬 Streaming Service"]
                ]
            }
            DataManager.save(user_id, data)
            return data

        with open(user_file, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def save(user_id, data):
        user_file = os.path.join(DATA_DIRECTORY, f"user_{user_id}.json")
        with open(user_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def log_transaction(action, user_id, txid, amount, status):
        """Log transaction to the audit log."""
        log_msg = f"User {user_id} | Action: {action} | TXID: {txid} | Amount: ${amount} | Status: {status}"
        logging.info(log_msg)
































# import logging
# import os
# import json

# DATA_FILE = "data.json"
# LOG_FILE = "transaction_audit.log"

# # Set up logging configuration
# logging.basicConfig(
#     filename=LOG_FILE,
#     level=logging.INFO,
#     format="%(asctime)s - %(message)s",
#     datefmt="%Y-%m-%d %H:%M:%S"
# )

# class DataManager:
#     @staticmethod
#     def load():
#         if not os.path.exists(DATA_FILE):
#             return {
#                 "giftcards": ["Amazon", "Google"],
#                 "services": ["Netflix", "Prime Video"],
#                 "balances": {},
#                 "topups": [
#                     "Bitcoin (BTC) Deposit",
#                     "Ethereum (ETH) Deposit",
#                     "USDT (TRC20) Deposit",
#                     "Litecoin (LTC) Deposit",
#                     "Tron (TRX) Deposit",
#                     "Cash App Deposit"
#                 ],
#                 "main_menu": [
#                     ["🎁 Gift Card", "🏷️ Apply Coupon"],
#                     ["💸 Balance Top Ups", "👥 Referrals"],
#                     ["🎬 Streaming Service"]
#                 ]
#             }
#         with open(DATA_FILE, "r", encoding="utf-8") as f:
#             return json.load(f)

#     @staticmethod
#     def save(data):
#         with open(DATA_FILE, "w", encoding="utf-8") as f:
#             json.dump(data, f, indent=4)

#     @staticmethod
#     def log_transaction(action, user_id, txid, amount, status):
#         """Log transaction to the audit log."""
#         log_msg = f"User {user_id} | Action: {action} | TXID: {txid} | Amount: ${amount} | Status: {status}"
#         logging.info(log_msg)
