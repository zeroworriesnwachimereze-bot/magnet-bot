import os, threading, asyncio, requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask

TOKEN = os.environ.get("BOT_TOKEN")
WALLET = os.environ.get("WALLET") or "0x53d9382d995095f7724832449902783187953d"
ETHERSCAN_API_KEY = os.environ.get("ETHERSCAN_API_KEY")
users = {}

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot Running V4.1 - Magnet Fixed"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in users:
        users[uid] = {"balance": 0}
    keyboard = [
        [InlineKeyboardButton("💰 Deposit", callback_data="deposit")],
        [InlineKeyboardButton("💳 Balance", callback_data="balance")],
        [InlineKeyboardButton("👥 Referral", callback_data="referral")]
    ]
    await update.message.reply_text(f"Welcome to Magnet Bot V4.1 Fixed!\nWallet: {WALLET}\n\n✅ Bot Ready", reply_markup=InlineKeyboardMarkup(keyboard))

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
        await q.message.reply_text(f"Send to:\n{WALLET}\n\nAuto-detected via Etherscan.")
    elif d == "balance":
        bal = users.get(uid, {"balance": 0})["balance"]
        await q.message.reply_text(f"Balance: {bal}")
    elif d == "referral":
        uname = (await context.bot.get_me()).username
        await q.message.reply_text(f"Your link:\nhttps://t.me/{uname}?start={uid}")
    else:
        await q.message.reply_text("Plans coming soon")

async def run_bot():
    app_tg = Application.builder().token(TOKEN).build()
    app_tg.add_handler(CommandHandler("start", start))
    app_tg.add_handler(CommandHandler("balance", balance_cmd))
    app_tg.add_handler(CallbackQueryHandler(button_handler))
    print("Starting Bot polling... V4.1 Fixed", flush=True)
    await app_tg.bot.delete_webhook(drop_pending_updates=True)
    await app_tg.initialize()
    await app_tg.start()
    await app_tg.updater.start_polling(drop_pending_updates=True)
    await asyncio.Event().wait()

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(run_bot())
