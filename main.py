import json, os, logging, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

# --- FAKE SERVER TO KEEP RENDER WEB SERVICE LIVE ---
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running - Live")
    def log_message(self, *a):
        pass

def start_fake_server():
    port = int(os.getenv("PORT", "10000"))
    HTTPServer(("0.0.0.0", port), H).serve_forever()

threading.Thread(target=start_fake_server, daemon=True).start()
# ----------------------------------------------------

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "5698222295"))
OWNER_WALLET = os.getenv("OWNER_WALLET", "THYourTronWalletHere")
DB_FILE = "users.json"
MIN_WITHDRAW = 10
FEE_PERCENT = 1

users = {}
pending_deposit = {}

def load_db():
    global users
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                users = json.load(f)
        except:
            users = {}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f)

load_db()

def effective_user(user_id):
    uid = str(user_id)
    if uid not in users:
        users[uid] = {"balance": 0.0, "investments": [], "ref_by": None, "refs": [], "username": ""}
    if "balance" not in users[uid]:
        users[uid]["balance"] = 0.0
    if "investments" not in users[uid]:
        users[uid]["investments"] = []
    if "refs" not in users[uid]:
        users[uid]["refs"] = []
    return users[uid]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    args = context.args
    u = effective_user(uid)
    u["username"] = update.effective_user.username or ""

    if args and args[0]!= uid and u.get("ref_by") is None:
        ref = args[0]
        if ref in users and ref!= uid:
            u["ref_by"] = ref
            rlist = users[ref].get("refs", [])
            if uid not in rlist:
                rlist.append(uid)
                users[ref]["refs"] = rlist
                cur = users[ref].get("balance", 0)
                users[ref]["balance"] = float(cur) + 0.5
            save_db(users)

    bal = round(u.get("balance", 0), 2)
    kb = [
        [InlineKeyboardButton("💰 Balance", callback_data="balance"), InlineKeyboardButton("📈 Invest", callback_data="invest")],
        [InlineKeyboardButton("👥 Referral", callback_data="referral"), InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")]
    ]
    txt = f"Welcome Boss!\n\nBalance: ${bal}\nInvest Min $10\nDaily 2% for 35 Days"
    await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))

async def credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID:
        await update.message.reply_text("Not admin")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Use: /credit user_id amount\nEx: /credit 5698222295 5")
        return
    try:
        target_id = str(context.args[0])
        amt = float(context.args[1])
        u = effective_user(target_id)
        cur = u.get("balance", 0)
        u["balance"] = float(cur) + amt
        save_db(users)
        newbal = round(u.get("balance", 0), 2)
        await update.message.reply_text(f"✅ Credited ${amt} to {target_id}\nNew Bal: ${newbal}")
        try:
            await context.bot.send_message(chat_id=int(target_id), text=f"✅ Wallet credited ${amt}!\nNew Bal: ${newbal}\nSend /start")
        except:
            pass
    except Exception as e:
        await update.message.reply_text(f"Error {e}")

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID:
        return
    await update.message.reply_text("Admin Panel OK\nUse /credit user_id amount")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = str(q.from_user.id)
    u = effective_user(uid)
    data = q.data

    if data == "balance":
        inv_text = ""
        for inv in u.get("investments", []):
            amt = inv.get("amount", 0)
            earned = round(inv.get("earned", 0), 2)
            days = inv.get("days_passed", 0)
            inv_text = inv_text + f"\n${amt} - Earned ${earned} Day {days}/35"
        if not inv_text:
            inv_text = "\nNo investments yet"
        bal = round(u.get("balance", 0), 2)
        await q.edit_message_text(f"💰 Balance: ${bal}{inv_text}")
    elif data == "invest":
        await q.edit_message_text(f"📈 Send: Invest 10\nWallet: {OWNER_WALLET}\nDaily 2% - Min $10")
    elif data == "withdraw":
        bal = round(u.get("balance", 0), 2)
        await q.edit_message_text(f"💸 Withdraw - Fee 1% Min ${MIN_WITHDRAW}\nBal: ${bal}\nSend: Withdraw 10")
    elif data == "referral":
        botname = context.bot.username
        link = f"https://t.me/{botname}?start={uid}"
        count = len(u.get("refs", []))
        await q.edit_message_text(f"👥 Your Link:\n{link}\nRefs: {count}\nEarn 5% referral + $0.5 bonus")

async def msg_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    uid = str(update.effective_user.id)
    u = effective_user(uid)
    low = text.lower()

    if low.startswith("invest"):
        try:
            amt = float(text.split()[1])
            if amt < 10:
                await update.message.reply_text("Min $10")
                return
            bal = u.get("balance", 0)
            if bal < amt:
                await update.message.reply_text(f"Low bal ${round(bal,2)}")
                return
            u["balance"] = bal - amt
            lst = u.get("investments", [])
            lst.append({"amount": amt, "earned": 0.0, "days_passed": 0})
            u["investments"] = lst
            save_db(users)
            await update.message.reply_text(f"✅ Invested ${amt} - Daily 2% started!")
        except:
            await update.message.reply_text("Send like: Invest 10")

    elif low.startswith("withdraw"):
        try:
            amt = float(text.split()[1])
            if amt < MIN_WITHDRAW:
                await update.message.reply_text(f"Min ${MIN_WITHDRAW}")
                return
            fee = amt * FEE_PERCENT / 100
            total = amt
            bal = u.get("balance", 0)
            if bal < amt:
                await update.message.reply_text(f"Need ${amt} you have ${round(bal,2)}")
                return
            u["balance"] = bal - amt
            save_db(users)
            rec = amt
