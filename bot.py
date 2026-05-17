#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os, re, logging, asyncio, base64
from datetime import datetime
import pytz
try:
    from supabase import create_client
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
except Exception as e:
    supabase_client = None
TIMEZONE = pytz.timezone("Asia/Riyadh")

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
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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

BOT_TOKEN = "8755290007:AAFYx4C08Aqq9YB89uJqdhbkjiO5KB1R6CY"

# قراءة .env مبكراً
_env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(_env_file):
    with open(_env_file) as _f:
        for _line in _f:
            _line = _line.strip()
            if "=" in _line and not _line.startswith("#"):
                _k, _v = _line.split("=", 1)
                os.environ[_k.strip()] = _v.strip()

# قراءة .env قبل تعريف المتغيرات
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _ef:
        for _el in _ef:
            _el = _el.strip()
            if "=" in _el and not _el.startswith("#"):
                _ek, _ev = _el.split("=", 1)
                os.environ[_ek.strip()] = _ev.strip()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
logger.info(f"API Key loaded: {len(ANTHROPIC_API_KEY)} chars")
DRUGS_FILE = "drugs.json"
REMINDER_SOUND = "reminder.mp3"

(STATE_LANGUAGE, STATE_MAIN_MENU, STATE_DRUG_SEARCH,
 STATE_CHILD_DRUG, STATE_CHILD_WEIGHT,
 STATE_REM_MENU, STATE_REM_ADD_NAME, STATE_REM_ADD_TIME,
 STATE_REM_ADD_FREQ, STATE_REM_EDIT_SEL,
 STATE_REM_EDIT_FIELD, STATE_REM_EDIT_VAL,
 STATE_BMI_WEIGHT, STATE_BMI_HEIGHT,
 STATE_BMI_AGE, STATE_BMI_DRUG,
 STATE_CHILD_CONC, STATE_PREMIUM,
 STATE_COUNTRY, STATE_REM_DURATION, STATE_INFECTION_SITE,
 STATE_CAL_GENDER, STATE_CAL_AGE, STATE_CAL_WEIGHT, STATE_CAL_HEIGHT, STATE_CAL_ACTIVITY, STATE_CAL_DISEASE,
 STATE_FOOD_SEARCH, STATE_SUGAR, STATE_BP, STATE_BP_AGE,
 STATE_PAT_MENU, STATE_PAT_NAME, STATE_PAT_AGE, STATE_PAT_WEIGHT,
 STATE_PAT_GENDER, STATE_PAT_DISEASE, STATE_PAT_MEDS, STATE_PAT_ALLERGY,
 STATE_INTERACTION, STATE_DRUG_FORM, STATE_PAT_NOTE, STATE_PAT_LOG) = range(43)

TEXTS = {
"ar": {
"welcome": "🏥 *مرحباً في بوت حاسبة الجرعات*\n🏥 *Welcome to Dose Calculator Bot*\n\nاختر لغتك | Choose your language:",
"main_menu": "📋 *القائمة الرئيسية*\n\nاختر:",
"btn_search": "🔍 استعلام عن دواء",
"btn_child": "🍼 جرعات الأطفال",
"btn_remind": "⏰ التذكير بالأدوية",
"btn_patient": "👤 ملف المريض",
"btn_interaction": "⚠️ التفاعلات الدوائية",
"btn_settings": "⚙️ الإعدادات",
"btn_premium": "⭐ الاشتراك المميز",
"premium_menu": "⭐ *الاشتراك المميز*\n\nاختر خطتك:",
"btn_month": "🗓️ شهري — 200 ⭐ (~$4)",
"btn_3month": "📅 3 أشهر — 500 ⭐ (~$10) وفّر 17%",
"btn_6month": "📆 6 أشهر — 900 ⭐ (~$18) وفّر 25%",
"btn_year": "🎯 سنوي — 1500 ⭐ (~$30) وفّر 37%",
"premium_features": (
    "✨ *مميزات الاشتراك:*\n\n"
    "🔍 بحث في 500+ دواء\n"
    "📸 تحليل صور غير محدود\n"
    "🔔 تذكيرات غير محدودة\n"
    "📄 تقارير طبية PDF\n"
    "⚡ أولوية في الدعم\n"
    "🆕 ميزات جديدة أولاً"
),
"already_premium": "✅ أنت مشترك مميز حتى: {date}",
"payment_sent": "⭐ شكراً! جارٍ تفعيل اشتراكك...",
"payment_success": "🎉 *تم تفعيل اشتراكك المميز!*\n\nصالح حتى: {date}",
"not_premium": "⭐ هذه الميزة للمشتركين المميزين فقط.\nاضغط لمعرفة المزيد:",
"btn_bmi": "📊 الوزن المثالي (BMI)",
"btn_cal": "🔥 حاسبة السعرات",
"btn_sugar": "🩸 ⭐ قراءة السكر",
"btn_bp": "💉 ⭐ قراءة الضغط",
"bmi_prompt_weight": "⚖️ أدخل وزن الطفل بالكيلوغرام:",
"bmi_prompt_height": "📏 أدخل طول الطفل بالسنتيمتر:",
"bmi_prompt_age": "🎂 أدخل عمر الطفل بالسنوات:",
"bmi_prompt_drug": "💊 أدخل اسم الدواء لحساب جرعته:",
"bmi_result": "📊 *نتيجة BMI*",
"bmi_underweight": "نقص وزن",
"bmi_normal": "وزن طبيعي",
"bmi_overweight": "زيادة وزن",
"bmi_obese": "سمنة",
"btn_back": "🔙 العودة للقائمة",
"search_prompt": "🔍 اكتب اسم الدواء أو أرسل صورة العلبة 📸:",
"not_found": "❌ لم يُعثر على دواء. حاول مرة أخرى.",
"multi_results": "🔍 نتائج متعددة، اختر:",
"child_prompt": "🍼 اكتب اسم الدواء أو أرسل صورة العبوة\n\n📸 *تعليمات التصوير:*\n• صوّر الوجه الأمامي للعبوة\n• تأكد أن الاسم والتركيز واضحان\n• مثال: 250مغ/5مل أو 100mg/5ml\n• الإضاءة جيدة والصورة واضحة\n• 💡 أفضل نتيجة إذا كان الاسم الإنجليزي ظاهراً",
"weight_prompt": "⚖️ أدخل وزن الطفل بالكيلوغرام:",
"bad_weight": "❌ وزن غير صحيح. أدخل رقماً بين 1 و 100.",
"analyzing": "🔎 جارٍ تحليل الصورة...",
"img_error": "❌ تعذّر التعرف على الدواء. اكتب الاسم نصاً.",
"no_api": "⚠️ تحليل الصور غير مفعّل. اكتب الاسم.",
"rem_menu": "⏰ *خدمة التذكير*\n\nاختر:",
"btn_add": "➕ إضافة تذكير",
"btn_list": "📋 تذكيراتي",
"btn_edit": "✏️ تعديل",
"btn_del": "🗑️ حذف",
"rem_name": "💊 اكتب اسم الدواء:",
"rem_time": "🕐 أدخل وقت التذكير HH:MM مثال 08:00",
"rem_freq": "🔁 كم مرة يومياً؟ من 1 إلى 6:",
"no_rems": "📭 لا توجد تذكيرات.",
"rems_title": "📋 *تذكيراتك:*\n\n",
"rem_deleted": "🗑️ تم الحذف.",
"rem_updated": "✅ تم التحديث.",
"rem_not_found": "❌ التذكير غير موجود.",
"alert": "🔔 *تذكير!*\n\n💊 حان وقت: *{drug}*",
"settings": "⚙️ *الإعدادات*",
"change_country": "🌍 تغيير الدولة",
"change_lang": "🌐 تغيير اللغة",
"sel_del": "🗑️ اختر تذكيراً للحذف:",
"sel_edit": "✏️ اختر تذكيراً للتعديل:",
"edit_fields": "✏️ ماذا تريد تعديل؟",
"ef_name": "💊 اسم الدواء",
"ef_time": "🕐 الوقت",
"ef_freq": "🔁 التكرار",
"new_val": "✏️ أدخل القيمة الجديدة:",

"bad_time": "❌ صيغة خاطئة. مثال: 08:30",
"bad_freq": "❌ أدخل رقماً من 1 إلى 6.",
},
"en": {
"welcome": "🏥 *مرحباً في بوت حاسبة الجرعات*\n🏥 *Welcome to Dose Calculator Bot*\n\nاختر لغتك | Choose your language:",
"main_menu": "📋 *Main Menu*\n\nChoose:",
"btn_search": "🔍 Drug Search",
"btn_child": "🍼 Child Doses",
"btn_remind": "⏰ Reminders",
"btn_patient": "👤 Patient File",
"btn_interaction": "⚠️ Drug Interactions",
"btn_settings": "⚙️ Settings",
"btn_premium": "⭐ Premium Subscription",
"premium_menu": "⭐ *Premium Subscription*\n\nChoose your plan:",
"btn_month": "🗓️ Monthly — 200 ⭐ (~$4)",
"btn_3month": "📅 3 Months — 500 ⭐ (~$10) Save 17%",
"btn_6month": "📆 6 Months — 900 ⭐ (~$18) Save 25%",
"btn_year": "🎯 Yearly — 1500 ⭐ (~$30) Save 37%",
"premium_features": (
    "✨ *Premium Features:*\n\n"
    "🔍 Search 500+ drugs\n"
    "📸 Unlimited image analysis\n"
    "🔔 Unlimited reminders\n"
    "📄 Medical PDF reports\n"
    "⚡ Priority support\n"
    "🆕 New features first"
),
"already_premium": "✅ You are subscribed until: {date}",
"payment_sent": "⭐ Thank you! Activating your subscription...",
"payment_success": "🎉 *Premium activated!*\n\nValid until: {date}",
"not_premium": "⭐ This feature is for premium subscribers only.\nTap to learn more:",
"btn_bmi": "📊 Ideal Weight (BMI)",
"btn_cal": "🔥 Calorie Calculator",
"btn_sugar": "🩸 ⭐ Blood Sugar",
"btn_bp": "💉 ⭐ Blood Pressure",
"bmi_prompt_weight": "⚖️ Enter child weight in kg:",
"bmi_prompt_height": "📏 Enter child height in cm:",
"bmi_prompt_age": "🎂 Enter child age in years:",
"bmi_prompt_drug": "💊 Enter drug name for dose calculation:",
"bmi_result": "📊 *BMI Result*",
"bmi_underweight": "Underweight",
"bmi_normal": "Normal weight",
"bmi_overweight": "Overweight",
"bmi_obese": "Obese",
"btn_back": "🔙 Back to Menu",
"search_prompt": "🔍 Type the drug name or part of it:",
"not_found": "❌ Drug not found. Try again.",
"multi_results": "🔍 Multiple results, choose:",
"child_prompt": "🍼 Type drug name or send a photo of the packaging\n\n📸 *Photo Tips:*\n• Take front of the packaging\n• Name and concentration must be clear\n• Example: 250mg/5ml or 120mg/5ml\n• Good lighting, clear image",
"weight_prompt": "⚖️ Enter child weight in kg:",
"bad_weight": "❌ Invalid weight. Enter 1 to 100.",
"analyzing": "🔎 Analyzing image...",
"img_error": "❌ Could not identify drug. Type the name.",
"no_api": "⚠️ Image analysis not enabled. Type the name.",
"rem_menu": "⏰ *Reminder Service*\n\nChoose:",
"btn_add": "➕ Add Reminder",
"btn_list": "📋 My Reminders",
"btn_edit": "✏️ Edit",
"btn_del": "🗑️ Delete",
"rem_name": "💊 Enter drug name:",
"rem_time": "🕐 Enter reminder time HH:MM e.g. 08:00",
"rem_freq": "🔁 How many times per day? 1 to 6:",
"no_rems": "📭 No reminders yet.",
"rems_title": "📋 *Your Reminders:*\n\n",
"rem_deleted": "🗑️ Deleted.",
"rem_updated": "✅ Updated.",
"rem_not_found": "❌ Reminder not found.",
"alert": "🔔 *Reminder!*\n\n💊 Time to take: *{drug}*",
"settings": "⚙️ *Settings*",
"change_country": "🌍 تغيير الدولة",
"change_country": "🌍 Change Country",
"change_lang": "🌐 Change Language",
"sel_del": "🗑️ Select reminder to delete:",
"sel_edit": "✏️ Select reminder to edit:",
"edit_fields": "✏️ What to edit?",
"ef_name": "💊 Drug name",
"ef_time": "🕐 Time",
"ef_freq": "🔁 Frequency",
"new_val": "✏️ Enter new value:",
"bad_time": "❌ Wrong format. Example: 08:30",
"bad_freq": "❌ Enter a number from 1 to 6.",
},
}

def tx(key, lang): return TEXTS.get(lang, TEXTS["ar"]).get(key, key)
def get_lang(ctx): return ctx.user_data.get("lang", "ar")

def load_drugs():
    try:
        with open(DRUGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list): return data
        for k in ("drugs", "data", "medications"):
            if k in data: return data[k]
        return []
    except Exception as e:
        logger.error(f"drugs.json error: {e}"); return []

DRUGS_DB = load_drugs()

def load_syrups():
    try:
        with open("syrups.json", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

SYRUPS_MAP = load_syrups()

def search_by_syrup_name(q):
    """البحث باسم الشراب التجاري"""
    q = q.strip().lower()
    # بحث مباشر
    if q in SYRUPS_MAP:
        return SYRUPS_MAP[q]
    # بحث جزئي
    for k, v in SYRUPS_MAP.items():
        if q in k.lower() or k.lower() in q:
            return v
    return None

# ─── إحصائيات البوت ───
STATS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stats.json")

def load_stats():
    # نقرأ من Supabase أولاً
    if supabase_client:
        try:
            res = supabase_client.table("stats").select("data").eq("id", "all").execute()
            if res.data:
                return json.loads(res.data[0]["data"])
        except Exception as e:
            logger.error(f"load_stats supabase: {e}")
    # fallback للملف المحلي
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"users": {}, "searches": 0, "child_doses": 0, "reminders": 0, "total_requests": 0, "image_search": 0, "bmi": 0, "calories": 0, "sugar": 0, "bp": 0}

def save_stats(stats):
    # نحفظ في Supabase
    if supabase_client:
        try:
            supabase_client.table("stats").upsert({"id": "all", "data": json.dumps(stats, ensure_ascii=False)}).execute()
        except Exception as e:
            logger.error(f"save_stats supabase: {e}")
    # نحفظ محلياً أيضاً
    try:
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"save_stats local: {e}")

def track(ctx, action="search"):
    stats = load_stats()
    uid = str(ctx.effective_user.id) if hasattr(ctx, "effective_user") and ctx.effective_user else "unknown"
    stats["users"][uid] = stats["users"].get(uid, 0) + 1
    stats[action] = stats.get(action, 0) + 1
    stats["total_requests"] = stats.get("total_requests", 0) + 1
    save_stats(stats)

def search_drugs(q):
    q = q.strip().lower()
    if not q: return []
    # البحث في قاموس الشرابات أولاً
    syrup_generic = search_by_syrup_name(q)
    if syrup_generic:
        q_mapped = syrup_generic.lower()
    else:
        q_mapped = q
    # قاموس الأسماء التجارية الشهيرة
    TRADE_MAP = {
        "panadol":"paracetamol","بنادول":"paracetamol","calpol":"paracetamol",
        "tylenol":"paracetamol","adol":"paracetamol","كالبول":"paracetamol",
        "nurofen":"ibuprofen","نوروفين":"ibuprofen","advil":"ibuprofen",
        "brufen":"ibuprofen","بروفين":"ibuprofen","motrin":"ibuprofen",
        "augmentin":"amoxicillin_clavulanate","أوجمنتين":"amoxicillin_clavulanate","كلافوكس":"amoxicillin_clavulanate","clavox":"amoxicillin_clavulanate","كلافاموكس":"amoxicillin_clavulanate","clavamox":"amoxicillin_clavulanate","كو-أموكسيكلاف":"amoxicillin_clavulanate","co-amoxiclav":"amoxicillin_clavulanate","كلافولانيك":"amoxicillin_clavulanate",
        "amoxil":"amoxicillin","أموكسيل":"amoxicillin",
        "zithromax":"azithromycin","زيثروماكس":"azithromycin",
        "glucophage":"metformin","جلوكوفاج":"metformin",
        "ventolin":"salbutamol","فنتولين":"salbutamol",
        "flagyl":"metronidazole","فلاجيل":"metronidazole",
        "voltaren":"diclofenac","فولتارين":"diclofenac",
        "nexium":"esomeprazole","نيكسيوم":"esomeprazole",
        "losec":"omeprazole","لوسك":"omeprazole",
        "klacid":"clarithromycin","كلاسيد":"clarithromycin",
        "diflucan":"fluconazole","ديفلوكان":"fluconazole",
        "cipro":"ciprofloxacin","سيبرو":"ciprofloxacin",
        "crestor":"rosuvastatin","كريستور":"rosuvastatin",
        "lipitor":"atorvastatin","ليبيتور":"atorvastatin",
        "concor":"bisoprolol","كونكور":"bisoprolol",
        "norvasc":"amlodipine","نورفاسك":"amlodipine",
        "lasix":"furosemide","لاسيكس":"furosemide",
        "aldactone":"spironolactone","ألداكتون":"spironolactone",
        "coversyl":"perindopril","كوفرسيل":"perindopril",
        "xarelto":"rivaroxaban","زاريلتو":"rivaroxaban",
        "plavix":"clopidogrel","بلافيكس":"clopidogrel",
        "lantus":"insulin_glargine","لانتوس":"insulin_glargine",
                        "zantac":"ranitidine","زانتاك":"ranitidine",
                "scobinal":"hyoscine_butylbromide","scobinal analysis":"hyoscine_butylbromide","scobinal syrup":"hyoscine_butylbromide","سكوبينال":"hyoscine_butylbromide",
                "buscopan":"hyoscine_butylbromide","بوسكوبان":"hyoscine_butylbromide",
                "claritine":"loratadine","claritin":"loratadine","كلاريتين":"loratadine",
                "zyrtec":"cetirizine","زيرتيك":"cetirizine",
                "aerius":"desloratadine","إيريوس":"desloratadine",
                "xyzal":"levocetirizine","زيزال":"levocetirizine",
                "bilaxten":"bilastine","بيلاكستن":"bilastine",
                "tavanic":"levofloxacin","تافانيك":"levofloxacin",
                "avelox":"moxifloxacin","أفيلوكس":"moxifloxacin",
                "zinnat":"cefuroxime","زينات":"cefuroxime",
                "rocephin":"ceftriaxone","روسيفين":"ceftriaxone",
                "dalacin":"clindamycin","دالاسين":"clindamycin",
                "vancocin":"vancomycin","فانكوسين":"vancomycin",
                "meronem":"meropenem","ميرونيم":"meropenem",
                "zovirax":"acyclovir","زوفيراكس":"acyclovir",
                "synthroid":"levothyroxine","سينثرويد":"levothyroxine",
                "eltroxin":"levothyroxine","إلتروكسين":"levothyroxine",
                "tapazole":"methimazole","تابازول":"methimazole",
                "deltacortril":"prednisolone","ديلتاكورتريل":"prednisolone",
                "decadron":"dexamethasone","ديكادرون":"dexamethasone",
                "betnovate":"betamethasone_cream","بيتنوفيت":"betamethasone_cream",
                "nasonex":"mometasone_nasal","ناسونيكس":"mometasone_nasal",
                "pulmicort":"budesonide_inhaler","بولميكورت":"budesonide_inhaler",
                "seretide":"fluticasone_salmeterol","سيريتيد":"fluticasone_salmeterol",
                "symbicort":"budesonide_formoterol","سيمبيكورت":"budesonide_formoterol",
                "spiriva":"tiotropium","سبيريفا":"tiotropium",
                "singulair":"montelukast","سينجولير":"montelukast",
                "keppra":"levetiracetam","كيبرا":"levetiracetam",
                "topamax":"topiramate","توباماكس":"topiramate",
                "lamictal":"lamotrigine","لاميكتال":"lamotrigine",
                "lyrica":"pregabalin","ليريكا":"pregabalin",
                "neurontin":"gabapentin","نيورونتين":"gabapentin",
                "depakine":"valproate","ديباكين":"valproate",
                "tegretol":"carbamazepine","تيجريتول":"carbamazepine",
                "risperdal":"risperidone","ريسبردال":"risperidone",
                "zyprexa":"olanzapine","زيبريكسا":"olanzapine",
                "seroquel":"quetiapine","سيروكويل":"quetiapine",
                "abilify":"aripiprazole","أبيليفاي":"aripiprazole",
                "haldol":"haloperidol","هالدول":"haloperidol",
                "stilnox":"zolpidem","ستيلنوكس":"zolpidem",
                "prozac":"fluoxetine","بروزاك":"fluoxetine",
                "zoloft":"sertraline","زولوفت":"sertraline",
                "lexapro":"escitalopram","ليكسابرو":"escitalopram",
                "effexor":"venlafaxine","إيفيكسور":"venlafaxine",
                "aricept":"donepezil","أريسيبت":"donepezil",
                "plaquenil":"hydroxychloroquine","بلاكينيل":"hydroxychloroquine",
                "imuran":"azathioprine","إيموران":"azathioprine",
                "cellcept":"mycophenolate","سيلسبت":"mycophenolate",
                "sandimmun":"cyclosporine","سانديمون":"cyclosporine",
                "humira":"adalimumab","هيوميرا":"adalimumab",
                "remicade":"infliximab","ريميكيد":"infliximab",
                "duphalac":"lactulose","دوفالاك":"lactulose",
                "imodium":"loperamide","إيموديوم":"loperamide",
                "maxolon":"metoclopramide","ماكسولون":"metoclopramide",
                "zofran":"ondansetron","زوفران":"ondansetron",
                "pantoloc":"pantoprazole","بانتولوك":"pantoprazole",
                "zyloric":"allopurinol","زيلوريك":"allopurinol",
                "mobic":"meloxicam","موبيك":"meloxicam",
                "ponstan":"mefenamic_acid","بونستان":"mefenamic_acid",
                "tramal":"tramadol","ترامال":"tramadol",
                "clomid":"clomiphene","كلوميد":"clomiphene",
                "clexane":"enoxaparin","كليكسان":"enoxaparin",
                "eliquis":"apixaban","إليكويس":"apixaban",
                "pradaxa":"dabigatran","برادكسا":"dabigatran",
                "jardiance":"empagliflozin","جارديانس":"empagliflozin",
                "forxiga":"dapagliflozin","فوركسيجا":"dapagliflozin",
                "ozempic":"semaglutide","أوزمبيك":"semaglutide",
                "procoralan":"ivabradine","بروكورالان":"ivabradine",
                "roaccutane":"isotretinoin","رواكيوتان":"isotretinoin",
                "betadine":"povidone_iodine","بيتادين":"povidone_iodine",
                "phenergan":"promethazine","فينيرغان":"promethazine",
                "stugeron":"cinnarizine","ستوجيرون":"cinnarizine",
                "serc":"betahistine","سيرك":"betahistine",
                "flomax":"tamsulosin","فلوماكس":"tamsulosin",
                "viagra":"sildenafil","فياغرا":"sildenafil",
                "cialis":"tadalafil","سياليس":"tadalafil",
                "macrobid":"nitrofurantoin","ماكروبيد":"nitrofurantoin",
                "narcan":"naloxone","ناركان":"naloxone",
                "diprivan":"propofol","ديبريفان":"propofol",
                "ketalar":"ketamine","كيتالار":"ketamine",
                "dormicum":"midazolam","دورميكم":"midazolam",
                "triprolidine_pseudoephedrine":"triprolidine_pseudoephedrine","bronchikam":"bronchikam","برونشيكام":"bronchikam","bronchicum":"bronchikam","برونكام":"bronchikam","actifed":"triprolidine_pseudoephedrine","أكتيفيد":"triprolidine_pseudoephedrine","اكتيفيد":"triprolidine_pseudoephedrine","actifed":"triprolidine_pseudoephedrine","dextromethorphan":"dextromethorphan","guaifenesin":"guaifenesin","chlorpheniramine_pseudoephedrine":"chlorpheniramine_pseudoephedrine","coldact":"chlorpheniramine_pseudoephedrine","diphenhydramine":"diphenhydramine","promethazine":"promethazine","chlorpheniramine":"chlorpheniramine","aspirin":"acetylsalicylic_acid","أسبرين":"acetylsalicylic_acid",
                "باراسيتامول":"paracetamol","بنادول":"paracetamol","بانادول":"paracetamol",
                "إيبوبروفين":"ibuprofen","ايبوبروفين":"ibuprofen","نيوروفين":"ibuprofen","نيورفين":"ibuprofen",
                "أموكسيسيلين":"amoxicillin","اموكسيسيلين":"amoxicillin",
                "ميترونيدازول":"metronidazole","ميتفورمين":"metformin",
                "سيتيريزين":"cetirizine","لوراتادين":"loratadine",
                "أزيثروميسين":"azithromycin","كلاريثروميسين":"clarithromycin",
                "سالبيوتامول":"salbutamol","فنتولين":"salbutamol",
                "هيوسين":"hyoscine_butylbromide","هيوسين بيوتيلبروميد":"hyoscine_butylbromide",
                "analysis of panadol":"paracetamol","panadol baby":"paracetamol",
                "panadol baby &":"paracetamol","scobinal analysis":"hyoscine_butylbromide",
                "looking at the":"unknown","analysis of":"unknown",
            }
    # تحويل الاسم التجاري للعلمي
    mapped = TRADE_MAP.get(q, q_mapped)
    # تطبيع النص - استبدال المسافات بشرطة سفلية والعكس
    q_normalized = q.replace(" ", "_").replace("-", "_")
    mapped_normalized = mapped.replace(" ", "_").replace("-", "_")
    out = []
    seen = set()
    for d in DRUGS_DB:
        ar = str(d.get("name_ar", "")).lower()
        en = str(d.get("name_en", "")).lower()
        aliases = str(d.get("aliases", "")).lower()
        key = en or ar
        if key in seen: continue
        if (q in ar or q in en or q in aliases or
            mapped in en or mapped in aliases or
            q_mapped in en or q_mapped in aliases or
            ar.startswith(q) or en.startswith(q) or
            en.startswith(mapped) or en.startswith(q_mapped)):
            out.append(d)
            seen.add(key)
    return out[:12]

def clean_val(v):
    """تنظيف القيمة من الأقواس والمسافات الزائدة"""
    if not v: return "—"
    if isinstance(v, dict):
        s = v.get("details", v.get("detailsen", v.get("status", "")))
        return str(s).strip() or "—"
    if isinstance(v, list):
        cleaned = []
        for i in v:
            s = str(i).strip().strip("'").strip('"')
            if s: cleaned.append(s)
        return ", ".join(cleaned) if cleaned else "—"
    s = str(v).strip().strip("'").strip('"')
    return s if s and s != "nan" else "—"


AR_TO_EN = {
    "مرة يوميًا":"once daily", "مرتين يوميًا":"twice daily",
    "3 مرات يوميًا":"3 times daily", "4 مرات يوميًا":"4 times daily",
    "يمنع إذا GFR < 30":"Avoid if GFR < 30",
    "لا حاجة لتعديل الجرعة":"No dose adjustment needed",
    "لا تعديل":"No adjustment", "لا تعديل الجرعة":"No dose adjustment",
    "مسموح":"Allowed", "ممنوع":"Contraindicated", "بحذر":"Use with caution",
    "مسموح بحذر":"Allowed with caution",
    "تعديل الجرعة":"Dose adjustment needed",
    "2 مرات يوميًا":"twice daily", "1 مرة يوميًا":"once daily",
    "غير محدد":"Not specified",
}

def ar_to_en(text):
    if not text or text == "—": return text
    return AR_TO_EN.get(str(text).strip(), str(text))

def fmt_drug(drug, lang):
    def g(*keys, fb="—"):
        for k in keys:
            v = drug.get(k, "")
            if v and str(v).strip() and str(v).strip() != "nan":
                return clean_val(v)
        return fb
    def dose_child():
        mn = drug.get("pediatric_min_mg_per_kg","")
        mx = drug.get("pediatric_max_mg_per_kg","")
        mpk = drug.get("pediatric_mg_per_kg","")
        if mn and mx: return f"{mn}–{mx} mg/kg"
        if mpk: return f"{mpk} mg/kg"
        return "—"
    def dose_adult():
        mn = drug.get("adult_dose_min","")
        mx = drug.get("adult_dose_max","")
        if mn and mx: return f"{mn}–{mx} mg"
        if mn: return f"{mn} mg"
        return "—"
    drug_link = f"https://www.drugs.com/{drug.get('name_en','').lower().replace(' ','_')}.html"
    if lang == "ar":
        n = g("name_ar","name_en")
        return (f"💊 *{n}*\n\n"
            f"🔬 *التصنيف الدوائي:* {g('drug_class','drug_class_en')}\n"
            f"🏷️ *الأسماء التجارية:* {g('aliases','drug_class')}\n"
            f"👶 *جرعة الأطفال:* {dose_child()}\n"
            f"🔁 *تكرار الأطفال:* {g('pediatric_frequency','pediatric_frequency_en')}\n"
            f"🧑 *جرعة الكبار:* {dose_adult()}\n"
            f"🔁 *تكرار الكبار:* {g('adult_frequency','adult_frequency_en')}\n"
            f"⚠️ *الحد الأقصى:* {g('max_daily','max_daily_pediatric')}\n\n"
            f"🚫 *موانع:* {g('contraindications','contraindications_en')}\n"
            f"⚡ *آثار جانبية:* {g('side_effects','side_effects_en')}\n"
            f"💊 *التفاعلات:* {g('interactions','interactions_en')}\n\n"
            f"🤰 *الحمل:* {g('pregnancy','pregnancy_en')}\n"
            f"🍼 *الرضاعة:* {g('lactation','lactation_en')}\n"
            f"🫘 *الكلى:* {g('renal','renal_dose')}\n\n"
            f"🔗 [مزيد من المعلومات]({drug_link})")
    else:
        n = g("name_en","name_ar")
        return (f"💊 *{n}*\n\n"
            f"🔬 *Drug Class:* {g('drug_class_en','drug_class')}\n"
            f"🏷️ *Aliases:* {g('aliases','drug_class_en','drug_class')}\n"
            f"👶 *Child Dose:* {dose_child()}\n"
            f"🔁 *Child Frequency:* {ar_to_en(g('pediatric_frequency_en') if g('pediatric_frequency_en') != '—' else g('pediatric_frequency'))}\n"
            f"🧑 *Adult Dose:* {dose_adult()}\n"
            f"🔁 *Adult Frequency:* {ar_to_en(g('adult_frequency_en') if g('adult_frequency_en') != '—' else g('adult_frequency'))}\n"
            f"⚠️ *Max Daily:* {g('max_daily')}\n\n"
            f"🚫 *Contraindications:* {g('contraindications_en','contraindications')}\n"
            f"⚡ *Side Effects:* {g('side_effects_en','side_effects')}\n"
            f"💊 *Interactions:* {g('interactions_en','interactions')}\n\n"
            f"🤰 *Pregnancy:* {ar_to_en(g('pregnancy_en') if g('pregnancy_en') != '—' else g('pregnancy'))}\n"
            f"🍼 *Lactation:* {ar_to_en(g('lactation_en') if g('lactation_en') != '—' else g('lactation'))}\n"
            f"🫘 *Renal:* {g('renal','renal_dose')}\n\n"
            f"🔗 [More Information]({drug_link})")

def calc_child(drug, w, lang):
    name_ar = drug.get("name_ar", drug.get("name_en", "—"))
    name_en = drug.get("name_en", drug.get("name_ar", "—"))
    n = name_ar if lang == "ar" else name_en
    mn = drug.get("pediatric_min_mg_per_kg", "")
    mx = drug.get("pediatric_max_mg_per_kg", "")
    mpk_val = drug.get("pediatric_mg_per_kg", "")
    freq = drug.get("pediatric_frequency" if lang=="ar" else "pediatric_frequency_en",
                    drug.get("pediatric_frequency","—"))
    max_d = drug.get("max_daily_pediatric", drug.get("max_daily","—"))
    lines = []
    if lang == "ar":
        lines += ["🍼 جرعة الطفل - " + n, "⚖️ الوزن: " + str(w) + " كغ", ""]
    else:
        lines += ["🍼 Child Dose - " + n, "⚖️ الوزن: " + str(w) + " kg", ""]

    # معالجة فيتامين د بالقطرات
    if drug.get("name_en") == "vitamin_d_drops":
        try:
            conc_str = str(drug.get("concentration","400IU/drop"))
            conc_iu = int(conc_str.replace("IU/drop","").replace("IU/قطرة","").strip())
        except:
            conc_iu = 400
        d0 = round(400 / conc_iu, 1)
        d1 = round(600 / conc_iu, 1)
        d2 = round(800 / conc_iu, 1)
        if lang == "ar":
            lines2 = ["💊 فيتامين د — " + str(conc_iu) + " IU/قطرة", ""]
            lines2.append("📋 الجرعة اليومية بالقطرات:")
            lines2.append("  • 0-12 شهر: " + str(d0) + " قطرة (400 IU)")
            lines2.append("  • 1-5 سنوات: " + str(d1) + " قطرة (600 IU)")
            lines2.append("  • 5-12 سنة: " + str(d2) + " قطرة (800 IU)")
        else:
            lines2 = ["💊 Vitamin D — " + str(conc_iu) + " IU/drop", ""]
            lines2.append("📋 Daily dose in drops:")
            lines2.append("  • 0-12 months: " + str(d0) + " drops (400 IU)")
            lines2.append("  • 1-5 years: " + str(d1) + " drops (600 IU)")
            lines2.append("  • 5-12 years: " + str(d2) + " drops (800 IU)")
        lines2.append("")
        lines2.append("⚠️ " + ("استشر الطبيب أو الصيدلاني." if lang=="ar" else "Consult doctor or pharmacist."))
        return "\n".join(lines2)

    # معالجة الأدوية ذات الجرعة الثابتة حسب العمر
    if drug.get("fixed_dose") and drug.get("age_doses"):
        age_doses = drug["age_doses"]
        dose_lines = ["📋 " + ("جرعة الأطفال:" if lang=="ar" else "Pediatric Doses:")]
        for age_range, dose in age_doses.items():
            dose_lines.append("  • " + age_range + ": " + dose if lang=="ar" else "  • " + age_range + ": " + dose)
        dose_lines.append("")
        dose_lines.append("🔁 " + freq)
        dose_lines.append("⚠️ " + ("استشر الطبيب أو الصيدلاني." if lang=="ar" else "Consult doctor or pharmacist."))
        return chr(10).join(dose_lines)

    try:
        # تركيزات الشراب الشائعة لحساب المل
        CONCENTRATIONS = {
            # مسكنات الألم والحرارة
            "paracetamol": 120, "acetaminophen": 120,
            "panadol": 120, "calpol": 120, "adol": 120,
            "ibuprofen": 100, "nurofen": 100, "brufen": 100,
            # مضادات حيوية
            "amoxicillin": 125, "amoxil": 125,
            "amoxicillin_clavulanate": 125, "augmentin": 125,
            "azithromycin": 200, "zithromax": 200,
            "clarithromycin": 125, "klacid": 125,
            "cephalexin": 125, "cefalexin": 125,
            "metronidazole": 200, "flagyl": 200,
            "trimethoprim_sulfa": 200, "cotrimoxazole": 200,
            "erythromycin": 125,
            # مضادات الحساسية
            "cetirizine": 5, "loratadine": 5,
            "fexofenadine": 30, "desloratadine": 2.5,
            "chlorphenamine": 2, "diphenhydramine": 12.5,
            # أدوية الجهاز الهضمي
            "omeprazole": 20, "domperidone": 5,
            "metoclopramide": 5, "ondansetron": 4,
            # أدوية الجهاز التنفسي
            "salbutamol": 2, "ventolin": 2,
            "prednisolone": 15, "dexamethasone": 0.5,
            "montelukast": 4,
            # أدوية أخرى
            "fluconazole": 50, "diflucan": 50,
            "acyclovir": 200, "valacyclovir": 500,
            "vitamin_c": 100, "zinc": 10,
        }
        name_key = drug.get("name_en", "").lower()
        conc = CONCENTRATIONS.get(name_key, 0)
        # الصورة أولاً (أولوية أدنى)
        import builtins
        img_conc = getattr(builtins, "_last_concentration", None)
        if img_conc:
            mg_val, ml_val = img_conc
            conc = (mg_val / ml_val) * 5
            builtins._last_concentration = None
        # اختيار المستخدم يتجاوز الصورة (أولوية عليا)
        _user_conc = drug.get("concentration", "")
        if _user_conc and _user_conc != "unknown":
            import re as _re3
            _mc = _re3.search(r"([\d.]+)\s*mg\s*/\s*([\d.]+)\s*ml", _user_conc, _re3.IGNORECASE)
            if _mc: conc = float(_mc.group(1)) / float(_mc.group(2)) * 5

        if mn and mx:
            mpk_min = float(str(mn)); mpk_max = float(str(mx))
            t_min = mpk_min * w; t_max = mpk_max * w
            if lang == "ar":
                lines.append(f"📊 {mpk_min}–{mpk_max} مغ/كغ × {w} كغ")
                lines.append(f"💉 *الجرعة: {t_min:.1f}–{t_max:.1f} مغ*")
                if conc:
                    ml_min = (t_min/conc)*5; ml_max = (t_max/conc)*5
                    lines.append(f"🥄 *بالمل ({conc}مغ/5مل): {ml_min:.1f}–{ml_max:.1f} مل*")
            else:
                lines.append(f"📊 {mpk_min}–{mpk_max} mg/kg × {w} kg")
                lines.append(f"💉 *Dose: {t_min:.1f}–{t_max:.1f} mg*")
                if conc:
                    ml_min = (t_min/conc)*5; ml_max = (t_max/conc)*5
                    lines.append(f"🥄 *In mL ({conc}mg/5mL): {ml_min:.1f}–{ml_max:.1f} mL*")
        elif mpk_val:
            mpk = float(str(mpk_val)); total = mpk * w
            if lang == "ar":
                lines.append(f"📊 {mpk} مغ/كغ × {w} كغ = *{total:.1f} مغ*")
                if conc:
                    ml = (total/conc)*5
                    lines.append(f"🥄 *بالمل ({conc}مغ/5مل): {ml:.1f} مل*")
            else:
                lines.append(f"📊 {mpk} mg/kg × {w} kg = *{total:.1f} mg*")
                if conc:
                    ml = (total/conc)*5
                    lines.append(f"🥄 *In mL ({conc}mg/5mL): {ml:.1f} mL*")
        else:
            raise ValueError
        lines.append("")
        if lang == "ar":
            lines.append(f"🔁 *التكرار:* {freq}")
            lines.append(f"⚠️ *الحد الأقصى:* {max_d}")
        else:
            lines.append(f"🔁 *Frequency:* {freq}")
            lines.append(f"⚠️ *Max Daily:* {max_d}")
    except:
        cd = drug.get("pediatric_frequency" if lang=="ar" else "pediatric_frequency_en","—")
        lines.append(f"📋 *جرعة الأطفال:* {cd}" if lang=="ar" else f"📋 *Child Dose:* {cd}")
    lines += ["", "⚠️ استشر الطبيب أو الصيدلاني." if lang=="ar" else "⚠️ Consult a doctor or pharmacist."]
    return "\n".join(lines)


# قاعدة بيانات الأطعمة (سعرات لكل 100 غرام)
FOODS_DB = {
    # خبز وحبوب
    "خبز":"bread","bread":{"cal":265,"protein":9,"carbs":49,"fat":3.2},
    "أرز":"rice","rice":{"cal":130,"protein":2.7,"carbs":28,"fat":0.3},
    "معكرونة":"pasta","pasta":{"cal":131,"protein":5,"carbs":25,"fat":1.1},
    "شوفان":"oats","oats":{"cal":389,"protein":17,"carbs":66,"fat":7},
    # بروتين
    "دجاج":"chicken","chicken":{"cal":165,"protein":31,"carbs":0,"fat":3.6},
    "لحم بقر":"beef","beef":{"cal":250,"protein":26,"carbs":0,"fat":15},
    "سمك":"fish","fish":{"cal":136,"protein":23,"carbs":0,"fat":4.8},
    "بيض":"egg","egg":{"cal":155,"protein":13,"carbs":1.1,"fat":11},
    "تونة":"tuna","tuna":{"cal":144,"protein":30,"carbs":0,"fat":2.5},
    # ألبان
    "حليب":"milk","milk":{"cal":61,"protein":3.2,"carbs":4.8,"fat":3.3},
    "جبنة":"cheese","cheese":{"cal":402,"protein":25,"carbs":1.3,"fat":33},
    "زبادي":"yogurt","yogurt":{"cal":59,"protein":10,"carbs":3.6,"fat":0.4},
    # خضروات
    "طماطم":"tomato","tomato":{"cal":18,"protein":0.9,"carbs":3.9,"fat":0.2},
    "خيار":"cucumber","cucumber":{"cal":16,"protein":0.7,"carbs":3.6,"fat":0.1},
    "بطاطا":"potato","potato":{"cal":77,"protein":2,"carbs":17,"fat":0.1},
    "جزر":"carrot","carrot":{"cal":41,"protein":0.9,"carbs":10,"fat":0.2},
    # فواكه
    "تفاح":"apple","apple":{"cal":52,"protein":0.3,"carbs":14,"fat":0.2},
    "موز":"banana","banana":{"cal":89,"protein":1.1,"carbs":23,"fat":0.3},
    "برتقال":"orange","orange":{"cal":47,"protein":0.9,"carbs":12,"fat":0.1},
    # زيوت ومكسرات
    "زيت زيتون":"olive oil","olive oil":{"cal":884,"protein":0,"carbs":0,"fat":100},
    "لوز":"almonds","almonds":{"cal":579,"protein":21,"carbs":22,"fat":50},
    "عسل":"honey","honey":{"cal":304,"protein":0.3,"carbs":82,"fat":0},
    # وجبات سريعة
    "برغر":"burger","burger":{"cal":295,"protein":17,"carbs":24,"fat":14},
    "بيتزا":"pizza","pizza":{"cal":266,"protein":11,"carbs":33,"fat":10},
    "بطاطس مقلية":"fries","fries":{"cal":312,"protein":3.4,"carbs":41,"fat":15},
    # بقوليات
    "عدس":"lentils","lentils":{"cal":116,"protein":9,"carbs":20,"fat":0.4},
    "حمص":"chickpeas","chickpeas":{"cal":164,"protein":9,"carbs":27,"fat":2.6},
    "فول":"fava beans","fava beans":{"cal":110,"protein":8,"carbs":20,"fat":0.4},
    "فاصولياء":"beans","beans":{"cal":127,"protein":9,"carbs":23,"fat":0.5},
    "بازلاء":"peas","peas":{"cal":81,"protein":5,"carbs":14,"fat":0.4},
    # لحوم
    "لحم غنم":"lamb","lamb":{"cal":294,"protein":25,"carbs":0,"fat":21},
    "لحم مفروم":"ground beef","ground beef":{"cal":332,"protein":26,"carbs":0,"fat":25},
    "كبدة":"liver","liver":{"cal":175,"protein":27,"carbs":4,"fat":5},
    "دجاج مقلي":"fried chicken","fried chicken":{"cal":260,"protein":25,"carbs":11,"fat":14},
    "دجاج مشوي":"grilled chicken","grilled chicken":{"cal":165,"protein":31,"carbs":0,"fat":3.6},
    # أسماك
    "سمك مقلي":"fried fish","fried fish":{"cal":232,"protein":18,"carbs":8,"fat":14},
    "سمك مشوي":"grilled fish","grilled fish":{"cal":136,"protein":23,"carbs":0,"fat":4.8},
    "سلمون":"salmon","salmon":{"cal":208,"protein":20,"carbs":0,"fat":13},
    "جمبري":"shrimp","shrimp":{"cal":99,"protein":24,"carbs":0,"fat":0.3},
    # حلويات
    "كيك":"cake","cake":{"cal":347,"protein":5,"carbs":51,"fat":15},
    "شوكولاته":"chocolate","chocolate":{"cal":546,"protein":5,"carbs":60,"fat":31},
    "شوكولاتة":"chocolate","بسكويت":"biscuit","biscuit":{"cal":418,"protein":6,"carbs":70,"fat":13},
    "حلوى":"candy","candy":{"cal":380,"protein":0,"carbs":95,"fat":0},
    "آيس كريم":"ice cream","ice cream":{"cal":207,"protein":4,"carbs":24,"fat":11},
    "ايس كريم":"ice cream",
    "تمر":"dates","dates":{"cal":282,"protein":2.5,"carbs":75,"fat":0.4},
    "تمور":"dates",
    # مشروبات
    "قهوة":"coffee","coffee":{"cal":2,"protein":0.3,"carbs":0,"fat":0},
    "شاي":"tea","tea":{"cal":1,"protein":0,"carbs":0.2,"fat":0},
    "عصير برتقال":"orange juice","orange juice":{"cal":45,"protein":0.7,"carbs":10,"fat":0.2},
    "عصير تفاح":"apple juice","apple juice":{"cal":46,"protein":0.1,"carbs":11,"fat":0.1},
    "كولا":"cola","cola":{"cal":42,"protein":0,"carbs":11,"fat":0},
    "مياه":"water","water":{"cal":0,"protein":0,"carbs":0,"fat":0},
    "حليب كامل":"whole milk","whole milk":{"cal":61,"protein":3.2,"carbs":4.8,"fat":3.3},
    # وجبات عربية
    "شاورما":"shawarma","shawarma":{"cal":245,"protein":18,"carbs":20,"fat":10},
    "فلافل":"falafel","falafel":{"cal":333,"protein":13,"carbs":32,"fat":18},
    "كبة":"kibbeh","kibbeh":{"cal":268,"protein":15,"carbs":22,"fat":13},
    "منسف":"mansaf","mansaf":{"cal":320,"protein":22,"carbs":25,"fat":15},
    "كبسة":"kabsa","kabsa":{"cal":280,"protein":20,"carbs":30,"fat":8},
    "مجبوس":"majboos","majboos":{"cal":275,"protein":19,"carbs":29,"fat":8},
    "هريسة":"harees","harees":{"cal":180,"protein":12,"carbs":25,"fat":4},
}

def search_food(query):
    q = query.strip().lower()
    # نبحث في كل مفاتيح FOODS_DB مباشرة
    for key, val in FOODS_DB.items():
        if isinstance(val, dict):
            if q in key.lower() or key.lower() in q:
                return key, val
        elif isinstance(val, str):
            # هذا alias - نبحث عن القيمة
            if q in key.lower() or key.lower() in q:
                if val in FOODS_DB and isinstance(FOODS_DB[val], dict):
                    return val, FOODS_DB[val]
    return None, None

def calc_bmr(weight, height, age, gender):
    if gender == "m":
        return 10*weight + 6.25*height - 5*age + 5
    else:
        return 10*weight + 6.25*height - 5*age - 161

ACTIVITY_FACTORS = {
    "1": 1.2,   # خامل
    "2": 1.375, # خفيف
    "3": 1.55,  # متوسط
    "4": 1.725, # نشيط
    "5": 1.9,   # رياضي
}


# جرعات المضادات الحيوية حسب موقع الالتهاب (مغ/كغ/يوم)
ANTIBIOTIC_DOSES = {
    "amoxicillin": {
        "ear": (40, 45, 3, "التهاب الأذن والحلق"),
        "lung": (45, 90, 3, "التهاب الرئة"),
        "urinary": (20, 40, 3, "التهاب المسالك البولية"),
        "skin": (25, 50, 3, "التهاب الجلد"),
        "general": (20, 40, 3, "عام"),
    },
    "amoxicillin_clavulanate": {
        "ear": (40, 45, 2, "التهاب الأذن والحلق"),
        "lung": (45, 90, 2, "التهاب الرئة"),
        "urinary": (25, 45, 2, "التهاب المسالك البولية"),
        "skin": (25, 45, 2, "التهاب الجلد"),
        "general": (25, 45, 2, "عام"),
    },
    "azithromycin": {
        "ear": (10, 10, 1, "التهاب الأذن والحلق"),
        "lung": (10, 10, 1, "التهاب الرئة"),
        "skin": (10, 10, 1, "التهاب الجلد"),
        "general": (10, 10, 1, "عام"),
    },
    "clarithromycin": {
        "ear": (7.5, 15, 2, "التهاب الأذن والحلق"),
        "lung": (7.5, 15, 2, "التهاب الرئة"),
        "skin": (7.5, 15, 2, "التهاب الجلد"),
        "general": (7.5, 15, 2, "عام"),
    },
    "cephalexin": {
        "ear": (12.5, 25, 4, "التهاب الأذن والحلق"),
        "urinary": (12.5, 25, 4, "التهاب المسالك البولية"),
        "skin": (12.5, 25, 4, "التهاب الجلد"),
        "general": (12.5, 25, 4, "عام"),
    },
}

INFECTION_SITES = {
    "ar": [
        ("ear", "👂 أذن / حلق / جيوب"),
        ("lung", "🫁 رئة / صدر"),
        ("urinary", "🫘 مسالك بولية"),
        ("skin", "🩹 جلد / جروح"),
        ("general", "🔵 عام"),
    ],
    "en": [
        ("ear", "👂 Ear / Throat / Sinus"),
        ("lung", "🫁 Lung / Chest"),
        ("urinary", "🫘 Urinary Tract"),
        ("skin", "🩹 Skin / Wound"),
        ("general", "🔵 General"),
    ]
}

async def analyze_image(img_bytes, lang):
    try:
        import telegram as _tg
        bot = _tg.Bot(token=os.environ.get("TELEGRAM_BOT_TOKEN",""))
    except: pass
    if not HTTPX_OK or not ANTHROPIC_API_KEY:
        logger.warning("No API key")
        return ""
    b64 = base64.b64encode(img_bytes).decode()
    concentration = None
    try:
        key = ANTHROPIC_API_KEY.encode("ascii", errors="ignore").decode("ascii").strip()
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post("https://api.anthropic.com/v1/messages",
                headers={"x-api-key": key,
                         "anthropic-version": "2023-06-01",
                         "content-type": "application/json"},
                json={"model": "claude-haiku-4-5-20251001", "max_tokens": 200,
                    "messages": [{"role": "user", "content": [
                        {"type": "image", "source": {"type": "base64",
                            "media_type": "image/jpeg", "data": b64}},
                            {"type": "text", "text": "You are a pharmacist. Identify the medicine in this image. Return ONLY: generic_name|concentration (example: paracetamol|125mg/5ml). Brand names: Panadol=paracetamol, Nurofen/Brufen/Prof=ibuprofen, Augmentin=amoxicillin_clavulanate, Actifed=triprolidine_pseudoephedrine, Aerius=desloratadine, Xyzal=levocetirizine, Ventolin=salbutamol, Flagyl=metronidazole, Prospan/Ezyban=hedera_helix, Ferose/Maltofer=iron_syrup, Otrivin=xylometazoline, Fucidin=fusidic_acid, Phenergan=promethazine, Piriton=chlorpheniramine, Buscopan=hyoscine_butylbromide, Klacid=clarithromycin. If unclear: UNKNOWN|unknown. ONE LINE ONLY."}
                    ]}]})
        logger.info(f"Image API status: {r.status_code}")
        logger.info(f"Image API status: {r.status_code}")
        logger.info(f"Image API response: {r.text[:200]}")
        txt = r.json().get("content", [{}])[0].get("text", "").strip()
        import re as _re
        txt = txt.split("\n")[0].strip()
        logger.info(f"Raw image response: {txt}")
        if not txt or txt == "UNKNOWN":
            return ""
        # بحث في القاموس
        ARABIC_MAP = {"bronchikam":"guaifenesin","برونشيكام":"guaifenesin","bronchikam syrup":"guaifenesin","bronchikam syrup analysis":"guaifenesin","bronchicum":"guaifenesin","برونكام":"guaifenesin","برونشيكام":"guaifenesin","برونكيكام":"guaifenesin","bronchicum":"guaifenesin","كلورفينيرامين":"chlorpheniramine","chlorphenamine":"chlorpheniramine","كلور فينيرامين":"chlorpheniramine","جوايفينيزين":"guaifenesin","غوايفينيزين":"guaifenesin","guaifenisine":"guaifenesin","فينيلايفرين":"phenylephrine","فينيل ايفرين":"phenylephrine","فينيلفرين":"phenylephrine","phenylephrine":"phenylephrine","برونكيكام":"guaifenesin","bronchicum":"guaifenesin","phenylephrine":"phenylephrine","فينيلفرين":"phenylephrine","nasofed":"phenylephrine","ناسوفيد":"phenylephrine","xylometazoline hydrochloride":"xylometazoline","rovfenac":"diclofenac_suppository","diclogesic":"diclofenac_suppository","ديكلوجيزيك":"diclofenac_suppository","diclofenac suppository":"diclofenac_suppository","voltaren supp":"diclofenac_suppository","روفيناك":"diclofenac_suppository","voltaren suppository":"diclofenac_suppository","paracetamol suppository":"paracetamol_suppository","panadol suppository":"paracetamol_suppository","تحميلة باراسيتامول":"paracetamol_suppository","paracetamol supp":"paracetamol_suppository","fucidicacid":"fusidic_acid","fucidic acid":"fusidic_acid","fucidin":"fusidic_acid","فيوسيدين":"fusidic_acid","fusidic":"fusidic_acid","xylometazoline hcl":"xylometazoline","oxymetazoline":"xylometazoline","otrivin":"xylometazoline","أوتريفين":"xylometazoline","سبيرونولاكتون شراب":"spironolactone_syrup","سبيرنولاكتون":"spironolactone_syrup","سبيرونولاكتون":"spironolactone_syrup","spironolactone":"spironolactone_syrup","aldactone":"spironolactone_syrup","gentamicin":"gentamicin","جنتاميسين":"gentamicin","توبراديكس":"tobradex","tobradex":"tobradex","توبراميسين":"tobramycin","tobramycin":"tobramycin","سيبروفلوكساسين قطرة":"ciprofloxacin_drops","كلورامفينيكول قطرة":"chloramphenicol_drops","سوفراديكس":"sofradex","أوتوسبورين":"otosporin","جينتاميسين":"gentamicin","جنتامايسين":"gentamicin","garamycin":"gentamicin","غاراميسين":"gentamicin","غارامايسين":"gentamicin","ألداكتون":"spironolactone_syrup","aldactone syrup":"spironolactone_syrup","spironolactone syrup":"spironolactone_syrup","infacol":"simethicone","simeticone":"simethicone","dimethicone":"simethicone","zinc origin":"zinc_syrup","zinc sulfate":"zinc_syrup","ferric hydroxide":"iron_syrup","ferrous sulphate":"iron_syrup","ferose":"iron_syrup","فيرومين":"iron_syrup","feromin":"iron_syrup","فيروز":"iron_syrup","feroz":"iron_syrup","ferrum":"iron_syrup","فيرم":"iron_syrup","ferroussyrup":"iron_syrup","label analysis":"unknown","medicine label reading":"unknown","medicine label":"unknown","label reading":"unknown","i can see a":"unknown","this is a":"unknown","the image shows":"unknown","medicine bottle":"unknown","drug label":"unknown","® label":"iron_syrup","ferose® label analysis":"iron_syrup","ferrous syrup":"iron_syrup","ferrous sulfate":"iron_syrup","ferrous gluconate":"iron_syrup","iron sulphate":"iron_syrup","iron sulfate":"iron_syrup","zinc gluconate":"zinc_syrup","zinc acetate":"zinc_syrup","zinc chloride":"zinc_syrup","multivitamin":"multivitamin","multi vitamin":"multivitamin","فيتامينات متعددة":"multivitamin","ferrous sulfate":"iron_syrup","iron drops":"iron_syrup","iron supplement":"iron_syrup","vitamin d drops":"vitamin_d_drops","vitamin d3":"vitamin_d_drops","cholecalciferol":"vitamin_d_drops","colecalciferol":"vitamin_d_drops","vit d":"vitamin_d_drops","vit d3":"vitamin_d_drops","bronchikam":"guaifenesin","برونشيكام":"guaifenesin","bronchikam syrup":"guaifenesin","bronchikam syrup analysis":"guaifenesin","bronchicum":"guaifenesin","برونكام":"guaifenesin","برونشيكام":"guaifenesin","برونكيكام":"guaifenesin","bronchicum":"guaifenesin","كلورفينيرامين":"chlorpheniramine","chlorphenamine":"chlorpheniramine","كلور فينيرامين":"chlorpheniramine","جوايفينيزين":"guaifenesin","غوايفينيزين":"guaifenesin","guaifenisine":"guaifenesin","فينيلايفرين":"phenylephrine","فينيل ايفرين":"phenylephrine","فينيلفرين":"phenylephrine","phenylephrine":"phenylephrine","برونكيكام":"guaifenesin","bronchicum":"guaifenesin","phenylephrine":"phenylephrine","فينيلفرين":"phenylephrine","nasofed":"phenylephrine","ناسوفيد":"phenylephrine","xylometazoline hydrochloride":"xylometazoline","rovfenac":"diclofenac_suppository","diclogesic":"diclofenac_suppository","ديكلوجيزيك":"diclofenac_suppository","diclofenac suppository":"diclofenac_suppository","voltaren supp":"diclofenac_suppository","روفيناك":"diclofenac_suppository","voltaren suppository":"diclofenac_suppository","paracetamol suppository":"paracetamol_suppository","panadol suppository":"paracetamol_suppository","تحميلة باراسيتامول":"paracetamol_suppository","paracetamol supp":"paracetamol_suppository","fucidicacid":"fusidic_acid","fucidic acid":"fusidic_acid","fucidin":"fusidic_acid","فيوسيدين":"fusidic_acid","fusidic":"fusidic_acid","xylometazoline hcl":"xylometazoline","oxymetazoline":"xylometazoline","otrivin":"xylometazoline","أوتريفين":"xylometazoline","سبيرونولاكتون شراب":"spironolactone_syrup","سبيرنولاكتون":"spironolactone_syrup","سبيرونولاكتون":"spironolactone_syrup","spironolactone":"spironolactone_syrup","aldactone":"spironolactone_syrup","gentamicin":"gentamicin","جنتاميسين":"gentamicin","توبراديكس":"tobradex","tobradex":"tobradex","توبراميسين":"tobramycin","tobramycin":"tobramycin","سيبروفلوكساسين قطرة":"ciprofloxacin_drops","كلورامفينيكول قطرة":"chloramphenicol_drops","سوفراديكس":"sofradex","أوتوسبورين":"otosporin","جينتاميسين":"gentamicin","جنتامايسين":"gentamicin","garamycin":"gentamicin","غاراميسين":"gentamicin","غارامايسين":"gentamicin","ألداكتون":"spironolactone_syrup","aldactone syrup":"spironolactone_syrup","spironolactone syrup":"spironolactone_syrup","infacol":"simethicone","انفاكول":"simethicone","simethicone":"simethicone","سيميثيكون":"simethicone","mylicon":"simethicone","zincomed":"zinc_syrup","زنكوميد":"zinc_syrup","zinc_syrup":"zinc_syrup","زنك شراب":"zinc_syrup","iron_syrup":"iron_syrup","maltofer":"iron_syrup","حديد شراب":"iron_syrup","فيروجلوبين":"iron_syrup","feroglobin":"iron_syrup","devit":"vitamin_d_drops","دي فيت":"vitamin_d_drops","vitamin_d_drops":"vitamin_d_drops","فيتامين د قطرات":"vitamin_d_drops","prospan":"hedera_helix","ezyban":"hedera_helix","ايزيبان":"hedera_helix","إيزيبان":"hedera_helix","bronchokor":"hedera_helix","برونشيكور":"hedera_helix","bronchocor":"hedera_helix","بروسبان":"hedera_helix","hedelix":"hedera_helix","hedera helix":"hedera_helix","hedera_helix":"hedera_helix","ivy leaf":"hedera_helix","piriton":"chlorpheniramine","بيريتون":"chlorpheniramine","chlorpheniramine":"chlorpheniramine","phenergan":"promethazine","فينيرغان":"promethazine","promethazine":"promethazine","robitussin":"guaifenesin","روبيتوسين":"guaifenesin","mucinex":"guaifenesin","guaifenesin":"guaifenesin","delsym":"dextromethorphan","dextromethorphan":"dextromethorphan","benylin":"dextromethorphan","coldact":"chlorpheniramine_pseudoephedrine","كولداكت":"chlorpheniramine_pseudoephedrine","triaminic":"chlorpheniramine_pseudoephedrine","تريامينيك":"chlorpheniramine_pseudoephedrine","diphenhydramine":"diphenhydramine","exylin":"diphenhydramine","إكسيلين":"diphenhydramine","exilin":"diphenhydramine","benylin":"diphenhydramine","بينيلين":"diphenhydramine","benadryl":"diphenhydramine","بينادريل":"diphenhydramine","ديفينهيدرامين":"diphenhydramine","actifed":"triprolidine_pseudoephedrine","أكتيفيد":"triprolidine_pseudoephedrine","triominic":"triprolidine_pseudoephedrine","exillin":"amoxicillin","إكسيلين":"amoxicillin","exacillin":"amoxicillin","ampicillin":"ampicillin","أمبيسيلين":"ampicillin","ampiclox":"ampicillin","أمبيكلوكس":"ampicillin","coldact":"chlorpheniramine","كولداكت":"chlorpheniramine","piriton":"chlorpheniramine","بيريتون":"chlorpheniramine","phenergan":"promethazine","فينيرغان":"promethazine","robitussin":"dextromethorphan","روبيتوسين":"dextromethorphan","actifed":"triprolidine_pseudoephedrine","أكتيفيد":"triprolidine_pseudoephedrine","broncholisin":"salbutamol_bromhexine","برونكوليتين":"salbutamol_bromhexine","sudafed":"pseudoephedrine","سودافيد":"pseudoephedrine","mucinex":"guaifenesin","موسينكس":"guaifenesin","aerius":"desloratadine","neoclarityn":"desloratadine","إيريوس":"desloratadine","xyzal":"levocetirizine","زيزال":"levocetirizine","ليفوسيتيريزين":"levocetirizine","ديسلوراتادين":"desloratadine","دولوبي":"domperidone","موتيلين":"domperidone","motilene":"domperidone","موتيليوم":"domperidone","motilium":"domperidone","بروكينين":"domperidone","prokineen":"domperidone","دومبيريدون":"domperidone","domperidone":"domperidone","دوميبيريدون":"domperidone","دوم بي":"domperidone","dolopi":"domperidone","dolopy":"domperidone","دومبي":"domperidone","dompy":"domperidone","motilium":"domperidone","موتيليوم":"domperidone","دوميريدون":"domperidone",
                # أموكسيسيلين
                "amoxicillin":"amoxicillin","أموكسيسيلين":"amoxicillin","اموكسيسيلين":"amoxicillin",
                "amoxil":"amoxicillin","أموكسيل":"amoxicillin","flumox":"amoxicillin","فلوموكس":"amoxicillin",
                "trimox":"amoxicillin","ospamox":"amoxicillin","أوسباموكس":"amoxicillin",
                # أوجمنتين
                "augmentin":"amoxicillin_clavulanate","أوجمنتين":"amoxicillin_clavulanate",
                "amoxiclav":"amoxicillin_clavulanate","كلافوموكس":"amoxicillin_clavulanate",
                "clavamox":"amoxicillin_clavulanate","أموكسيكلاف":"amoxicillin_clavulanate",
                # أزيثروميسين
                "azithromycin":"azithromycin","أزيثروميسين":"azithromycin","ازيثروميسين":"azithromycin",
                "zithromax":"azithromycin","زيثروماكس":"azithromycin","azithral":"azithromycin",
                "أزيثرال":"azithromycin","zmax":"azithromycin","sumamed":"azithromycin",
                # كلاريثروميسين
                "clarithromycin":"clarithromycin","كلاريثروميسين":"clarithromycin",
                "klacid":"clarithromycin","كلاسيد":"clarithromycin","klaricid":"clarithromycin",
                "biaxin":"clarithromycin","بياكسين":"clarithromycin",
                # سيفالكسين
                "cephalexin":"cephalexin","سيفالكسين":"cephalexin","كيفلكس":"cephalexin",
                "keflex":"cephalexin","cefalexin":"cephalexin","ospexin":"cephalexin",
                # سيتيريزين
                "cetirizine":"cetirizine","سيتيريزين":"cetirizine","زيرتيك":"cetirizine",
                "zyrtec":"cetirizine","citriz":"cetirizine","سيتريكس":"cetirizine",
                "reactine":"cetirizine","alerid":"cetirizine",
                # لوراتادين
                "loratadine":"loratadine","لوراتادين":"loratadine","كلاريتين":"loratadine",
                "claritin":"loratadine","claritine":"loratadine","loratin":"loratadine",
                "لوراتا":"loratadine","clarityn":"loratadine",
                # ديسلوراتادين
                "desloratadine":"desloratadine","ديسلوراتادين":"desloratadine",
                "aerius":"desloratadine","إيريوس":"desloratadine","neoclarityn":"desloratadine",
                # ليفوسيتيريزين
                "levocetirizine":"levocetirizine","ليفوسيتيريزين":"levocetirizine",
                "xyzal":"levocetirizine","زيزال":"levocetirizine",
                # أوندانسيترون
                "ondansetron":"ondansetron","أوندانسيترون":"ondansetron","زوفران":"ondansetron",
                "zofran":"ondansetron","onseran":"ondansetron","ونسيران":"ondansetron",
                # ميتوكلوبراميد
                "metoclopramide":"metoclopramide","ميتوكلوبراميد":"metoclopramide",
                "maxolon":"metoclopramide","ماكسولون":"metoclopramide","primperan":"metoclopramide",
                # بريدنيزولون
                "prednisolone":"prednisolone","بريدنيزولون":"prednisolone","بريدنزلون":"prednisolone","prednisolone":"prednisolone","سولوبريد":"prednisolone","solupred":"prednisolone","prednisone":"prednisolone","بريدنيزولون":"prednisolone",
                "solupred":"prednisolone","سولوبريد":"prednisolone","deltacortril":"prednisolone",
                "ديلتاكورتريل":"prednisolone","prednisolone syrup":"prednisolone",
                # سالبيوتامول
                "salbutamol":"salbutamol","سالبيوتامول":"salbutamol",
                "ventolin":"salbutamol","فنتولين":"salbutamol","albuterol":"salbutamol",
                "ventolin syrup":"salbutamol","salbutamol syrup":"salbutamol",
                # فلوكونازول
                "fluconazole":"fluconazole","فلوكونازول":"fluconazole",
                "diflucan":"fluconazole","ديفلوكان":"fluconazole","flucoral":"fluconazole",
                # برومهيكسين
                "bromhexine":"bromhexine","برومهيكسين":"bromhexine","bisolvon":"bromhexine",
                "بيسولفون":"bromhexine","bromhexine syrup":"bromhexine",
                # أمبروكسول
                "ambroxol":"ambroxol","أمبروكسول":"ambroxol","mucosolvan":"ambroxol",
                "ميوكوسولفان":"ambroxol","ambroxol syrup":"ambroxol","medicine label analysis":"unknown","i can see":"unknown","i can read":"unknown","looking at":"unknown","this appears":"unknown","the label":"unknown","ibuprofen suspension":"ibuprofen","ibuprofen oral suspension":"ibuprofen","ibuprofen syrup":"ibuprofen","ibuprofen 100mg":"ibuprofen","ibuprofen 200mg":"ibuprofen","ibuprofen ds":"ibuprofen","brufen suspension":"ibuprofen","brufen syrup":"ibuprofen","nurofen suspension":"ibuprofen","أيبوبروفين معلق":"ibuprofen","إيبوبروفين معلق":"ibuprofen","أيبوبروفين شراب":"ibuprofen","ايبوبروفين للاطفال":"ibuprofen","ايبوبروفين للأطفال":"ibuprofen","ibuprofen for children":"ibuprofen","children ibuprofen":"ibuprofen","prof syrup":"ibuprofen","prof suspension":"ibuprofen","prof oral":"ibuprofen","prof":"ibuprofen","Prof":"ibuprofen","بروف":"ibuprofen","ibuprofen":"ibuprofen","ibuprofen ds":"ibuprofen","ibuprofen oral":"ibuprofen","nurofen":"ibuprofen","Nurofen":"ibuprofen","نيوروفين":"ibuprofen","نيورفين":"ibuprofen","brufen":"ibuprofen","Brufen":"ibuprofen","advil":"ibuprofen","sabfen":"ibuprofen","سابوفين":"ibuprofen","أيبوبروفين":"ibuprofen","ايبوبروفين":"ibuprofen","إيبوبروفين":"ibuprofen","باراسيتامول":"paracetamol","بنادول":"paracetamol","بانادول":"paracetamol","panadol":"paracetamol","إيبوبروفين":"ibuprofen","نيوروفين":"ibuprofen","نيورفين":"ibuprofen","nurofen":"ibuprofen","نيوروفين للأطفال":"ibuprofen","بروف":"ibuprofen","brufen":"ibuprofen","برووف":"ibuprofen","سابوفين":"ibuprofen","sabfen":"ibuprofen","advil":"ibuprofen","أدفيل":"ibuprofen","ibufen":"ibuprofen","أيبوفين":"ibuprofen","calprofen":"ibuprofen","junifen":"ibuprofen","أيبوبروفين":"ibuprofen","ايبوبروفين":"ibuprofen","إيبوبروفين":"ibuprofen","ibuprofen":"ibuprofen","nurofen":"ibuprofen","brufen":"ibuprofen","أموكسيسيلين":"amoxicillin","amoxil":"amoxicillin","ميترونيدازول":"metronidazole","فلاجيل":"metronidazole","أزيثروميسين":"azithromycin","زيثروماكس":"azithromycin","سيتيريزين":"cetirizine","زيرتيك":"cetirizine","لوراتادين":"loratadine","كلاريتين":"loratadine","هيوسين":"hyoscine_butylbromide","سكوبينال":"hyoscine_butylbromide","buscopan":"hyoscine_butylbromide","سالبيوتامول":"salbutamol","فنتولين":"salbutamol","ميتفورمين":"metformin","جلوكوفاج":"metformin","كلاريثروميسين":"clarithromycin","كلاسيد":"clarithromycin","بريدنيزولون":"prednisolone","أوندانسيترون":"ondansetron","زوفران":"ondansetron","فيفادول":"paracetamol","فيفا دول":"paracetamol","vifadol":"paracetamol","adol":"paracetamol","أدول":"paracetamol","calpol":"paracetamol","كالبول":"paracetamol","tylenol":"paracetamol","تايلينول":"paracetamol","tempra":"paracetamol","تمبرا":"paracetamol","febricol":"paracetamol","فيبريكول":"paracetamol","dymadon":"paracetamol","فارفيكس":"paracetamol","farfex":"paracetamol","فيفا دول":"paracetamol","vifadol":"paracetamol","دومبي":"domperidone","dompy":"domperidone","dompé":"domperidone","سكوبينال":"hyoscine_butylbromide","scobinal":"hyoscine_butylbromide","hyoscine butylbromide":"hyoscine_butylbromide","نيوروفين":"ibuprofen","نيورفين":"ibuprofen","nurofen":"ibuprofen","نيوروفين للأطفال":"ibuprofen","بروف":"ibuprofen","brufen":"ibuprofen","برووف":"ibuprofen","سابوفين":"ibuprofen","sabfen":"ibuprofen","advil":"ibuprofen","أدفيل":"ibuprofen","ibufen":"ibuprofen","أيبوفين":"ibuprofen","calprofen":"ibuprofen","junifen":"ibuprofen","أيبوبروفين":"ibuprofen","ايبوبروفين":"ibuprofen","إيبوبروفين":"ibuprofen","ibuprofen":"ibuprofen","nurofen for children":"ibuprofen","فنتولين":"salbutamol","ventolin syrup":"salbutamol","salbutamol syrup":"salbutamol","أوجمنتين":"amoxicillin_clavulanate","augmentin":"amoxicillin_clavulanate","كلافوموكس":"amoxicillin_clavulanate","زيناتا":"cefuroxime","زينات":"cefuroxime","بروف":"ibuprofen","brufen":"ibuprofen","برووف":"ibuprofen","دومبي":"domperidone","دوم بي":"domperidone","domperidone":"domperidone","دومبيريدون":"domperidone"}
        for _k, _v in ARABIC_MAP.items():
            if _k in txt or _k.lower() in txt.lower():
                txt = _v
                break
                # بحث ذكي في الكلمات المُرجعة

        # تصحيح خاص للأدوية المتشابهة
        BRAND_OVERRIDE = {}
        raw_lower = txt.lower()
        if "aerius" in raw_lower or "neoclarityn" in raw_lower:
            txt = "desloratadine|0.5mg/ml"
        elif "xyzal" in raw_lower:
            txt = "levocetirizine|0.5mg/ml"
            # تحويل خاص لفيتامين د
        if "vitamin_d" in txt.lower() or "cholecalciferol" in txt.lower():
            txt = "vitamin_d_drops|400IU/drop"
        drug_name = txt.split("|")[0].strip().lower()
        if "|" in txt:
            parts = txt.split("|", 1)
            drug_name = parts[0].strip()
            conc_raw = parts[1].strip().lower()
            if conc_raw != "unknown":
                # استخراج الرقم من التركيز مثل 250mg/5ml
                m = _re.search(r"([\d.]+)\s*mg/\s*([\d.]+)\s*ml", conc_raw)
                if m:
                    concentration = (float(m.group(1)), float(m.group(2)))
                    logger.info(f"Concentration found: {concentration}")

        # تنظيف اسم الدواء
        drug_name = _re.sub(r"[#*\.,:;]", "", drug_name).strip().lower()

        if not drug_name or drug_name == "unknown":
            return ""

        # حفظ التركيز في متغير عام مؤقت
        if concentration:
            import builtins
            builtins._last_concentration = concentration

        words = drug_name.split()
        result = " ".join(words[:3])
        logger.info(f"Image identified: {result}, concentration: {concentration}")
        return result
    except Exception as e:
        logger.error(f"Image API error: {e}")
        try:
            import httpx as _h2
        except: pass
        await asyncio.sleep(0)  # dummy
        return ""
        return ""

def kb_lang():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar"),
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")]])

def kb_main(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(tx("btn_search", lang), callback_data="m_search")],
        [InlineKeyboardButton(tx("btn_child", lang), callback_data="m_child")],
        [InlineKeyboardButton(tx("btn_bmi", lang), callback_data="m_bmi")],
        [InlineKeyboardButton(tx("btn_cal", lang), callback_data="m_cal")],
        [InlineKeyboardButton(tx("btn_patient", lang), callback_data="m_patient")],
        [InlineKeyboardButton(tx("btn_interaction", lang), callback_data="m_interaction")],
        [InlineKeyboardButton(tx("btn_sugar", lang), callback_data="m_sugar")],
        [InlineKeyboardButton(tx("btn_bp", lang), callback_data="m_bp")],
        [InlineKeyboardButton(tx("btn_remind", lang), callback_data="m_remind")],
        [InlineKeyboardButton(tx("btn_premium", lang), callback_data="m_premium")],
        [InlineKeyboardButton(tx("btn_settings", lang), callback_data="m_settings")]])

def kb_back(lang):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(tx("btn_back", lang), callback_data="back")]])

def kb_remind(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(tx("btn_add", lang), callback_data="r_add")],
        [InlineKeyboardButton(tx("btn_list", lang), callback_data="r_list")],
        [InlineKeyboardButton(tx("btn_edit", lang), callback_data="r_edit")],
        [InlineKeyboardButton(tx("btn_del", lang), callback_data="r_del")],
        [InlineKeyboardButton(tx("btn_back", lang), callback_data="back")]])

REMINDERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reminders.json")

# نحفظ في ملف JSON محلي
def load_all_reminders():
    # نحاول من Supabase أولاً
    if supabase_client:
        try:
            res = supabase_client.table("reminders").select("data").eq("id", "all").execute()
            if res.data:
                return json.loads(res.data[0]["data"])
        except Exception as e:
            logger.error(f"Supabase load error: {e}")
    # نقرأ من الملف المحلي
    try:
        with open(REMINDERS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_all_reminders(data):
    try:
        with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"reminders save error: {e}")
    # نحفظ في Supabase
    if supabase_client:
        try:
            supabase_client.table("reminders").upsert({"id": "all", "data": json.dumps(data, ensure_ascii=False)}).execute()
        except Exception as e:
            logger.error(f"Supabase save error: {e}")

def get_rems(ctx):
    try:
        if hasattr(ctx, "effective_user") and ctx.effective_user:
            uid = str(ctx.effective_user.id)
        elif hasattr(ctx, "_user_id"):
            uid = str(ctx._user_id)
        else:
            uid = str(ctx.user_data.get("uid", "0"))
    except:
        uid = "0"
    ctx.user_data["uid"] = uid
    # نقرأ دائماً من Supabase
    all_rems = load_all_reminders()
    rems = all_rems.get(uid, [])
    ctx.user_data["reminders"] = rems
    return rems

def save_rems(ctx):
    try:
        if hasattr(ctx, "effective_user") and ctx.effective_user:
            uid = str(ctx.effective_user.id)
        elif hasattr(ctx, "_user_id"):
            uid = str(ctx._user_id)
        else:
            uid = ctx.user_data.get("uid", "0")
        all_rems = load_all_reminders()
        all_rems[uid] = ctx.user_data.get("reminders", [])
        save_all_reminders(all_rems)
        logger.info(f"save_rems: uid={uid}, count={len(all_rems[uid])}")
    except Exception as e:
        logger.error(f"save_rems error: {e}")

def fmt_rems(rems, lang):
    if not rems: return tx("no_rems", lang)
    lines = [tx("rems_title", lang)]
    for r in rems:
        suf = "x/يوم" if lang == "ar" else "x/day"
        days = r.get("days", 0)
        dur = ""
        if days > 0:
            dur = " — 📅 " + str(days) + (" يوم" if lang=="ar" else " days")
        pat_tag = " 👤 " + r["patient"] if r.get("patient") else ""
        lines.append("🔸 " + str(r['id']) + " 💊 " + str(r['drug']) + pat_tag + " — 🕐 " + str(r['time']) + " — 🔁 " + str(r['freq']) + suf + dur)
    return "\n".join(lines)

async def send_alert(ctx):
    d = ctx.job.data
    lang = d.get("lang", "ar")
    drug = d.get("drug", "")
    chat_id = d.get("chat_id")
    attempt = d.get("attempt", 1)
    
    if lang == "ar":
        msg = "⏰ تذكير الدواء\n\n💊 حان وقت دواء: " + drug
        if attempt > 1: msg += "\n\n🔔 تذكير رقم " + str(attempt)
        btn_done = "✅ تم إعطاء الدواء"
        btn_later = "⏳ لاحقاً (15 دقيقة)"
    else:
        msg = "⏰ Medication Reminder\n\n💊 Time for: " + drug
        if attempt > 1: msg += "\n\n🔔 Reminder #" + str(attempt)
        btn_done = "✅ Done"
        btn_later = "⏳ Remind in 15 min"
    job_id = str(chat_id)
    btns = InlineKeyboardMarkup([
        [InlineKeyboardButton(btn_done, callback_data="rem_done_" + job_id)],
        [InlineKeyboardButton(btn_later, callback_data="rem_snooze_" + job_id + "_" + str(drug))],
    ])

    try:
        await ctx.bot.send_message(chat_id, msg, reply_markup=btns, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"send_alert error: {e}")
    
    # إذا لم يُستجب وعدد المحاولات أقل من 3 — نجدول تذكيراً بعد 15 دقيقة
    if attempt < 3:
        from datetime import timedelta
        next_time = datetime.now(TIMEZONE) + timedelta(minutes=15)
        new_data = dict(d)
        new_data["attempt"] = attempt + 1
        ctx.job.application.job_queue.run_once(
            send_alert,
            when=next_time,
            data=new_data,
            name="alert_" + str(chat_id) + "_" + str(drug) + "_retry" + str(attempt)        )

async def rem_done(update, ctx):
    """المستخدم ضغط تم"""
    q = update.callback_query
    await q.answer("✅ تم تسجيل الجرعة", show_alert=True)
    lang = "ar" if "ar" in str(q.data) else "en"
    msg = "✅ تم! الجرعة التالية ستُذكّرك في وقتها." if lang=="ar" else "✅ Done! Next dose reminder is set."
    await q.message.edit_text(msg)
    # نلغي التذكيرات الإضافية
    job_id = q.data.replace("rem_done_", "")
    for job in ctx.job_queue.jobs():
        if "retry" in job.name and job_id.split("_")[0] in job.name:
            job.schedule_removal()

async def rem_later(update, ctx):
    """المستخدم ضغط لاحقاً - يجدول تذكيراً بعد 15 دقيقة"""
    q = update.callback_query
    await q.answer("⏳ سيتم تذكيرك بعد 15 دقيقة", show_alert=True)
    raw = q.data.replace("rem_snooze_", "")
    parts = raw.split("_", 1)
    chat_id = int(parts[0]) if parts[0].isdigit() else q.message.chat_id
    drug = parts[1] if len(parts) > 1 else "دواء"
    lang = "ar"
    msg = "⏳ سيُذكّرك البوت بعد 15 دقيقة." if lang=="ar" else "⏳ Reminder set for 15 minutes."
    await q.message.edit_text(msg)
    # نجدول تذكيراً بعد 15 دقيقة
    from datetime import timedelta
    next_time = datetime.now(TIMEZONE) + timedelta(minutes=15)
    ctx.application.job_queue.run_once(
        send_alert,
        when=next_time,
        data={"chat_id": chat_id, "drug": drug, "lang": lang, "attempt": 1, "is_retry": True},
        name="snooze_" + str(chat_id) + "_" + str(drug)
    )

def sched(app, chat_id, drug, time_str, freq, lang, tz_str="Asia/Riyadh"):
    try:
        h, m = map(int, time_str.split(":"))
        try:
            user_tz = pytz.timezone(tz_str)
        except:
            user_tz = TIMEZONE
        from datetime import time as dtime, timedelta
        # نحسب الأوقات حسب التكرار
        interval_hours = 24 // max(freq, 1)
        times = []
        for i in range(freq):
            total_minutes = (h * 60 + m) + (i * interval_hours * 60)
            new_h = (total_minutes // 60) % 24
            new_m = total_minutes % 60
            times.append(dtime(new_h, new_m, tzinfo=user_tz))
        # نجدول run_daily لكل وقت
        for i, t in enumerate(times):
            app.job_queue.run_daily(
                send_alert,
                time=t,
                data={"chat_id": chat_id, "drug": drug, "lang": lang},
                name="rem_" + str(chat_id) + "_" + str(drug) + "_" + str(i))
        logger.info("sched: " + str(drug) + " x" + str(freq) + " times=" + str([str(t) for t in times]))
    except Exception as e:
        logger.error(f"sched error: {e}")

async def show_main(msg, lang, edit=False):
    t = tx("main_menu", lang)
    k = kb_main(lang)
    if edit:
        await msg.edit_text(t, reply_markup=k, parse_mode=ParseMode.MARKDOWN)
    else:
        await msg.reply_text(t, reply_markup=k, parse_mode=ParseMode.MARKDOWN)

def calc_bmi(weight, height_cm):
    """حساب BMI"""
    h = height_cm / 100
    bmi = weight / (h * h)
    return round(bmi, 1)

def bmi_category(bmi, lang):
    """تصنيف BMI"""
    if bmi < 18.5:
        return tx("bmi_underweight", lang)
    elif bmi < 25:
        return tx("bmi_normal", lang)
    elif bmi < 30:
        return tx("bmi_overweight", lang)
    else:
        return tx("bmi_obese", lang)

def ideal_weight(height_cm, age):
    """الوزن المثالي للطفل"""
    if age <= 10:
        return round(2 * age + 8, 1)
    else:
        return round((age * 4 - 2.5) / 2, 1)

async def auto_welcome(u, ctx):
    """ترحيب تلقائي عند أي رسالة بدون حالة محادثة"""
    if not ctx.user_data.get("lang"):
        _tz = ctx.user_data.get("timezone"); ctx.user_data.clear(); ctx.user_data["timezone"] = _tz if _tz else ctx.user_data.get("timezone")
        await u.message.reply_text(tx("welcome", "ar"), reply_markup=kb_lang(), parse_mode=ParseMode.MARKDOWN)
        return STATE_LANGUAGE
    lang = get_lang(ctx)
    await show_main(u.message, lang)
    return STATE_MAIN_MENU

async def start(u, ctx):
    _tz = ctx.user_data.get("timezone"); ctx.user_data.clear(); ctx.user_data["timezone"] = _tz if _tz else ctx.user_data.get("timezone")
    await u.message.reply_text(tx("welcome", "ar"), reply_markup=kb_lang(), parse_mode=ParseMode.MARKDOWN)
    return STATE_LANGUAGE

async def reg_name_country(u, ctx):
    """يحفظ الاسم والدولة بعد التسجيل"""
    lang = "ar"
    text = u.message.text.strip()
    uid = str(u.effective_user.id)
    
    # نفصل الاسم والدولة
    parts = text.replace("—","–").replace("-","–").split("–")
    name = parts[0].strip() if parts else text
    country = parts[1].strip() if len(parts) > 1 else ""
    
    # نكتشف المنطقة الزمنية
    if country:
        tz = detect_country_tz(country)
        if tz:
            ctx.user_data["timezone"] = tz
    
    # نحفظ في الإحصائيات
    stats = load_stats()
    if "users" not in stats: stats["users"] = {}
    stats["users"][uid] = {
        "count": 1,
        "registered": True,
        "role": ctx.user_data.get("reg_role", "عام"),
        "name": name,
        "country": country
    }
    save_stats(stats)
    
    await u.message.reply_text("✅ مرحباً " + name + "! 🎉\n\nاختر لغتك:", reply_markup=kb_lang())
    return STATE_LANGUAGE

async def pick_lang(u, ctx):
    q = u.callback_query; await q.answer()
    ctx.user_data["lang"] = "ar" if q.data == "lang_ar" else "en"
    lang = get_lang(ctx)
    
    await show_main(q.message, lang, edit=True)
    return STATE_MAIN_MENU

async def set_country(u, ctx):
    lang = get_lang(ctx)
    txt = u.message.text.strip()
    tz = detect_country_tz(txt)
    if tz:
        ctx.user_data["timezone"] = tz
        country_name = txt
        msg = f"✅ تم ضبط التوقيت: {tz}" if lang == "ar" else f"✅ Timezone set: {tz}"
        await u.message.reply_text(msg)
    else:
        msg = "⚠️ لم أتعرف على الدولة، سيتم استخدام توقيت الرياض افتراضياً" if lang == "ar" else "⚠️ Country not found, using Riyadh timezone as default"
        await u.message.reply_text(msg)
        ctx.user_data["timezone"] = "Asia/Riyadh"
    await show_main(u.message, lang)
    return STATE_MAIN_MENU

async def go_back(u, ctx):
    q = u.callback_query; await q.answer()
    lang = get_lang(ctx)
    for k in ("results", "child_drug", "edit_id", "edit_field"):
        ctx.user_data.pop(k, None)
    await show_main(q.message, lang, edit=True)
    return STATE_MAIN_MENU

async def main_cb(u, ctx):
    q = u.callback_query; await q.answer()
    lang = get_lang(ctx)
    if q.data == "m_search":
        await q.message.edit_text(tx("search_prompt", lang), reply_markup=kb_back(lang), parse_mode=ParseMode.MARKDOWN)
        return STATE_DRUG_SEARCH
    elif q.data == "m_child":
        return await ask_drug_form(u, ctx)
    elif q.data == "m_child_skip":
        await q.message.edit_text(tx("child_prompt", lang), reply_markup=kb_back(lang), parse_mode=ParseMode.MARKDOWN)
        return STATE_CHILD_DRUG
    elif q.data == "m_premium":
        return await premium_menu(u, ctx)
    elif q.data in ("pay_month","pay_3month","pay_6month","pay_year"):
        return await process_payment(u, ctx)
    elif q.data == "m_bmi":
        ctx.user_data.pop("bmi_step", None)
        ctx.user_data.pop("bmi_w", None)
        ctx.user_data.pop("bmi_h", None)
        text = "📊 *BMI Calculator*" + chr(10) + chr(10) + ("اختر نوع الحساب:" if lang=="ar" else "Choose type:")
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("👶 " + ("طفل (مع جرعة الدواء)" if lang=="ar" else "Child (with drug dose)"), callback_data="bmi_child")],
            [InlineKeyboardButton("🧑 " + ("بالغ" if lang=="ar" else "Adult"), callback_data="bmi_adult")],
            [InlineKeyboardButton(tx("btn_back", lang), callback_data="back")],
        ])
        await q.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        return STATE_BMI_WEIGHT
    elif q.data == "m_remind":
        await q.message.edit_text(tx("rem_menu", lang), reply_markup=kb_remind(lang), parse_mode=ParseMode.MARKDOWN)
        return STATE_REM_MENU
    elif q.data == "m_cal":
        lang = get_lang(ctx)
        btns = InlineKeyboardMarkup([
            [InlineKeyboardButton("👨 ذكر" if lang=="ar" else "👨 Male", callback_data="cal_m"),
             InlineKeyboardButton("👩 أنثى" if lang=="ar" else "👩 Female", callback_data="cal_f")],
            [InlineKeyboardButton("🍎 سعرات طعام" if lang=="ar" else "🍎 Food Calories", callback_data="cal_food")],
            [InlineKeyboardButton(tx("btn_back", lang), callback_data="back")]])
        await q.message.edit_text("🔥 حاسبة السعرات" if lang=="ar" else "🔥 Calorie Calculator", reply_markup=btns, parse_mode=ParseMode.MARKDOWN)


        return STATE_CAL_GENDER
    elif q.data == "m_interaction":
        return await interaction_start(u, ctx)
    elif q.data == "m_patient":
        load_patients(ctx)
        await q.message.edit_text("👤 " + ("ملف المريض" if lang=="ar" else "Patient File"), reply_markup=kb_patient_menu(lang))
        return STATE_PAT_MENU
    elif q.data == "m_sugar":
        uid = u.effective_user.id
        if not is_premium(uid):
            await q.message.edit_text(tx("not_premium", lang), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tx("btn_premium", lang), callback_data="m_premium")],[InlineKeyboardButton(tx("btn_back", lang), callback_data="back")]]))
            return STATE_MAIN_MENU
        btns = InlineKeyboardMarkup([
            [InlineKeyboardButton("🌅 سكر الصيام" if lang=="ar" else "🌅 Fasting", callback_data="sugar_fasting")],
            [InlineKeyboardButton("🍽️ بعد الأكل" if lang=="ar" else "🍽️ Post-meal", callback_data="sugar_postmeal")],
            [InlineKeyboardButton("📊 HbA1c تراكمي" if lang=="ar" else "📊 HbA1c", callback_data="sugar_hba1c")],
            [InlineKeyboardButton(tx("btn_back", lang), callback_data="back")]])
        await q.message.edit_text("🩸 اختر نوع قراءة السكر:" if lang=="ar" else "🩸 Select sugar reading type:", reply_markup=btns)
        return STATE_SUGAR
    elif q.data == "m_bp":
        uid = u.effective_user.id
        if not is_premium(uid):
            await q.message.edit_text(tx("not_premium", lang), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tx("btn_premium", lang), callback_data="m_premium")],[InlineKeyboardButton(tx("btn_back", lang), callback_data="back")]]))
            return STATE_MAIN_MENU
        await q.message.edit_text("👤 كم عمرك؟" if lang=="ar" else "👤 How old are you?", reply_markup=kb_back(lang))
        return STATE_BP_AGE
    elif q.data == "m_settings":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(tx("change_lang", lang), callback_data="do_lang")],
            [InlineKeyboardButton("🌍 " + ("تغيير الدولة" if lang=="ar" else "Change Country"), callback_data="do_country")],
            [InlineKeyboardButton(tx("btn_back", lang), callback_data="back")]])
        await q.message.edit_text(tx("settings", lang), reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        return STATE_MAIN_MENU
    elif q.data == "do_country":
        msg = "🌍 اكتب اسم دولتك الجديدة:" if lang == "ar" else "🌍 Type your new country:"
        await q.message.edit_text(msg)
        return STATE_COUNTRY
    elif q.data == "do_lang":
        await q.message.edit_text(tx("welcome", "ar"), reply_markup=kb_lang(), parse_mode=ParseMode.MARKDOWN)
        return STATE_LANGUAGE
    return STATE_MAIN_MENU

async def drug_search_image(u, ctx):
    """البحث عن دواء عبر الصورة"""
    lang = get_lang(ctx)
    if not ANTHROPIC_API_KEY:
        await u.message.reply_text(tx("no_api", lang), reply_markup=kb_back(lang))
        return STATE_DRUG_SEARCH
    msg = await u.message.reply_text(tx("analyzing", lang))
    photo = u.message.photo[-1]
    f = await photo.get_file()
    img = await f.download_as_bytearray()
    name = await analyze_image(bytes(img), lang)
    await msg.delete()
    if not name:
        btns = InlineKeyboardMarkup([
            [InlineKeyboardButton("✏️ " + ("أدخل الاسم يدوياً" if lang=="ar" else "Type name manually"), callback_data="manual_input")],
            [InlineKeyboardButton("📸 " + ("أرسل صورة أخرى" if lang=="ar" else "Send another photo"), callback_data="retry_photo")],
            [InlineKeyboardButton(tx("btn_back", lang), callback_data="back")]
        ])
        msg = "❌ لم أتعرف على الدواء\n\n💡 جرّب صورة أوضح أو أدخل الاسم يدوياً" if lang=="ar" else "❌ Could not identify drug\n\n💡 Try a clearer photo or type the name"
        await u.message.reply_text(msg, reply_markup=kb_image_result(lang))
        return STATE_DRUG_SEARCH
    res = search_drugs(name)
    if not res:
        await u.message.reply_text("📸 " + name + "\n\n" + ("❌ لم يُعثر على الدواء" if lang=="ar" else "❌ Drug not found"), reply_markup=kb_image_result(lang, name), parse_mode=ParseMode.MARKDOWN)
        return STATE_DRUG_SEARCH
    track(u, "searches")
    if len(res) == 1:
        ctx.user_data["img_drug"] = name
        await u.message.reply_text("📸 " + name + "\n\n" + fmt_drug(res[0], lang), reply_markup=kb_image_result(lang, name), parse_mode=ParseMode.MARKDOWN)
        return STATE_DRUG_SEARCH
    btns = [[InlineKeyboardButton(
        str(d.get("name_ar" if lang=="ar" else "name_en", "?")),
        callback_data=f"ds_{i}")] for i, d in enumerate(res)]
    btns.append([InlineKeyboardButton(tx("btn_back", lang), callback_data="back")])
    await u.message.reply_text("📸 " + name + chr(10) + chr(10) + tx("multi_results", lang), reply_markup=InlineKeyboardMarkup(btns), parse_mode=ParseMode.MARKDOWN)
    return STATE_DRUG_SEARCH

async def drug_search(u, ctx):
    lang = get_lang(ctx)
    track(u, "searches")
    query = u.message.text.strip()
    
    # Claude API مباشرة
    thinking = await u.message.reply_text("🔍 " + ("جارٍ البحث..." if lang=="ar" else "Searching..."))
    try:
        if lang == "ar":
            prompt = f"""أنت صيدلاني خبير. أعطني معلومات شاملة عن دواء: {query}
أجب بالعربية فقط:
💊 الاسم العلمي:
🏷️ الأسماء التجارية:
📋 الاستخدامات:
💉 الجرعة للبالغين:
👶 جرعة الأطفال:
⚠️ الآثار الجانبية:
🔴 موانع الاستخدام:
🤰 الحمل والرضاعة:
🫘 الكلى والكبد:
💊 التفاعلات الدوائية:
❗ تحذيرات خاصة:
إذا لم تعرف اكتب: غير معروف"""
        else:
            prompt = f"""You are an expert pharmacist. Give info about: {query}
Reply in English ONLY:
💊 Generic Name:
🏷️ Brand Names:
📋 Indications:
💉 Adult Dose:
👶 Pediatric Dose:
⚠️ Side Effects:
🔴 Contraindications:
🤰 Pregnancy & Lactation:
🫘 Renal & Hepatic:
💊 Drug Interactions:
❗ Special Warnings:
If unknown write: unknown"""
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post("https://api.anthropic.com/v1/messages",
                headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": "claude-haiku-4-5-20251001", "max_tokens": 800,
                    "messages": [{"role": "user", "content": prompt}]})
            result = r.json().get("content", [{}])[0].get("text", "").strip()
        await thinking.delete()
        if "غير معروف" not in result and "unknown" not in result.lower():
            await u.message.reply_text(result, reply_markup=kb_back(lang))
            return STATE_DRUG_SEARCH
    except Exception as e:
        logger.error(f"drug_search: {e}")
        try: await thinking.delete()
        except: pass
    
    await u.message.reply_text(tx("not_found", lang), reply_markup=kb_back(lang))
    return STATE_DRUG_SEARCH

async def drug_sel(u, ctx):
    q = u.callback_query; await q.answer()
    lang = get_lang(ctx)
    if q.data == "back": return await go_back(u, ctx)
    i = int(q.data.replace("ds_", ""))
    d = ctx.user_data.get("results", [])[i]
    await q.message.edit_text(fmt_drug(d, lang), reply_markup=kb_back(lang), parse_mode=ParseMode.MARKDOWN)
    return STATE_DRUG_SEARCH

async def child_input(u, ctx):
    lang = get_lang(ctx)
    drug_form = ctx.user_data.get("drug_form", "syrup")
    if u.message.photo:
        if not ANTHROPIC_API_KEY:
            await u.message.reply_text(tx("no_api", lang), reply_markup=kb_back(lang))
            return STATE_CHILD_DRUG
        msg = await u.message.reply_text(tx("analyzing", lang))
        photo = u.message.photo[-1]
        f = await photo.get_file()
        img = await f.download_as_bytearray()
        name = await analyze_image(bytes(img), lang)
        if not name:
            btns = InlineKeyboardMarkup([
                [InlineKeyboardButton("✏️ " + ("أدخل الاسم يدوياً" if lang=="ar" else "Type name manually"), callback_data="manual_input")],
                [InlineKeyboardButton("📸 " + ("أرسل صورة أخرى" if lang=="ar" else "Send another photo"), callback_data="retry_photo")],
                [InlineKeyboardButton(tx("btn_back", lang), callback_data="back")]
            ])
            msg = "❌ لم أتعرف على الدواء\n\n💡 جرّب صورة أوضح أو أدخل الاسم يدوياً" if lang=="ar" else "❌ Could not identify drug\n\n💡 Try a clearer photo or type the name"
            await u.message.reply_text(msg, reply_markup=kb_image_result(lang))
            return STATE_CHILD_DRUG
        res = search_drugs(name)
        if not res:
            # نستخدم Claude API مباشرة
            thinking2 = await u.message.reply_text("🔍 " + ("جارٍ البحث..." if lang=="ar" else "Searching..."))
            try:
                drug_form = ctx.user_data.get("drug_form", "syrup")
                form_ar = {"syrup":"شراب","cream":"كريم","drops":"قطرة","suppository":"تحميلة"}.get(drug_form,"شراب")
                form_en = {"syrup":"syrup","cream":"cream","drops":"drops","suppository":"suppository"}.get(drug_form,"syrup")
                if lang == "ar":
                    p = f"أنت صيدلاني. الدواء: {name} ({form_ar}). أعطني جرعة الأطفال بهذا الشكل فقط:\n💊 الدواء: {name}\n📋 النوع: {form_ar}\n💉 الجرعة حسب العمر:\n• 0-2 سنة: ...\n• 2-6 سنة: ...\n• 6-12 سنة: ...\n🔁 التكرار:\n⚠️ تحذير:"
                else:
                    p = f"You are a pharmacist. Drug: {name} ({form_en}). Give pediatric dose only:\n💊 Drug: {name}\n📋 Form: {form_en}\n💉 Dose by age:\n• 0-2 years: ...\n• 2-6 years: ...\n• 6-12 years: ...\n🔁 Frequency:\n⚠️ Warning:"
                async with httpx.AsyncClient(timeout=30) as hc:
                    r2 = await hc.post("https://api.anthropic.com/v1/messages",
                        headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                        json={"model": "claude-haiku-4-5-20251001", "max_tokens": 300,
                            "messages": [{"role": "user", "content": p}]})
                    ai_dose = r2.json().get("content", [{}])[0].get("text", "").strip()
                await thinking2.delete()
                if ai_dose:
                    await u.message.reply_text("📸 " + name + "\n\n" + ai_dose, reply_markup=kb_image_result(lang))
                else:
                    await u.message.reply_text("📸 " + name + "\n\n" + ("❌ لم يُعثر على الدواء\n\n💡 جرّب صورة أخرى أو أدخل الاسم يدوياً" if lang=="ar" else "❌ Drug not found\n\n💡 Try another photo or type name manually"), reply_markup=kb_image_result(lang))
            except Exception as e:
                logger.error(f"Image drug API: {e}")
                try: await thinking2.delete()
                except: pass
                await u.message.reply_text("📸 " + name + "\n\n" + ("❌ لم يُعثر على الدواء\n\n💡 جرّب صورة أخرى أو أدخل الاسم يدوياً" if lang=="ar" else "❌ Drug not found\n\n💡 Try another photo or type name manually"), reply_markup=kb_image_result(lang))
            return STATE_CHILD_DRUG
        ctx.user_data["child_drug"] = res[0]
        ctx.user_data["img_drug"] = name
        drug_form_img = ctx.user_data.get("drug_form","syrup")
        if drug_form_img in ["cream","drops"]:
            # نسأل عن العمر للقطرات والكريمات
            ctx.user_data["child_drug"] = res[0]
            await u.message.reply_text("📸 *" + name + "*\n\n📅 " + ("كم عمر الطفل بالسنوات؟" if lang=="ar" else "Child age in years?"),
                reply_markup=kb_back(lang), parse_mode="Markdown")
            return STATE_CHILD_WEIGHT
        msg2 = "📸 *" + name + "*\n\n" + tx("weight_prompt", lang)
        await u.message.reply_text(msg2, reply_markup=kb_image_result(lang, name), parse_mode=ParseMode.MARKDOWN)
        return STATE_CHILD_WEIGHT
    res = search_drugs(u.message.text)
    if not res:
        await u.message.reply_text(tx("not_found", lang), reply_markup=kb_back(lang))
        return STATE_CHILD_DRUG
    if len(res) == 1:
        ctx.user_data["child_drug"] = res[0]
        drug_form_txt = ctx.user_data.get("drug_form","syrup")
        if drug_form_txt in ["cream","drops"]:
            # نسأل عن العمر
            await u.message.reply_text("📅 " + ("كم عمر الطفل بالسنوات؟" if lang=="ar" else "Child age in years?"),
                reply_markup=kb_back(lang))
            return STATE_CHILD_WEIGHT
        await u.message.reply_text(tx("weight_prompt", lang), reply_markup=kb_back(lang))
        return STATE_CHILD_WEIGHT
    ctx.user_data["results"] = res
    btns = [[InlineKeyboardButton(
        str(d.get("name_ar" if lang=="ar" else "name_en", "?")),
        callback_data=f"cs_{i}")] for i, d in enumerate(res)]
    btns.append([InlineKeyboardButton(tx("btn_back", lang), callback_data="back")])
    await u.message.reply_text(tx("multi_results", lang), reply_markup=InlineKeyboardMarkup(btns))
    return STATE_CHILD_DRUG

async def child_sel(u, ctx):
    q = u.callback_query; await q.answer()
    lang = get_lang(ctx)
    if q.data == "back": return await go_back(u, ctx)
    i = int(q.data.replace("cs_", ""))
    ctx.user_data["child_drug"] = ctx.user_data.get("results", [])[i]
    await q.message.edit_text(tx("weight_prompt", lang), reply_markup=kb_back(lang))
    return STATE_CHILD_WEIGHT

async def child_weight(u, ctx):
    await u.message.reply_text("✅ child_weight called")
    lang = get_lang(ctx)
    track(u, "child_doses")
    try:
        w = float(u.message.text.strip().replace(",", "."))
        if not 0.5 <= w <= 150: raise ValueError
    except:
        await u.message.reply_text(tx("bad_weight", lang), reply_markup=kb_back(lang))
        return STATE_CHILD_WEIGHT
    d = ctx.user_data.get("child_drug")
    logger.info(f"child_weight: drug={d}, weight={w}, form={ctx.user_data.get('drug_form')}")
    if not d:
        await u.message.reply_text("❌ " + ("لم يُحدد الدواء، ابدأ من جديد" if lang=="ar" else "Drug not set, start over"), reply_markup=kb_back(lang))
        return STATE_CHILD_DRUG
    ctx.user_data["child_weight"] = w
    # القطرات والكريمات - نستخدم العمر
    drug_form_cw = ctx.user_data.get("drug_form","syrup")
    if drug_form_cw in ["cream","drops"]:
        drug_name_cw = d.get("name_ar" if lang=="ar" else "name_en","") or d.get("name_en","")
        age_years = w  # هنا w = العمر بالسنوات
        thinking_cw = await u.message.reply_text("🔍 " + ("جارٍ البحث..." if lang=="ar" else "Searching..."))
        try:
            result_cw = await calc_special_form(drug_name_cw, age_years, drug_form_cw, lang)
            await thinking_cw.delete()
            if result_cw:
                await u.message.reply_text(result_cw, reply_markup=kb_back(lang))
                return STATE_MAIN_MENU
        except Exception as e:
            logger.error(f"drops/cream: {e}")
            try: await thinking_cw.delete()
            except: pass
    # نتحقق إذا كان مضاد حيوي
    name_key = d.get("name_en","").lower()
    logger.info(f"child_weight step2: name_key={name_key}, drug_form={ctx.user_data.get('drug_form')}")
    if name_key in ANTIBIOTIC_DOSES:
        sites = INFECTION_SITES.get(lang, INFECTION_SITES["ar"])
        available = [(k,v) for k,v in sites if k in ANTIBIOTIC_DOSES[name_key]]
        btns = [[InlineKeyboardButton(v, callback_data=f"site_{k}")] for k,v in available]
        btns.append([InlineKeyboardButton(tx("btn_back", lang), callback_data="back")])
        msg = "🦠 مكان الالتهاب؟" if lang=="ar" else "🦠 Infection site?"
        await u.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(btns))
        return STATE_INFECTION_SITE
    # التحقق من صحة شكل الدواء عبر Claude API
    drug_form = ctx.user_data.get("drug_form", "syrup")
    drug_name_check = d.get("name_ar","") or d.get("name_en","")
    
    if drug_form == "syrup" and not d.get("concentration") and not d.get("fixed_dose") and not d.get("pediatric_min_mg_per_kg"):
        try:
            async with httpx.AsyncClient(timeout=15) as hc:
                r_check = await hc.post("https://api.anthropic.com/v1/messages",
                    headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                    json={"model": "claude-haiku-4-5-20251001", "max_tokens": 50,
                        "messages": [{"role": "user", "content": f"Is {drug_name_check} available as oral syrup/liquid for children? Answer ONLY: YES or NO"}]})
                check_result = r_check.json().get("content", [{}])[0].get("text","").strip().upper()
                if "NO" in check_result:
                    msg = "⚠️ " + (f"{drug_name_check} غير متوفر كشراب للأطفال.\nيرجى اختيار الشكل الصحيح للدواء." if lang=="ar" else f"{drug_name_check} is not available as syrup for children.\nPlease select the correct drug form.")
                    await u.message.reply_text(msg, reply_markup=kb_back(lang))
                    return STATE_MAIN_MENU
        except: pass
    if drug_form in ["suppository", "cream", "drops"]:
        drug_name = d.get("name_ar","") if lang=="ar" else d.get("name_en","")
        if not drug_name: drug_name = d.get("name_en","") or d.get("name_ar","")
        thinking_f = await u.message.reply_text("🔍 " + ("جارٍ البحث..." if lang=="ar" else "Searching..."))
        try:
            result_f = await calc_special_form(drug_name, w, drug_form, lang)
            await thinking_f.delete()
            if result_f:
                await u.message.reply_text(result_f, reply_markup=kb_back(lang))
                return STATE_MAIN_MENU
        except Exception as e:
            logger.error(f"Special form error: {e}")
            try: await thinking_f.delete()
            except: pass

    # تراكيز شائعة لكل دواء
    DRUG_CONCS = {
        "paracetamol": ["120mg/5ml", "125mg/5ml", "160mg/5ml", "250mg/5ml"],
        "ibuprofen": ["100mg/5ml", "200mg/5ml"],
        "amoxicillin": ["125mg/5ml", "156mg/5ml", "250mg/5ml", "312mg/5ml"],
        "amoxicillin_clavulanate": ["156mg/5ml", "228mg/5ml", "312mg/5ml", "457mg/5ml", "600mg/5ml"],
        "azithromycin": ["100mg/5ml", "200mg/5ml"],
        "metronidazole": ["125mg/5ml", "200mg/5ml"],
        "cetirizine": ["5mg/5ml"],
        "loratadine": ["5mg/5ml"],
        "prednisolone": ["5mg/5ml", "15mg/5ml"],
        "hyoscine_butylbromide": ["5mg/5ml"],
        "hyoscine": ["5mg/5ml"],
        "clarithromycin": ["125mg/5ml", "250mg/5ml"],
        "cephalexin": ["125mg/5ml", "250mg/5ml"],
        "salbutamol": ["2mg/5ml"],
        "domperidone": ["5mg/5ml"],
    "vitamin_d_drops": ["100IU/drop", "400IU/drop", "1000IU/drop"],
    "xylometazoline": ["0.05%", "0.1%"],
    "latanoprost": ["0.005%"],
    "nitazoxanide": ["100mg/5ml", "200mg/5ml"],
    "cinnarizine": ["25mg/5ml"],
    "phenobarbital": ["10mg/5ml", "15mg/5ml"],
    "levetiracetam": ["100mg/ml", "100mg/5ml"],
    "lactulose": ["3.35g/5ml"],
    "spironolactone": ["5mg/5ml", "25mg/5ml"],
    "spironolactone_syrup": ["5mg/5ml", "25mg/5ml"],
    "clarithromycin": ["125mg/5ml", "250mg/5ml"],
    "cefuroxime": ["125mg/5ml", "250mg/5ml"],
    "fusidic_acid": ["2% cream"],
    "clotrimazole_cream": ["1% cream"],
    "betamethasone_cream": ["0.1% cream"],
    "zinc_syrup": ["10mg/5ml", "20mg/5ml"],
    "iron_syrup": ["25mg/ml", "15mg/ml"],
        "ondansetron": ["4mg/5ml"],
        "fluconazole": ["50mg/5ml", "100mg/5ml"],
    }
    name_key = d.get("name_en","").lower()
    concs = DRUG_CONCS.get(name_key, [])
    default_conc = d.get("concentration", "")
    btns = []
    shown = set()
    if default_conc and default_conc != "unknown":
        btns.append([InlineKeyboardButton("✅ " + default_conc + " (افتراضي)", callback_data="conc_" + default_conc)])
        shown.add(default_conc)
    for c in concs:
        if c not in shown:
            btns.append([InlineKeyboardButton(c, callback_data="conc_" + c)])
            shown.add(c)
    if not btns:
        for c in ["120mg/5ml", "250mg/5ml", "100mg/5ml", "200mg/5ml"]:
            btns.append([InlineKeyboardButton(c, callback_data="conc_" + c)])
    btns.append([InlineKeyboardButton("🔢 تركيز آخر", callback_data="conc_custom")])
    btns.append([InlineKeyboardButton(tx("btn_back", lang), callback_data="back")])
    # نعطي الجرعة بالتركيز الافتراضي مباشرة مع زر لتغيير التركيز
    default_conc = btns[0][0].text.replace("✅ ","").replace(" (افتراضي)","") if btns else "125mg/5ml"
    d_copy = dict(d)
    d_copy["concentration"] = default_conc.split("callback")[0] if "callback" in default_conc else default_conc
    
    # نأخذ التركيز الافتراضي من الزر الأول
    first_conc = concs[0] if concs else d.get("concentration","125mg/5ml")
    d_copy["concentration"] = first_conc
    result = calc_child(d_copy, w, lang)
    
    # نضيف أزرار التراكيز في الأسفل
    change_btns = [[InlineKeyboardButton(c, callback_data="conc_" + c)] for c in concs[:4]]
    change_btns.append([InlineKeyboardButton("🔙 " + ("رجوع" if lang=="ar" else "Back"), callback_data="back")])
    
    note = "\n\n🔄 " + ("تغيير التركيز:" if lang=="ar" else "Change concentration:")

    try:
        await u.message.reply_text(result + note, reply_markup=InlineKeyboardMarkup(change_btns))
    except Exception as e:
        logger.error(f"child_weight final error: {e}")
        await u.message.reply_text(result, reply_markup=InlineKeyboardMarkup(change_btns))
    return STATE_CHILD_CONC


async def child_conc(u, ctx):
    """معالجة اختيار التركيز"""
    lang = get_lang(ctx)
    q = u.callback_query
    if q:
        await q.answer()
        data = q.data
        if data == "back":
            return await go_back(u, ctx)
        if data == "conc_custom":
            btns = [[InlineKeyboardButton(tx("btn_back", lang), callback_data="back")]]
            await q.message.edit_text("ادخل التركيز. مثال: 250mg/5ml", reply_markup=InlineKeyboardMarkup(btns))
            return STATE_CHILD_CONC
        if data.startswith("conc_"):
            conc_str = data.replace("conc_", "")
            d = ctx.user_data.get("child_drug")
            w = ctx.user_data.get("child_weight", 0)
            # نضع التركيز مؤقتاً في الدواء
            d_copy = dict(d)
            d_copy["concentration"] = conc_str
            result = calc_child(d_copy, w, lang)
            await q.message.edit_text(result, reply_markup=kb_back(lang), parse_mode=ParseMode.MARKDOWN)
            return STATE_CHILD_WEIGHT
    else:
        # إدخال نصي للتركيز
        txt = u.message.text.strip()
        d = ctx.user_data.get("child_drug")
        w = ctx.user_data.get("child_weight", 0)
        d_copy = dict(d)
        d_copy["concentration"] = txt
        result = calc_child(d_copy, w, lang)
        await u.message.reply_text(result, reply_markup=kb_back(lang), parse_mode=ParseMode.MARKDOWN)
        return STATE_CHILD_WEIGHT


async def cal_gender(u, ctx):
    q = u.callback_query; await q.answer()
    lang = get_lang(ctx)
    if q.data == "back": return await go_back(u, ctx)
    if q.data == "cal_food":
        await q.message.edit_text("🍎 اكتب اسم الطعام والكمية" if lang=="ar" else "🍎 Type food name and grams")
        return STATE_FOOD_SEARCH
    ctx.user_data["cal_gender"] = "m" if q.data == "cal_m" else "f"
    await q.message.edit_text("📅 كم عمرك؟" if lang=="ar" else "📅 How old are you?")
    return STATE_CAL_AGE

async def cal_age(u, ctx):
    lang = get_lang(ctx)
    try:
        age = int(u.message.text.strip())
        if not 5 <= age <= 100: raise ValueError
    except:
        await u.message.reply_text("❌ أدخل عمراً صحيحاً" if lang=="ar" else "❌ Enter valid age")
        return STATE_CAL_AGE
    ctx.user_data["cal_age"] = age
    await u.message.reply_text("⚖️ كم وزنك بالكيلو؟" if lang=="ar" else "⚖️ Weight in kg?")
    return STATE_CAL_WEIGHT

async def cal_weight(u, ctx):
    lang = get_lang(ctx)
    try:
        w = float(u.message.text.strip())
        if not 20 <= w <= 300: raise ValueError
    except:
        await u.message.reply_text("❌ أدخل وزناً صحيحاً" if lang=="ar" else "❌ Enter valid weight")
        return STATE_CAL_WEIGHT
    ctx.user_data["cal_weight"] = w
    await u.message.reply_text("📏 كم طولك بالسنتيمتر؟" if lang=="ar" else "📏 Height in cm?")
    return STATE_CAL_HEIGHT

async def cal_height(u, ctx):
    lang = get_lang(ctx)
    try:
        h = float(u.message.text.strip())
        if not 100 <= h <= 250: raise ValueError
    except:
        await u.message.reply_text("❌ أدخل طولاً صحيحاً" if lang=="ar" else "❌ Enter valid height")
        return STATE_CAL_HEIGHT
    ctx.user_data["cal_height"] = h
    btns = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛋️ خامل" if lang=="ar" else "🛋️ Sedentary", callback_data="act_1")],
        [InlineKeyboardButton("🚶 خفيف" if lang=="ar" else "🚶 Light", callback_data="act_2")],
        [InlineKeyboardButton("🏃 متوسط" if lang=="ar" else "🏃 Moderate", callback_data="act_3")],
        [InlineKeyboardButton("💪 نشيط" if lang=="ar" else "💪 Active", callback_data="act_4")],
        [InlineKeyboardButton("🏋️ رياضي" if lang=="ar" else "🏋️ Athlete", callback_data="act_5")]])
    await u.message.reply_text("🏃 مستوى النشاط؟" if lang=="ar" else "🏃 Activity level?", reply_markup=btns)
    return STATE_CAL_ACTIVITY

async def cal_activity(u, ctx):
    q = u.callback_query; await q.answer()
    lang = get_lang(ctx)
    act = q.data.replace("act_", "")
    ctx.user_data["cal_act"] = act
    btns = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ لا يوجد" if lang=="ar" else "✅ None", callback_data="dis_none")],
        [InlineKeyboardButton("🩺 سكري" if lang=="ar" else "🩺 Diabetes", callback_data="dis_diabetes")],
        [InlineKeyboardButton("❤️ قلب" if lang=="ar" else "❤️ Heart", callback_data="dis_heart")],
        [InlineKeyboardButton("🫘 كلى" if lang=="ar" else "🫘 Kidney", callback_data="dis_kidney")],
        [InlineKeyboardButton("⚖️ سمنة" if lang=="ar" else "⚖️ Obesity", callback_data="dis_obesity")]])
    await q.message.edit_text("🏥 هل لديك مرض مزمن؟" if lang=="ar" else "🏥 Any chronic disease?", reply_markup=btns)
    return STATE_CAL_DISEASE

async def cal_disease(u, ctx):
    q = u.callback_query; await q.answer()
    lang = get_lang(ctx)
    disease = q.data.replace("dis_", "")
    w = ctx.user_data.get("cal_weight", 70)
    h = ctx.user_data.get("cal_height", 170)
    age = ctx.user_data.get("cal_age", 30)
    gender = ctx.user_data.get("cal_gender", "m")
    act = ctx.user_data.get("cal_act", "2")
    bmr = calc_bmr(w, h, age, gender)
    tdee = bmr * ACTIVITY_FACTORS.get(act, 1.375)
    # تعديل حسب المرض
    note = ""
    if disease == "diabetes":
        tdee = tdee * 0.9
        note = "⚠️ تقليل الكربوهيدرات" if lang=="ar" else "⚠️ Reduce carbs"
    elif disease == "heart":
        note = "⚠️ تقليل الدهون المشبعة" if lang=="ar" else "⚠️ Reduce saturated fat"
    elif disease == "kidney":
        tdee = tdee * 0.85
        note = "⚠️ تقليل البروتين والبوتاسيوم" if lang=="ar" else "⚠️ Reduce protein & potassium"
    elif disease == "obesity":
        tdee = tdee * 0.8
        note = "⚠️ عجز 500 سعرة للتخسيس" if lang=="ar" else "⚠️ 500 cal deficit for weight loss"
    protein = w * 1.2
    carbs = (tdee * 0.5) / 4
    fat = (tdee * 0.3) / 9
    if lang == "ar":
        msg = "🔥 نتيجة حاسبة السعرات\n\n"
        msg += "⚖️ الوزن: " + str(w) + " كغ | الطول: " + str(h) + " سم\n"
        msg += "📅 العمر: " + str(age) + "\n"
        msg += "🔥 الاحتياج اليومي: " + str(int(tdee)) + " سعرة\n"
        msg += "💪 بروتين: " + str(int(protein)) + " غ\n"
        msg += "🍞 كربوهيدرات: " + str(int(carbs)) + " غ\n"
        msg += "🫙 دهون: " + str(int(fat)) + " غ\n"
        if note: msg += "\n" + note
    else:
        msg = "🔥 Calorie Calculator Result\n\n"
        msg += "Weight: " + str(w) + "kg | Height: " + str(h) + "cm\n"
        msg += "Age: " + str(age) + "\n"
        msg += "Daily Needs: " + str(int(tdee)) + " cal\n"
        msg += "Protein: " + str(int(protein)) + "g\n"
        msg += "Carbs: " + str(int(carbs)) + "g\n"
        msg += "Fat: " + str(int(fat)) + "g\n"
        if note: msg += "\n" + note


        if note: msg += note
    await q.message.edit_text(msg, reply_markup=kb_back(lang), parse_mode=ParseMode.MARKDOWN)
    return STATE_MAIN_MENU

async def food_search(u, ctx):
    lang = get_lang(ctx)
    txt = u.message.text.strip()
    parts = txt.split()
    grams = 100
    query = txt
    for p in parts:
        try:
            grams = float(p)
            query = txt.replace(p, "").strip()
            break
        except: pass
    food_en, food_data = search_food(query)
    if not food_data:
        await u.message.reply_text("❌ لم أجد هذا الطعام. جرّب: دجاج، أرز، بيض..." if lang=="ar" else "❌ Food not found. Try: chicken, rice, egg...")
        return STATE_FOOD_SEARCH
    factor = grams / 100
    cal = food_data["cal"] * factor
    prot = food_data["protein"] * factor
    carbs = food_data["carbs"] * factor
    fat = food_data["fat"] * factor
    if lang == "ar":
        msg = "🍎 " + str(query) + " - " + str(int(grams)) + " غرام\n\n"
        msg += "🔥 السعرات: " + str(int(cal)) + "\n"
        msg += "💪 بروتين: " + str(round(prot,1)) + " غ\n"
        msg += "🍞 كربوهيدرات: " + str(round(carbs,1)) + " غ\n"
        msg += "🫙 دهون: " + str(round(fat,1)) + " غ\n"
    else:
        msg = "🍎 " + str(query) + " - " + str(int(grams)) + "g\n\n"
        msg += "Calories: " + str(int(cal)) + "\n"
        msg += "Protein: " + str(round(prot,1)) + "g\n"
        msg += "Carbs: " + str(round(carbs,1)) + "g\n"
        msg += "Fat: " + str(round(fat,1)) + "g\n"
    await u.message.reply_text(msg, reply_markup=kb_back(lang), parse_mode=ParseMode.MARKDOWN)
    return STATE_FOOD_SEARCH

async def infection_site(u, ctx):
    q = u.callback_query; await q.answer()
    lang = get_lang(ctx)
    if q.data == "back": return await go_back(u, ctx)
    site = q.data.replace("site_", "")
    d = ctx.user_data.get("child_drug")
    w = ctx.user_data.get("child_weight", 0)
    name_key = d.get("name_en","").lower()
    doses = ANTIBIOTIC_DOSES.get(name_key, {}).get(site, ANTIBIOTIC_DOSES.get(name_key, {}).get("general"))
    if doses:
        min_mpk, max_mpk, freq, site_name = doses
        t_min = min_mpk * w / freq
        t_max = max_mpk * w / freq
        conc_str = d.get("concentration", "250mg/5ml")
        import re as _re4
        _mc = _re4.search(r"([\d.]+)mg/([\d.]+)ml", conc_str)
        conc = float(_mc.group(1)) / float(_mc.group(2)) * 5 if _mc else 50
        ml_min = (t_min / conc) * 5
        ml_max = (t_max / conc) * 5
        name_ar = d.get("name_ar", d.get("name_en", ""))
        if lang == "ar":
            msg = "🍼 جرعة الطفل - " + str(name_ar) + "\n"
            msg += "⚖️ الوزن: " + str(w) + " كغ\n"
            msg += "🦠 " + str(site_name) + "\n\n"

            msg += "📊 " + str(min_mpk) + "-" + str(max_mpk) + " مغ/كغ/يوم ÷ " + str(freq) + "\n"
            msg += "💉 الجرعة: " + str(int(t_min)) + "-" + str(int(t_max)) + " مغ\n"
            msg += "🥄 بالمل (" + conc_str + "): " + str(round(ml_min,1)) + "-" + str(round(ml_max,1)) + " مل\n\n"

            msg += "🔁 التكرار: " + str(freq) + " مرات يومياً\n"
            msg += "⚠️ استشر الطبيب أو الصيدلاني."
        else:
            msg = "🍼 Child Dose - " + str(name_key) + "\n"
            msg += "Weight: " + str(w) + "kg | " + str(site_name) + "\n\n"

            msg += str(min_mpk) + "-" + str(max_mpk) + " mg/kg/day\n"
            msg += "Dose: " + str(int(t_min)) + "-" + str(int(t_max)) + " mg\n"
            msg += "In ml (" + conc_str + "): " + str(round(ml_min,1)) + "-" + str(round(ml_max,1)) + " ml\n\n"

            msg += "Frequency: " + str(freq) + " times/day\n"
            msg += "⚠️ Consult doctor or pharmacist."
        # نسأل عن التركيز
        DRUG_CONCS_LOCAL = {
            "amoxicillin": ["125mg/5ml", "156mg/5ml", "250mg/5ml", "312mg/5ml"],
            "amoxicillin_clavulanate": ["156mg/5ml", "228mg/5ml", "312mg/5ml", "457mg/5ml", "600mg/5ml"],
            "azithromycin": ["100mg/5ml", "200mg/5ml"],
            "clarithromycin": ["125mg/5ml", "250mg/5ml"],
            "cephalexin": ["125mg/5ml", "250mg/5ml"],
        }
        concs = DRUG_CONCS_LOCAL.get(name_key, [])
        ctx.user_data["infection_msg"] = msg
        if concs:
            btns = [[InlineKeyboardButton(c, callback_data="conc_" + c)] for c in concs]
            btns.append([InlineKeyboardButton("🔢 تركيز آخر" if lang=="ar" else "🔢 Other", callback_data="conc_custom")])
            btns.append([InlineKeyboardButton(tx("btn_back", lang), callback_data="back")])
            cmsg = "💊 اختر التركيز:" if lang=="ar" else "💊 Select concentration:"
            await q.message.edit_text(cmsg, reply_markup=InlineKeyboardMarkup(btns))
            return STATE_CHILD_CONC
        await q.message.edit_text(msg, reply_markup=kb_back(lang), parse_mode=ParseMode.MARKDOWN)
    return STATE_CHILD_WEIGHT


def kb_image_result(lang, drug_name=""):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ " + ("الدواء خطأ — أدخل الاسم" if lang=="ar" else "Wrong drug — Type name"), callback_data="manual_input")],
        [InlineKeyboardButton("📸 " + ("جرّب صورة أخرى" if lang=="ar" else "Try another photo"), callback_data="retry_photo")],
        [InlineKeyboardButton("🔙 " + ("القائمة الرئيسية" if lang=="ar" else "Main Menu"), callback_data="back")],
    ])

async def img_ok(u, ctx):
    q = u.callback_query; await q.answer()
    lang = get_lang(ctx)
    await q.message.edit_text(tx("weight_prompt", lang))
    return STATE_CHILD_WEIGHT

async def retry_photo(u, ctx):
    q = u.callback_query; await q.answer()
    lang = get_lang(ctx)
    msg = "📸 أرسل صورة العبوة:" if lang=="ar" else "📸 Send the medicine photo:"
    await q.message.edit_text(msg)
    return STATE_CHILD_DRUG

async def manual_drug_input(u, ctx):
    q = u.callback_query; await q.answer()
    lang = get_lang(ctx)
    msg = "✏️ اكتب اسم الدواء:" if lang=="ar" else "✏️ Type the drug name:"
    await q.message.edit_text(msg)
    return STATE_CHILD_DRUG
    return STATE_CHILD_DRUG


async def sugar_handler(u, ctx):
    track(u, "sugar")
    q = u.callback_query; await q.answer()
    lang = get_lang(ctx)
    ctx.user_data["sugar_type"] = q.data
    msgs = {
        "sugar_fasting": "🌅 أدخل قراءة سكر الصيام (mg/dL):" if lang=="ar" else "🌅 Enter fasting sugar (mg/dL):",
        "sugar_postmeal": "🍽️ أدخل قراءة السكر بعد الأكل بساعتين على الأقل (mg/dL):" if lang=="ar" else "🍽️ Enter post-meal sugar (2hrs after eating) (mg/dL):",
        "sugar_hba1c": "📊 أدخل قيمة HbA1c (%):" if lang=="ar" else "📊 Enter HbA1c (%):",
    }
    await q.message.edit_text(msgs.get(q.data, "أدخل القراءة:"))
    return STATE_SUGAR

async def sugar_result(u, ctx):
    lang = get_lang(ctx)
    sugar_type = ctx.user_data.get("sugar_type", "sugar_fasting")
    try:
        val = float(u.message.text.strip())
    except:
        await u.message.reply_text("❌ أدخل رقماً صحيحاً" if lang=="ar" else "❌ Enter valid number")
        return STATE_SUGAR

    if sugar_type == "sugar_fasting":
        if val < 70:
            status = "⚠️ منخفض - Hypoglycemia" if lang=="ar" else "⚠️ Low - Hypoglycemia"
            color = "🔴"
        elif val <= 100:
            status = "✅ طبيعي" if lang=="ar" else "✅ Normal"
            color = "🟢"
        elif val <= 125:
            status = "🟡 ما قبل السكري" if lang=="ar" else "🟡 Pre-diabetes"
            color = "🟡"
        else:
            status = "🔴 مرتفع - سكري" if lang=="ar" else "🔴 High - Diabetes"
            color = "🔴"
        msg = color + " سكر الصيام: " + str(val) + " mg/dL\n" + status

    elif sugar_type == "sugar_postmeal":
        if val < 140:
            status = "✅ طبيعي" if lang=="ar" else "✅ Normal"
            color = "🟢"
        elif val <= 199:
            status = "🟡 ما قبل السكري" if lang=="ar" else "🟡 Pre-diabetes"
            color = "🟡"
        else:
            status = "🔴 مرتفع - سكري" if lang=="ar" else "🔴 High - Diabetes"
            color = "🔴"
        msg = color + " سكر ما بعد الأكل: " + str(val) + " mg/dL\n" + status

    else:  # hba1c
        avg = round((val * 28.7) - 46.7, 1)
        if val < 5.7:
            status = "✅ طبيعي" if lang=="ar" else "✅ Normal"
        elif val < 6.5:
            status = "🟡 ما قبل السكري" if lang=="ar" else "🟡 Pre-diabetes"
        else:
            status = "🔴 سكري" if lang=="ar" else "🔴 Diabetes"
        msg = "📊 HbA1c: " + str(val) + "%\n" + status + "\n" + ("متوسط السكر: " if lang=="ar" else "Avg Sugar: ") + str(avg) + " mg/dL"

    await u.message.reply_text(msg, reply_markup=kb_back(lang))
    return STATE_MAIN_MENU

async def bp_age(u, ctx):
    track(u, "bp")
    lang = get_lang(ctx)
    try:
        age = int(u.message.text.strip())
        if not 1 <= age <= 120: raise ValueError
    except:
        await u.message.reply_text("❌ أدخل عمراً صحيحاً" if lang=="ar" else "❌ Enter valid age")
        return STATE_BP_AGE
    ctx.user_data["bp_age"] = age
    await u.message.reply_text("💉 أدخل قراءة الضغط مثال: 120/80" if lang=="ar" else "💉 Enter BP example: 120/80")
    return STATE_BP

async def bp_result(u, ctx):
    lang = get_lang(ctx)
    age = ctx.user_data.get("bp_age", 40)
    try:
        parts = u.message.text.strip().replace(" ", "").split("/")
        sys = int(parts[0])
        dia = int(parts[1])
    except:
        await u.message.reply_text("❌ صيغة خاطئة. مثال: 120/80" if lang=="ar" else "❌ Wrong format. Example: 120/80")
        return STATE_BP
    # تعديل حدود الضغط حسب العمر
    normal_sys = 110 + (age // 10) if age > 40 else 120
    age_note = " (عمر: " + str(age) + " سنة)" if lang=="ar" else " (Age: " + str(age) + " yr)"

    # معايير الأطفال حسب العمر
    if age < 18:
        if age < 6:
            norm_sys, norm_dia = 100, 65
        elif age < 10:
            norm_sys, norm_dia = 110, 70
        elif age < 13:
            norm_sys, norm_dia = 115, 75
        else:
            norm_sys, norm_dia = 120, 80

        if sys < norm_sys - 20 or dia < norm_dia - 10:
            status = "⚠️ انخفاض الضغط" if lang=="ar" else "⚠️ Low BP"
            advice = "راجع الطبيب." if lang=="ar" else "See doctor."
            color = "🔵"
        elif sys <= norm_sys and dia <= norm_dia:
            status = "✅ طبيعي للعمر" if lang=="ar" else "✅ Normal for age"
            advice = "ممتاز!" if lang=="ar" else "Excellent!"
            color = "🟢"
        elif sys <= norm_sys + 10:
            status = "🟡 مرتفع قليلاً" if lang=="ar" else "🟡 Slightly High"
            advice = "راقب الضغط وراجع الطبيب." if lang=="ar" else "Monitor and see doctor."
            color = "🟡"
        else:
            status = "🔴 مرتفع - راجع الطبيب" if lang=="ar" else "🔴 High - See doctor"
            advice = "راجع الطبيب فوراً." if lang=="ar" else "See doctor immediately."
            color = "🔴"

        msg = color + " الضغط: " + str(sys) + "/" + str(dia) + " mmHg" + age_note + "\n" + status + "\n\n💡 " + advice
        await u.message.reply_text(msg, reply_markup=kb_back(lang))
        return STATE_MAIN_MENU

    if sys < 90 or dia < 60:
        status = "⚠️ انخفاض الضغط" if lang=="ar" else "⚠️ Low Blood Pressure"
        advice = "اشرب ماء واستلقِ، راجع الطبيب إذا استمر." if lang=="ar" else "Drink water, lie down. See doctor if it persists."
        color = "🔵"
    elif sys < 120 and dia < 80:
        status = "✅ ضغط طبيعي ممتاز" if lang=="ar" else "✅ Optimal BP"
        advice = "ممتاز! حافظ على نمط حياة صحي." if lang=="ar" else "Excellent! Maintain healthy lifestyle."
        color = "🟢"
    elif sys < 130 and dia < 80:
        status = "✅ ضغط طبيعي" if lang=="ar" else "✅ Normal BP"
        advice = "جيد. استمر على النظام الصحي." if lang=="ar" else "Good. Continue healthy habits."
        color = "🟢"
    elif sys < 140 and dia < 90:
        status = "🟡 ارتفاع خفيف (مرحلة 1)" if lang=="ar" else "🟡 Mild Hypertension (Stage 1)"
        advice = "قلل الملح والدهون، مارس الرياضة، راقب الضغط يومياً وراجع الطبيب." if lang=="ar" else "Reduce salt and fat, exercise regularly, monitor daily and see doctor."
        color = "🟡"
    elif sys < 160 or dia < 100:
        status = "🔴 ارتفاع متوسط (مرحلة 2)" if lang=="ar" else "🔴 Moderate Hypertension (Stage 2)"
        advice = "راجع الطبيب فوراً. قد تحتاج دواءً لضبط الضغط." if lang=="ar" else "See doctor soon. Medication may be required."
        color = "🔴"
    elif sys < 180 or dia < 120:
        status = "🚨 ارتفاع شديد (مرحلة 3)" if lang=="ar" else "🚨 Severe Hypertension (Stage 3)"
        advice = "راجع الطبيب اليوم! خطر على القلب والكلى." if lang=="ar" else "See doctor today! Risk of heart and kidney damage."
        color = "🚨"
    else:
        status = "🆘 أزمة ضغط خبيثة" if lang=="ar" else "🆘 Hypertensive Crisis"
        advice = "اذهب للطوارئ فوراً!" if lang=="ar" else "Go to emergency immediately!"
        color = "🆘"

    msg = color + " الضغط: " + str(sys) + "/" + str(dia) + " mmHg\n" + status + "\n\n💡 " + advice
    await u.message.reply_text(msg, reply_markup=kb_back(lang))
    return STATE_MAIN_MENU


# ═══════════════ ملف المريض ═══════════════

def get_patients(ctx):
    uid = ctx.user_data.get("uid", "0")
    return ctx.user_data.setdefault("patients", {})

def save_patients(ctx):
    uid = ctx.user_data.get("uid", "0")
    all_rems = load_all_reminders()
    patients = ctx.user_data.get("patients", {})
    all_rems[uid + "_patients"] = patients
    save_all_reminders(all_rems)

def load_patients(ctx):
    uid = ctx.user_data.get("uid", "0")
    all_data = load_all_reminders()
    patients = all_data.get(uid + "_patients", {})
    ctx.user_data["patients"] = patients
    return patients

def kb_patient_menu(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ " + ("إضافة مريض" if lang=="ar" else "Add Patient"), callback_data="pat_add")],
        [InlineKeyboardButton("📋 " + ("قائمة المرضى" if lang=="ar" else "Patient List"), callback_data="pat_list")],
        [InlineKeyboardButton(tx("btn_back", lang), callback_data="back")]
    ])

async def patient_menu(u, ctx):
    q = u.callback_query; await q.answer()
    lang = get_lang(ctx)
    if q.data == "back": return await go_back(u, ctx)
    load_patients(ctx)
    patients = ctx.user_data.get("patients", {})
    
    if q.data == "pat_add":
        await q.message.edit_text("👤 " + ("أدخل اسم المريض:" if lang=="ar" else "Enter patient name:"))
        return STATE_PAT_NAME
    
    if q.data == "pat_list":
        patients = ctx.user_data.get("patients", {})
        if not patients:
            await q.message.edit_text("📭 " + ("لا يوجد مرضى" if lang=="ar" else "No patients"), reply_markup=kb_patient_menu(lang))
            return STATE_PAT_MENU
        btns = [[InlineKeyboardButton("👤 " + name, callback_data="pat_view_" + pid)] for pid, name in [(p, patients[p]["name"]) for p in patients]]
        btns.append([InlineKeyboardButton(tx("btn_back", lang), callback_data="back")])
        await q.message.edit_text("📋 " + ("المرضى:" if lang=="ar" else "Patients:"), reply_markup=InlineKeyboardMarkup(btns))
        return STATE_PAT_MENU
    
    if q.data.startswith("pat_view_"):
        pid = q.data.replace("pat_view_", "")
        patients = ctx.user_data.get("patients", {})
        p = patients.get(pid, {})
        if not p:
            await q.message.edit_text("❌ " + ("لم يوجد" if lang=="ar" else "Not found"), reply_markup=kb_patient_menu(lang))
            return STATE_PAT_MENU
        lines = ["👤 *" + p.get("name","") + "*", ""]
        lines.append(("📅 العمر: " if lang=="ar" else "📅 Age: ") + str(p.get("age","-")))
        lines.append(("⚖️ الوزن: " if lang=="ar" else "⚖️ Weight: ") + str(p.get("weight","-")) + " kg")
        gender_val = p.get("gender","-")
        if lang == "en":
            gender_val = {"ذكر":"Male","أنثى":"Female"}.get(gender_val, gender_val)
        lines.append(("👤 الجنس: " if lang=="ar" else "👤 Gender: ") + str(gender_val))
        if p.get("diseases"):
            lines.append(("🏥 الأمراض: " if lang=="ar" else "🏥 Diseases: ") + p["diseases"])
        if p.get("meds"):
            lines.append(("💊 الأدوية: " if lang=="ar" else "💊 Medications: ") + p["meds"])
        if p.get("allergy"):
            lines.append(("⚠️ حساسية: " if lang=="ar" else "⚠️ Allergy: ") + p["allergy"])
        meds_btns = []
        if p.get("meds"):
            meds_list = [m.strip() for m in p["meds"].replace("،",",").split(",") if m.strip()]
            pat_name = p.get("name","")
            for med in meds_list[:3]:
                safe_med = med.replace("|","").replace("__","")[:10]
                cb = ("pr__" + pid + "__" + safe_med)[:64]
                meds_btns.append([InlineKeyboardButton("⏰ " + med[:15], callback_data=cb)])
        
        btns = meds_btns + [
            [InlineKeyboardButton("📊 " + ("سجل السكر/الضغط" if lang=="ar" else "Sugar/BP Log"), callback_data="pat_log_" + pid)],
            [InlineKeyboardButton("🖨️ " + ("تصدير PDF" if lang=="ar" else "Export PDF"), callback_data="pat_pdf_" + pid)],
            [InlineKeyboardButton("📝 " + ("إضافة ملاحظة" if lang=="ar" else "Add Note"), callback_data="pat_note_" + pid)],
            [InlineKeyboardButton("📊 " + ("سجل السكر والضغط" if lang=="ar" else "Sugar & BP Log"), callback_data="pat_log_" + pid)],
            [InlineKeyboardButton("✏️ " + ("تعديل البيانات" if lang=="ar" else "Edit Data"), callback_data="pat_edit_" + pid)],
            [InlineKeyboardButton("➕ " + ("إضافة مريض آخر" if lang=="ar" else "Add Another Patient"), callback_data="pat_add")],
            [InlineKeyboardButton("🗑️ " + ("حذف" if lang=="ar" else "Delete"), callback_data="pat_del_" + pid)],
            [InlineKeyboardButton("🔙 " + ("القائمة الرئيسية" if lang=="ar" else "Main Menu"), callback_data="back")]
        ]
        await q.message.edit_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(btns), parse_mode=ParseMode.MARKDOWN)
        return STATE_PAT_MENU
    
    if q.data.startswith("pr__"):
        parts = q.data.split("__")
        if len(parts) >= 3:
            pid2 = parts[1]
            med2 = parts[2]
            pat_name2 = patients.get(pid2,{}).get("name","")
            ctx.user_data["nr_drug"] = med2
            ctx.user_data["nr_patient"] = pat_name2
            await q.message.edit_text("🕐 " + ("أدخل وقت التذكير مثال 08:00:" if lang=="ar" else "Enter time e.g. 08:00:"))
            return STATE_REM_ADD_TIME
    
    if q.data.startswith("pat_pdf_"):
        pid = q.data.replace("pat_pdf_","")
        p = patients.get(pid,{})
        await q.answer("🔄 " + ("جارٍ إنشاء PDF..." if lang=="ar" else "Creating PDF..."), show_alert=True)
        
        # نبني محتوى التقرير
        from datetime import datetime
        lines = []
        lines.append("=" * 40)
        lines.append("ملف المريض الطبي" if lang=="ar" else "Patient Medical File")
        lines.append("=" * 40)
        lines.append("")
        lines.append(("الاسم: " if lang=="ar" else "Name: ") + p.get("name",""))
        lines.append(("العمر: " if lang=="ar" else "Age: ") + str(p.get("age","")))
        lines.append(("الوزن: " if lang=="ar" else "Weight: ") + str(p.get("weight","")) + " kg")
        lines.append(("الجنس: " if lang=="ar" else "Gender: ") + str(p.get("gender","")))
        if p.get("diseases"):
            lines.append(("الأمراض: " if lang=="ar" else "Diseases: ") + p["diseases"])
        if p.get("meds"):
            lines.append(("الأدوية: " if lang=="ar" else "Medications: ") + p["meds"])
        if p.get("allergy"):
            lines.append(("الحساسية: " if lang=="ar" else "Allergies: ") + p["allergy"])
        
        # القراءات
        readings = p.get("readings",[])
        if readings:
            lines.append("")
            lines.append("=" * 40)
            lines.append("سجل القراءات:" if lang=="ar" else "Readings Log:")
            
            bp_r = [r for r in readings if r.get("bp")]
            fasting_r = [r for r in readings if r.get("sugar") and r.get("stype") == "fasting"]
            postmeal_r = [r for r in readings if r.get("sugar") and r.get("stype") == "postmeal"]
            hba1c_r = [r for r in readings if r.get("sugar") and r.get("stype") == "hba1c"]
            random_r = [r for r in readings if r.get("sugar") and r.get("stype","random") not in ["fasting","postmeal","hba1c"]]
            
            if bp_r:
                lines.append("💉 قراءات الضغط:")
                for r in bp_r: lines.append("  " + r["date"] + ": " + str(r["bp"]))
            if fasting_r:
                lines.append("🌅 سكر الصيام:")
                for r in fasting_r: lines.append("  " + r["date"] + ": " + str(r["sugar"]) + " mg/dL")
            if postmeal_r:
                lines.append("🍽️ سكر بعد الأكل:")
                for r in postmeal_r: lines.append("  " + r["date"] + ": " + str(r["sugar"]) + " mg/dL")
            if hba1c_r:
                lines.append("📊 HbA1c التراكمي:")
                for r in hba1c_r: lines.append("  " + r["date"] + ": " + str(r["sugar"]) + "%")
            if random_r:
                lines.append("🎲 قراءات عشوائية:")
                for r in random_r: lines.append("  " + r["date"] + ": " + str(r["sugar"]) + " mg/dL")
        
        # الملاحظات
        notes = p.get("notes",[])
        if notes:
            lines.append("")
            lines.append("=" * 40)
            lines.append("الملاحظات:" if lang=="ar" else "Notes:")
            for n in notes:
                if n.get("type") == "text":
                    lines.append("📝 " + n["date"] + ": " + n["content"])
                elif n.get("type") == "photo":
                    lines.append("📸 " + n["date"] + ": " + ("صورة - سيتم إرسالها منفصلة" if lang=="ar" else "Photo - will be sent separately"))
                elif n.get("type") == "file":
                    lines.append("📄 " + n["date"] + ": " + n.get("name","ملف"))
        
        lines.append("")
        lines.append("تاريخ التصدير: " + datetime.now().strftime("%Y-%m-%d %H:%M"))
        
        report = "\n".join(lines)
        await u.effective_chat.send_message("```\n" + report + "\n```", parse_mode="Markdown")
        
        # نرسل الصور منفصلة
        photos = [n for n in p.get("notes",[]) if n.get("type") == "photo"]
        if photos:
            await u.effective_chat.send_message("📸 " + ("صور الملف:" if lang=="ar" else "File Photos:"))
            for ph in photos:
                try:
                    caption = ph.get("caption","") or ph.get("date","")
                    await u.effective_chat.send_photo(ph["file_id"], caption=caption)
                except: pass
        
        return STATE_PAT_MENU
    
    if q.data.startswith("pat_log_"):
        pid = q.data.replace("pat_log_","")
        p = patients.get(pid,{})
        readings = p.get("readings",[])
        lines = ["📊 *" + ("سجل " if lang=="ar" else "Log: ") + p.get("name","") + "*",""]
        if readings:
            sugar_readings = [r for r in readings if r.get("sugar")]
            bp_readings = [r for r in readings if r.get("bp")]
            if bp_readings:
                lines.append("💉 " + ("آخر قراءات الضغط:" if lang=="ar" else "Latest BP:"))
                for r in bp_readings[-3:]:
                    sys_val = r.get("sys",0)
                    if sys_val < 120: status = "✅"
                    elif sys_val < 130: status = "🟡"
                    elif sys_val < 140: status = "🟠"
                    else: status = "🔴"
                    lines.append("  " + status + " " + r["date"] + ": " + str(r["bp"]))
            if sugar_readings:
                lines.append("")
                lines.append("🩸 " + ("آخر قراءات السكر:" if lang=="ar" else "Latest Sugar:"))
                for r in sugar_readings[-3:]:
                    val = r["sugar"]
                    if val < 70: status = "⚠️"
                    elif val <= 100: status = "✅"
                    elif val <= 125: status = "🟡"
                    else: status = "🔴"
                    stype = r.get("stype","")
                    stype_ar = r.get("stype_ar","")
                    if stype == "hba1c":
                        if val < 5.7: status = "✅"
                        elif val <= 6.4: status = "🟡"
                        elif val <= 7.0: status = "🟠"
                        else: status = "🔴"
                        lines.append("  " + status + " " + r["date"] + ": " + str(val) + "% (HbA1c تراكمي)")
                    else:
                        if val < 70: status = "⚠️"
                        elif val <= 100: status = "✅"
                        elif val <= 125: status = "🟡"
                        else: status = "🔴"
                        label = " (" + stype_ar + ")" if stype_ar else ""
                        lines.append("  " + status + " " + r["date"] + ": " + str(val) + " mg/dL" + label)
        else:
            lines.append("📭 " + ("لا توجد قراءات" if lang=="ar" else "No readings"))
        btns = InlineKeyboardMarkup([
            [InlineKeyboardButton("✏️ " + ("أضف قراءة" if lang=="ar" else "Add Reading"), callback_data="pat_addreading_" + pid)],
            [InlineKeyboardButton("📈 " + ("سجل السكر" if lang=="ar" else "Sugar Log"), callback_data="pat_viewsugar_" + pid),
             InlineKeyboardButton("📉 " + ("سجل الضغط" if lang=="ar" else "BP Log"), callback_data="pat_viewbp_" + pid)],
            [InlineKeyboardButton(tx("btn_back", lang), callback_data="pat_view_" + pid)]
        ])
        await q.message.edit_text("\n".join(lines), reply_markup=btns, parse_mode="Markdown")
        return STATE_PAT_MENU
    
    if q.data.startswith("pat_viewfasting_") or q.data.startswith("pat_viewpostmeal_") or q.data.startswith("pat_viewhba1c_") or q.data.startswith("pat_viewrandom_"):
        for prefix in ["pat_viewfasting_","pat_viewpostmeal_","pat_viewhba1c_","pat_viewrandom_"]:
            if q.data.startswith(prefix):
                pid = q.data.replace(prefix,"")
                stype = prefix.replace("pat_view","").replace("_","")
                break
        p = patients.get(pid,{})
        readings = p.get("readings",[])
        
        stype_map = {"fasting":"🌅 سكر الصيام","postmeal":"🍽️ سكر بعد الأكل","hba1c":"📊 HbA1c التراكمي","random":"🎲 عشوائي"}
        unit_map = {"hba1c":"%","fasting":"mg/dL","postmeal":"mg/dL","random":"mg/dL"}
        
        filtered = [r for r in readings if r.get("sugar") and r.get("stype","random") == stype]
        lines = [stype_map.get(stype,"📊") + " *" + p.get("name","") + "*",""]
        
        if filtered:
            for i, r in enumerate(filtered[-10:]):
                unit = unit_map.get(stype,"mg/dL")
                lines.append(f"  {i+1}. {r['date'][:16]}: {r['sugar']} {unit}")
        else:
            lines.append("📭 لا توجد قراءات")
        
        # أزرار حذف
        del_btns = []
        for i, r in enumerate(filtered[-5:]):
            del_btns.append([InlineKeyboardButton(f"🗑️ {r['date'][:10]}: {r['sugar']}", callback_data=f"pat_delreading_{pid}_{r['date']}")])
        del_btns.append([InlineKeyboardButton(tx("btn_back", lang), callback_data="pat_log_" + pid)])
        
        await q.message.edit_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(del_btns), parse_mode="Markdown")
        return STATE_PAT_MENU

    if q.data.startswith("pat_delreading_"):
        parts = q.data.replace("pat_delreading_","").split("_",1)
        pid = parts[0]
        date_key = parts[1] if len(parts)>1 else ""
        p = patients.get(pid,{})
        before = len(p.get("readings",[]))
        p["readings"] = [r for r in p.get("readings",[]) if r.get("date","") != date_key]
        after = len(p.get("readings",[]))
        save_patients(ctx)
        await q.answer("✅ " + (f"تم حذف {before-after} قراءة" if lang=="ar" else f"Deleted {before-after} reading"))
        return STATE_PAT_MENU

    if q.data.startswith("pat_viewsugar_"):
        pid = q.data.replace("pat_viewsugar_","")
        p = patients.get(pid,{})
        readings = [r for r in p.get("readings",[]) if r.get("sugar")]
        lines = ["🩸 *" + ("سجل السكر - " if lang=="ar" else "Sugar Log - ") + p.get("name","") + "*",""]
        if readings:
            for r in readings[-15:]:
                val = r["sugar"]
                if val < 70: status = "⚠️"
                elif val <= 100: status = "✅"
                elif val <= 125: status = "🟡"
                else: status = "🔴"
                lines.append(status + " " + r["date"] + ": " + str(val) + " mg/dL")
        else:
            lines.append("📭 " + ("لا توجد قراءات" if lang=="ar" else "No readings"))
        await q.message.edit_text("\n".join(lines),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tx("btn_back", lang), callback_data="pat_log_" + pid)]]),
            parse_mode="Markdown")
        return STATE_PAT_MENU

    if q.data.startswith("pat_viewbp_"):
        pid = q.data.replace("pat_viewbp_","")
        p = patients.get(pid,{})
        readings = [r for r in p.get("readings",[]) if r.get("bp")]
        lines = ["💉 *" + ("سجل الضغط - " if lang=="ar" else "BP Log - ") + p.get("name","") + "*",""]
        if readings:
            for r in readings[-15:]:
                sys_val = r.get("sys",0)
                if sys_val < 120: status = "✅"
                elif sys_val < 130: status = "🟡"
                elif sys_val < 140: status = "🟠"
                else: status = "🔴"
                lines.append(status + " " + r["date"] + ": " + str(r["bp"]))
        else:
            lines.append("📭 " + ("لا توجد قراءات" if lang=="ar" else "No readings"))
        await q.message.edit_text("\n".join(lines),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tx("btn_back", lang), callback_data="pat_log_" + pid)]]),
            parse_mode="Markdown")
        return STATE_PAT_MENU

    if q.data.startswith("pat_addreading_"):
        pid = q.data.replace("pat_addreading_","")
        ctx.user_data["log_pid"] = pid
        btns = InlineKeyboardMarkup([
            [InlineKeyboardButton("💉 " + ("قراءة ضغط" if lang=="ar" else "Blood Pressure"), callback_data="sugtype_bp_" + pid)],
            [InlineKeyboardButton("🌅 " + ("سكر صيام" if lang=="ar" else "Fasting Sugar"), callback_data="sugtype_fasting_" + pid)],
            [InlineKeyboardButton("🍽️ " + ("سكر بعد الأكل بساعتين" if lang=="ar" else "Post-meal 2hrs"), callback_data="sugtype_postmeal_" + pid)],
            [InlineKeyboardButton("📊 " + ("سكر تراكمي HbA1c" if lang=="ar" else "HbA1c"), callback_data="sugtype_hba1c_" + pid)],
            [InlineKeyboardButton("🎲 " + ("سكر عشوائي" if lang=="ar" else "Random Sugar"), callback_data="sugtype_random_" + pid)],
            [InlineKeyboardButton(tx("btn_back", lang), callback_data="pat_log_" + pid)]
        ])
        await q.message.edit_text("📝 " + ("اختر نوع القراءة:" if lang=="ar" else "Select reading type:"), reply_markup=btns)
        return STATE_PAT_MENU

    if q.data.startswith("pat_addsugar_"):
        pid = q.data.replace("pat_addsugar_","")
        ctx.user_data["log_pid"] = pid
        ctx.user_data["log_type"] = "sugar"
        btns = InlineKeyboardMarkup([
            [InlineKeyboardButton("🌅 " + ("صيام" if lang=="ar" else "Fasting"), callback_data="sugtype_fasting_" + pid),
             InlineKeyboardButton("🍽️ " + ("بعد الأكل" if lang=="ar" else "Post-meal"), callback_data="sugtype_postmeal_" + pid)],
            [InlineKeyboardButton("🎲 " + ("عشوائي" if lang=="ar" else "Random"), callback_data="sugtype_random_" + pid),
             InlineKeyboardButton("📊 " + ("تراكمي HbA1c" if lang=="ar" else "HbA1c"), callback_data="sugtype_hba1c_" + pid)],
        ])
        await q.message.edit_text("🩸 " + ("نوع قراءة السكر؟" if lang=="ar" else "Sugar reading type?"), reply_markup=btns)
        return STATE_PAT_MENU
    
    if q.data.startswith("sugtype_"):
        parts = q.data.split("_")
        stype = parts[1]
        pid = parts[2]
        ctx.user_data["log_pid"] = pid
        ctx.user_data[f"stype_{pid}"] = stype
        
        if stype == "bp":
            ctx.user_data["log_type"] = "bp"
            await q.message.edit_text("💉 " + ("أدخل قراءة الضغط (مثال: 120/80):" if lang=="ar" else "Enter BP (e.g. 120/80):"),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tx("btn_back", lang), callback_data="pat_addreading_" + pid)]]))
            return STATE_PAT_LOG
        else:
            ctx.user_data["log_type"] = "sugar"
            ctx.user_data["sugar_type"] = stype
        type_names = {"fasting":"صيام","postmeal":"بعد الأكل","random":"عشوائي","hba1c":"تراكمي"}
        type_name = type_names.get(stype, stype)
        type_emoji = {"hba1c":"📊","fasting":"🌅","postmeal":"🍽️","random":"🎲"}.get(stype,"🩸")
        type_unit = "%" if stype == "hba1c" else "mg/dL"
        # نحفظ النوع في اسم المفتاح الثابت
        ctx.user_data[f"stype_{pid}"] = stype
        if stype == "hba1c":
            msg = "📊 اكتب مثال: تراكمي 7.5"
        elif stype == "fasting":
            msg = "🌅 اكتب مثال: صيام 95"
        elif stype == "postmeal":
            msg = "🍽️ اكتب مثال: بعداكل 140"
        else:
            msg = "🎲 اكتب مثال: عشوائي 110"
        await q.message.edit_text(msg)
        return STATE_PAT_LOG
    
    if q.data.startswith("pat_addbp_"):
        pid = q.data.replace("pat_addbp_","")
        ctx.user_data["log_pid"] = pid
        ctx.user_data["log_type"] = "bp"
        await q.message.edit_text("💉 اكتب مثال: ضغط 120/80")
        return STATE_PAT_LOG
    
    if q.data.startswith("pat_edit_"):
        pid = q.data.replace("pat_edit_","")
        p = patients.get(pid,{})
        btns = InlineKeyboardMarkup([
            [InlineKeyboardButton("👤 " + ("الاسم: " if lang=="ar" else "Name: ") + str(p.get("name","")), callback_data="patedit_name_" + pid)],
            [InlineKeyboardButton("📅 " + ("العمر: " if lang=="ar" else "Age: ") + str(p.get("age","")), callback_data="patedit_age_" + pid)],
            [InlineKeyboardButton("⚖️ " + ("الوزن: " if lang=="ar" else "Weight: ") + str(p.get("weight","")), callback_data="patedit_weight_" + pid)],
            [InlineKeyboardButton("💊 " + ("الأدوية" if lang=="ar" else "Medications"), callback_data="patedit_meds_" + pid)],
            [InlineKeyboardButton("🏥 " + ("الأمراض" if lang=="ar" else "Diseases"), callback_data="patedit_diseases_" + pid)],
            [InlineKeyboardButton("⚠️ " + ("الحساسية" if lang=="ar" else "Allergies"), callback_data="patedit_allergy_" + pid)],
            [InlineKeyboardButton(tx("btn_back", lang), callback_data="pat_view_" + pid)]
        ])
        await q.message.edit_text("✏️ " + ("اختر ما تريد تعديله:" if lang=="ar" else "Select what to edit:"), reply_markup=btns)
        return STATE_PAT_MENU

    if q.data.startswith("patedit_"):
        parts = q.data.split("_")
        field = parts[1]
        pid = parts[2]
        ctx.user_data["edit_pid"] = pid
        ctx.user_data["edit_field"] = field
        p = patients.get(pid,{})
        
        if field in ["meds","diseases"]:
            current = p.get(field,"")
            selected = [x.strip() for x in current.replace("،",",").split(",") if x.strip()] if current else []
            
            if field == "diseases":
                options = ["ضغط","سكري","قلب","كلى","كبد","غدة","ربو","سرطان","روماتيزم","أنيميا","كولسترول","جلطة","قرحة","حساسية"] if lang=="ar" else ["Hypertension","Diabetes","Heart disease","Kidney disease","Liver disease","Thyroid","Asthma","Cancer","Arthritis","Anemia","Cholesterol","Stroke","Ulcer","Allergy"]
            else:
                options = ["ميتفورمين","أملودبين","ليزينوبريل","أتورفاستاتين","أسبرين","ميتوبرولول","ليفوثيروكسين","أوميبرازول","وارفارين","لوساتران","إنسولين","كونكور"] if lang=="ar" else ["Metformin","Amlodipine","Lisinopril","Atorvastatin","Aspirin","Metoprolol","Levothyroxine","Omeprazole","Warfarin","Losartan","Insulin","Bisoprolol"]
            
            lines = ["✏️ " + ("اختر الأمراض:" if field=="diseases" else "اختر الأدوية:"), ""]
            lines.append("✅ " + ("المختار: " if lang=="ar" else "Selected: ") + ("، ".join(selected) if selected else "لا يوجد"))
            
            btns = []
            row = []
            for opt in options:
                icon = "☑️" if opt in selected else "⬜"
                row.append(InlineKeyboardButton(icon + " " + opt, callback_data=f"pattoggle_{field}_{pid}_{opt[:12]}"))
                if len(row) == 2:
                    btns.append(row)
                    row = []
            if row: btns.append(row)
            btns.append([InlineKeyboardButton("➕ " + ("إضافة يدوي" if lang=="ar" else "Add manually"), callback_data=f"patadd_{field}_{pid}")])
            btns.append([InlineKeyboardButton("✅ " + ("حفظ" if lang=="ar" else "Save"), callback_data=f"pat_edit_{pid}")])
            btns.append([InlineKeyboardButton(tx("btn_back", lang), callback_data="pat_edit_" + pid)])
            await q.message.edit_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(btns))
            return STATE_PAT_MENU
        else:
            field_names = {
                "name": "الاسم" if lang=="ar" else "Name",
                "age": "العمر" if lang=="ar" else "Age",
                "weight": "الوزن (كغ)" if lang=="ar" else "Weight (kg)",
                "allergy": "الحساسية" if lang=="ar" else "Allergies"
            }
            current_val = str(p.get(field,""))
            await q.message.edit_text(
                "✏️ " + ("القيمة الحالية: " if lang=="ar" else "Current: ") + current_val + "\n" +
                ("أدخل القيمة الجديدة:" if lang=="ar" else "Enter new value:"),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tx("btn_back", lang), callback_data="pat_edit_" + pid)]]))
            return STATE_PAT_NOTE

    if q.data.startswith("pattoggle_"):
        parts = q.data.split("_",4)
        field = parts[1]
        pid = parts[2]
        item = parts[3]
        p = patients.get(pid,{})
        current = p.get(field,"")
        items = [x.strip() for x in current.replace("،",",").split(",") if x.strip()] if current else []
        if item in items:
            items.remove(item)
        else:
            items.append(item)
        p[field] = "، ".join(items)
        save_patients(ctx)
        
        # نعرض الصفحة مرة أخرى حسب اللغة
        if field == "diseases":
            options = ["ضغط","سكري","قلب","كلى","كبد","غدة","ربو","سرطان","روماتيزم","أنيميا","كولسترول","جلطة","قرحة","حساسية"] if lang=="ar" else ["Hypertension","Diabetes","Heart disease","Kidney disease","Liver disease","Thyroid","Asthma","Cancer","Arthritis","Anemia","Cholesterol","Stroke","Ulcer","Allergy"]
        else:
            options = ["ميتفورمين","أملودبين","ليزينوبريل","أتورفاستاتين","أسبرين","ميتوبرولول","ليفوثيروكسين","أوميبرازول","وارفارين","لوساتران","إنسولين","كونكور"] if lang=="ar" else ["Metformin","Amlodipine","Lisinopril","Atorvastatin","Aspirin","Metoprolol","Levothyroxine","Omeprazole","Warfarin","Losartan","Insulin","Bisoprolol"]
        
        selected = items
        lines = ["✏️ " + ("اختر الأمراض:" if field=="diseases" else "اختر الأدوية:"), ""]
        lines.append("✅ " + ("المختار: " if lang=="ar" else "Selected: ") + ("، ".join(selected) if selected else "لا يوجد"))
        btns = []
        row = []
        for opt in options:
            icon = "☑️" if opt in selected else "⬜"
            row.append(InlineKeyboardButton(icon + " " + opt, callback_data=f"pattoggle_{field}_{pid}_{opt[:12]}"))
            if len(row) == 2:
                btns.append(row)
                row = []
        if row: btns.append(row)
        btns.append([InlineKeyboardButton("➕ " + ("إضافة يدوي" if lang=="ar" else "Add manually"), callback_data=f"patadd_{field}_{pid}")])
        btns.append([InlineKeyboardButton("✅ " + ("حفظ" if lang=="ar" else "Save"), callback_data=f"pat_edit_{pid}")])
        btns.append([InlineKeyboardButton(tx("btn_back", lang), callback_data="pat_edit_" + pid)])
        await q.answer("✅ " + ("تم التحديث" if lang=="ar" else "Updated"))
        await q.message.edit_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(btns))
        return STATE_PAT_MENU

    if q.data.startswith("patdel_"):
        # حذف عنصر من قائمة
        parts = q.data.split("_",4)
        field = parts[1]
        pid = parts[2]
        item = parts[3] if len(parts) > 3 else ""
        p = patients.get(pid,{})
        current = p.get(field,"")
        items = [x.strip() for x in current.replace("،",",").split(",") if x.strip()]
        items = [x for x in items if not x.startswith(item)]
        p[field] = "، ".join(items)
        save_patients(ctx)
        await q.answer("✅ " + ("تم الحذف" if lang=="ar" else "Deleted"))
        # نعيد عرض القائمة
        btns = []
        for i in items:
            btns.append([InlineKeyboardButton("🗑️ " + i, callback_data=f"patdel_{field}_{pid}_{i[:15]}")])
        btns.append([InlineKeyboardButton("➕ " + ("إضافة" if lang=="ar" else "Add"), callback_data=f"patadd_{field}_{pid}")])
        btns.append([InlineKeyboardButton(tx("btn_back", lang), callback_data="pat_edit_" + pid)])
        await q.message.edit_text("✅ " + ("تم الحذف\n" if lang=="ar" else "Deleted\n") + "\n".join(["• " + i for i in items]) if items else "📭", reply_markup=InlineKeyboardMarkup(btns))
        return STATE_PAT_MENU

    if q.data.startswith("patadd_"):
        parts = q.data.split("_",3)
        field = parts[1]
        pid = parts[2]
        ctx.user_data["edit_pid"] = pid
        ctx.user_data["edit_field"] = field
        ctx.user_data["edit_append"] = True
        await q.message.edit_text("➕ " + ("أدخل الإضافة:" if lang=="ar" else "Enter to add:"),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tx("btn_back", lang), callback_data=f"patedit_{field}_{pid}")]]))
        return STATE_PAT_NOTE

    if q.data.startswith("pat_del_"):
        pid = q.data.replace("pat_del_", "")
        patients = ctx.user_data.get("patients", {})
        if pid in patients:
            del patients[pid]
            save_patients(ctx)
        await q.message.edit_text("✅ " + ("تم الحذف" if lang=="ar" else "Deleted"), reply_markup=kb_patient_menu(lang))
        return STATE_PAT_MENU
    
    await q.message.edit_text("👤 " + ("ملف المريض" if lang=="ar" else "Patient File"), reply_markup=kb_patient_menu(lang))
    return STATE_PAT_MENU

async def pat_name(u, ctx):
    lang = get_lang(ctx)
    name = u.message.text.strip()
    if not name:
        await u.message.reply_text("❌ " + ("أدخل اسماً صحيحاً" if lang=="ar" else "Enter valid name"))
        return STATE_PAT_NAME
    ctx.user_data["new_patient"] = {"name": name}
    btns = InlineKeyboardMarkup([
        [InlineKeyboardButton("👦 " + ("ذكر" if lang=="ar" else "Male"), callback_data="pat_gender_m"),
         InlineKeyboardButton("👧 " + ("أنثى" if lang=="ar" else "Female"), callback_data="pat_gender_f")]
    ])
    await u.message.reply_text("👤 " + ("الجنس؟" if lang=="ar" else "Gender?"), reply_markup=btns)
    return STATE_PAT_GENDER

async def pat_gender(u, ctx):
    q = u.callback_query; await q.answer()
    lang = get_lang(ctx)
    ctx.user_data["new_patient"]["gender"] = "ذكر" if q.data == "pat_gender_m" else "أنثى"
    await q.message.edit_text("📅 " + ("كم عمره؟" if lang=="ar" else "Age?"))
    return STATE_PAT_AGE

async def pat_age(u, ctx):
    lang = get_lang(ctx)
    try:
        age = int(u.message.text.strip())
    except:
        await u.message.reply_text("❌ " + ("أدخل رقماً" if lang=="ar" else "Enter number"))
        return STATE_PAT_AGE
    ctx.user_data["new_patient"]["age"] = age
    await u.message.reply_text("⚖️ " + ("الوزن بالكيلو؟" if lang=="ar" else "Weight in kg?"))
    return STATE_PAT_WEIGHT

async def pat_weight(u, ctx):
    lang = get_lang(ctx)
    try:
        w = float(u.message.text.strip())
    except:
        await u.message.reply_text("❌ " + ("أدخل رقماً" if lang=="ar" else "Enter number"))
        return STATE_PAT_WEIGHT
    ctx.user_data["new_patient"]["weight"] = w
    ctx.user_data["new_patient"]["diseases_list"] = []
    await show_disease_btns(u.message, ctx, lang)
    return STATE_PAT_DISEASE

def get_disease_kb(selected, lang):
    diseases = [
        ("سكري","🩺","Diabetes"), ("ضغط","💉","BP"), ("قلب","❤️","Heart"),
        ("كلى","🫘","Kidney"), ("ربو","🫁","Asthma"), ("غدة","🦋","Thyroid"),
        ("كبد","🟡","Liver"), ("سمنة","⚖️","Obesity"),
    ]
    btns = []
    row = []
    for ar, icon, en in diseases:
        name = ar if lang=="ar" else en
        tick = "✅ " if ar in selected else ""
        row.append(InlineKeyboardButton(tick + icon + name, callback_data="pat_dis_" + ar))
        if len(row) == 2:
            btns.append(row)
            row = []
    if row: btns.append(row)
    btns.append([InlineKeyboardButton("✅ " + ("انتهيت" if lang=="ar" else "Done"), callback_data="pat_dis_done")])
    return InlineKeyboardMarkup(btns)

async def show_disease_btns(msg, ctx, lang):
    selected = ctx.user_data["new_patient"].get("diseases_list", [])
    title = "🏥 اختر الأمراض المزمنة (يمكن تعدد الاختيار):" if lang=="ar" else "🏥 Select chronic diseases (multiple):"
    await msg.reply_text(title, reply_markup=get_disease_kb(selected, lang))

async def pat_disease(u, ctx):
    q = u.callback_query; await q.answer()
    lang = get_lang(ctx)
    data = q.data.replace("pat_dis_", "")
    
    if data == "done":
        diseases = ctx.user_data["new_patient"].get("diseases_list", [])
        ctx.user_data["new_patient"]["diseases"] = "، ".join(diseases) if diseases else ""
        ctx.user_data["new_patient"]["meds_list"] = []
        await show_meds_btns(q.message, ctx, lang, edit=True)
        return STATE_PAT_MEDS
    
    selected = ctx.user_data["new_patient"].setdefault("diseases_list", [])
    if data in selected:
        selected.remove(data)
    else:
        selected.append(data)
    await q.message.edit_reply_markup(reply_markup=get_disease_kb(selected, lang))
    return STATE_PAT_DISEASE

def get_meds_kb(selected, lang):
    meds = [
        ("ميتفورمين","💊","Metformin"), ("أملودبين","💊","Amlodipine"),
        ("أتورفاستاتين","💊","Atorvastatin"), ("ليزينوبريل","💊","Lisinopril"),
        ("أسبرين","💊","Aspirin"), ("ميتوبرولول","💊","Metoprolol"),
        ("أوميبرازول","💊","Omeprazole"), ("ليفوثيروكسين","💊","Levothyroxine"),
    ]
    btns = []
    row = []
    for ar, icon, en in meds:
        name = ar if lang=="ar" else en
        tick = "✅ " if ar in selected else ""
        row.append(InlineKeyboardButton(tick + name, callback_data="pat_med_" + ar))
        if len(row) == 2:
            btns.append(row)
            row = []
    if row: btns.append(row)
    btns.append([InlineKeyboardButton("➕ " + ("أضف دواء آخر" if lang=="ar" else "Add other"), callback_data="pat_med_other")])
    btns.append([InlineKeyboardButton("✅ " + ("انتهيت" if lang=="ar" else "Done"), callback_data="pat_med_done")])
    return InlineKeyboardMarkup(btns)

async def show_meds_btns(msg, ctx, lang, edit=False):
    selected = ctx.user_data["new_patient"].get("meds_list", [])
    title = "💊 اختر الأدوية الثابتة:" if lang=="ar" else "💊 Select regular medications:"
    if edit:
        await msg.edit_text(title, reply_markup=get_meds_kb(selected, lang))
    else:
        await msg.reply_text(title, reply_markup=get_meds_kb(selected, lang))

async def pat_meds(u, ctx):
    lang = get_lang(ctx)
    # إذا كان نص (دواء مخصص)
    if u.message:
        med = u.message.text.strip()
        if med and med.lower() not in ["لا","no","none","-"]:
            ctx.user_data["new_patient"].setdefault("meds_list", []).append(med)
        await show_meds_btns(u.message, ctx, lang)
        return STATE_PAT_MEDS
    return STATE_PAT_MEDS

async def pat_meds_cb(u, ctx):
    q = u.callback_query; await q.answer()
    lang = get_lang(ctx)
    data = q.data.replace("pat_med_", "")

    if data == "done":
        meds = ctx.user_data["new_patient"].get("meds_list", [])
        ctx.user_data["new_patient"]["meds"] = "، ".join(meds) if meds else ""
        await q.message.edit_text("⚠️ " + ("حساسية من أدوية؟ (اكتب اسمها أو لا):" if lang=="ar" else "Drug allergies? (type name or none):"))
        return STATE_PAT_ALLERGY

    if data == "other":
        await q.message.edit_text("💊 " + ("اكتب اسم الدواء:" if lang=="ar" else "Type medication name:"))
        return STATE_PAT_MEDS

    selected = ctx.user_data["new_patient"].setdefault("meds_list", [])
    if data in selected:
        selected.remove(data)
    else:
        selected.append(data)
    await q.message.edit_reply_markup(reply_markup=get_meds_kb(selected, lang))
    return STATE_PAT_MEDS

async def pat_allergy(u, ctx):
    lang = get_lang(ctx)
    text = u.message.text.strip()
    
    # إذا كنا في وضع تسجيل القراءات
    log_type = ctx.user_data.get("log_type","")
    if log_type == "reading":
        pid = ctx.user_data.get("log_pid","")
        load_patients(ctx)
        patients = ctx.user_data.get("patients",{})
        p = patients.get(pid,{})
        if p:
            from datetime import datetime
            date = datetime.now().strftime("%Y-%m-%d %H:%M")
            readings = p.setdefault("readings",[])
            txt_lower = text.lower().strip()
            
            # نحدد النوع والقيمة
            if txt_lower.startswith("صيام") or txt_lower.startswith("fasting"):
                val = txt_lower.replace("صيام","").replace("fasting","").strip()
                readings.append({"date":date,"sugar":float(val),"stype":"fasting","stype_ar":"صيام"})
                msg = "✅ سكر صيام: " + val + " mg/dL"
            elif txt_lower.startswith("بعد_اكل") or txt_lower.startswith("postmeal"):
                val = txt_lower.replace("بعد_اكل","").replace("postmeal","").strip()
                readings.append({"date":date,"sugar":float(val),"stype":"postmeal","stype_ar":"بعد الأكل"})
                msg = "✅ سكر بعد الأكل: " + val + " mg/dL"
            elif txt_lower.startswith("hba1c"):
                val = txt_lower.replace("hba1c","").strip()
                readings.append({"date":date,"sugar":float(val),"stype":"hba1c","stype_ar":"تراكمي HbA1c","unit":"%"})
                msg = "✅ HbA1c: " + val + "%"
            elif txt_lower.startswith("ضغط") or txt_lower.startswith("bp"):
                val = txt_lower.replace("ضغط","").replace("bp","").strip()
                parts = val.split("/")
                readings.append({"date":date,"bp":val,"sys":int(parts[0]),"dia":int(parts[1])})
                msg = "✅ ضغط: " + val
            else:
                try:
                    val = float(txt_lower)
                    readings.append({"date":date,"sugar":val,"stype":"random","stype_ar":"عشوائي"})
                    msg = "✅ قراءة عشوائية: " + str(val) + " mg/dL"
                except:
                    await u.message.reply_text("❌ صيغة خاطئة — جرّب: صيام 95")
                    return STATE_PAT_ALLERGY
            
            save_patients(ctx)
            ctx.user_data.pop("log_type","")
            await u.message.reply_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📊 " + ("عرض السجل" if lang=="ar" else "View Log"), callback_data="pat_log_" + pid)]]))
            return STATE_PAT_MENU
    
    if log_type in ["sugar","bp"]:
        pid = ctx.user_data.get("log_pid","")
        load_patients(ctx)
        patients = ctx.user_data.get("patients",{})
        p = patients.get(pid,{})
        if p:
            from datetime import datetime
            date = datetime.now().strftime("%Y-%m-%d %H:%M")
            readings = p.setdefault("readings",[])
            if log_type == "sugar":
                try:
                    val = float(text)
                    stype = ctx.user_data.pop("sugar_type","random")
                    type_names = {"fasting":"صيام","postmeal":"بعد الأكل","random":"عشوائي","hba1c":"تراكمي HbA1c"}
                    readings.append({"date":date,"sugar":val,"stype":stype,"stype_ar":type_names.get(stype,stype)})
                    if stype_clean == "hba1c":
                        if val < 5.7: status = "✅ طبيعي"
                        elif val <= 6.4: status = "🟡 ما قبل السكري"
                        elif val <= 7.0: status = "🟠 مضبوط"
                        else: status = "🔴 مرتفع"
                    else:
                        if val < 70: status = "⚠️ منخفض"
                        elif val <= 100: status = "✅ طبيعي"
                        elif val <= 125: status = "🟡 ما قبل السكري"
                        else: status = "🔴 مرتفع"
                    msg = "✅ تم الحفظ\n🩸 " + str(val) + " mg/dL " + status
                except:
                    await u.message.reply_text("❌ أدخل رقماً")
                    return STATE_PAT_ALLERGY
            else:
                try:
                    parts = text.replace(" ","").split("/")
                    readings.append({"date":date,"bp":text,"sys":int(parts[0]),"dia":int(parts[1])})
                    msg = "✅ تم الحفظ\n💉 " + text
                except:
                    await u.message.reply_text("❌ صيغة خاطئة مثال: 120/80")
                    return STATE_PAT_ALLERGY
            save_patients(ctx)
            ctx.user_data.pop("log_type","")
            await u.message.reply_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📊 " + ("عرض السجل" if lang=="ar" else "View Log"), callback_data="pat_log_" + pid)]]))
            return STATE_PAT_MENU
    
    allergy = text
    ctx.user_data["new_patient"]["allergy"] = "" if allergy.lower() in ["لا","no","none","-"] else allergy
    # نحفظ المريض
    import time
    pid = str(int(time.time()))
    patients = ctx.user_data.setdefault("patients", {})
    patients[pid] = ctx.user_data["new_patient"]
    save_patients(ctx)
    name = ctx.user_data["new_patient"]["name"]
    await u.message.reply_text("✅ " + ("تم حفظ ملف " + name if lang=="ar" else "Patient " + name + " saved!"), reply_markup=kb_patient_menu(lang))
    return STATE_PAT_MENU


# ═══════════════ التفاعلات الدوائية ═══════════════
DRUG_INTERACTIONS = {
    # مضادات التخثر
    ("warfarin","aspirin"): ("🔴 خطير", "زيادة خطر النزيف الشديد", "تجنب الجمع — استشر الطبيب فوراً"),
    ("warfarin","ibuprofen"): ("🔴 خطير", "زيادة خطر النزيف", "تجنب — استخدم باراسيتامول بديلاً"),
    ("warfarin","metronidazole"): ("🔴 خطير", "يرفع مستوى الوارفارين بشكل كبير", "راقب INR بشكل مكثف"),
    ("warfarin","clarithromycin"): ("🔴 خطير", "يزيد تأثير الوارفارين", "راقب INR"),
    ("warfarin","fluconazole"): ("🔴 خطير", "يرفع مستوى الوارفارين", "قلل الجرعة وراقب INR"),
    # القلب
    ("digoxin","amiodarone"): ("🔴 خطير", "يرفع مستوى الديجوكسين للضعف", "قلل جرعة الديجوكسين 50%"),
    ("digoxin","clarithromycin"): ("🔴 خطير", "يرفع مستوى الديجوكسين", "راقب مستوى الديجوكسين"),
    ("metoprolol","verapamil"): ("🔴 خطير", "خطر بطء القلب الشديد والانهيار", "تجنب الجمع"),
    ("amiodarone","simvastatin"): ("🔴 خطير", "خطر تلف العضلات الشديد", "لا تتجاوز 20mg سيمفاستاتين"),
    # الصرف
    ("carbamazepine","warfarin"): ("🔴 خطير", "يقلل تأثير الوارفارين", "راقب INR وعدّل الجرعة"),
    ("valproate","aspirin"): ("🟠 متوسط", "يرفع مستوى الفالبروات", "راقب الأعراض"),
    ("phenytoin","fluconazole"): ("🔴 خطير", "يرفع مستوى الفينيتوين لمستويات سامة", "راقب مستوى الدم"),
    # المضادات الحيوية
    ("metronidazole","alcohol"): ("🔴 خطير", "تفاعل ديسولفيرام — غثيان وقيء شديد", "تجنب الكحول تماماً أثناء العلاج وبعده بيومين"),
    ("ciprofloxacin","antacids"): ("🟠 متوسط", "يقلل امتصاص السيبروفلوكساسين", "خذ السيبرو قبل المضاد بساعتين"),
    ("azithromycin","amiodarone"): ("🔴 خطير", "إطالة فترة QT وخطر اضطراب النظم", "تجنب الجمع"),
    ("clarithromycin","simvastatin"): ("🔴 خطير", "خطر تلف العضلات الشديد", "أوقف السيمفاستاتين أثناء العلاج"),
    ("rifampicin","warfarin"): ("🔴 خطير", "يقلل تأثير الوارفارين بشكل كبير", "رفع جرعة الوارفارين ومراقبة INR"),
    ("rifampicin","oral_contraceptives"): ("🔴 خطير", "يقلل فاعلية حبوب منع الحمل", "استخدم وسيلة منع حمل إضافية"),
    # مسكنات الألم
    ("ibuprofen","aspirin"): ("🟠 متوسط", "يقلل تأثير الأسبرين الوقائي للقلب", "خذ الأسبرين قبل الإيبوبروفين بساعتين"),
    ("ibuprofen","lisinopril"): ("🟠 متوسط", "يقلل فاعلية خافضات الضغط", "راقب ضغط الدم"),
    ("ibuprofen","methotrexate"): ("🔴 خطير", "يرفع سمية الميثوتريكسات", "تجنب الجمع"),
    ("tramadol","ssri"): ("🔴 خطير", "خطر متلازمة السيروتونين", "تجنب الجمع"),
    ("tramadol","mao_inhibitors"): ("🔴 خطير", "تفاعل خطير جداً", "تجنب تماماً"),
    # أدوية السكري
    ("metformin","alcohol"): ("🟠 متوسط", "خطر حماض اللاكتات", "تجنب الكحول الزائد"),
    ("glibenclamide","fluconazole"): ("🔴 خطير", "هبوط سكر حاد", "راقب السكر بشكل مكثف"),
    ("insulin","alcohol"): ("🟠 متوسط", "يزيد خطر هبوط السكر", "راقب مستوى السكر"),
    # ضغط الدم
    ("lisinopril","potassium"): ("🟠 متوسط", "ارتفاع البوتاسيوم في الدم", "راقب مستوى البوتاسيوم"),
    ("amlodipine","simvastatin"): ("🟠 متوسط", "يرفع مستوى السيمفاستاتين", "لا تتجاوز 20mg سيمفاستاتين"),
    ("verapamil","simvastatin"): ("🔴 خطير", "خطر تلف العضلات", "تجنب أو قلل جرعة السيمفاستاتين"),
    # مضادات الاكتئاب
    ("fluoxetine","tramadol"): ("🔴 خطير", "متلازمة السيروتونين", "تجنب الجمع"),
    ("sertraline","warfarin"): ("🟠 متوسط", "يزيد خطر النزيف", "راقب INR"),
    ("mao_inhibitors","tyramine"): ("🔴 خطير", "أزمة ارتفاع ضغط", "تجنب الأطعمة الغنية بالتيرامين"),
    # أدوية أخرى
    ("sildenafil","nitrates"): ("🔴 خطير جداً", "انهيار ضغط الدم الحاد", "ممنوع منعاً باتاً"),
    ("simvastatin","grapefruit"): ("🟠 متوسط", "يرفع مستوى السيمفاستاتين", "تجنب عصير الجريب فروت"),
    ("levothyroxine","calcium"): ("🟠 متوسط", "يقلل امتصاص الليفوثيروكسين", "خذ الليفوثيروكسين قبل الكالسيوم بأربع ساعات"),
    ("methotrexate","folic_acid"): ("🟢 مفيد", "يقلل آثار الميثوتريكسات الجانبية", "خذ حمض الفوليك في أيام مختلفة"),
    ("omeprazole","clopidogrel"): ("🟠 متوسط", "يقلل فاعلية الكلوبيدوجريل", "استخدم بانتوبرازول بديلاً"),
    ("ssri","nsaids"): ("🟠 متوسط", "يزيد خطر النزيف الهضمي", "استخدم واقي المعدة"),
    ("lithium","ibuprofen"): ("🔴 خطير", "يرفع مستوى الليثيوم لمستويات سامة", "استخدم باراسيتامول بديلاً"),
    ("theophylline","ciprofloxacin"): ("🔴 خطير", "يرفع مستوى الثيوفيلين", "قلل جرعة الثيوفيلين وراقبه"),
    ("tacrolimus","clarithromycin"): ("🔴 خطير", "يرفع مستوى التاكروليموس", "راقب المستوى وعدّل الجرعة"),
}

def normalize_drug_name(name):
    name = name.strip().lower()
    aliases = {
        "وارفارين":"warfarin","warfarin":"warfarin",
        "أسبرين":"aspirin","aspirin":"aspirin","asprin":"aspirin",
        "إيبوبروفين":"ibuprofen","ibuprofen":"ibuprofen","بروفين":"ibuprofen","نيوروفين":"ibuprofen",
        "باراسيتامول":"paracetamol","paracetamol":"paracetamol","بنادول":"paracetamol",
        "ميترونيدازول":"metronidazole","metronidazole":"metronidazole","فلاجيل":"metronidazole",
        "أموكسيسيلين":"amoxicillin","amoxicillin":"amoxicillin",
        "أزيثروميسين":"azithromycin","azithromycin":"azithromycin","زيثروماكس":"azithromycin",
        "كلاريثروميسين":"clarithromycin","clarithromycin":"clarithromycin","كلاسيد":"clarithromycin",
        "سيبروفلوكساسين":"ciprofloxacin","ciprofloxacin":"ciprofloxacin","سيبرو":"ciprofloxacin",
        "ميتفورمين":"metformin","metformin":"metformin","جلوكوفاج":"metformin",
        "أملودبين":"amlodipine","amlodipine":"amlodipine","نورفاسك":"amlodipine",
        "ليزينوبريل":"lisinopril","lisinopril":"lisinopril",
        "سيمفاستاتين":"simvastatin","simvastatin":"simvastatin","زوكور":"simvastatin",
        "أتورفاستاتين":"atorvastatin","atorvastatin":"atorvastatin","ليبيتور":"atorvastatin",
        "ديجوكسين":"digoxin","digoxin":"digoxin",
        "أميودارون":"amiodarone","amiodarone":"amiodarone",
        "فلوكونازول":"fluconazole","fluconazole":"fluconazole","ديفلوكان":"fluconazole",
        "فينيتوين":"phenytoin","phenytoin":"phenytoin",
        "كاربامازيبين":"carbamazepine","carbamazepine":"carbamazepine","تيجريتول":"carbamazepine",
        "فالبروات":"valproate","valproate":"valproate","ديباكين":"valproate",
        "ترامادول":"tramadol","tramadol":"tramadol","ترامال":"tramadol",
        "فلوكستين":"fluoxetine","fluoxetine":"fluoxetine","بروزاك":"fluoxetine",
        "سيرترالين":"sertraline","sertraline":"sertraline","زولوفت":"sertraline",
        "سيلدينافيل":"sildenafil","sildenafil":"sildenafil","فياغرا":"sildenafil",
        "نيترات":"nitrates","nitrates":"nitrates","نيتروجلسرين":"nitrates",
        "كلوبيدوجريل":"clopidogrel","clopidogrel":"clopidogrel","بلافيكس":"clopidogrel",
        "أوميبرازول":"omeprazole","omeprazole":"omeprazole","لوسك":"omeprazole",
        "ليفوثيروكسين":"levothyroxine","levothyroxine":"levothyroxine","إلتروكسين":"levothyroxine",
        "ميثوتريكسات":"methotrexate","methotrexate":"methotrexate",
        "ريفامبيسين":"rifampicin","rifampicin":"rifampicin",
        "ليثيوم":"lithium","lithium":"lithium",
        "ثيوفيلين":"theophylline","theophylline":"theophylline",
        "إنسولين":"insulin","insulin":"insulin",
        "فيراباميل":"verapamil","verapamil":"verapamil",
        "ميتوبرولول":"metoprolol","metoprolol":"metoprolol",
        "ريفامبسين":"rifampicin",
        "بوتاسيوم":"potassium","potassium":"potassium",
        "كالسيوم":"calcium","calcium":"calcium",
        "كحول":"alcohol","alcohol":"alcohol",
        "جريب فروت":"grapefruit","grapefruit":"grapefruit",
    }
    return aliases.get(name, name)

def check_interaction(drug1, drug2):
    d1 = normalize_drug_name(drug1)
    d2 = normalize_drug_name(drug2)
    result = DRUG_INTERACTIONS.get((d1, d2)) or DRUG_INTERACTIONS.get((d2, d1))
    return result

async def interaction_start(u, ctx):
    q = u.callback_query; await q.answer()
    lang = get_lang(ctx)
    msg = "⚠️ *التفاعلات الدوائية*\n\nاكتب اسم الدواء الأول:" if lang=="ar" else "⚠️ *Drug Interactions*\n\nEnter first drug name:"
    await q.message.edit_text(msg, parse_mode=ParseMode.MARKDOWN)
    ctx.user_data["interaction_step"] = 1
    return STATE_INTERACTION

async def interaction_input(u, ctx):
    lang = get_lang(ctx)
    step = ctx.user_data.get("interaction_step", 1)
    text = u.message.text.strip()

    if step == 1:
        ctx.user_data["drug1"] = text
        ctx.user_data["interaction_step"] = 2
        await u.message.reply_text("💊 " + ("الآن اكتب اسم الدواء الثاني:" if lang=="ar" else "Now enter second drug name:"))
        return STATE_INTERACTION

    elif step == 2:
        drug1 = ctx.user_data.get("drug1", "")
        drug2 = text

        # نتحقق أولاً من القاعدة المحلية
        result = check_interaction(drug1, drug2)

        if result:
            severity, effect, advice = result
            msg = severity + " تفاعل دوائي\n\n💊 " + drug1 + " + " + drug2 + "\n\n⚡ التأثير: " + effect + "\n\n💡 النصيحة: " + advice if lang=="ar" else severity + " Drug Interaction\n\n💊 " + drug1 + " + " + drug2 + "\n\n⚡ Effect: " + effect + "\n\n💡 Advice: " + advice

        else:
            # نستخدم Claude API للبحث
            thinking_msg = await u.message.reply_text("🔍 " + ("جارٍ البحث عن التفاعلات..." if lang=="ar" else "Searching for interactions..."))
            try:
                prompt = f"""أنت صيدلاني خبير. اكتشف التفاعل الدوائي بين: {drug1} و {drug2}

أجب بالتنسيق التالي فقط:
درجة الخطورة: [🔴 خطير / 🟠 متوسط / 🟡 خفيف / ✅ آمن]
التأثير: [وصف مختصر]
النصيحة: [نصيحة عملية]

إذا لم يوجد تفاعل معروف اكتب: ✅ لا يوجد تفاعل دوائي معروف بين هذين الدوائين

أجب {"بالعربية" if lang=="ar" else "in English"} فقط."""

                async with httpx.AsyncClient(timeout=30) as c:
                    r = await c.post("https://api.anthropic.com/v1/messages",
                        headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                        json={"model": "claude-haiku-4-5-20251001", "max_tokens": 300,
                            "messages": [{"role": "user", "content": prompt}]})
                    ai_result = r.json().get("content", [{}])[0].get("text", "").strip()
                    msg = "⚠️ التفاعل الدوائي\n\n💊 " + drug1 + " + " + drug2 + "\n\n" + ai_result if lang=="ar" else "⚠️ Drug Interaction\n\n💊 " + drug1 + " + " + drug2 + "\n\n" + ai_result
            except Exception as e:
                msg = "✅ لا يوجد تفاعل معروف\n\n💊 " + drug1 + " + " + drug2 if lang=="ar" else "✅ No known interaction\n\n💊 " + drug1 + " + " + drug2
            await thinking_msg.delete()

        btns = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 " + ("بحث جديد" if lang=="ar" else "New Search"), callback_data="m_interaction")],
            [InlineKeyboardButton(tx("btn_back", lang), callback_data="back")]
        ])
        await u.message.reply_text(msg, reply_markup=btns, parse_mode=ParseMode.MARKDOWN)
        ctx.user_data["interaction_step"] = 1
        return STATE_MAIN_MENU


async def ask_drug_form(u, ctx):
    lang = get_lang(ctx)
    if hasattr(u, "callback_query") and u.callback_query:
        q = u.callback_query; await q.answer()
        edit = q.message.edit_text
    else:
        edit = u.message.reply_text
    
    btns = InlineKeyboardMarkup([
        [InlineKeyboardButton("🥄 " + ("شراب" if lang=="ar" else "Syrup"), callback_data="form_syrup"),
         InlineKeyboardButton("💉 " + ("حقنة" if lang=="ar" else "Injection"), callback_data="form_injection")],
        [InlineKeyboardButton("🧴 " + ("كريم/مرهم" if lang=="ar" else "Cream/Ointment"), callback_data="form_cream"),
         InlineKeyboardButton("💧 " + ("قطرة" if lang=="ar" else "Drops"), callback_data="form_drops")],
        [InlineKeyboardButton("🕯️ " + ("تحميلة" if lang=="ar" else "Suppository"), callback_data="form_suppository"),
         InlineKeyboardButton("💊 " + ("أخرى" if lang=="ar" else "Other"), callback_data="form_other")],
        [InlineKeyboardButton(tx("btn_back", lang), callback_data="back")]
    ])
    msg = "💊 اختر نوع الدواء:" if lang=="ar" else "💊 Select drug form:"
    await edit(msg, reply_markup=btns)
    return STATE_DRUG_FORM

async def drug_form_selected(u, ctx):
    q = u.callback_query; await q.answer()
    lang = get_lang(ctx)
    form = q.data.replace("form_", "")
    ctx.user_data["drug_form"] = form
    
    form_names = {
        "syrup": "شراب" if lang=="ar" else "Syrup",
        "injection": "حقنة" if lang=="ar" else "Injection",
        "cream": "كريم/مرهم" if lang=="ar" else "Cream/Ointment",
        "drops": "قطرة" if lang=="ar" else "Drops",
        "suppository": "تحميلة" if lang=="ar" else "Suppository",
        "other": "أخرى" if lang=="ar" else "Other",
    }
    
    if form == "injection":
        msg = "💉 " + ("الحقن تستلزم وصفة طبية ومتابعة طبيب متخصص.\n\nلا يمكن إعطاء جرعات الحقن عبر البوت لأسباب سلامة المريض.\n\n🏥 يرجى مراجعة الطبيب أو الصيدلاني." if lang=="ar" else "Injections require a prescription and medical supervision.\n\nFor patient safety, injection doses cannot be provided via the bot.\n\n🏥 Please consult your doctor or pharmacist.")
        await q.message.edit_text(msg, reply_markup=kb_back(lang))
        return STATE_MAIN_MENU
    elif form == "cream":
        msg = "🧴 " + ("اكتب اسم الكريم أو أرسل صورة العبوة:" if lang=="ar" else "Enter cream name or send photo:")
    elif form == "drops":
        msg = "💧 " + ("اكتب اسم القطرة أو أرسل صورة العبوة:" if lang=="ar" else "Enter drops name or send photo:")
    elif form == "suppository":
        msg = "🕯️ " + ("اكتب اسم التحميلة أو أرسل صورة العبوة:" if lang=="ar" else "Enter suppository name or send photo:")
    else:
        msg = "💊 " + ("اكتب اسم الدواء أو أرسل صورة العبوة 📸" if lang=="ar" else "Enter drug name or send photo 📸")
    
    await q.message.edit_text(msg)
    return STATE_CHILD_DRUG


async def calc_special_form(drug_name, weight, drug_form, lang):
    """يستخدم Claude API لحساب جرعة الحقن والكريم والقطرات والتحاميل"""
    form_names = {
        "injection": "حقنة IV/IM" if lang=="ar" else "IV/IM Injection",
        "cream": "كريم/مرهم موضعي" if lang=="ar" else "Topical Cream/Ointment",
        "drops": "قطرة عين/أنف/أذن" if lang=="ar" else "Eye/Nose/Ear Drops",
        "suppository": "تحميلة شرجية" if lang=="ar" else "Rectal Suppository",
    }
    form_name = form_names.get(drug_form, drug_form)
    
    if lang == "ar":
        prompt = f"""أنت صيدلاني خبير. احسب جرعة {form_name} لـ {drug_name} لطفل وزنه {weight} كغ.
الجرعات المرجعية الصحيحة:
- باراسيتامول: 15 مغ/كغ (تحميلة أو شراب)
- إيبوبروفين: 10 مغ/كغ
- ديكلوفيناك: 1 مغ/كغ
- ديازيبام: 0.5 مغ/كغ
لأي دواء آخر استخدم المرجع الطبي الصحيح.

أجب بهذا التنسيق فقط:
💊 الدواء: {drug_name}
📋 النوع: {form_name}
👶 العمر: {int(weight)} سنوات
💉 الجرعة: [احسب بدقة حسب الوزن]
🔁 التكرار: 
⏱️ مدة العلاج: 
⚠️ تحذير مهم: 

مهم: احسب الجرعة حسب وزن {weight} كغ فقط. لا تذكر جرعة الشراب."""
    else:
        prompt = f"""You are an expert pharmacist. Calculate {form_name} dose for {drug_name} for a child weighing {weight} kg.
Calculate accurately based on standard medical references (BNF, Pediatric Dosing). Use the standard therapeutic dose.

Reply in this format only:
💊 Drug: {drug_name}
📋 Form: {form_name}
⚖️ Weight: {weight} kg
💉 Calculated dose: [calculate accurately based on weight]
🔁 Frequency: 
⏱️ Duration: 
⚠️ Important warning: 

Important: Calculate dose for {weight} kg only. Do not mention syrup dose."""

    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post("https://api.anthropic.com/v1/messages",
                headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": "claude-haiku-4-5-20251001", "max_tokens": 400,
                    "messages": [{"role": "user", "content": prompt}]})
            result = r.json().get("content", [{}])[0].get("text", "").strip()
            if "غير معروف" in result or "unknown" in result.lower():
                return None
            return result
    except Exception as e:
        logger.error(f"Special form API error: {e}")
        return None


async def check_registration(u, ctx):
    """يتحقق إذا المستخدم مسجل"""
    uid = str(u.effective_user.id)
    stats = load_stats()
    users = stats.get("users", {})
    return uid in users and users[uid].get("registered", False)

async def show_registration(u, ctx, lang):
    """يعرض شاشة التسجيل السريع"""
    btns = InlineKeyboardMarkup([
        [InlineKeyboardButton("👨‍⚕️ " + ("طبيب" if lang=="ar" else "Doctor"), callback_data="reg_doctor"),
         InlineKeyboardButton("💊 " + ("صيدلاني" if lang=="ar" else "Pharmacist"), callback_data="reg_pharmacist")],
        [InlineKeyboardButton("👩 " + ("أم/أب" if lang=="ar" else "Parent"), callback_data="reg_parent"),
         InlineKeyboardButton("🎓 " + ("طالب طب" if lang=="ar" else "Med Student"), callback_data="reg_student")],
        [InlineKeyboardButton("👤 " + ("مستخدم عام" if lang=="ar" else "General User"), callback_data="reg_general")],
    ])
    msg = "👋 " + ("مرحباً! اختر نوع مستخدمك للبدء:" if lang=="ar" else "Welcome! Select your user type to start:")
    if hasattr(u, "message") and u.message:
        await u.message.reply_text(msg, reply_markup=btns)
    else:
        await u.callback_query.message.edit_text(msg, reply_markup=btns)

async def reg_handler(u, ctx):
    """يحفظ التسجيل ويكمل للقائمة الرئيسية"""
    q = u.callback_query; await q.answer()
    lang = get_lang(ctx)
    user = u.effective_user
    uid = str(user.id)
    
    role_map = {
        "reg_doctor": "طبيب" if lang=="ar" else "Doctor",
        "reg_pharmacist": "صيدلاني" if lang=="ar" else "Pharmacist", 
        "reg_parent": "أم/أب" if lang=="ar" else "Parent",
        "reg_student": "طالب طب" if lang=="ar" else "Med Student",
        "reg_general": "مستخدم عام" if lang=="ar" else "General User",
    }
    role = role_map.get(q.data, "عام")
    
    # نحفظ في الإحصائيات
    stats = load_stats()
    if "users" not in stats:
        stats["users"] = {}
    if uid not in stats["users"]:
        stats["users"][uid] = 0
    if isinstance(stats["users"][uid], int):
        stats["users"][uid] = {"count": stats["users"][uid], "registered": True, "role": role, "name": user.first_name or ""}
    else:
        stats["users"][uid]["registered"] = True
        stats["users"][uid]["role"] = role
    save_stats(stats)
    
    ctx.user_data["reg_role"] = role
    ctx.user_data["lang"] = "ar"
    await q.message.edit_text("✅ ممتاز!\n\n📝 اكتب اسمك ودولتك في رسالة واحدة\nمثال: أحمد — السعودية")
    return STATE_LANGUAGE


async def pat_note_start(u, ctx):
    q = u.callback_query; await q.answer()
    lang = get_lang(ctx)
    pid = q.data.replace("pat_note_", "")
    ctx.user_data["note_pid"] = pid
    await q.message.edit_text(
        "📝 " + ("اكتب ملاحظتك أو أرسل صورة/ملف:" if lang=="ar" else "Write your note or send a photo/file:"),
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tx("btn_back", lang), callback_data="back")]]))
    return STATE_PAT_NOTE

async def pat_note_save(u, ctx):
    lang = get_lang(ctx)
    
    # تعديل بيانات المريض
    edit_pid = ctx.user_data.get("edit_pid","")
    edit_field = ctx.user_data.get("edit_field","")
    if edit_pid and edit_field:
        load_patients(ctx)
        patients = ctx.user_data.get("patients",{})
        p = patients.get(edit_pid,{})
        if p:
            val = u.message.text.strip()
            if edit_field == "weight":
                try: p["weight"] = float(val)
                except: pass
            elif edit_field == "age":
                try: p["age"] = int(val)
                except: p["age"] = val
            elif ctx.user_data.get("edit_append") and edit_field in ["meds","diseases"]:
                current = p.get(edit_field,"")
                p[edit_field] = current + "، " + val if current else val
                ctx.user_data.pop("edit_append","")
            else:
                p[edit_field] = val
            save_patients(ctx)
            ctx.user_data.pop("edit_pid","")
            ctx.user_data.pop("edit_field","")
            await u.message.reply_text("✅ " + ("تم التعديل!" if lang=="ar" else "Updated!"),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👤 " + ("عرض الملف" if lang=="ar" else "View File"), callback_data="pat_view_" + edit_pid)]]))
            return STATE_PAT_MENU
    
    pid = ctx.user_data.get("note_pid", "")
    if not pid:
        return STATE_PAT_MENU
    
    load_patients(ctx)
    patients = ctx.user_data.get("patients", {})
    p = patients.get(pid, {})
    if not p:
        return STATE_PAT_MENU
    
    notes = p.setdefault("notes", [])
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    if u.message.photo:
        # حفظ صورة
        photo = u.message.photo[-1]
        file_id = photo.file_id
        caption = u.message.caption or ""
        notes.append({"type": "photo", "file_id": file_id, "caption": caption, "date": timestamp})
        msg = "✅ " + ("تم حفظ الصورة" if lang=="ar" else "Photo saved")
    elif u.message.document:
        # حفظ ملف
        doc = u.message.document
        file_id = doc.file_id
        file_name = doc.file_name or "ملف"
        notes.append({"type": "file", "file_id": file_id, "name": file_name, "date": timestamp})
        msg = "✅ " + ("تم حفظ الملف: " + file_name if lang=="ar" else "File saved: " + file_name)
    elif u.message.text:
        # حفظ نص
        notes.append({"type": "text", "content": u.message.text, "date": timestamp})
        msg = "✅ " + ("تم حفظ الملاحظة" if lang=="ar" else "Note saved")
    else:
        msg = "❌ " + ("نوع غير مدعوم" if lang=="ar" else "Unsupported type")
    
    save_patients(ctx)
    
    # نعرض ملف المريض
    lines = ["👤 *" + p.get("name","") + "*", ""]
    if p.get("notes"):
        lines.append("📝 " + ("الملاحظات:" if lang=="ar" else "Notes:"))
        for n in p["notes"][-3:]:
            if n["type"] == "text":
                lines.append("  • " + n["date"] + ": " + n["content"][:50])
            elif n["type"] == "photo":
                lines.append("  • " + n["date"] + ": 📸 " + ("صورة" if lang=="ar" else "Photo"))
            elif n["type"] == "file":
                lines.append("  • " + n["date"] + ": 📄 " + n.get("name",""))
    
    btns = InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 " + ("إضافة ملاحظة أخرى" if lang=="ar" else "Add Another"), callback_data="pat_note_" + pid)],
        [InlineKeyboardButton("📋 " + ("عرض كل الملاحظات" if lang=="ar" else "View All Notes"), callback_data="pat_viewnotes_" + pid)],
        [InlineKeyboardButton(tx("btn_back", lang), callback_data="pat_list")]
    ])
    
    await u.message.reply_text(msg + "\n\n" + "\n".join(lines), reply_markup=btns, parse_mode="Markdown")
    return STATE_PAT_MENU

async def pat_view_notes(u, ctx):
    q = u.callback_query; await q.answer()
    lang = get_lang(ctx)
    pid = q.data.replace("pat_viewnotes_", "")
    load_patients(ctx)
    patients = ctx.user_data.get("patients", {})
    p = patients.get(pid, {})
    notes = p.get("notes", [])
    
    if not notes:
        await q.message.edit_text("📭 " + ("لا توجد ملاحظات" if lang=="ar" else "No notes"), 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tx("btn_back", lang), callback_data="back")]]))
        return STATE_PAT_MENU
    
    # نرسل كل ملاحظة
    for n in notes:
        if n["type"] == "text":
            await u.effective_chat.send_message("📝 " + n["date"] + ":\n" + n["content"])
        elif n["type"] == "photo":
            try:
                await u.effective_chat.send_photo(n["file_id"], caption="📸 " + n["date"] + ("\n" + n["caption"] if n.get("caption") else ""))
            except: pass
        elif n["type"] == "file":
            try:
                await u.effective_chat.send_document(n["file_id"], caption="📄 " + n["date"] + ": " + n.get("name",""))
            except: pass
    
    await u.effective_chat.send_message("✅ " + ("انتهت الملاحظات" if lang=="ar" else "End of notes"),
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tx("btn_back", lang), callback_data="back")]]))
    return STATE_PAT_MENU


async def pat_log_menu(u, ctx):
    q = u.callback_query; await q.answer()
    lang = get_lang(ctx)
    pid = q.data.replace("pat_log_","")
    ctx.user_data["log_pid"] = pid
    load_patients(ctx)
    patients = ctx.user_data.get("patients",{})
    p = patients.get(pid,{})
    
    # نعرض آخر القراءات
    logs = p.get("readings", [])
    lines = ["📊 *" + ("سجل " if lang=="ar" else "Log: ") + p.get("name","") + "*", ""]
    
    if logs:
        for r in logs[-5:]:
            date = r.get("date","")
            if r.get("sugar"):
                lines.append("🩸 " + date + ": سكر " + str(r["sugar"]) + " mg/dL")
            if r.get("bp"):
                lines.append("💉 " + date + ": ضغط " + str(r["bp"]))
    else:
        lines.append("📭 " + ("لا توجد قراءات" if lang=="ar" else "No readings yet"))
    
    btns = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ " + ("أضف قراءة" if lang=="ar" else "Add Reading"), callback_data="pat_addreading_" + pid)],
        [InlineKeyboardButton("💉 " + ("سجل الضغط" if lang=="ar" else "BP Log"), callback_data="pat_viewbp_" + pid)],
        [InlineKeyboardButton("🌅 " + ("سكر صيام" if lang=="ar" else "Fasting"), callback_data="pat_viewfasting_" + pid)],
        [InlineKeyboardButton("🍽️ " + ("سكر بعد الأكل" if lang=="ar" else "Post-meal"), callback_data="pat_viewpostmeal_" + pid)],
        [InlineKeyboardButton("📊 " + ("سكر تراكمي HbA1c" if lang=="ar" else "HbA1c"), callback_data="pat_viewhba1c_" + pid)],
        [InlineKeyboardButton("🎲 " + ("سكر عشوائي" if lang=="ar" else "Random"), callback_data="pat_viewrandom_" + pid)],
        [InlineKeyboardButton(tx("btn_back", lang), callback_data="pat_view_" + pid)]
    ])
    
    await q.message.edit_text("\n".join(lines), reply_markup=btns, parse_mode="Markdown")
    return STATE_PAT_MENU

async def pat_add_reading(u, ctx):
    q = u.callback_query; await q.answer()
    lang = get_lang(ctx)
    
    if q.data.startswith("pat_viewfasting_") or q.data.startswith("pat_viewpostmeal_") or q.data.startswith("pat_viewhba1c_") or q.data.startswith("pat_viewrandom_"):
        for prefix in ["pat_viewfasting_","pat_viewpostmeal_","pat_viewhba1c_","pat_viewrandom_"]:
            if q.data.startswith(prefix):
                pid = q.data.replace(prefix,"")
                stype = prefix.replace("pat_view","").replace("_","")
                break
        p = patients.get(pid,{})
        readings = p.get("readings",[])
        
        stype_map = {"fasting":"🌅 سكر الصيام","postmeal":"🍽️ سكر بعد الأكل","hba1c":"📊 HbA1c التراكمي","random":"🎲 عشوائي"}
        unit_map = {"hba1c":"%","fasting":"mg/dL","postmeal":"mg/dL","random":"mg/dL"}
        
        filtered = [r for r in readings if r.get("sugar") and r.get("stype","random") == stype]
        lines = [stype_map.get(stype,"📊") + " *" + p.get("name","") + "*",""]
        
        if filtered:
            for i, r in enumerate(filtered[-10:]):
                unit = unit_map.get(stype,"mg/dL")
                lines.append(f"  {i+1}. {r['date'][:16]}: {r['sugar']} {unit}")
        else:
            lines.append("📭 لا توجد قراءات")
        
        # أزرار حذف
        del_btns = []
        for i, r in enumerate(filtered[-5:]):
            del_btns.append([InlineKeyboardButton(f"🗑️ {r['date'][:10]}: {r['sugar']}", callback_data=f"pat_delreading_{pid}_{r['date']}")])
        del_btns.append([InlineKeyboardButton(tx("btn_back", lang), callback_data="pat_log_" + pid)])
        
        await q.message.edit_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(del_btns), parse_mode="Markdown")
        return STATE_PAT_MENU

    if q.data.startswith("pat_delreading_"):
        parts = q.data.replace("pat_delreading_","").split("_",1)
        pid = parts[0]
        date_key = parts[1] if len(parts)>1 else ""
        p = patients.get(pid,{})
        before = len(p.get("readings",[]))
        p["readings"] = [r for r in p.get("readings",[]) if r.get("date","") != date_key]
        after = len(p.get("readings",[]))
        save_patients(ctx)
        await q.answer("✅ " + (f"تم حذف {before-after} قراءة" if lang=="ar" else f"Deleted {before-after} reading"))
        return STATE_PAT_MENU

    if q.data.startswith("pat_viewsugar_"):
        pid = q.data.replace("pat_viewsugar_","")
        p = patients.get(pid,{})
        readings = [r for r in p.get("readings",[]) if r.get("sugar")]
        lines = ["🩸 *" + ("سجل السكر - " if lang=="ar" else "Sugar Log - ") + p.get("name","") + "*",""]
        if readings:
            for r in readings[-15:]:
                val = r["sugar"]
                if val < 70: status = "⚠️"
                elif val <= 100: status = "✅"
                elif val <= 125: status = "🟡"
                else: status = "🔴"
                lines.append(status + " " + r["date"] + ": " + str(val) + " mg/dL")
        else:
            lines.append("📭 " + ("لا توجد قراءات" if lang=="ar" else "No readings"))
        await q.message.edit_text("\n".join(lines),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tx("btn_back", lang), callback_data="pat_log_" + pid)]]),
            parse_mode="Markdown")
        return STATE_PAT_MENU

    if q.data.startswith("pat_viewbp_"):
        pid = q.data.replace("pat_viewbp_","")
        p = patients.get(pid,{})
        readings = [r for r in p.get("readings",[]) if r.get("bp")]
        lines = ["💉 *" + ("سجل الضغط - " if lang=="ar" else "BP Log - ") + p.get("name","") + "*",""]
        if readings:
            for r in readings[-15:]:
                sys_val = r.get("sys",0)
                if sys_val < 120: status = "✅"
                elif sys_val < 130: status = "🟡"
                elif sys_val < 140: status = "🟠"
                else: status = "🔴"
                lines.append(status + " " + r["date"] + ": " + str(r["bp"]))
        else:
            lines.append("📭 " + ("لا توجد قراءات" if lang=="ar" else "No readings"))
        await q.message.edit_text("\n".join(lines),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tx("btn_back", lang), callback_data="pat_log_" + pid)]]),
            parse_mode="Markdown")
        return STATE_PAT_MENU


    if q.data.startswith("pat_addsugar_"):
        pid = q.data.replace("pat_addsugar_","")
        ctx.user_data["log_pid"] = pid
        ctx.user_data["log_type"] = "sugar"
        btns = InlineKeyboardMarkup([
            [InlineKeyboardButton("🌅 " + ("صيام" if lang=="ar" else "Fasting"), callback_data="logsugar_fasting"),
             InlineKeyboardButton("🍽️ " + ("بعد الأكل" if lang=="ar" else "Post-meal"), callback_data="logsugar_postmeal")],
            [InlineKeyboardButton("📊 HbA1c", callback_data="logsugar_hba1c")],
        ])
        await q.message.edit_text("🩸 " + ("نوع قراءة السكر؟" if lang=="ar" else "Sugar reading type?"), reply_markup=btns)
        return STATE_PAT_LOG
    
    elif q.data.startswith("pat_addbp_"):
        pid = q.data.replace("pat_addbp_","")
        ctx.user_data["log_pid"] = pid
        ctx.user_data["log_type"] = "bp"
        await q.message.edit_text("💉 اكتب مثال: ضغط 120/80")
        return STATE_PAT_LOG
    
    elif q.data.startswith("logsugar_"):
        ctx.user_data["sugar_log_type"] = q.data.replace("logsugar_","")
        await q.message.edit_text("🩸 " + ("أدخل قراءة السكر (mg/dL):" if lang=="ar" else "Enter sugar value (mg/dL):"))
        return STATE_PAT_LOG

async def pat_save_reading(u, ctx):
    lang = get_lang(ctx)
    pid = ctx.user_data.get("log_pid","")
    log_type = ctx.user_data.get("log_type","")
    text = u.message.text.strip()
    # نقرأ النوع من النص مباشرة
    txt = text.strip()
    stype_detected = "random"
    val_text = txt
    for kw, st in [("صيام ","fasting"),("صايم ","fasting"),("بعداكل ","postmeal"),
                   ("بعد اكل ","postmeal"),("تراكمي ","hba1c"),("hba1c ","hba1c"),
                   ("ضغط ","bp"),("عشوائي ","random")]:
        if txt.lower().startswith(kw.lower()):
            stype_detected = st
            val_text = txt[len(kw):].strip()
            break
    
    
    load_patients(ctx)
    patients = ctx.user_data.get("patients",{})
    p = patients.get(pid,{})
    if not p: return STATE_PAT_MENU
    
    from datetime import datetime
    date = datetime.now().strftime("%Y-%m-%d %H:%M")
    readings = p.setdefault("readings",[])
    
    # نقرأ النوع من النص مباشرة
    text_lower = text.strip().lower()
    detected_stype = "random"
    detected_val = text_lower
    
    type_keywords = {
        "صيام": "fasting", "صايم": "fasting", "fasting": "fasting", "f ": "fasting",
        "بعداكل": "postmeal", "بعد اكل": "postmeal", "postmeal": "postmeal", "p ": "postmeal",
        "تراكمي": "hba1c", "hba1c": "hba1c", "h ": "hba1c",
        "ضغط": "bp", "bp": "bp", "b ": "bp",
        "عشوائي": "random", "random": "random", "r ": "random"
    }
    
    for keyword, stype_val in type_keywords.items():
        if text_lower.startswith(keyword):
            detected_stype = stype_val
            detected_val = text_lower.replace(keyword,"").strip().strip(":")
            break
    
    if detected_stype == "bp" or (log_type == "bp" and "/"  in text):
        # معالجة الضغط
        try:
            bp_text = detected_val if detected_val else text
            parts_bp = bp_text.replace(" ","").split("/")
            from datetime import datetime
            date = datetime.now().strftime("%Y-%m-%d %H:%M")
            load_patients(ctx)
            patients = ctx.user_data.get("patients",{})
            p2 = patients.get(pid,{})
            if p2:
                p2.setdefault("readings",[]).append({"date":date,"bp":bp_text,"sys":int(parts_bp[0]),"dia":int(parts_bp[1])})
                save_patients(ctx)
                await u.message.reply_text("✅ 💉 ضغط: " + bp_text,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="pat_view_" + pid)]]))
        except:
            await u.message.reply_text("❌ صيغة خاطئة مثال: ضغط 120/80")
            return STATE_PAT_LOG
        return STATE_PAT_MENU

    if log_type == "sugar" or detected_stype != "random":
        try:
            val = float(detected_val.replace(",",".") if detected_val else text.replace(",","."))
            # نقرأ النوع من كل المصادر الممكنة
            sugar_type = (ctx.user_data.get(f"stype_{pid}") or 
                         ctx.user_data.get("sugar_type") or 
                         ctx.user_data.get("sugar_type_confirmed") or 
                         "random")
            type_names = {
                "fasting":"صيام","postmeal":"بعد الأكل",
                "random":"عشوائي","hba1c":"تراكمي HbA1c"
            }
            stype_clean = sugar_type.replace("sugar_","")
            readings.append({"date": date, "sugar": val, "stype": stype_clean, "stype_ar": type_names.get(sugar_type,"")})
            
            # تصنيف القراءة
            if stype_clean == "hba1c" or val < 20:
                if val < 5.7: status = "✅ طبيعي"
                elif val <= 6.4: status = "🟡 ما قبل السكري"
                elif val <= 7.0: status = "🟠 مضبوط"
                else: status = "🔴 مرتفع"
            elif stype_clean == "fasting":
                if val < 70: status = "⚠️ منخفض"
                elif val <= 100: status = "✅ طبيعي"
                elif val <= 125: status = "🟡 ما قبل السكري"
                else: status = "🔴 مرتفع"
            else:
                if val < 140: status = "✅ طبيعي"
                elif val <= 199: status = "🟡 ما قبل السكري"
                else: status = "🔴 مرتفع"
            
            msg = "✅ " + ("تم حفظ قراءة السكر\n🩸 " if lang=="ar" else "Sugar reading saved\n🩸 ") + str(val) + " mg/dL " + status
        except:
            await u.message.reply_text("❌ " + ("أدخل رقماً صحيحاً" if lang=="ar" else "Enter valid number"))
            return STATE_PAT_LOG
    
    elif log_type == "bp":
        try:
            parts = text.replace(" ","").split("/")
            sys_val = int(parts[0])
            dia_val = int(parts[1])
            readings.append({"date": date, "bp": text, "sys": sys_val, "dia": dia_val})
            
            if sys_val < 120 and dia_val < 80: status = "✅ طبيعي"
            elif sys_val < 130: status = "🟡 مرتفع قليلاً"
            elif sys_val < 140: status = "🟠 مرحلة 1"
            else: status = "🔴 مرتفع"
            
            msg = "✅ " + ("تم حفظ قراءة الضغط\n💉 " if lang=="ar" else "BP saved\n💉 ") + text + " " + status
        except:
            await u.message.reply_text("❌ " + ("صيغة خاطئة، مثال: 120/80" if lang=="ar" else "Wrong format, e.g. 120/80"))
            return STATE_PAT_LOG
    
    save_patients(ctx)
    
    btns = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 " + ("سجل القراءات" if lang=="ar" else "View Log"), callback_data="pat_log_" + pid)],
        [InlineKeyboardButton(tx("btn_back", lang), callback_data="pat_view_" + pid)]
    ])
    await u.message.reply_text(msg, reply_markup=btns)
    return STATE_PAT_MENU

async def pat_view_log(u, ctx):
    q = u.callback_query; await q.answer()
    lang = get_lang(ctx)
    pid = q.data.replace("pat_viewlog_","")
    load_patients(ctx)
    patients = ctx.user_data.get("patients",{})
    p = patients.get(pid,{})
    readings = p.get("readings",[])
    
    if not readings:
        await q.message.edit_text("📭 " + ("لا توجد قراءات" if lang=="ar" else "No readings"),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tx("btn_back", lang), callback_data="pat_log_" + pid)]]))
        return STATE_PAT_MENU
    
    lines = ["📊 *" + ("كل القراءات - " if lang=="ar" else "All Readings - ") + p.get("name","") + "*", ""]
    for r in readings[-20:]:
        if r.get("sugar"):
            lines.append("🩸 " + r["date"] + ": " + str(r["sugar"]) + " mg/dL")
        if r.get("bp"):
            lines.append("💉 " + r["date"] + ": " + str(r["bp"]))
    
    await q.message.edit_text("\n".join(lines),
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tx("btn_back", lang), callback_data="pat_log_" + pid)]]),
        parse_mode="Markdown")
    return STATE_PAT_MENU

async def rem_menu(u, ctx):
    q = u.callback_query; await q.answer()
    lang = get_lang(ctx)
    if q.data == "back": return await go_back(u, ctx)
    if q.data == "r_add":
        await q.message.edit_text(tx("rem_name", lang), reply_markup=kb_back(lang))
        return STATE_REM_ADD_NAME
    if q.data == "r_list":
        await q.message.edit_text(fmt_rems(get_rems(ctx), lang),
            reply_markup=kb_remind(lang), parse_mode=ParseMode.MARKDOWN)
        return STATE_REM_MENU
    if q.data in ("r_del", "r_edit"):
        rems = get_rems(ctx)
        if not rems:
            await q.message.edit_text(tx("no_rems", lang), reply_markup=kb_remind(lang))
            return STATE_REM_MENU
        cb = "dr_" if q.data == "r_del" else "er_"
        lbl = tx("sel_del", lang) if q.data == "r_del" else tx("sel_edit", lang)
        btns = [[InlineKeyboardButton(
            f"[{r['id']}] {r['drug']} {r['time']}", callback_data=f"{cb}{r['id']}")] for r in rems]
        btns.append([InlineKeyboardButton(tx("btn_back", lang), callback_data="r_back")])
        await q.message.edit_text(lbl, reply_markup=InlineKeyboardMarkup(btns))
        return STATE_REM_EDIT_SEL if q.data == "r_edit" else STATE_REM_MENU
    if q.data.startswith("dr_"):
        rid = int(q.data[3:])
        rems = get_rems(ctx)
        ok = False
        for i, r in enumerate(rems):
            if r["id"] == rid: rems.pop(i); ok = True; break
        if ok: save_rems(ctx)
        await q.message.edit_text(tx("rem_deleted" if ok else "rem_not_found", lang), reply_markup=kb_remind(lang))
        return STATE_REM_MENU
    if q.data == "r_back":
        await q.message.edit_text(tx("rem_menu", lang), reply_markup=kb_remind(lang), parse_mode=ParseMode.MARKDOWN)
        return STATE_REM_MENU
    return STATE_REM_MENU

async def rem_add_name(u, ctx):
    lang = get_lang(ctx)
    ctx.user_data["nr_drug"] = u.message.text.strip()
    await u.message.reply_text(tx("rem_time", lang), reply_markup=kb_back(lang))
    return STATE_REM_ADD_TIME

async def rem_add_time(u, ctx):
    lang = get_lang(ctx)
    t = u.message.text.strip()
    if not re.match(r"^\d{1,2}:\d{2}$", t):
        await u.message.reply_text(tx("bad_time", lang), reply_markup=kb_back(lang))
        return STATE_REM_ADD_TIME
    try:
        h, m = map(int, t.split(":"))
        if not (0 <= h <= 23 and 0 <= m <= 59): raise ValueError
        ctx.user_data["nr_time"] = f"{h:02d}:{m:02d}"
    except:
        await u.message.reply_text(tx("bad_time", lang), reply_markup=kb_back(lang))
        return STATE_REM_ADD_TIME
    await u.message.reply_text(tx("rem_freq", lang), reply_markup=kb_back(lang))
    return STATE_REM_ADD_FREQ

async def rem_add_freq(u, ctx):
    lang = get_lang(ctx)
    track(u, "reminders")
    try:
        f = int(u.message.text.strip())
        if not 1 <= f <= 6: raise ValueError
    except:
        await u.message.reply_text(tx("bad_freq", lang), reply_markup=kb_back(lang))
        return STATE_REM_ADD_FREQ
    ctx.user_data["nr_freq"] = f
    # نحفظ مباشرة
    drug = ctx.user_data.get("nr_drug", "?")
    time_s = ctx.user_data.get("nr_time", "08:00")
    f = ctx.user_data.get("nr_freq", 1)
    rems = get_rems(ctx)
    pat_name_rem = ctx.user_data.pop("nr_patient", "")
    rem_entry = {"id": len(rems)+1, "drug": drug, "time": time_s, "freq": f}
    if pat_name_rem:
        rem_entry["patient"] = pat_name_rem
    rems.append(rem_entry)
    save_rems(ctx)
    sched(ctx.application, u.effective_chat.id, drug, time_s, f, lang, ctx.user_data.get("timezone", "Asia/Riyadh"))
    msg = "✅ " + drug + " - " + time_s + " - " + str(f) + ("x/يوم" if lang=="ar" else "x/day")
    await u.message.reply_text(msg, reply_markup=kb_remind(lang))
    return STATE_REM_MENU

async def rem_edit_sel(u, ctx):
    q = u.callback_query; await q.answer()
    lang = get_lang(ctx)
    if q.data == "r_back":
        await q.message.edit_text(tx("rem_menu", lang), reply_markup=kb_remind(lang), parse_mode=ParseMode.MARKDOWN)
        return STATE_REM_MENU
    if q.data.startswith("er_"):
        ctx.user_data["edit_id"] = int(q.data[3:])
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(tx("ef_name", lang), callback_data="ef_drug")],
            [InlineKeyboardButton(tx("ef_time", lang), callback_data="ef_time")],
            [InlineKeyboardButton(tx("ef_freq", lang), callback_data="ef_freq")],
            [InlineKeyboardButton(tx("btn_back", lang), callback_data="r_back")]])
        await q.message.edit_text(tx("edit_fields", lang), reply_markup=kb)
        return STATE_REM_EDIT_FIELD
    return STATE_REM_EDIT_SEL

async def rem_edit_field(u, ctx):
    q = u.callback_query; await q.answer()
    lang = get_lang(ctx)
    if q.data == "r_back":
        await q.message.edit_text(tx("rem_menu", lang), reply_markup=kb_remind(lang), parse_mode=ParseMode.MARKDOWN)
        return STATE_REM_MENU
    fmap = {"ef_drug": "drug", "ef_time": "time", "ef_freq": "freq"}
    if q.data in fmap:
        ctx.user_data["edit_field"] = fmap[q.data]
        await q.message.edit_text(tx("new_val", lang), reply_markup=kb_back(lang))
        return STATE_REM_EDIT_VAL
    return STATE_REM_EDIT_FIELD

async def rem_edit_val(u, ctx):
    lang = get_lang(ctx)
    val = u.message.text.strip()
    rid = ctx.user_data.get("edit_id")
    field = ctx.user_data.get("edit_field", "")
    for r in get_rems(ctx):
        if r["id"] == rid:
            if field == "drug":
                r["drug"] = val
            elif field == "time":
                if not re.match(r"^\d{1,2}:\d{2}$", val):
                    await u.message.reply_text(tx("bad_time", lang))
                    return STATE_REM_EDIT_VAL
                r["time"] = val
            elif field == "freq":
                try:
                    f = int(val)
                    if not 1 <= f <= 6: raise ValueError
                    r["freq"] = f
                except:
                    await u.message.reply_text(tx("bad_freq", lang))
                    return STATE_REM_EDIT_VAL
            break
    save_rems(ctx)
    await u.message.reply_text(tx("rem_updated", lang), reply_markup=kb_remind(lang))
    return STATE_REM_MENU

async def fallback(u, ctx):
    # تجاهل callbacks فقط
    if u.callback_query:
        return None
    # لا نتدخل في النصوص - نتركها للـ handlers
    return None

async def stats_cmd(u, ctx):
    stats = load_stats()
    users_dict = stats.get("users", {})
    users = len(users_dict)
    searches = stats.get("searches", 0)
    child = stats.get("child_doses", 0)
    rems = stats.get("reminders", 0)
    total = stats.get("total_requests", 0)
    drugs = len(DRUGS_DB)
    images = stats.get("image_search", 0)
    bmi = stats.get("bmi", 0)
    cal = stats.get("calories", 0)
    sugar = stats.get("sugar", 0)
    bp = stats.get("bp", 0)
    premium = stats.get("premium", 0)
    # أكثر المستخدمين نشاطاً
    top_users = sorted(users_dict.items(), key=lambda x: x[1].get("count",0) if isinstance(x[1],dict) else x[1], reverse=True)[:3]
    lang = get_lang(ctx)
    if lang == "ar":
        lines = [
            "📊 *إحصائيات البوت التفصيلية*", "",
            "👥 *المستخدمون:*",
            "  • إجمالي المستخدمين: *" + str(users) + "*",
            "  • المشتركون المميزون: *" + str(premium) + "*", "",
            "🔧 *استخدام الميزات:*",
            "  • 🔍 البحث عن دواء: *" + str(searches) + "*",
            "  • 🍼 جرعات الأطفال: *" + str(child) + "*",
            "  • 📸 قراءة الصور: *" + str(images) + "*",
            "  • ⏰ التذكيرات: *" + str(rems) + "*",
            "  • 📊 BMI: *" + str(bmi) + "*",
            "  • 🔥 السعرات: *" + str(cal) + "*",
            "  • 🩸 السكر: *" + str(sugar) + "*",
            "  • 💉 الضغط: *" + str(bp) + "*", "",
            "📈 *الإجمالي:*",
            "  • طلبات: *" + str(total) + "*",
            "  • أدوية: *" + str(drugs) + "*",
        ]
        if top_users:
            lines += ["", "🏆 *أكثر المستخدمين نشاطاً:*"]
            for i, (uid, count) in enumerate(top_users, 1):
                lines.append("  " + str(i) + ". ID:" + str(uid) + " — " + str(count) + " طلب")
        msg = "\n".join(lines)
    else:
        lines = [
            "📊 *Bot Statistics*", "",
            f"👥 Users: *{users}*",
            f"💊 Drugs in DB: *{drugs}*",
            f"🔍 Drug Searches: *{searches}*",
            f"🍼 Child Doses: *{child}*",
            f"⏰ Reminders Added: *{rems}*",
            f"📈 Total Requests: *{total}*",
        ]
        msg = "\n".join(lines)
    await u.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

def build_conv():
    return ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
        ],
        states={
            STATE_CAL_GENDER: [
                CallbackQueryHandler(cal_gender, pattern="^(cal_|back)")],
            STATE_CAL_AGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, cal_age)],
            STATE_CAL_WEIGHT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, cal_weight)],
            STATE_CAL_HEIGHT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, cal_height)],
            STATE_CAL_ACTIVITY: [
                CallbackQueryHandler(cal_activity, pattern="^act_")],
            STATE_CAL_DISEASE: [
                CallbackQueryHandler(cal_disease, pattern="^dis_")],
            STATE_FOOD_SEARCH: [
                CallbackQueryHandler(go_back, pattern="^back$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, food_search)],
            STATE_INTERACTION: [
                CallbackQueryHandler(go_back, pattern="^back$"),
                CallbackQueryHandler(interaction_start, pattern="^m_interaction$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, interaction_input)],
            STATE_PAT_LOG: [
                CallbackQueryHandler(pat_add_reading, pattern="^(pat_addsugar_|pat_addbp_|logsugar_)"),
                CallbackQueryHandler(pat_view_log, pattern="^pat_viewlog_"),
                CallbackQueryHandler(patient_menu, pattern="^pat_log_"),
                CallbackQueryHandler(go_back, pattern="^back$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, pat_save_reading)],
            STATE_PAT_NOTE: [
                CallbackQueryHandler(go_back, pattern="^back$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, pat_note_save),
                MessageHandler(filters.PHOTO, pat_note_save),
                MessageHandler(filters.Document.ALL, pat_note_save)],
            STATE_PAT_MENU: [
                CallbackQueryHandler(go_back, pattern="^back$"),
                CallbackQueryHandler(pat_log_menu, pattern="^pat_log_"),
                CallbackQueryHandler(patient_menu, pattern="^sugtype_"),
                CallbackQueryHandler(patient_menu, pattern="^pat_edit_"),
                CallbackQueryHandler(patient_menu, pattern="^patedit_"),
                CallbackQueryHandler(patient_menu, pattern="^pattoggle_"),
                CallbackQueryHandler(patient_menu, pattern="^patdel_"),
                CallbackQueryHandler(patient_menu, pattern="^patadd_"),
                CallbackQueryHandler(pat_add_reading, pattern="^(pat_addsugar_|pat_addbp_)"),
                CallbackQueryHandler(pat_note_start, pattern="^pat_note_"),
                CallbackQueryHandler(pat_view_notes, pattern="^pat_viewnotes_"),
                CallbackQueryHandler(patient_menu, pattern="^pat_"),
                CallbackQueryHandler(patient_menu, pattern="^pr__")],
            STATE_PAT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, pat_name)],
            STATE_PAT_GENDER: [
                CallbackQueryHandler(pat_gender, pattern="^pat_gender_")],
            STATE_PAT_AGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, pat_age)],
            STATE_PAT_WEIGHT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, pat_weight)],
            STATE_PAT_DISEASE: [
                CallbackQueryHandler(pat_disease, pattern="^pat_dis_")],
            STATE_PAT_MEDS: [
                CallbackQueryHandler(pat_meds_cb, pattern="^pat_med_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, pat_meds)],
            STATE_PAT_ALLERGY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, pat_allergy)],
            STATE_SUGAR: [
                CallbackQueryHandler(go_back, pattern="^back$"),
                CallbackQueryHandler(sugar_handler, pattern="^sugar_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, sugar_result)],
            STATE_BP_AGE: [
                CallbackQueryHandler(go_back, pattern="^back$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, bp_age)],
            STATE_BP: [
                CallbackQueryHandler(go_back, pattern="^back$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, bp_result)],
            STATE_INFECTION_SITE: [
                CallbackQueryHandler(go_back, pattern="^back$"),
                CallbackQueryHandler(infection_site, pattern="^site_")],

            STATE_COUNTRY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_country)],
            STATE_LANGUAGE: [
                CallbackQueryHandler(pick_lang, pattern="^lang_"),
],
            STATE_MAIN_MENU: [
                CallbackQueryHandler(rem_done, pattern="^rem_done_"),
                CallbackQueryHandler(rem_later, pattern="^rem_snooze_"),

                CallbackQueryHandler(go_back, pattern="^back$"),
                CallbackQueryHandler(reg_handler, pattern="^reg_"),
                CallbackQueryHandler(main_cb, pattern="^(m_|do_lang|do_country|change_lang|pay_|cal_|act_|dis_|sugar_)"),
                CallbackQueryHandler(manual_drug_input, pattern="^manual_input$")],
            STATE_BMI_WEIGHT: [
                CallbackQueryHandler(bmi_cb, pattern="^bmi_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, bmi_text)],
            STATE_BMI_DRUG: [
                CallbackQueryHandler(bmi_cb, pattern="^bmi_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, bmi_text)],
            STATE_DRUG_SEARCH: [
                CallbackQueryHandler(manual_drug_input, pattern="^manual_input$"),
                CallbackQueryHandler(go_back, pattern="^back$"),
                CallbackQueryHandler(drug_sel, pattern="^ds_"),
                MessageHandler(filters.PHOTO, drug_search_image),
                MessageHandler(filters.TEXT & ~filters.COMMAND, drug_search)],
            STATE_DRUG_FORM: [
                CallbackQueryHandler(go_back, pattern="^back$"),
                CallbackQueryHandler(drug_form_selected, pattern="^form_")],
            STATE_CHILD_DRUG: [
                CallbackQueryHandler(go_back, pattern="^back$"),
                CallbackQueryHandler(manual_drug_input, pattern="^manual_input$"),
                CallbackQueryHandler(child_sel, pattern="^cs_"),
                MessageHandler(filters.PHOTO, child_input),
                MessageHandler(filters.TEXT & ~filters.COMMAND, child_input)],
            STATE_CHILD_WEIGHT: [
                CallbackQueryHandler(manual_drug_input, pattern="^manual_input$"),
                CallbackQueryHandler(retry_photo, pattern="^retry_photo$"),
                CallbackQueryHandler(go_back, pattern="^back$"),
                CallbackQueryHandler(go_back, pattern="^back$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, child_weight)],
            STATE_CHILD_CONC: [
                CallbackQueryHandler(go_back, pattern="^back$"),
                CallbackQueryHandler(child_conc, pattern="^conc_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, child_conc)],
            STATE_REM_MENU: [
                CallbackQueryHandler(go_back, pattern="^back$"),
                CallbackQueryHandler(rem_menu)],
            STATE_REM_ADD_NAME: [
                CallbackQueryHandler(go_back, pattern="^back$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, rem_add_name)],
            STATE_REM_ADD_TIME: [
                CallbackQueryHandler(go_back, pattern="^back$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, rem_add_time)],
            STATE_REM_ADD_FREQ: [
                CallbackQueryHandler(go_back, pattern="^back$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, rem_add_freq)],
            STATE_REM_EDIT_SEL: [
                CallbackQueryHandler(rem_edit_sel)],
            STATE_REM_EDIT_FIELD: [
                CallbackQueryHandler(rem_edit_field)],
            STATE_REM_EDIT_VAL: [
                CallbackQueryHandler(go_back, pattern="^back$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, rem_edit_val)],
        },
        fallbacks=[
            CallbackQueryHandler(retry_photo, pattern="^retry_photo$"),
            CommandHandler("start", start),
            CommandHandler("stats", stats_cmd),
            MessageHandler(filters.ALL, fallback)],
        allow_reentry=True,
        per_user=True,
        per_chat=True)


async def fix_doses_cmd(u, ctx):
    """أمر للأدمن لإصلاح الجرعات من Claude API"""
    if str(u.effective_user.id) != "6298206492":
        return
    
    import json
    with open("drugs.json", encoding="utf-8") as f:
        drugs = json.load(f)
    
    await u.message.reply_text("🔍 جارٍ فحص الجرعات...")
    fixed = 0
    
    for d in drugs:
        name_en = d.get("name_en","")
        name_ar = d.get("name_ar","")
        
        # نتخطى الأدوية ذات الجرعات الثابتة الصحيحة
        if d.get("fixed_dose") and d.get("age_doses"):
            continue
        
        # نتخطى الأدوية التي لديها جرعات صحيحة
        mn = d.get("pediatric_min_mg_per_kg", 0)
        mx = d.get("pediatric_max_mg_per_kg", 0)
        if mn and mx and float(str(mn)) < 100 and float(str(mx)) < 100:
            continue
        
        # نطلب الجرعة الصحيحة من Claude
        try:
            async with httpx.AsyncClient(timeout=20) as hc:
                prompt = f"""What is the correct pediatric oral syrup dose for {name_en}?
Reply ONLY in this format:
min_mg_per_kg: [number]
max_mg_per_kg: [number]
concentration: [e.g. 125mg/5ml]
frequency: [e.g. 3 times daily]
If not available as syrup write: NOT_SYRUP"""
                
                r = await hc.post("https://api.anthropic.com/v1/messages",
                    headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                    json={"model": "claude-haiku-4-5-20251001", "max_tokens": 100,
                        "messages": [{"role": "user", "content": prompt}]})
                result = r.json().get("content", [{}])[0].get("text","").strip()
                
                if "NOT_SYRUP" in result:
                    d["not_syrup"] = True
                    continue
                
                lines = result.split("\n")
                for line in lines:
                    if "min_mg_per_kg:" in line:
                        val = line.split(":")[1].strip()
                        try: d["pediatric_min_mg_per_kg"] = float(val)
                        except: pass
                    if "max_mg_per_kg:" in line:
                        val = line.split(":")[1].strip()
                        try: d["pediatric_max_mg_per_kg"] = float(val)
                        except: pass
                    if "concentration:" in line:
                        val = line.split(":")[1].strip()
                        if val and val != "N/A":
                            d["concentration"] = val
                    if "frequency:" in line:
                        val = line.split(":")[1].strip()
                        if val:
                            d["pediatric_frequency_en"] = val
                
                fixed += 1
                
        except Exception as e:
            logger.error(f"fix_doses: {name_en}: {e}")
    
    with open("drugs.json", "w", encoding="utf-8") as f:
        json.dump(drugs, f, ensure_ascii=False, indent=2)
    
    await u.message.reply_text(f"✅ تم إصلاح {fixed} دواء!")

async def restore_reminders(app):
    """إعادة جدولة التذكيرات عند بدء التشغيل"""
    all_rems = load_all_reminders()
    count = 0
    for uid, rems in all_rems.items():
        if uid == "0" or not uid.isdigit():
            continue
        for r in rems:
            try:
                lang = "ar"
                tz = r.get("tz", "Asia/Riyadh")
                sched(app, int(uid), r["drug"], r["time"], r["freq"], lang, tz)
                count += 1
            except Exception as e:
                logger.error(f"restore reminder error: {e}")
    if count:
        logger.info(f"✅ تم استعادة {count} تذكير")

def get_bmi_category(bmi, age, is_child, lang):
    """تصنيف BMI حسب العمر"""
    if is_child:
        CDC = {
            2:(14.7,17.0,17.8), 3:(14.0,16.5,17.4), 4:(13.6,16.2,17.1),
            5:(13.5,16.2,17.4), 6:(13.5,16.6,18.0), 7:(13.7,17.2,18.9),
            8:(14.0,17.9,19.9), 9:(14.3,18.7,21.0), 10:(14.7,19.5,22.1),
            11:(15.2,20.4,23.2), 12:(15.7,21.2,24.2), 13:(16.2,22.0,25.1),
            14:(16.7,22.6,25.9), 15:(17.2,23.2,26.5), 16:(17.6,23.7,27.0),
            17:(18.0,24.0,27.4), 18:(18.4,24.3,27.8),
        }
        a = min(max(int(age), 2), 18)
        p5, p85, p95 = CDC.get(a, (14.0, 17.0, 19.0))
        if bmi < p5:
            return ("نقص وزن (<5%)" if lang=="ar" else "Underweight (<5th %ile)")
        elif bmi < p85:
            return ("وزن طبيعي (5-85%)" if lang=="ar" else "Normal (5th-85th %ile)")
        elif bmi < p95:
            return ("زيادة وزن (85-95%)" if lang=="ar" else "Overweight (85th-95th %ile)")
        else:
            return ("سمنة (>95%)" if lang=="ar" else "Obese (>95th %ile)")
    else:
        if bmi < 18.5:
            return ("نقص وزن" if lang=="ar" else "Underweight")
        elif bmi < 25:
            return ("وزن طبيعي" if lang=="ar" else "Normal weight")
        elif bmi < 30:
            return ("زيادة وزن" if lang=="ar" else "Overweight")
        elif bmi < 35:
            return ("سمنة درجة 1" if lang=="ar" else "Obesity grade 1")
        elif bmi < 40:
            return ("سمنة درجة 2" if lang=="ar" else "Obesity grade 2")
        else:
            return ("سمنة مرضية" if lang=="ar" else "Morbid obesity")

async def bmi_cb(update, ctx):
    """معالج موحد لكل BMI callbacks"""
    q = update.callback_query
    await q.answer()
    lang = get_lang(ctx)
    data = q.data

    if data == "bmi_back":
        ctx.user_data.pop("bmi_step", None)
        await show_main(q.message, lang, edit=True)
        return STATE_MAIN_MENU

    if data in ("bmi_child", "bmi_adult"):
        ctx.user_data["bmi_is_child"] = (data == "bmi_child")
        ctx.user_data["bmi_step"] = "weight"
        prompt = ("⚖️ أدخل الوزن بالكيلوغرام:" if lang=="ar" else "⚖️ Enter weight in kg:")
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(
            "🔙 " + ("رجوع" if lang=="ar" else "Back"), callback_data="bmi_back")]])
        await q.message.edit_text(prompt, reply_markup=kb)
        return STATE_BMI_WEIGHT

    if data == "bmi_dose_yes":
        ctx.user_data["bmi_step"] = "drug"
        prompt = ("💊 أدخل اسم الدواء:" if lang=="ar" else "💊 Enter drug name:")
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(
            "🔙 " + ("رجوع" if lang=="ar" else "Back"), callback_data="bmi_back")]])
        await q.message.edit_text(prompt, reply_markup=kb)
        return STATE_BMI_DRUG

    if data == "bmi_dose_no":
        await show_main(q.message, lang, edit=True)
        return STATE_MAIN_MENU

    return STATE_BMI_WEIGHT

async def bmi_text(update, ctx):
    """معالج النصوص لحاسبة BMI"""
    lang = get_lang(ctx)
    step = ctx.user_data.get("bmi_step", "weight")
    text = update.message.text.strip().replace(",", ".")

    kb_back_bmi = InlineKeyboardMarkup([[InlineKeyboardButton(
        "🔙 " + ("رجوع" if lang=="ar" else "Back"), callback_data="bmi_back")]])

    if step == "weight":
        try:
            w = float(text)
            if not 1 <= w <= 300: raise ValueError
        except:
            err = "❌ وزن غير صحيح" if lang=="ar" else "❌ Invalid weight"
            await update.message.reply_text(err, reply_markup=kb_back_bmi)
            return STATE_BMI_WEIGHT
        ctx.user_data["bmi_w"] = w
        ctx.user_data["bmi_step"] = "height"
        prompt = ("📏 أدخل الطول بالسنتيمتر:" if lang=="ar" else "📏 Enter height in cm:")
        await update.message.reply_text(prompt, reply_markup=kb_back_bmi)
        return STATE_BMI_WEIGHT

    if step == "height":
        try:
            h = float(text)
            if not 30 <= h <= 250: raise ValueError
        except:
            err = "❌ طول غير صحيح" if lang=="ar" else "❌ Invalid height"
            await update.message.reply_text(err, reply_markup=kb_back_bmi)
            return STATE_BMI_WEIGHT
        ctx.user_data["bmi_h"] = h
        ctx.user_data["bmi_step"] = "age"
        prompt = ("🎂 أدخل العمر بالسنوات:" if lang=="ar" else "🎂 Enter age in years:")
        await update.message.reply_text(prompt, reply_markup=kb_back_bmi)
        return STATE_BMI_WEIGHT

    if step == "age":
        try:
            age = float(text)
            if not 0 <= age <= 120: raise ValueError
        except:
            err = "❌ عمر غير صحيح" if lang=="ar" else "❌ Invalid age"
            await update.message.reply_text(err, reply_markup=kb_back_bmi)
            return STATE_BMI_WEIGHT

        w = ctx.user_data.get("bmi_w", 0)
        h = ctx.user_data.get("bmi_h", 0)
        is_child = ctx.user_data.get("bmi_is_child", True)
        bmi = round(w / ((h/100)**2), 1)
        cat = get_bmi_category(bmi, age, is_child, lang)
        ideal = round(2*age+8, 1) if age <= 10 else round((age*4-2.5)/2, 1)

        if lang == "ar":
            msg = (
                "📊 *نتيجة BMI*\n\n"
                + f"⚖️ الوزن: {w} كغ\n"
                + f"📏 الطول: {h} سم\n"
                + f"🎂 العمر: {int(age)} سنة\n\n"
                + f"📊 *BMI: {bmi}*\n"
                + f"✅ التصنيف: *{cat}*\n"
                + (f"🎯 الوزن المثالي: *{ideal} كغ*" if is_child else "")
            )
        else:
            msg = (
                "📊 *BMI Result*\n\n"
                + f"⚖️ Weight: {w} kg\n"
                + f"📏 Height: {h} cm\n"
                + f"🎂 Age: {int(age)} years\n\n"
                + f"📊 *BMI: {bmi}*\n"
                + f"✅ Category: *{cat}*\n"
                + (f"🎯 Ideal Weight: *{ideal} kg*" if is_child else "")
            )

        if is_child:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "💊 " + ("احسب جرعة دواء" if lang=="ar" else "Calculate drug dose"),
                    callback_data="bmi_dose_yes")],
                [InlineKeyboardButton(
                    "🔙 " + ("القائمة الرئيسية" if lang=="ar" else "Main Menu"),
                    callback_data="bmi_dose_no")],
            ])
        else:
            kb = InlineKeyboardMarkup([[InlineKeyboardButton(
                "🔙 " + ("القائمة الرئيسية" if lang=="ar" else "Main Menu"),
                callback_data="bmi_dose_no")]])

        ctx.user_data["bmi_step"] = "done"
        await update.message.reply_text(msg, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        return STATE_BMI_DRUG

    if step == "drug":
        res = search_drugs(text)
        w = ctx.user_data.get("bmi_w", 0)
        if not res:
            err = tx("not_found", lang)
            await update.message.reply_text(err, reply_markup=kb_back_bmi)
            return STATE_BMI_DRUG
        dose = calc_child(res[0], w, lang)
        await update.message.reply_text(dose, reply_markup=kb_back(lang), parse_mode=ParseMode.MARKDOWN)
        return STATE_BMI_DRUG

    await show_main(update.message, lang)
    return STATE_MAIN_MENU

# نظام الاشتراكات المميزة
# ═══════════════════════════════════════

import json
from datetime import datetime, timedelta

SUBS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "subscriptions.json")

PLANS = {
    "month":  {"stars": 200,  "days": 30,  "label": "شهري"},
    "3month": {"stars": 500,  "days": 90,  "label": "3 أشهر"},
    "6month": {"stars": 900,  "days": 180, "label": "6 أشهر"},
    "year":   {"stars": 1500, "days": 365, "label": "سنوي"},
}

def load_subs():
    try:
        with open(SUBS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_subs(data):
    with open(SUBS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_premium(user_id):
    return True  # مجاني مؤقتاً حتى 1000 مستخدم

def get_expiry(user_id):
    subs = load_subs()
    uid = str(user_id)
    if uid not in subs:
        return None
    return subs[uid]["expiry"]

def activate_premium(user_id, days):
    subs = load_subs()
    uid = str(user_id)
    now = datetime.now()
    if uid in subs:
        current = datetime.fromisoformat(subs[uid]["expiry"])
        if current > now:
            expiry = current + timedelta(days=days)
        else:
            expiry = now + timedelta(days=days)
    else:
        expiry = now + timedelta(days=days)
    subs[uid] = {"expiry": expiry.isoformat(), "activated": now.isoformat()}
    save_subs(subs)
    return expiry.strftime("%Y-%m-%d")

def kb_premium(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(tx("btn_month", lang), callback_data="pay_month")],
        [InlineKeyboardButton(tx("btn_3month", lang), callback_data="pay_3month")],
        [InlineKeyboardButton(tx("btn_6month", lang), callback_data="pay_6month")],
        [InlineKeyboardButton(tx("btn_year", lang), callback_data="pay_year")],
        [InlineKeyboardButton(tx("btn_back", lang), callback_data="back")],
    ])

async def premium_menu(update, ctx):
    q = update.callback_query
    await q.answer()
    lang = get_lang(ctx)
    uid = update.effective_user.id

    if is_premium(uid):
        expiry = get_expiry(uid)
        msg = tx("already_premium", lang).format(date=expiry[:10])
        await q.message.edit_text(msg, reply_markup=kb_back(lang), parse_mode=ParseMode.MARKDOWN)
        return STATE_MAIN_MENU

    msg = tx("premium_menu", lang) + chr(10) + chr(10) + tx("premium_features", lang)
    await q.message.edit_text(msg, reply_markup=kb_premium(lang), parse_mode=ParseMode.MARKDOWN)
    return STATE_PREMIUM

async def process_payment(update, ctx):
    q = update.callback_query
    await q.answer()
    lang = get_lang(ctx)
    plan_key = q.data.replace("pay_", "")
    plan = PLANS.get(plan_key)

    if not plan:
        return STATE_MAIN_MENU

    stars = plan["stars"]
    title = "⭐ " + ("اشتراك مميز" if lang=="ar" else "Premium Subscription")
    desc = plan["label"] if lang=="ar" else plan_key.replace("month","month").replace("year","year")

    try:
        await ctx.bot.send_invoice(
            chat_id=update.effective_chat.id,
            title=title,
            description=("✨ وصول كامل لجميع ميزات البوت" if lang=="ar"
                        else "✨ Full access to all bot features"),
            payload=f"premium_{plan_key}_{update.effective_user.id}",
            currency="XTR",
            prices=[{"label": title, "amount": stars}],
        )
    except Exception as e:
        logger.error(f"Invoice error: {e}")
        await q.message.reply_text(
            "❌ خطأ في إنشاء الفاتورة" if lang=="ar" else "❌ Invoice error",
            reply_markup=kb_back(lang)
        )
    return STATE_MAIN_MENU

async def pre_checkout(update, ctx):
    query = update.pre_checkout_query
    await query.answer(ok=True)

async def successful_payment(update, ctx):
    lang = get_lang(ctx)
    payload = update.message.successful_payment.invoice_payload
    parts = payload.split("_")
    plan_key = parts[1] if len(parts) > 1 else "month"
    plan = PLANS.get(plan_key, PLANS["month"])
    uid = update.effective_user.id
    expiry = activate_premium(uid, plan["days"])
    msg = tx("payment_success", lang).format(date=expiry)
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

def main():
    print(f"✅ تم تحميل {len(DRUGS_DB)} دواء")
    persistence = PicklePersistence(filepath="bot_data.pkl")
    app = Application.builder().token(BOT_TOKEN).persistence(persistence).build()
    app.add_handler(build_conv())
    app.add_handler(CallbackQueryHandler(rem_done, pattern="^rem_done_"))
    app.add_handler(CallbackQueryHandler(rem_later, pattern="^rem_snooze_"))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("fixdose", fix_doses_cmd))
    app.add_handler(PreCheckoutQueryHandler(pre_checkout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    # استعادة التذكيرات
    import asyncio
    asyncio.get_event_loop().run_until_complete(restore_reminders(app)) if False else None
    app.post_init = restore_reminders
    print("🚀 البوت يعمل!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

# ═══════════════════════════════════════
# حاسبة BMI - كود نظيف
# ═══════════════════════════════════════


# ═══════════════════════════════════════
