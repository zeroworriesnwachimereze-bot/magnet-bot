import os
from flask import Flask
from threading import Thread
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
ADDR = "0x55d398326f99059fF775485246999027B3197955"

# storage
users = {}

flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return "Live"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Deposit", callback_data="dep"), InlineKeyboardButton("📊 Balance", callback_data="bal")],
        [InlineKeyboardButton("📈 Invest Plans", callback_data="plans"), InlineKeyboardButton("💸 Withdraw", callback_data="with")],
        [InlineKeyboardButton("👥 Referral", callback_data="ref")]
    ])

def get_user(uid):
    if uid not in users:
        users[uid] = {"balance": 0, "invested": 0, "profit": 0}
    return users[uid]

async def start(update, context):
    get_user(update.effective_user.id)
    await update.message.reply_text(f"Welcome to Magnet Investment Bot!\n\nUSDT BEP20: {ADDR}\n\nInvest and earn daily!", reply_markup=menu())

async def btns(update, context):
    q = update.callback_query
    await q.answer()
    u = get_user(q.from_user.id)

    if q.data == "dep":
        await q.edit_message_text(f"Send USDT BEP20 to:\n{ADDR}\n\nMin: 10 USDT\nAfter payment, contact admin", reply_markup=menu())
    elif q.data == "bal":
        await q.edit_message_text(f"Balance: {u['balance']} USDT\nInvested: {u['invested']} USDT\nProfit: {u['profit']} USDT", reply_markup=menu())
    elif q.data == "plans":
        txt = "PLANS:\n1. 50 USDT -> 10% daily for 10 days\n2. 100 USDT -> 12% daily for 15 days\n3. 500 USDT -> 15% daily for 20 days\n\nClick Deposit to start"
        await q.edit_message_text(txt, reply_markup=menu())
    elif q.data == "with":
        await q.edit_message_text(f"Withdraw:\nBalance: {u['balance']} USDT\n\nSend your USDT address to admin for withdrawal", reply_markup=menu())
    elif q.data == "ref":
        link = f"https://t.me/{context.bot.username}?start={q.from_user.id}"
        await q.edit_message_text(f"Referral Link:\n{link}\nEarn 10% of referral deposit!", reply_markup=menu())
    else:
        await q.edit_message_text(f"USDT: {ADDR}", reply_markup=menu())

def main():
    Thread(target=run_flask, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(btns))
    print("Bot started!")
    app.run_polling()

if __name__ == "__main__":
    main()
