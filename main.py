from flask import Flask
from threading import Thread
import os, time, threading, requests
from pymongo import MongoClient
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is Live!"

def run_web():
    flask_app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

Thread(target=run_web, daemon=True).start()

import os
BOT_TOKEN = os.getenv("BOT_TOKEN")
WALLET = os.getenv("WALLET_ADDRESS", "T9yD8b8J39rH8XNoWaA7t2b1ad6bAdf7dF")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7355405895"))
MONGO_URL = os.getenv("MONGO_URL", "")
BSC_API = os.getenv("BSC_API", "")

# Mongo
if not MONGO_URL:
    print("WARNING: MONGO_URL not set!")
    users_col = None
else:
    client = MongoClient(MONGO_URL)
    db = client["magnet_bot"]
    users_col = db["users"]

def get_user(uid):
    if users_col is None:
        return {"_id": str(uid), "balance": 0.0, "deposited": 0.0}
    u = users_col.find_one({"_id": str(uid)})
    if not u:
        u = {"_id": str(uid), "balance": 0.0, "deposited": 0.0, "ref_by": None}
        users_col.insert_one(u)
    return u

def save_user(u):
    if users_col is not None:
        users_col.replace_one({"_id": u["_id"]}, u, upsert=True)

def main_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Deposit AUTO", callback_data="deposit"), InlineKeyboardButton("Plans", callback_data="plans")],
        [InlineKeyboardButton("Withdraw", callback_data="withdraw"), InlineKeyboardButton("My Investments", callback_data="myinv")]
    ])

async def start(update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    args = ctx.args
    user = get_user(uid)
    if args and args[0]!= str(uid) and not user.get('ref_by'):
        ref_id = args[0]
        user['ref_by'] = ref_id
        save_user(user)
    await update.message.reply_text(f"Magnet V10 FOREVER! Wallet: {WALLET}\nBalance: {user['balance']}", reply_markup=main_kb())

async def admin(update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID:
        return
    await update.message.reply_text("Admin OK")

async def button_handler(update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "balance":
        u = get_user(q.from_user.id)
        await q.message.reply_text(f"Balance: {u['balance']}")

def check_deposits(app_bot):
    print("Deposit checker started V10")
    while True:
        time.sleep(60)

if __name__ == "__main__":
    print("V10 FINAL - ADMIN - FOREVER LIVE - Starting...")
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN not set in Render!")
    else:
        application = Application.builder().token(BOT_TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("admin", admin))
        application.add_handler(CallbackQueryHandler(button_handler))
        threading.Thread(target=check_deposits, args=(application,), daemon=True).start()
        print("V10 FINAL - ADMIN - FOREVER LIVE")
        application.run_polling()
