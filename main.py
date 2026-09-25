import os, logging
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
USDT_ADDR = "0x55d398326f99059fF775485246999027B3197955"

logging.basicConfig(level=logging.INFO)

app_flask = Flask(__name__)
@app_flask.route('/')
def home(): return "Bot is Live!"

def run_flask():
    app_flask.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Deposit", callback_data="deposit")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("💳 Balance", callback_data="balance")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"👋 Welcome {update.effective_user.first_name}!\n\n"
        f"💵 *USDT BEP20 Bot is ONLINE!*\n\n"
        f"Your deposit address:\n`{USDT_ADDR}`\n"
        f"Network: BEP20\n\nChoose:",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "deposit":
        await q.edit_message_text(f"💰 Deposit USDT BEP20 to:\n`{USDT_ADDR}`", parse_mode="Markdown")
    elif q.data == "withdraw":
        await q.edit_message_text("💸 Use: /withdraw ADDRESS AMOUNT")
    else:
        await q.edit_message_text("💳 Balance: 0.00 USDT")

def main():
    Thread(target=run_flask, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    print("Bot started!")
    app.run_polling()

if __name__ == "__main__":
    main()
