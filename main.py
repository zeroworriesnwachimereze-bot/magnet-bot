import os, json, logging, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot Running OK")
    def log_message(self, *a): pass

def run_server():
    port = int(os.getenv("PORT", "10000"))
    HTTPServer(("0.0.0.0", port), H).serve_forever()
threading.Thread(target=run_server, daemon=True).start()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "5698222295"))
OWNER_WALLET = os.getenv("OWNER_WALLET", "TRYourWalletHere")
DB_FILE = "users.json"
users = {}

def load_db():
    global users
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: users = json.load(f)
        except: users = {}
    else: users = {}
def save_db():
    with open(DB_FILE, "w") as f: json.dump(users, f)
load_db()

def get_user(uid):
    uid = str(uid)
    if uid not in users: users[uid] = {"balance": 0.0, "investments": [], "refs": [], "ref_by": None}
    return users[uid]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    args = context.args
    u = get_user(uid)
    if args and u.get("ref_by") is None:
        ref = str(args[0])
        if ref!= uid and ref in users:
            u["ref_by"] = ref
            if uid not in users[ref]["refs"]:
                users[ref]["refs"].append(uid)
                users[ref]["balance"] = float(users[ref].get("balance", 0)) + 0.5
                save_db()
    bal = round(u.get("balance", 0), 2)
    kb = [[InlineKeyboardButton("Balance", callback_data="balance"), InlineKeyboardButton("Invest", callback_data="invest")],[InlineKeyboardButton("Referral", callback_data="referral"), InlineKeyboardButton("Withdraw", callback_data="withdraw")]]
    await update.message.reply_text(f"Welcome Boss! Balance: ${bal}\nInvest min $10 - 2% daily 35 days", reply_markup=InlineKeyboardMarkup(kb))

async def credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID:
        await update.message.reply_text("Not admin"); return
    if len(context.args) < 2:
        await update.message.reply_text("Use: /credit user_id amount"); return
    target_id = str(context.args[0])
    try: amt = float(context.args[1])
    except: await update.message.reply_text("Amount must be number"); return
    u = get_user(target_id)
    u["balance"] = float(u.get("balance", 0)) + amt
    save_db()
    new_bal = round(u["balance"], 2)
    await update.message.reply_text(f"Credited {amt} to {target_id} New Bal {new_bal}")
    try: await context.bot.send_message(chat_id=int(target_id), text=f"Wallet credited {amt} New Bal {new_bal} Send /start")
    except: pass

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = str(q.from_user.id); u = get_user(uid); data = q.data
    if data == "balance":
        bal = round(u.get("balance", 0), 2)
        txt = f"Balance: ${bal}"
        for inv in u.get("investments", []): txt += f"\n${inv['amount']} Earned ${round(inv.get('earned',0),2)} Day {inv.get('days_passed',0)}/35"
        await q.edit_message_text(txt)
    elif data == "invest": await q.edit_message_text(f"Send: Invest 10 Wallet: {OWNER_WALLET}")
    elif data == "withdraw": await q.edit_message_text(f"Balance: ${round(u.get('balance',0),2)} Send: Withdraw 10 Min 10 Fee 1%")
    elif data == "referral":
        botname = context.bot.username; link = f"https://t.me/{botname}?start={uid}"; cnt = len(u.get("refs", []))
        await q.edit_message_text(f"Link: {link} Refs: {cnt}")

async def msg_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip(); uid = str(update.effective_user.id); u = get_user(uid); low = text.lower()
    if low.startswith("invest"):
        try:
            amt = float(text.split()[1])
            if amt < 10: await update.message.reply_text("Min 10"); return
            bal = float(u.get("balance", 0))
            if bal < amt: await update.message.reply_text(f"Low bal {bal}"); return
            u["balance"] = bal - amt; u["investments"].append({"amount": amt, "earned": 0.0, "days_passed": 0}); save_db()
            await update.message.reply_text(f"Invested {amt}")
        except: await update.message.reply_text("Send Invest 10")
    elif low.startswith("withdraw"):
        try:
            amt = float(text.split()[1])
            if amt < 10: await update.message.reply_text("Min 10"); return
            bal = float(u.get("balance", 0)); fee = amt * 0.01; total = amt + fee
            if bal < total: await update.message.reply_text(f"Need {total} have {bal}"); return
            u["balance"] = bal - total; save_db()
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"WD User {uid} Amt {amt}"); await update.message.reply_text(f"Request sent {amt}")
        except: await update.message.reply_text("Send Withdraw 10")

async def daily_job(context: ContextTypes.DEFAULT_TYPE):
    for uid in list(users.keys()):
        for inv in users[uid].get("investments", []):
            if inv.get("days_passed", 0) < 35:
                profit = inv["amount"] * 0.02; inv["earned"] = inv.get("earned", 0) + profit; inv["days_passed"] = inv.get("days_passed", 0) + 1; users[uid]["balance"] = float(users[uid].get("balance", 0)) + profit
    save_db()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("credit", credit))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg_handler))
    if app.job_queue: app.job_queue.run_repeating(daily_job, interval=86400, first=10)
    app.run_polling(drop_pending_updates=True)
