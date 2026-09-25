import os
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7340892518

# Storage for groups
magnet_data = {}

def extract_magnet(text):
    match = re.search(r'magnet:\?xt=urn:btih:[a-zA-Z0-9]+.*', text)
    if match:
        return match.group(0).strip()
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Magnet Bot!\n\n"
        "Just forward any magnet link here and I will save it.\n\n"
        "Commands:\n"
        "/magnet - Get latest magnet\n"
        "/all - Get all magnets\n"
        "/clear - Clear all (admin only)"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text or update.message.caption or ""
    
    magnet = extract_magnet(text)
    if not magnet:
        return

    if chat_id not in magnet_data:
        magnet_data[chat_id] = []
    
    magnet_data[chat_id].append(magnet)
    # keep only last 100
    magnet_data[chat_id] = magnet_data[chat_id][-100:]
    
    await update.message.reply_text(f"✅ Magnet saved! Total: {len(magnet_data[chat_id])}")

async def get_magnet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in magnet_data or not magnet_data[chat_id]:
        await update.message.reply_text("❌ No magnets saved yet.")
        return
    
    latest = magnet_data[chat_id][-1]
    await update.message.reply_text(f"🧲 Latest magnet:\n\n`{latest}`", parse_mode='Markdown')

async def get_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in magnet_data or not magnet_data[chat_id]:
        await update.message.reply_text("❌ No magnets saved yet.")
        return
    
    all_magnets = "\n\n".join(magnet_data[chat_id][-10:])
    await update.message.reply_text(f"🧲 Last 10 magnets:\n\n{all_magnets}")

async def clear_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Only admin can clear.")
        return
    chat_id = update.effective_chat.id
    magnet_data[chat_id] = []
    await update.message.reply_text("🗑️ All magnets cleared!")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("magnet", get_magnet))
    app.add_handler(CommandHandler("all", get_all))
    app.add_handler(CommandHandler("clear", clear_all))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot running...")
    app.run_polling()
