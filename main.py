import os
import json
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from fastapi import FastAPI, Request, HTTPException
import uvicorn
import logging
from typing import Dict, Any

# تحميل المتغيرات البيئية من ملف .env
load_dotenv()

# تعريف المتغيرات الأساسية
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 8000))
SECRET_TOKEN = os.getenv("SECRET_TOKEN")  # توكن سري للتحقق من طلبات الويب هوك
COMMISSION_RATE = 0.25  # نسبة العمولة 25%
DATA_FILE = 'referrals.json'  # ملف تخزين بيانات الإحالات

# إعداد نظام التسجيل (Logging)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# إنشاء تطبيق FastAPI وتطبيق Telegram
fastapi_app = FastAPI(title="Waslak Referral Bot")
telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

# ============= وظائف إدارة البيانات =============
def load_data() -> Dict[str, Dict[str, Any]]:
    """
    تحميل بيانات الإحالات من ملف JSON
    """
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.info("ملف البيانات غير موجود، سيتم إنشاء ملف جديد")
        return {}
    except json.JSONDecodeError:
        logger.error("خطأ في قراءة ملف البيانات، سيتم إنشاء ملف جديد")
        return {}

def save_data(data: Dict[str, Dict[str, Any]]) -> None:
    """
    حفظ بيانات الإحالات إلى ملف JSON
    """
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"فشل في حفظ البيانات: {e}")
        raise

# ============= أوامر البوت =============
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    عرض رصيد الإحالات للعضو
    الاستخدام: /mybalance <رمز_الإحالة>
    """
    if len(context.args) < 1:
        await update.message.reply_text("❌ استخدم:\n/mybalance <رمز_الإحالة>")
        return
    
    code = context.args[0].strip().upper()
    data = load_data()
    
    if code in data:
        count = data[code]["count"]
        commission = data[code]["commission"]
        response = (
            f"🔐 رمز الإحالة: {code}\n"
            f"👥 عدد الإحالات: {count}\n"
            f"💰 عمولتك: {commission} MRU\n\n"
            f"للسحب تواصل مع @ammah_24"
        )
    else:
        response = "⚠️ رمز الإحالة غير موجود."
    
    await update.message.reply_text(response)

async def confirm_sale(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    تأكيد عملية بيع وإضافة العمولة (للمشرف فقط)
    الاستخدام: /confirm_sale <ref_code> <amount> <buyer_code>
    """
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ هذا الأمر مخصص للمشرف فقط.")
        return
    
    if len(context.args) < 3:
        await update.message.reply_text("❌ استخدم:\n/confirm_sale <ref_code> <amount> <buyer_code>")
        return
    
    ref_code = context.args[0].strip().upper()
    buyer_code = context.args[2].strip().upper()
    
    try:
        amount = float(context.args[1])
        if amount <= 0:
            raise ValueError
    except (ValueError, IndexError):
        await update.message.reply_text("❌ المبلغ غير صالح. يجب أن يكون رقمًا موجبًا.")
        return
    
    if ref_code == buyer_code:
        await update.message.reply_text("❌ لا يمكنك إحالة نفسك.")
        return
    
    data = load_data()
    
    if ref_code not in data:
        data[ref_code] = {"count": 0, "commission": 0}
    
    commission = round(amount * COMMISSION_RATE)
    data[ref_code]["count"] += 1
    data[ref_code]["commission"] += commission
    save_data(data)
    
    response = (
        f"✅ تم تسجيل البيع بنجاح\n\n"
        f"📌 رمز المسوق: {ref_code}\n"
        f"💳 المبلغ: {amount} MRU\n"
        f"💸 العمولة: {commission} MRU\n\n"
        f"📊 الإحالات الإجمالية: {data[ref_code]['count']}\n"
        f"💰 الرصيد الحالي: {data[ref_code]['commission']} MRU"
    )
    
    await update.message.reply_text(response)

async def cancel_sale(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    إلغاء عملية بيع (للمشرف فقط)
    الاستخدام: /cancel_sale <ref_code> <amount>
    """
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ هذا الأمر مخصص للمشرف فقط.")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("❌ استخدم:\n/cancel_sale <ref_code> <amount>")
        return
    
    ref_code = context.args[0].strip().upper()
    
    try:
        amount = float(context.args[1])
        if amount <= 0:
            raise ValueError
    except (ValueError, IndexError):
        await update.message.reply_text("❌ المبلغ غير صالح. يجب أن يكون رقمًا موجبًا.")
        return
    
    data = load_data()
    
    if ref_code not in data:
        await update.message.reply_text("❌ رمز الإحالة غير موجود.")
        return
    
    commission = round(amount * COMMISSION_RATE)
    data[ref_code]["count"] = max(0, data[ref_code]["count"] - 1)
    data[ref_code]["commission"] = max(0, data[ref_code]["commission"] - commission)
    save_data(data)
    
    response = (
        f"✅ تم إلغاء البيع بنجاح\n\n"
        f"📌 رمز المسوق: {ref_code}\n"
        f"💸 العمولة المخصومة: {commission} MRU\n\n"
        f"📊 الإحالات الحالية: {data[ref_code]['count']}\n"
        f"💰 الرصيد الحالي: {data[ref_code]['commission']} MRU"
    )
    
    await update.message.reply_text(response)

async def check_ref(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    التحقق من رصيد إحالة معينة (للمشرف فقط)
    الاستخدام: /check <ref_code>
    """
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ هذا الأمر مخصص للمشرف فقط.")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text("❌ استخدم:\n/check <ref_code>")
        return
    
    code = context.args[0].strip().upper()
    data = load_data()
    
    if code in data:
        count = data[code]["count"]
        commission = data[code]["commission"]
        response = (
            f"🔎 تفاصيل الرمز: {code}\n\n"
            f"👥 عدد الإحالات: {count}\n"
            f"💰 العمولة المتراكمة: {commission} MRU"
        )
    else:
        response = "❌ رمز الإحالة غير موجود."
    
    await update.message.reply_text(response)

async def set_commission(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    تعيين عمولة يدويًا (للمشرف فقط)
    الاستخدام: /set_commission <ref_code> <amount>
    """
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ هذا الأمر مخصص للمشرف فقط.")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("❌ استخدم:\n/set_commission <ref_code> <amount>")
        return
    
    code = context.args[0].strip().upper()
    
    try:
        new_amount = int(context.args[1])
        if new_amount < 0:
            raise ValueError
    except (ValueError, IndexError):
        await update.message.reply_text("❌ المبلغ غير صالح. يجب أن يكون رقمًا صحيحًا موجبًا.")
        return
    
    data = load_data()
    
    if code not in data:
        data[code] = {"count": 0, "commission": 0}
    
    data[code]["commission"] = new_amount
    save_data(data)
    
    await update.message.reply_text(f"✅ تم تعيين العمولة إلى {new_amount} MRU للرمز {code}.")

# ============= معالجة الأخطاء =============
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالجة الأخطاء العامة للبوت"""
    logger.error(f"حدث خطأ: {context.error}", exc_info=context.error)
    
    if update and isinstance(update, Update):
        if update.message:
            await update.message.reply_text("❌ حدث خطأ غير متوقع. يرجى المحاولة لاحقًا.")
        elif update.callback_query:
            await update.callback_query.message.reply_text("❌ حدث خطأ أثناء معالجة طلبك.")

# ============= إعداد معالجات الأوامر =============
def setup_handlers(app):
    """تكوين معالجات الأوامر للبوت"""
    app.add_handler(CommandHandler("mybalance", balance))
    app.add_handler(CommandHandler("confirm_sale", confirm_sale))
    app.add_handler(CommandHandler("cancel_sale", cancel_sale))
    app.add_handler(CommandHandler("check", check_ref))
    app.add_handler(CommandHandler("set_commission", set_commission))
    app.add_error_handler(error_handler)

# ============= نقاط نهاية FastAPI =============
@fastapi_app.post("/")
async def telegram_webhook(request: Request):
    """نقطة نهاية الويب هوك لاستقبال تحديثات التيليجرام"""
    # التحقق من التوكن السري إذا كان موجودًا
    if SECRET_TOKEN:
        token = request.headers.get('X-Telegram-Bot-Api-Secret-Token')
        if token != SECRET_TOKEN:
            logger.warning("محاولة وصول غير مصرح بها للويب هوك")
            raise HTTPException(status_code=403, detail="غير مصرح به")
    
    try:
        data = await request.json()
        update = Update.de_json(data, telegram_app.bot)
        await telegram_app.process_update(update)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"خطأ في معالجة التحديث: {e}")
        raise HTTPException(status_code=400, detail="طلب غير صالح")

@fastapi_app.get("/")
async def health_check():
    """نقطة نهاية للتحقق من حالة السيرفر"""
    return {
        "status": "running",
        "bot": "Waslak Referral Bot",
        "version": "1.0"
    }

# ============= أحداث بدء/إيقاف التطبيق =============
@fastapi_app.on_event("startup")
async def startup_application():
    """تهيئة التطبيق عند البدء"""
    try:
        logger.info("جاري تهيئة بوت التيليجرام...")
        await telegram_app.initialize()
        
        logger.info("جاري تعيين الويب هوك...")
        await telegram_app.bot.set_webhook(
            url=WEBHOOK_URL,
            secret_token=SECRET_TOKEN,
            drop_pending_updates=True
        )
        
        setup_handlers(telegram_app)
        logger.info(f"✅ تم تهيئة البوت بنجاح. الويب هوك مضبوط على: {WEBHOOK_URL}")
    except Exception as e:
        logger.error(f"فشل في تهيئة البوت: {e}")
        raise

@fastapi_app.on_event("shutdown")
async def shutdown_application():
    """تنظيف الموارد عند إيقاف التطبيق"""
    try:
        logger.info("جاري إيقاف بوت التيليجرام...")
        await telegram_app.shutdown()
        logger.info("✅ تم إيقاف البوت بنجاح")
    except Exception as e:
        logger.error(f"فشل في إيقاف البوت: {e}")

# ============= تشغيل التطبيق =============
if __name__ == '__main__':
    # إعدادات تشغيل uvicorn
    uvicorn_config = uvicorn.Config(
        app="main:fastapi_app",
        host="0.0.0.0",
        port=PORT,
        log_level="info",
        reload=False,
        server_header=False
    )
    
    server = uvicorn.Server(uvicorn_config)
    
    try:
        logger.info(f"🚀 بدء تشغيل السيرفر على المنفذ {PORT}")
        server.run()
    except Exception as e:
        logger.critical(f"فشل في تشغيل السيرفر: {e}")
