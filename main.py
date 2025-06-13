import os
import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
COMMISSION_RATE = 0.25
DATA_FILE = 'referrals.json'

def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("Use: /mybalance <ref_code>")
        return
    code = context.args[0]
    data = load_data()
    if code in data:
        count = data[code]["count"]
        commission = data[code]["commission"]
        await update.message.reply_text(f"Referral Code: {code}\nReferrals: {count}\nCommission: {commission} MRU")
    else:
        await update.message.reply_text("Referral code not found.")

async def confirm_sale(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Admins only.")
        return
    if len(context.args) < 3:
        await update.message.reply_text("Use: /confirm_sale <ref_code> <amount> <buyer_code>")
        return
    ref_code = context.args[0]
    try:
        amount = float(context.args[1])
    except:
        await update.message.reply_text("Invalid amount.")
        return
    buyer_code = context.args[2]
    if ref_code == buyer_code:
        await update.message.reply_text("Cannot refer self.")
        return
    data = load_data()
    if ref_code not in data:
        data[ref_code] = {"count": 0, "commission": 0}
    data[ref_code]["count"] += 1
    data[ref_code]["commission"] += round(amount * COMMISSION_RATE)
    save_data(data)
    await update.message.reply_text(f"Sale recorded.\nReferrals: {data[ref_code]['count']}\nCommission: {data[ref_code]['commission']} MRU")

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["1. Bankily", "2. Saddad", "3. Bank Transfer"]]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text("Select withdrawal method:", reply_markup=markup)

async def handle_withdraw_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    method = update.message.text
    context.user_data["withdraw_method"] = method
    await update.message.reply_text("Enter account number:")

async def handle_account_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    account = update.message.text
    method = context.user_data.get("withdraw_method", "Unknown")
    user = update.effective_user
    admin_text = f"Withdrawal request:\nUser: {user.first_name} (@{user.username})\nMethod: {method}\nAccount: {account}"
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text)
    await update.message.reply_text("Your withdrawal request has been sent to admin.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("mybalance", balance))
    app.add_handler(CommandHandler("confirm_sale", confirm_sale))
    app.add_handler(CommandHandler("withdraw", withdraw))
    app.add_handler(MessageHandler(filters.Regex("^(1\. Bankily|2\. Saddad|3\. Bank Transfer)$"), handle_withdraw_choice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_account_number))
    print("Bot is running...")
    app.run_polling()
