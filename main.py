import os, time, threading, logging
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
TOKEN = os.environ.get("BOT_TOKEN")
WALLET = "0x55d398326f99059fF775485246999027B3197955"
print(f"TOKEN OK: {bool(TOKEN)}", flush=True)

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is Running! Magnet Bot Live!"

# Database simple
users = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users[user_id] = users.get(user_id, {"balance": 0.0})

    # Check referral
    if context.args:
        ref_id = int(context.args[0])
        if ref_id!= user_id and ref_id in users:
            users[ref_id]["balance"] += 0.5
            await context.bot.send_message(ref_id, f"🎉 New referral! +$0.50! Balance: ${users[ref_id]['balance']}")

    keyboard = [
        [InlineKeyboardButton("💰 Deposit", callback_data="deposit"),
         InlineKeyboardButton("💳 Balance", callback_data="balance")],
        [InlineKeyboardButton("👥 Referral", callback_data="referral"),
         InlineKeyboardButton("📋 Plans", callback_data="plans")]
    ]
    text = f"🔥 Welcome to Dans la magnette Bot!\n\nYour ID: {user_id}\n\n💰 Earn money by referrals!\n\nUSDT Wallet for deposits:\n`{WALLET}`"
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bal = users.get(user_id, {"balance": 0.0})["balance"]
    await update.message.reply_text(f"💰 Your Balance: ${bal:.2f}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    bal = users.get(user_id, {"balance": 0.0})["balance"]

    if query.data == "deposit":
        await query.message.reply_text(f"💳 Deposit to:\n\nUSDT (BEP20):\n`{WALLET}`\n\nSend screenshot after payment!", parse_mode="Markdown")
    elif query.data == "balance":
        await query.message.reply_text(f"💰 Balance: ${bal:.2f}\n\nRefer friends to earn!")
    elif query.data == "referral":
        bot_username = (await context.bot.get_me()).username
        link = f"https://t.me/{bot_username}?start={user_id}"
        await query.message.reply_text(f"👥 Your Referral Link:\n{link}\n\nEarn $0.50 per friend!")
    elif query.data == "plans":
        await query.message.reply_text("📋 Plans:\n\nFree: Earn by referrals\nBasic $10: 2x earnings\nPro $50: 5x")

def run_bot():
    while True:
        try:
            print("Starting Bot polling...", flush=True)
            application = Application.builder().token(TOKEN).build()
            application.add_handler(CommandHandler("start", start))
            application.add_handler(CommandHandler("balance", balance_cmd))
            application.add_handler(CallbackQueryHandler(button_handler))
            application.run_polling()
        except Exception as e:
            print(f"Bot crashed: {e}, restarting in 5s...", flush=True)
            time.sleep(5)

if __name__ == '__main__':
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
