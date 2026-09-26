import os, time, threading
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask
TOKEN=os.environ.get("BOT_TOKEN")
WALLET=os.environ.get("WALLET") or "0x55d398326f99059fF775485246999027B3197955"
app=Flask(__name__)
users={}
@app.route('/')
def home(): return "Bot Running"
async def start(update, context):
    users.setdefault(update.effective_user.id, {"balance": 0})
    await update.message.reply_text("Welcome!")
async def balance_cmd(update, context):
    bal=users.get(update.effective_user.id, {"balance": 0})["balance"]
    await update.message.reply_text(f"Balance: {bal}")
async def button_handler(update, context):
    q=update.callback_query
    await q.answer()
    d=q.data
    uid=q.from_user.id
    if d=="deposit": await q.message.reply_text(f"Send to: {WALLET}")
    elif d=="balance": await q.message.reply_text(f"Balance: {users.get(uid, {'balance':0})['balance']}")
    elif d=="referral":
        u=(await context.bot.get_me()).username
        await q.message.reply_text(f"Your link: https://t.me/{u}?start={uid}")
    else: await q.message.reply_text("Plans coming soon")
def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
if __name__=='__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    while True:
        try:
            print("Starting Bot polling...", flush=True)
            a=Application.builder().token(TOKEN).build()
            a.add_handler(CommandHandler("start", start))
            a.add_handler(CommandHandler("balance", balance_cmd))
            a.add_handler(CallbackQueryHandler(button_handler))
            a.run_polling()
        except Exception as e:
            print(f"Crashed {e}", flush=True)
            time.sleep(5)
