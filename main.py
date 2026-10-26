import os
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- CONFIG (Safe - from Replit Secrets) ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "7016458590"))
OWNER_WALLET = "0xCD0Dc238555E212af71346A1DF26D22d92486982"

# --- KEEP-ALIVE FOR REPLIT ---
app = Flask('')
@app.route('/')
def home():
    return "Magnet SECURE V10 LIVE on Replit!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# --- TELEGRAM BOT LOGIC ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🧲 *Dollars Magnet Bot V10 SECURE LIVE!*\n\n"
        f"Welcome {update.effective_user.first_name}!\n\n"
        f"💰 Investment Plans:\n"
        f"• $10 -> $20 in 7 days\n"
        f"• $50 -> $110 in 7 days\n"
        f"• $100 -> $230 in 7 days\n\n"
        f"📩 Wallet: `{OWNER_WALLET}`\n\n"
        f"Send proof to Admin after payment.\n"
        f"Admin ID: {ADMIN_ID}",
        parse_mode="Markdown"
    )

async def alive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is LIVE on Replit + GitHub!")

def main():
    # Start Flask in background
    Thread(target=run_flask, daemon=True).start()
    
    # Start Bot
    print("Magnet SECURE V10 LIVE")
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("alive", alive))
    application.run_polling()

if __name__ == "__main__":
    main()
