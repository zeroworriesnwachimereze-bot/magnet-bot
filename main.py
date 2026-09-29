import os, json, logging, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

# --- Keep Render LIVE ---
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"Magnet V9 FINAL 2% LIVE")
    def log_message(self, *a): pass

def run_server():
    HTTPServer(("0.0.0.0", int(os.getenv("PORT","10000"))), H).serve_forever()
threading.Thread(target=run_server, daemon=True).start()

BOT_TOKEN = os.getenv("BOT_TOKEN","")
ADMIN_ID = int(os.getenv("ADMIN_ID","7016458590"))
OWNER_WALLET = os.getenv("OWNER_WALLET","0x79f805319c0ff9b99eaf8a717110e468a496f9d8")
DB_FILE = "users.json"
users = {}

def load_db():
    global users
    if os.path.exists(DB_FILE):
        try: users = json.load(open(DB_FILE,"r"))
        except: users = {}
def save_db():
    json.dump(users, open(DB_FILE,"w"))
load_db()

def get_user(uid):
    uid=str(uid)
    if uid not in users:
        users[uid]={"balance":0.0,"investments":[],"refs":[],"ref_by":None}
    return users[uid]

PLANS = """🔥 Magnet V9 FINAL
📈 2% DAILY EARNING

VIP1 $5 → $10
VIP2 $10 → $20
VIP3 $15 → $30
VIP4 $20 → $40
VIP5 $25 → $50

💰 Earning: 2% Daily for 35 Days
✅ Deposit AUTO
💸 Withdraw Manual 1% Min $2
👥 Referral 5%"""

def main_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Deposit AUTO", callback_data="deposit"), InlineKeyboardButton("💵 Balance", callback_data="balance")],
        [InlineKeyboardButton("📈 Plans 2% Daily", callback_data="plans"), InlineKeyboardButton("📊 Invest", callback_data="invest")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw"), InlineKeyboardButton("👥 Referral Link", callback_data="referral")],
        [InlineKeyboardButton("📊 My Investments", callback_data="myinv")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=str(update.effective_user.id); u=get_user(uid)
    if context.args and not u.get("ref_by"):
        ref=str(context.args[0])
        if ref!=uid and ref in users:
            u["ref_by"]=ref
            if uid not in users[ref]["refs"]:
                users[ref]["refs"].append(uid); users[ref]["balance"]+=0.5
    save_db()
    await update.message.reply_text(f"🔥 Welcome Boss! Balance: ${round(u['balance'],2)}\nInvest min $5 - 2% daily 35 days\n\n💼 Wallet:\n`{OWNER_WALLET}`\n\n{PLANS}", parse_mode="Markdown", reply_markup=main_kb())

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID:
        await update.message.reply_text(f"Not admin\nYour ID: {update.effective_user.id}\nAdmin should be {ADMIN_ID}")
        return
    await update.message.reply_text(f"👑 Admin Panel\nUsers: {len(users)}\n\nUse:\n/credit user_id amount\nEx: /credit 5698222295 5")

async def credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID:
        await update.message.reply_text("Not admin"); return
    if len(context.args)<2:
        await update.message.reply_text("Use: /credit user_id amount"); return
    tid=str(context.args[0]); amt=float(context.args[1])
    u=get_user(tid); u["balance"]+=amt; save_db()
    await update.message.reply_text(f"✅ Credited ${amt} to {tid} New Bal ${round(u['balance'],2)}")
    try: await context.bot.send_message(chat_id=int(tid), text=f"💰 Deposit ${amt} confirmed! Now do /start and Invest")
    except: pass

async def btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=str(q.from_user.id); u=get_user(uid); d=q.data
    if d=="balance": await q.edit_message_text(f"💵 Balance: ${round(u['balance'],2)}\nEarning 2% Daily", reply_markup=main_kb())
    elif d=="deposit": await q.edit_message_text(f"💰 Deposit AUTO BEP20\nSend BNB to:\n`{OWNER_WALLET}`\n\nMin $5", parse_mode="Markdown", reply_markup=main_kb())
    elif d=="plans": await q.edit_message_text(PLANS, reply_markup=main_kb())
    elif d=="invest": await q.edit_message_text(f"📊 Invest - 2% Daily\nWallet:\n`{OWNER_WALLET}`\n\nYour Bal: ${round(u['balance'],2)}\n\nType: Invest 5 (Min $5)\nVIP1 $5 VIP2 $10 VIP3 $15 VIP4 $20 VIP5 $25", parse_mode="Markdown", reply_markup=main_kb())
    elif d=="withdraw": await q.edit_message_text(f"💸 Withdraw Manual 1% Min $2\nBal ${round(u['balance'],2)}\nType: Withdraw 2", reply_markup=main_kb())
    elif d=="referral":
        link=f"https://t.me/{context.bot.username}?start={uid}"
        await q.edit_message_text(f"👥 Referral 5%\nLink: {link}\nRefs {len(u.get('refs',[]))}", reply_markup=main_kb())
    elif d=="myinv":
        if not u["investments"]: await q.edit_message_text("No investments yet. Do Invest 5", reply_markup=main_kb())
        else:
            txt="📊 My Investments 2% Daily\n\n"
            for inv in u["investments"]: txt+=f"${inv['amount']} Earn ${round(inv['earned'],2)} Day {inv['days_passed']}/35\n"
            await q.edit_message_text(txt, reply_markup=main_kb())

async def msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t=update.message.text.strip(); uid=str(update.effective_user.id); u=get_user(uid); low=t.lower()
    if low.startswith("invest"):
        try:
            amt=float(t.split()[1])
            if amt<5: await update.message.reply_text("Min $5"); return
            if u["balance"]<amt: await update.message.reply_text(f"Low bal ${round(u['balance'],2)} Deposit to {OWNER_WALLET} first"); return
            u["balance"]-=amt; u["investments"].append({"amount":amt,"earned":0.0,"days_passed":0}); save_db()
            await update.message.reply_text(f"✅ Invested ${amt} 2% Daily for 35 Days", reply_markup=main_kb())
        except: await update.message.reply_text("Use: Invest 5")
    elif low.startswith("withdraw"):
        try:
            amt=float(t.split()[1])
            if amt<2: await update.message.reply_text("Min $2"); return
            fee=amt*0.01
            if u["balance"]<amt+fee: await update.message.reply_text(f"Need ${amt+fee} you have ${round(u['balance'],2)}"); return
            u["balance"]-=amt+fee; save_db()
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"🔔 WITHDRAW User {uid} Amount ${amt} Fee ${fee}")
            await update.message.reply_text(f"✅ Withdraw ${amt} requested Fee 1% ${fee}")
        except: await update.message.reply_text("Use: Withdraw 2")

async def daily(context: ContextTypes.DEFAULT_TYPE):
    for uid in list(users.keys()):
        for inv in users[uid].get("investments",[]):
            if inv["days_passed"]<35:
                p=inv["amount"]*0.02; inv["earned"]+=p; inv["days_passed"]+=1; users[uid]["balance"]+=p
    save_db()

if __name__=="__main__":
    app=ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("credit", credit))
    app.add_handler(CallbackQueryHandler(btn))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg))
    if app.job_queue: app.job_queue.run_repeating(daily, interval=86400, first=10)
    app.run_polling(drop_pending_updates=True)
