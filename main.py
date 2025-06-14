import os
import json
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from fastapi import FastAPI, Request
import uvicorn

# تحميل المتغيرات من .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 8000))

COMMISSION_RATE = 0.25
DATA_FILE = 'referrals.json'

# إنشاء تطبيق FastAPI وتطبيق Telegram
fastapi_app = FastAPI()
telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

# تحميل البيانات من ملف JSON
def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# حفظ البيانات في ملف JSON
def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# أوامر البوت
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

# التعامل مع الأخطاء
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print(f"حدث خطأ: {context.error}")
    if isinstance(update, Update) and update.message:
        await update.message.reply_text("❌ حصل خطأ غير متوقع. سيتم إصلاحه.")

# إضافة الأوامر والأخطاء للبوت
telegram_app.add_handler(CommandHandler("mybalance", balance))
telegram_app.add_handler(CommandHandler("confirm_sale", confirm_sale))
telegram_app.add_handler(CommandHandler("cancel_sale", cancel_sale))
telegram_app.add_handler(CommandHandler("check", check_ref))
telegram_app.add_handler(CommandHandler("set_commission", set_commission))
telegram_app.add_error_handler(error_handler)

# Webhook (POST من تيليجرام)
@fastapi_app.post("/")
async def webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"status": "ok"}

# اختبار GET
@fastapi_app.get("/")
async def root():
    return {"message": "✅ Waslak bot is running"}

# بدء التشغيل مع تعيين Webhook
if __name__ == '__main__':
    import asyncio

    async def main():
        await telegram_app.bot.set_webhook(WEBHOOK_URL)
        print(f"✅ Webhook set to: {WEBHOOK_URL}")

        config = uvicorn.Config("main:fastapi_app", host="0.0.0.0", port=PORT, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

    asyncio.run(main())
