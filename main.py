import json, os, asyncio, logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

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
            if uid not in users[ref].get("refs", []):
                users[ref]["refs"].append(uid)
                users[ref]["balance"] = float(users[ref].get("balance", 0)) + 0.5
            save_db(users)
    bal = round(u.get("balance", 0), 2)
    kb = [
        [InlineKeyboardButton("💰 Balance", callback_data="balance"), InlineKeyboardButton("📈 Invest", callback_data="invest")],
        [InlineKeyboardButton("👥 Referral", callback_data="referral"), InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")]
    ]
    await update.message.reply_text(
        f"Welcome Boss!\n\n💰 Balance: ${bal}\n📈 Invest min $10 - Daily 2% for 35 days\n👥 Referral earn $0.5 + 5%\n\nSend: `Invest 10` or `Withdraw 10`",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID:
        await update.message.reply_text("❌ Not admin")
        return
    kb = []
    for tid, info in pending_deposit.items():
        kb.append([InlineKeyboardButton(f"✅ Approve {tid} ${info['amount']}", callback_data=f"approve_{tid}")])
        kb.append([InlineKeyboardButton(f"❌ Reject {tid}", callback_data=f"reject_{tid}")])
    if not kb:
        kb = [[InlineKeyboardButton("No pending", callback_data="none")]]
    await update.message.reply_text("Admin Panel - Pending:", reply_markup=InlineKeyboardMarkup(kb))

# === NEW CREDIT COMMAND - FIXES DASHBOARD ===
async def credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID:
        await update.message.reply_text("❌ Not admin")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Use: /credit user_id amount\nEx: /credit 5698222295 5")
        return
    try:
        target_id = str(context.args[0])
        amt = float(context.args[1])
        u = effective_user(target_id)
        u["balance"] = float(u.get("balance", 0)) + amt
        save_db(users)
        await update.message.reply_text(f"✅ Credited ${amt} to {target_id}\nNew Bal: ${round(u['balance'],2)}")
        try:
            await context.bot.send_message(chat_id=int(target_id), text=f"✅ Your wallet credited ${amt}!\nNew Balance: ${round(u['balance'],2)}\nSend /start to refresh")
        except:
            pass
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = str(q.from_user.id)
    u = effective_user(uid)
    data = q.data
    if data == "balance":
        inv_text = ""
        for inv in u.get("investments", []):
            inv_text += f"\n${inv['amount']} - Earned ${round(inv.get
