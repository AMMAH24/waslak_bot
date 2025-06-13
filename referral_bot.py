import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# إعدادات البوت
TOKEN = '7643555865:AAGd1PnBqZseymXTXS-1hIXKJStE4gSuqZg'  #
ADMIN_ID = 5308674788           # 
COMMISSION_RATE = 0.25         #

DATA_FILE = 'referrals.json'

# تحميل البيانات
def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# حفظ البيانات
def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# /رصيدي <الكود>
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("❗️اكتب رمز الإحالة بعد الأمر، مثل:\n/رصيدي 20201233")
        return

    code = context.args[0]
    data = load_data()
    if code in data:
        count = data[code]["count"]
        commission = data[code]["commission"]
        await update.message.reply_text(f"✅ رمز الإحالة: {code}\n📦 عدد الإحالات: {count}\n💰 العمولة: {commission} أوقية")
    else:
        await update.message.reply_text(f"❌ رمز الإحالة {code} غير مسجل.")

# /تأكيد_شراء <كود> <المبلغ> <المشتري>
async def confirm_sale(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 هذا الأمر مخصص للإدارة فقط.")
        return

    if len(context.args) < 3:
        await update.message.reply_text("❗️الاستخدام:\n/تأكيد_شراء <رمز الإحالة> <المبلغ> <المشتري>")
        return

    ref_code = context.args[0]
    try:
        amount = float(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ المبلغ غير صالح.")
        return

    buyer_code = context.args[2]
    if ref_code == buyer_code:
        await update.message.reply_text("❌ لا يمكن للمحيل أن يشتري من رابط نفسه. لم تُسجّل الإحالة.")
        return

    data = load_data()
    if ref_code not in data:
        data[ref_code] = {"count": 0, "commission": 0}

    data[ref_code]["count"] += 1
    data[ref_code]["commission"] += round(amount * COMMISSION_RATE)

    save_data(data)

    await update.message.reply_text(f"✅ تم تسجيل إحالة لرمز: {ref_code}\n📦 الإحالات: {data[ref_code]['count']}\n💰 العمولة: {data[ref_code]['commission']} أوقية")

# /إلغاء_شراء <كود> <المبلغ>
async def cancel_sale(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 هذا الأمر مخصص للإدارة فقط.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("❗️الاستخدام:\n/إلغاء_شراء <رمز الإحالة> <المبلغ>")
        return

    code = context.args[0]
    try:
        amount = float(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ المبلغ غير صالح.")
        return

    data = load_data()
    if code not in data:
        await update.message.reply_text("❌ هذا الرمز غير مسجل.")
        return

    data[code]["count"] = max(0, data[code]["count"] - 1)
    data[code]["commission"] = max(0, data[code]["commission"] - round(amount * COMMISSION_RATE))

    save_data(data)

    await update.message.reply_text(f"❌ تم إلغاء إحالة لرمز: {code}\n📦 الإحالات: {data[code]['count']}\n💰 العمولة: {data[code]['commission']} أوقية")

# /تعديل_الرصيد <كود> <رصيد>
# /عرض_رصيد <رمز الإحالة> (خاص بالإدارة)
async def view_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 هذا الأمر مخصص للإدارة فقط.")
        return

    if len(context.args) < 1:
        await update.message.reply_text("❗️يرجى إدخال رمز الإحالة:\n/عرض_رصيد <الكود>")
        return

    code = context.args[0]
    data = load_data()
    if code in data:
        count = data[code]["count"]
        commission = data[code]["commission"]
        await update.message.reply_text(f"📋 تقرير المحيل:\n✅ رمز الإحالة: {code}\n📦 عدد الإحالات: {count}\n💰 العمولة: {commission} أوقية")
    else:
        await update.message.reply_text("❌ هذا الرمز غير مسجل.")


# تشغيل البوت
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("رصيدي", balance))
    app.add_handler(CommandHandler("تأكيد_شراء", confirm_sale))
    app.add_handler(CommandHandler("إلغاء_شراء", cancel_sale))
    app.add_handler(CommandHandler("تعديل_الرصيد", modify_commission))
    app.add_handler(CommandHandler("عرض_رصيد", view_referral))


    print("✅ البوت يعمل الآن...")
    app.run_polling()
