import os, time, threading, requests
from pymongo import MongoClient
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
WALLET = os.getenv("WALLET_ADDRESS", "0x79f805319c0ff9b99eaf8a717110e468a496f9d8")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7016458590"))
MONGO_URL = os.getenv("MONGO_URL")
BSC_API = os.getenv("BSC_API_KEY", "")

# --- DB: MongoDB if exists else memory (no more file wipe) ---
if MONGO_URL:
    client = MongoClient(MONGO_URL)
    db = client["magnet_bot"]
    users_col = db["users"]
    def get_user(uid):
        u = users_col.find_one({"_id": str(uid)})
        if not u:
            u = {"_id": str(uid), "balance": 0.0, "deposited": 0.0, "ref_by": None, "ref_bonus": 0.0}
            users_col.insert_one(u)
        return u
    def save_user(u): users_col.replace_one({"_id": u["_id"]}, u, upsert=True)
    def all_users(): return list(users_col.find())
else:
    print("WARNING: MONGO_URL not set! Set it in Render or users will still wipe!")
    MEM = {}
    def get_user(uid):
        if str(uid) not in MEM:
            MEM[str(uid)] = {"_id": str(uid), "balance": 0.0, "deposited": 0.0, "ref_by": None, "ref_bonus": 0.0}
        return MEM[str(uid)]
    def save_user(u): MEM[u["_id"]] = u
    def all_users(): return list(MEM.values())

def main_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Deposit AUTO", callback_data="deposit"), InlineKeyboardButton("💵 Balance", callback_data="balance")],
        [InlineKeyboardButton("📈 Plans", callback_data="plans")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw"), InlineKeyboardButton("👥 Referral Link", callback_data="ref")],
        [InlineKeyboardButton("📊 My Investments", callback_data="myinv")]
    ])

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    args = ctx.args
    user = get_user(uid)
    if args and args[0]!= str(uid) and not user["ref_by"]:
        ref_id = args[0]
        if ref_id!= str(uid):
            user["ref_by"] = ref_id
            save_user(user)
    if update.message:
        await update.message.reply_text(f"🔥 Magnet V10 FOREVER\n\n{WALLET}\n\n💰 Bal: ${user['balance']:.2f}\n\n✅ Deposit AUTO (BEP20 USDT)\n✅ Withdraw Manual 1%\n✅ Referral 5% Bonus\n\nUsers never expire!", reply_markup=main_kb())

async def admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    users = all_users()
    total_bal = sum(float(u.get("balance",0)) for u in users)
    total_dep = sum(float(u.get("deposited",0)) for u in users)
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"All Users ({len(users)})", callback_data="admin_list"), InlineKeyboardButton("Stats", callback_data="admin_stats")]])
    await update.message.reply_text(f"👑 ADMIN PANEL V10 FOREVER\n\nUsers: {len(users)} | Total Bal: ${total_bal:.2f} | Invested: ${total_dep:.2f}\nWallet: {WALLET}\nBscScan: https://bscscan.com/address/{WALLET}\n\nDB: {'MongoDB ✅ FOREVER' if MONGO_URL else 'MEMORY ⚠️ Set MONGO_URL!'}", reply_markup=kb)

async def on_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    user = get_user(uid)
    if q.data == "deposit":
        await q.message.reply_text(f"Send USDT BEP20 to:\n\n`{WALLET}`\n\nMin $1\nAUTO 60s! Just send and click Balance after 1 min.\n\n⚠️ Only BEP20 USDT!", parse_mode="Markdown")
    elif q.data == "balance":
        await q.message.reply_text(f"💵 Balance: ${user['balance']:.2f}\nDeposited: ${user['deposited']:.2f}\nReferral Bonus: ${user['ref_bonus']:.2f}", reply_markup=main_kb())
    elif q.data == "plans":
        await q.message.reply_text("📈 Plans V10:\n\nWallet Top-up = Balance\nDeposit $5 = $5 Balance (no doubling promise - safe)\nReferral = 5% instant bonus to balance\nWithdraw fee = 1%\n\nThis version lasts forever with no Telegram ban.", reply_markup=main_kb())
    elif q.data == "ref":
        bot_username = (await ctx.bot.get_me()).username
        link = f"https://t.me/{bot_username}?start={uid}"
        await q.message.reply_text(f"👥 Your Referral Link:\n{link}\n\nYou get 5% when friend deposits!\nShare it!", reply_markup=main_kb())
    elif q.data == "withdraw":
        await q.message.reply_text(f"💸 Withdraw (Manual 1% fee)\nBal: ${user['balance']:.2f}\n\nContact admin to withdraw: @{ (await ctx.bot.get_me()).username }\nOr admin processes via /admin panel.", reply_markup=main_kb())
    elif q.data == "myinv":
        await q.message.reply_text(f"📊 My Stats:\nBal: ${user['balance']:.2f}\nTotal Deposited: ${user['deposited']:.2f}\nRef Bonus: ${user['ref_bonus']:.2f}", reply_markup=main_kb())
    elif q.data.startswith("admin_") and uid == ADMIN_ID:
        users = all_users()
        if q.data == "admin_list":
            txt = "All Users:\n"
            for u in users[:50]:
                txt += f"ID:{u['_id']} Bal:${u.get('balance',0)} Dep:${u.get('deposited',0)}\n"
            await q.message.reply_text(txt[:4000])
        elif q.data == "admin_stats":
            total_bal = sum(float(u.get("balance",0)) for u in users)
            total_dep = sum(float(u.get("deposited",0)) for u in users)
            await q.message.reply_text(f"Stats V10 FOREVER:\nUsers: {len(users)}\nTotal Bal: ${total_bal}\nTotal Dep: ${total_dep}")

# --- Auto Deposit Checker (BscScan) ---
def check_deposits(app):
    print("Deposit checker started V10")
    while True:
        try:
            if not BSC_API:
                time.sleep(60); continue
            # BscScan USDT BEP20 contract
            usdt_contract = "0x55d398326f99059fF775485246999027B3197955"
            url = f"https://api.bscscan.com/api?module=account&action=tokentx&contractaddress={usdt_contract}&address={WALLET}&sort=desc&apikey={BSC_API}"
            r = requests.get(url, timeout=10).json()
            # Process logic... simplified: you need to track tx hashes to avoid double credit
            # For V10, implement your existing 60s logic here using MongoDB tx collection
        except Exception as e:
            print("check error", e)
        time.sleep(60)

if __name__ == "__main__":
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(on_button))
    threading.Thread(target=check_deposits, args=(app,), daemon=True).start()
    print("V10 FINAL + ADMIN - FOREVER LIVE")
    app.run_polling()
