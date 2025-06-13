import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters, ConversationHandler
)

TOKEN = '7643555865:AAGd1PnBqZseymXTXS-1hIXKJStE4gSuqZg'
ADMIN_ID = 5308674788
DATA_FILE = 'referrals.json'
COMMISSION_RATE = 0.25

SELECT_METHOD, ENTER_ACCOUNT = range(2)

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
        await update.message.reply_text("❗️Enter referral code after command, like:\n/mybalance 20201233")
        return

    code = context.args[0]
    data = load_data()
    if code in data:
        count = data[code]["count"]
        commission = data[code]["commission"]
        await update.message.reply_text(f"✅ Referral code: {code}\n📦 Referrals: {count}\n💰 Commission: {commission} MRU")
    else:
        await update.message.reply_text(f"❌ Referral code {code} not found.")

async def confirm_sale(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 Admin only command.")
        return

    if len(context.args) < 3:
        await update.message.reply_text("❗️Usage:\n/confirm_sale <ref_code> <amount> <buyer_code>")
        return

    ref_code = context.args[0]
    try:
        amount = float(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Invalid amount.")
        return

    buyer_code = context.args[2]
    if ref_code == buyer_code:
        await update.message.reply_text("❌ Referrer cannot refer themselves.")
        return

    data = load_data()
    if ref_code not in data:
        data[ref_code] = {"count": 0, "commission": 0}

    data[ref_code]["count"] += 1
    data[ref_code]["commission"] += round(amount * COMMISSION_RATE)

    save_data(data)

    await update.message.reply_text(f"✅ Referral confirmed: {ref_code}\n📦 Referrals: {data[ref_code]['count']}\n💰 Commission: {data[ref_code]['commission']} MRU")

async def cancel_sale(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 Admin only command.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("❗️Usage:\n/cancel_sale <ref_code> <amount>")
        return

    code = context.args[0]
    try:
        amount = float(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Invalid amount.")
        return

    data = load_data()
    if code not in data:
        await update.message.reply_text("❌ Code not found.")
        return

    data[code]["count"] = max(0, data[code]["count"] - 1)
    data[code]["commission"] = max(0, data[code]["commission"] - round(amount * COMMISSION_RATE))

    save_data(data)

    await update.message.reply_text(f"❌ Referral canceled: {code}\n📦 Referrals: {data[code]['count']}\n💰 Commission: {data[code]['commission']} MRU")

async def view_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 Admin only command.")
        return

    if len(context.args) < 1:
        await update.message.reply_text("❗️Usage:\n/view_balance <ref_code>")
        return

    code = context.args[0]
    data = load_data()
    if code in data:
        count = data[code]["count"]
        commission = data[code]["commission"]
        await update.message.reply_text(f"📋 Report for {code}\n📦 Referrals: {count}\n💰 Commission: {commission} MRU")
    else:
        await update.message.reply_text("❌ Code not found.")

async def modify_commission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 Admin only command.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("❗️Usage:\n/edit_balance <ref_code> <new_amount>")
        return

    code = context.args[0]
    try:
        new_amount = float(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Invalid amount.")
        return

    data = load_data()
    if code not in data:
        data[code] = {"count": 0, "commission": 0}

    data[code]["commission"] = round(new_amount)
    save_data(data)

    await update.message.reply_text(f"✅ Commission updated for {code}: {data[code]['commission']} MRU")

async def start_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📤 Choose withdrawal method:\n1 - Bankily\n2 - Sadad\n3 - Bank Transfer",
        reply_markup=ReplyKeyboardMarkup([['1', '2', '3']], one_time_keyboard=True, resize_keyboard=True)
    )
    return SELECT_METHOD

async def select_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    method_map = {'1': 'Bankily', '2': 'Sadad', '3': 'Bank Transfer'}
    choice = update.message.text.strip()

    if choice not in method_map:
        await update.message.reply_text("❌ Invalid option. Type 1, 2, or 3.")
        return SELECT_METHOD

    context.user_data['withdraw_method'] = method_map[choice]
    await update.message.reply_text(f"✅ Selected: {method_map[choice]}\nEnter your account number:")
    return ENTER_ACCOUNT

async def enter_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    account_number = update.message.text.strip()
    method = context.user_data['withdraw_method']
    username = update.effective_user.username or "No username"
    user_id = update.effective_user.id

    message = (
        f"📥 Withdrawal request:\n"
        f"👤 @{username} (ID: {user_id})\n"
        f"💳 Method: {method}\n"
        f"🔢 Account Number: {account_number}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=message)

    await update.message.reply_text("✅ Request sent to admin.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Withdrawal canceled.")
    return ConversationHandler.END

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    withdraw_conv = ConversationHandler(
        entry_points=[CommandHandler("withdraw", start_withdraw)],
        states={
            SELECT_METHOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_method)],
            ENTER_ACCOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_account)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("mybalance", balance))
    app.add_handler(CommandHandler("confirm_sale", confirm_sale))
    app.add_handler(CommandHandler("cancel_sale", cancel_sale))
    app.add_handler(CommandHandler("edit_balance", modify_commission))
    app.add_handler(CommandHandler("view_balance", view_referral))
    app.add_handler(withdraw_conv)

    print("✅ Bot is running...")
    app.run_polling()
