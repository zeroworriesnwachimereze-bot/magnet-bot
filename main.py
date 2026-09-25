import os, re
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
BOT_TOKEN=os.getenv("BOT_TOKEN")
ADMIN_ID=7340892518
magnet_data={}
def extract_magnet(t):
    m=re.search(r'magnet:\?xt=urn:btih:[a-zA-Z0-9]+.*',t)
    return m.group(0).strip() if m else None
async def start(u,c):
    await u.message.reply_text("Welcome! Send magnets")
async def handle_message(u,c):
    m=extract_magnet(u.message.text or "")
    if not m: return
    cid=u.effective_chat.id
    magnet_data.setdefault(cid,[]).append(m)
    await u.message.reply_text("✅ Saved!")
async def get_magnet(u,c):
    cid=u.effective_chat.id
    if not magnet_data.get(cid):
        await u.message.reply_text("No magnets");return
    await u.message.reply_text(magnet_data[cid][-1])
async def get_all(u,c):
    cid=u.effective_chat.id
    if not magnet_data.get(cid):
        await u.message.reply_text("No magnets");return
    await u.message.reply_text("\n\n".join(magnet_data[cid]))
async def clear_all(u,c):
    if u.effective_user.id!=ADMIN_ID:
        await u.message.reply_text("Admin only");return
    magnet_data[u.effective_chat.id]=[]
    await u.message.reply_text("Cleared!")
if __name__=="__main__":
    app=ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("magnet",get_magnet))
    app.add_handler(CommandHandler("all",get_all))
    app.add_handler(CommandHandler("clear",clear_all))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,handle_message))
    app.run_polling()
