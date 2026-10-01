import os
BOT_TOKEN = os.getenv("BOT_TOKEN")


async def handle_symptoms_action(update, context):
    query = update.callback_query
    await query.answer()
    lang = getattr(context, "user_data", {}).get("lang", "ar")
    if lang == "en":
        msg = "🩺 *Clinical Symptom Checker (DDx):*\n\nPlease describe your symptoms in a message, or open our web tool:"
        btn = "🖥️ Open Symptom Checker Web"
    else:
        msg = "🩺 *فاحص الأعراض والتشخيص التفريقي السريري (DDx):*\n\nاكتب الآن أعراضك بالتفصيل في رسالة، أو افتح الفاحص التفاعلي بالموقع:"
        btn = "🖥️ فتح فاحص الأعراض الشامل بالموقع"
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(btn, url="https://web-dose.vercel.app/?welcome=1#symptoms")]])
    await query.message.reply_text(msg, reply_markup=kb, parse_mode="Markdown")


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os, re, logging, asyncio, base64
from datetime import datetime
import pytz
try:
    from supabase import create_client
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://finwslipvvasokmuxdla.supabase.co")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_7g9H8VEBGrgGcF9CEfLrNg_Bu6xlorY")  # dose_bot key
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
except Exception as e:
    print(f"❌ Supabase init error: {e}")
    supabase_client = None
TIMEZONE = pytz.timezone("Asia/Riyadh")

# ══════════════════════════════════════
# ربط البوت بـ API الموقع
# ══════════════════════════════════════
import urllib.request as _ur
import json as _json

API_BASE = os.environ.get("API_BASE", "https://web-dose.vercel.app")
BOT_SECRET = os.environ.get("BOT_SECRET", "bot-secret-key-123")

def api_check_sub(telegram_id: str) -> dict:
    """تحقق من اشتراك المستخدم عبر API الموقع"""
    try:
        req = _ur.Request(
            f"{API_BASE}/bot/verify/{telegram_id}",
            headers={"x-bot-secret": BOT_SECRET}
        )
        with _ur.urlopen(req, timeout=5) as r:
            return _json.loads(r.read())
    except:
        return {"linked": False, "has_sub": False, "plan": "Free",
                "search_limit": 5, "reminder_limit": 0,
                "register_url": "https://web-dose.vercel.app"}

def api_track_usage(telegram_id: str, action: str = "search") -> dict:
    """يسجّل استخدام ويعيد هل مسموح أم لا"""
    try:
        req = _ur.Request(
            f"{API_BASE}/bot/track/{telegram_id}?action={action}",
            method="POST",
            headers={"x-bot-secret": BOT_SECRET, "Content-Length": "0"}
        )
        with _ur.urlopen(req, timeout=5) as r:
            return _json.loads(r.read())
    except:
        return {"allowed": True, "used": 0, "limit": -1}

LINK_MSG = {
    "ar": "🔗 *ربط حساب الموقع*\n\nبربط حسابك ستحصل على:\n✅ اشتراك موحد للموقع والبوت\n✅ لوحة تحكم كاملة\n✅ تاريخ بحث محفوظ\n\n👇 سجّل من هنا:",
    "en": "🔗 *Link Website Account*\n\nBy linking you get:\n✅ Unified subscription\n✅ Full dashboard\n✅ Saved history\n\n👇 Register here:"
}
LINK_URL = "https://web-dose.vercel.app"


# قاموس الدول والمناطق الزمنية
COUNTRY_TIMEZONES = {
    # العربية
    "السعودية":"Asia/Riyadh","سعودية":"Asia/Riyadh","saudi":"Asia/Riyadh","ksa":"Asia/Riyadh",
    "الإمارات":"Asia/Dubai","امارات":"Asia/Dubai","uae":"Asia/Dubai","dubai":"Asia/Dubai",
    "الكويت":"Asia/Kuwait","kuwait":"Asia/Kuwait",
    "قطر":"Asia/Qatar","qatar":"Asia/Qatar",
    "البحرين":"Asia/Bahrain","bahrain":"Asia/Bahrain",
    "عمان":"Asia/Muscat","oman":"Asia/Muscat",
    "اليمن":"Asia/Aden","yemen":"Asia/Aden",
    "العراق":"Asia/Baghdad","iraq":"Asia/Baghdad",
    "سوريا":"Asia/Damascus","syria":"Asia/Damascus",
    "لبنان":"Asia/Beirut","lebanon":"Asia/Beirut",
    "الأردن":"Asia/Amman","jordan":"Asia/Amman",
    "فلسطين":"Asia/Gaza","palestine":"Asia/Gaza",
    "مصر":"Africa/Cairo","egypt":"Africa/Cairo",
    "السودان":"Africa/Khartoum","sudan":"Africa/Khartoum",
    "ليبيا":"Africa/Tripoli","libya":"Africa/Tripoli",
    "تونس":"Africa/Tunis","tunisia":"Africa/Tunis",
    "الجزائر":"Africa/Algiers","algeria":"Africa/Algiers",
    "المغرب":"Africa/Casablanca","morocco":"Africa/Casablanca",
    "موريتانيا":"Africa/Nouakchott","mauritania":"Africa/Nouakchott",
    "الصومال":"Africa/Mogadishu","somalia":"Africa/Mogadishu",
    "جيبوتي":"Africa/Djibouti","djibouti":"Africa/Djibouti",
    "تركيا":"Europe/Istanbul","turkey":"Europe/Istanbul",
    "إيران":"Asia/Tehran","iran":"Asia/Tehran",
    "باكستان":"Asia/Karachi","pakistan":"Asia/Karachi",
    "أفغانستان":"Asia/Kabul","afghanistan":"Asia/Kabul",
    # أوروبا
    "بريطانيا":"Europe/London","uk":"Europe/London","england":"Europe/London",
    "فرنسا":"Europe/Paris","france":"Europe/Paris",
    "ألمانيا":"Europe/Berlin","germany":"Europe/Berlin",
    "هولندا":"Europe/Amsterdam","netherlands":"Europe/Amsterdam",
    "بلجيكا":"Europe/Brussels","belgium":"Europe/Brussels",
    "السويد":"Europe/Stockholm","sweden":"Europe/Stockholm",
    "النرويج":"Europe/Oslo","norway":"Europe/Oslo",
    "الدنمارك":"Europe/Copenhagen","denmark":"Europe/Copenhagen",
    "سويسرا":"Europe/Zurich","switzerland":"Europe/Zurich",
    "إسبانيا":"Europe/Madrid","spain":"Europe/Madrid",
    "إيطاليا":"Europe/Rome","italy":"Europe/Rome",
    "اليونان":"Europe/Athens","greece":"Europe/Athens",
    "النمسا":"Europe/Vienna","austria":"Europe/Vienna",
    "بولندا":"Europe/Warsaw","poland":"Europe/Warsaw",
    # أمريكا
    "كندا":"America/Toronto","canada":"America/Toronto",
    "أمريكا":"America/New_York","usa":"America/New_York","us":"America/New_York",
    "المكسيك":"America/Mexico_City","mexico":"America/Mexico_City",
    "البرازيل":"America/Sao_Paulo","brazil":"America/Sao_Paulo",
    "الأرجنتين":"America/Argentina/Buenos_Aires","argentina":"America/Argentina/Buenos_Aires",
    # آسيا
    "الهند":"Asia/Kolkata","india":"Asia/Kolkata",
    "الصين":"Asia/Shanghai","china":"Asia/Shanghai",
    "اليابان":"Asia/Tokyo","japan":"Asia/Tokyo",
    "كوريا":"Asia/Seoul","korea":"Asia/Seoul",
    "ماليزيا":"Asia/Kuala_Lumpur","malaysia":"Asia/Kuala_Lumpur",
    "إندونيسيا":"Asia/Jakarta","indonesia":"Asia/Jakarta",
    "أستراليا":"Australia/Sydney","australia":"Australia/Sydney",
}

def get_timezone(ctx):
    tz_str = ctx.user_data.get("timezone", "Asia/Riyadh")
    try:
        return pytz.timezone(tz_str)
    except:
        return pytz.timezone("Asia/Riyadh")

def detect_country_tz(text):
    text = text.strip().lower()
    for key, tz in COUNTRY_TIMEZONES.items():
        if key in text or text in key:
            return tz
    return None

# قراءة .env
_env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(_env_file):
    with open(_env_file) as _f:
        for _line in _f:
            _line = _line.strip()
            if "=" in _line and not _line.startswith("#"):
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())
from telegram import Update, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.request import HTTPXRequest
from telegram.ext import PicklePersistence
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, ContextTypes, filters, JobQueue,
    PreCheckoutQueryHandler)
from telegram.constants import ParseMode
try:
    import httpx
    HTTPX_OK = True
except ImportError:
    HTTPX_OK = False

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
# Duplicate server removed safely

async def link_account_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /link لربط حساب الموقع"""
    uid = str(update.effective_user.id)
    lang = get_lang(context)
    
    sub = api_check_sub(uid)
    
    if sub.get("linked"):
        email = sub.get("email","")
        plan = sub.get("plan_ar", sub.get("plan","Free"))
        if lang == "ar":
            msg = f"✅ *حسابك مرتبط*\n\n📧 البريد: {email}\n💳 الخطة: {plan}\n\n[🌐 فتح لوحة التحكم](https://web-dose.vercel.app"
        else:
            msg = f"✅ *Account Linked*\n\n📧 Email: {email}\n💳 Plan: {plan}\n\n[🌐 Open Dashboard](https://web-dose.vercel.app"
    else:
        if lang == "ar":
            msg = f"🔗 *ربط حساب الموقع*\n\nاربط حسابك للحصول على:\n✅ اشتراك موحد للموقع والبوت\n✅ لوحة تحكم كاملة\n✅ تاريخ بحث محفوظ\n✅ تذكيرات متقدمة\n\n👇 سجّل أو ادخل من هنا:"
        else:
            msg = f"🔗 *Link Website Account*\n\nGet unified subscription for website & bot\n\n👇 Register or login here:"
        
    keyboard = [[InlineKeyboardButton(
        "🌐 تسجيل / دخول" if lang=="ar" else "🌐 Register / Login",
        url="https://web-dose.vercel.app/?welcome=1"
    )]]
    
    await update.message.reply_text(
        msg, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def upgrade_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /upgrade لترقية الاشتراك"""
    uid = str(update.effective_user.id)
    lang = get_lang(context)
    sub = api_check_sub(uid)
    plan = sub.get("plan_ar", sub.get("plan","Free"))
    
    if lang == "ar":
        msg = f"💳 *خطتك الحالية: {plan}*\n\nللترقية والحصول على:\n🔍 بحث غير محدود\n⏰ تذكيرات غير محدودة\n📄 تصدير PDF\n\n👇 اختر خطتك:"
    else:
        msg = f"💳 *Your plan: {plan}*\n\nUpgrade for:\n🔍 Unlimited search\n⏰ Unlimited reminders\n📄 PDF export\n\n👇 Choose your plan:"
    
    keyboard = [[InlineKeyboardButton(
        "⭐ الترقية الآن" if lang=="ar" else "⭐ Upgrade Now",
        url="https://web-dose.vercel.app/?welcome=1"
    )]]
    
    await update.message.reply_text(
        msg, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def main():
    drugs_count = 500
    try:
        with open("drugs.json", "r", encoding="utf-8") as _df:
            _ddata = json.load(_df)
            drugs_count = len(_ddata) if isinstance(_ddata, list) else len(_ddata.get("drugs", []))
    except Exception:
        pass
    print(f"✅ تم تحميل {drugs_count} دواء")
    print(f"✅ Supabase: {bool(supabase_client)}")
    if supabase_client:
        try:
            supabase_client.table("users").select("uid").limit(1).execute()
            print("✅ Supabase connection OK")
        except Exception as e:
            print(f"❌ Supabase error: {e}")
    persistence = PicklePersistence(filepath="bot_data.pkl")
    request = HTTPXRequest(http_version="1.1")
    app = Application.builder().token(BOT_TOKEN).request(request).persistence(persistence).build()
    app.add_handler(build_conv())
    app.add_handler(CallbackQueryHandler(rem_done, pattern="^rem_done_"), group=2)
    app.add_handler(CallbackQueryHandler(rem_show_photo, pattern="^rem_showphoto_"), group=2)
    app.add_handler(CallbackQueryHandler(rem_later, pattern="^rem_snooze_"), group=2)
    app.add_handler(CommandHandler("link", link_account_cmd))
    app.add_handler(CommandHandler("upgrade", upgrade_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("activate", activate_cmd))
    app.add_handler(CommandHandler("fixdose", fix_doses_cmd))
    app.add_handler(PreCheckoutQueryHandler(pre_checkout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    # استعادة التذكيرات
    import asyncio
    app.post_init = restore_reminders
    print("🚀 البوت يعمل!")
    app.add_handler(CallbackQueryHandler(handle_symptoms_action, pattern="^symptoms$"))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

# ═══════════════════════════════════════
# حاسبة BMI - كود نظيف
# ═══════════════════════════════════════


# ═══════════════════════════════════════
