import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Bot is Live!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Send me magnet links 🧲")

async def handle_magnet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "magnet:" in text.lower():
        await update.message.reply_text(f"🧲 Magnet received!\n\nTesting OK! Next: download feature.")
    else:
        await update.message.reply_text("Send magnet: link please.")

def main():
    threading.Thread(target=run_web, daemon=True).start()
    print("Bot starting...", flush=True)
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_magnet))
    application.run_polling()

if __name__ == "__main__":
    main()
