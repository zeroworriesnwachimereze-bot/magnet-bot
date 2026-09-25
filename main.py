import os, logging
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
ADDR = "0x1234567890ABCDEF1234567890ABCDEF12345678"

logging.basicConfig(level=logging.INFO)
web = Flask(__name__)
@web.route('/')
def h(): return "Live"
def run(): web.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

def menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("💰 Deposit", callback_data="d"), InlineKeyboardButton("💸 Withdraw", callback_data="w")],[InlineKeyboardButton("💳 Balance", callback_data="b")]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"👋 Welcome {update.effective_user.first_name}!\n\n💵 USDT BEP20 Bot is LIVE!\n\nAddress: `{ADDR}`\n\nClick below:", reply_markup=menu(), parse_mode="Markdown")

async def btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if q.data=="d": await q.edit_message_text(f"💰 Deposit to:\n`{ADDR}`\n\nNetwork: BEP20", parse_mode="Markdown")
    elif q.data=="w": await q.edit_message_text("💸 Send: withdraw ADDRESS AMOUNT")
    else: await q.edit_message_text("💳 Balance: 0 USDT")

def main():
    Thread(target=run, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(btn))
    app.run_polling()

if __name__=="__main__": main()
