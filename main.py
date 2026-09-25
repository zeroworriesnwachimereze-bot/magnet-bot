import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
print(f"TOKEN OK: {bool(TOKEN)}")

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is Running! Go to Telegram and send /start"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 Welcome to Magnet Bot!\n\n"
        "✅ Bot is LIVE and Working!\n\n"
        "Commands:\n"
        "/start - Start bot\n"
        "/balance - Check balance\n"
        "/referral - Referral link\n"
        "/plan - Plans\n"
    )

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💰 Your Balance: $0.00\nInvite friends to earn!")

async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bot_username = (await context.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start={user_id}"
    await update.message.reply_text(f"🔗 Your Referral Link:\n{link}\n\nEarn 10% per invite!")

async def plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 Plans:\n\n"
        "Free: $0 - Earn by referrals\n"
        "Basic: $10 - 2x earnings\n"
        "Pro: $50 - 5x earnings"
    )

def run_bot():
    print("Starting Bot polling...")
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("balance", balance))
    application.add_handler(CommandHandler("referral", referral))
    application.add_handler(CommandHandler("plan", plan))
    application.run_polling()

if __name__ == '__main__':
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
