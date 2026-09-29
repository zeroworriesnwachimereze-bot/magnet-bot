import json, os, logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
import asyncio

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "5698222295"))
OWNER_WALLET = os.getenv("OWNER_WALLET", "THYourWallet")
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
        [InlineKeyboardButton("Balance", callback_data="balance"), InlineKeyboardButton("Invest", callback_data="invest")],
        [InlineKeyboardButton("Referral", callback_data="referral"), InlineKeyboardButton("Withdraw", callback_data="withdraw")]
    ]
    txt = f"Welcome Boss! Balance: {bal} Invest min 10 Daily 2pct 35 days"
    await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID:
        await update.message.reply_text("Not admin")
        return
    kb = []
    for tid, info in pending_deposit.items():
        amt = info.get("amount", 0)
        kb.append([InlineKeyboardButton(f"Approve {tid} {amt}", callback_data=f"approve_{tid}")])
        kb.append([InlineKeyboardButton(f"Reject {tid}", callback_data=f"reject_{tid}")])
    if not kb:
        kb = [[InlineKeyboardButton("No pending", callback_data="none")]]
    await update.message.reply_text("Admin Panel:", reply_markup=InlineKeyboardMarkup(kb))

async def credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID:
        await update.message.reply_text("Not admin")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Use: /credit user_id amount Ex /credit 5698222295 5")
        return
    try:
        target_id = str(context.args[0])
        amt = float(context.args[1])
        u = effective_user(target_id)
        cur = u.get("balance", 0)
        u["balance"] = float(cur) + amt
        save_db(users)
        newbal = round(u.get("balance", 0), 2)
        await update.message.reply_text(f"Credited {amt} to {target_id} New Bal {newbal}")
        try:
            await context.bot.send_message(chat_id=int(target_id), text=f"Wallet credited {amt} New Bal {newbal} Send /start")
        except:
            pass
    except Exception as e:
        await update.message.reply_text(f"Error {e}")

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
            inv_text = inv_text + f"\n{amt} - Earned {earned} Day {days}/35"
        if not inv_text:
            inv_text = "\nNo investments"
        bal = round(u.get("balance", 0), 2)
        await q.edit_message_text(f"Balance {bal}{inv_text}")
    elif data == "invest":
        await q.edit_message_text(f"Send Invest 10 Min 10 Wallet {OWNER_WALLET} Daily 2pct")
    elif data == "withdraw":
        bal = round(u.get("balance", 0), 2)
        await q.edit_message_text(f"Withdraw Fee 1pct Min {MIN_WITHDRAW} Bal {bal} Send Withdraw 10")
    elif data == "referral":
        botname = context.bot.username
        link = f"https://t.me/{botname}?start={uid}"
        count = len(u.get("refs", []))
        await q.edit_message_text(f"Link {link} Refs {count} Earn 5pct")
    elif data.startswith("approve_"):
        tid = data.replace("approve_", "")
        if tid in pending_deposit:
            info = pending_deposit[tid]
            target = str(info.get("uid", ""))
            amt = float(info.get("amount", 0))
            tu = effective_user(target)
            cur = tu.get("balance", 0)
            tu["balance"] = float(cur) + amt
            save_db(users)
            del pending_deposit[tid]
            await q.edit_message_text(f"Approved {tid} {amt}")
    elif data.startswith("reject_"):
        tid = data.replace("reject_", "")
        if tid in pending_deposit:
            del pending_deposit[tid]
            await q.edit_message_text(f"Rejected {tid}")

async def msg_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    uid = str(update.effective_user.id)
    u = effective_user(uid)
    low = text.lower()
    if low.startswith("invest"):
        try:
            amt = float(text.split()[1])
            if amt < 10:
                await update.message.reply_text("Min 10")
                return
            bal = u.get("balance", 0)
            if bal < amt:
                await update.message.reply_text(f"Low bal {round(bal,2)}")
                return
            u["balance"] = bal - amt
            lst = u.get("investments", [])
            lst.append({"amount": amt, "earned": 0.0, "days_passed": 0})
            u["investments"] = lst
            save_db(users)
            await update.message.reply_text(f"Invested {amt}")
        except:
            await update.message.reply_text("Send Invest 10")
    elif low.startswith("withdraw"):
        try:
            amt = float(text.split()[1])
            if amt < MIN_WITHDRAW:
                await update.message.reply_text(f"Min {MIN_WITHDRAW}")
                return
            fee = amt * FEE_PERCENT / 100
            total = amt + fee
            bal = u.get("balance", 0)
            if bal < total:
                await update.message.reply_text(f"Need {total}")
                return
            rec = amt - fee
            u["balance"] = bal - total
            save_db(users)
            admin_msg = f"WD User {uid} Amt {amt} Fee {fee} Gets {rec}"
            kb = [[InlineKeyboardButton(f"Approve WD {uid}", callback_data=f"approve_{uid}_{amt}")]]
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, reply_markup=InlineKeyboardMarkup(kb))
            await update.message.reply_text(f"Request sent {rec}")
        except:
            await update.message.reply_text("Send Withdraw 10")

async def daily_job(context: ContextTypes.DEFAULT_TYPE):
    for uid in list(users.keys()):
        for inv in users[uid].get("investments", []):
            dp = inv.get("days_passed", 0)
            if dp < 35:
                amt = inv.get("amount", 0)
                profit = amt * 0.02
                inv["earned"] = inv.get("earned", 0) + profit
                inv["days_passed"] = dp + 1
                cur = users[uid].get("balance", 0)
                users[uid]["balance"] = cur + profit
    save_db(users)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("credit", credit))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg_handler))
    if app.job_queue:
        app.job_queue.run_repeating(daily_job, interval=86400, first=10)
        app.run_polling(drop_pending_updates=True)
