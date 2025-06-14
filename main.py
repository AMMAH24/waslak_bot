import os
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
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
        await update.message.reply_text("استخدم:\n/mybalance <رمز_الإحالة>")
        return
    code = context.args[0]
    data = load_data()
    if code in data:
        count = data[code]["count"]
        commission = data[code]["commission"]
        await update.message.reply_text(
            f"🔐 رمز الإحالة: {code}\n"
            f"👥 عدد الإحالات: {count}\n"
            f"💰 عمولتك: {commission} MRU\n\n"
            f"للسحب تواصل مع @ammah_24"
        )
    else:
        await update.message.reply_text("رمز الإحالة غير موجود.")

async def confirm_sale(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("هذا الأمر مخصص للمشرف فقط.")
        return
    if len(context.args) < 3:
        await update.message.reply_text("استخدم:\n/confirm_sale <ref_code> <amount> <buyer_code>")
        return
    ref_code = context.args[0]
    try:
        amount = float(context.args[1])
    except:
        await update.message.reply_text("المبلغ غير صالح.")
        return
    buyer_code = context.args[2]
    if ref_code == buyer_code:
        await update.message.reply_text("لا يمكنك إحالة نفسك.")
        return
    data = load_data()
    if ref_code not in data:
        data[ref_code] = {"count": 0, "commission": 0}
    data[ref_code]["count"] += 1
    data[ref_code]["commission"] += round(amount * COMMISSION_RATE)
    save_data(data)
    await update.message.reply_text(
        f"✅ تم تسجيل البيع.\n"
        f"الإحالات: {data[ref_code]['count']}\n"
        f"العمولة: {data[ref_code]['commission']} MRU"
    )

async def cancel_sale(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("هذا الأمر مخصص للمشرف فقط.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("استخدم:\n/cancel_sale <ref_code> <amount>")
        return
    ref_code = context.args[0]
    try:
        amount = float(context.args[1])
    except:
        await update.message.reply_text("المبلغ غير صالح.")
        return
    data = load_data()
    if ref_code not in data:
        await update.message.reply_text("رمز الإحالة غير موجود.")
        return
    data[ref_code]["count"] = max(0, data[ref_code]["count"] - 1)
    data[ref_code]["commission"] = max(0, data[ref_code]["commission"] - round(amount * COMMISSION_RATE))
    save_data(data)
    await update.message.reply_text(
        f"✅ تم إلغاء البيع.\n"
        f"الإحالات الآن: {data[ref_code]['count']}\n"
        f"العمولة الآن: {data[ref_code]['commission']} MRU"
    )

async def check_ref(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("هذا الأمر مخصص للمشرف فقط.")
        return
    if len(context.args) < 1:
        await update.message.reply_text("استخدم:\n/check <ref_code>")
        return
    code = context.args[0]
    data = load_data()
    if code in data:
        count = data[code]["count"]
        commission = data[code]["commission"]
        await update.message.reply_text(
            f"🔎 رمز: {code}\n"
            f"👥 إحالات: {count}\n"
            f"💰 عمولة: {commission} MRU"
        )
    else:
        await update.message.reply_text("رمز الإحالة غير موجود.")

async def set_commission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("هذا الأمر مخصص للمشرف فقط.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("استخدم:\n/set_commission <ref_code> <amount>")
        return
    code = context.args[0]
    try:
        new_amount = int(context.args[1])
    except:
        await update.message.reply_text("المبلغ غير صالح.")
        return
    data = load_data()
    if code not in data:
        data[code] = {"count": 0, "commission": 0}
    data[code]["commission"] = new_amount
    save_data(data)
    await update.message.reply_text(f"✅ تم تعيين العمولة إلى {new_amount} MRU لـ {code}.")
    
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print(f"حدث استثناء: {context.error}")
    # خيار إضافي: أرسل الخطأ للمشرف في تيليغرام
    if isinstance(update, Update) and update.message:
        await update.message.reply_text("❌ حصل خطأ غير متوقع. سيتم إصلاحه قريباً.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("mybalance", balance))
    app.add_handler(CommandHandler("confirm_sale", confirm_sale))
    app.add_handler(CommandHandler("cancel_sale", cancel_sale))
    app.add_handler(CommandHandler("check", check_ref))
    app.add_handler(CommandHandler("set_commission", set_commission))
    app.add_error_handler(error_handler)

    print("✅ Bot is running...")
    app.run_polling()
