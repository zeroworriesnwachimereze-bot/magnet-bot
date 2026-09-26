import os
import time
import threading
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask

TOKEN = os.environ.get("BOT_TOKEN")
WALLET = os.environ.get("WALLET") or "0x55d398326f99059fF775485246999027B3197955"
app = Flask(__name__)
users = {}

@app.route('/')
def home():
    return "Bot is running"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users.setdefault(user_id, {"balance": 0})
    await update.message.reply_text("Welcome!")

async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bal = users.get(user_id, {"balance": 0})["balance"]
    await update.message.reply_text(f"Balance: {bal}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    if data == "deposit":
        await query.message.reply_text(f"Send to {WALLET}")
    elif data == "balance":
        bal = users.get(user_id, {"balance": 0})["balance"]
        await query.message.reply_text(f"Balance: {bal}")
    elif data == "referral":
        username = (await context.bot.get_me()).username
        link = f"https://t.me/{username}?start={user_id}"
        await query.message.reply_text(f"Your link: {link}")
    elif data == "plans":
        await query.message.reply_text("Plans coming soon")

def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    while True:
        try:
            print("Starting Bot polling...", flush=True)
            application = Application.builder().token(TOKEN).build()
            application.add_handler(CommandHandler("start", start))
            application.add_handler(CommandHandler("balance", balance_cmd))
            application.add_handler(CallbackQueryHandler(button_handler))
            application.run_polling()
        except Exception as e:
            print(f"Crashed {e}", flush=True)
            time.sleep(5)

if __name__ == '__main__':
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
