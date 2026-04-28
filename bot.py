#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os, re, logging, asyncio, base64
from datetime import datetime
import pytz
TIMEZONE = pytz.timezone("Asia/Riyadh")

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

ANTHROPIC_API_KEY = "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"
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
 STATE_CHILD_CONC, STATE_PREMIUM) = range(18)

TEXTS = {
"ar": {
"welcome": "🏥 *مرحباً في بوت حاسبة الجرعات*\n🏥 *Welcome to Dose Calculator Bot*\n\nاختر لغتك | Choose your language:",
"main_menu": "📋 *القائمة الرئيسية*\n\nاختر:",
"btn_search": "🔍 استعلام عن دواء",
"btn_child": "🍼 جرعات الأطفال",
"btn_remind": "⏰ التذكير بالأدوية",
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
"child_prompt": "🍼 اكتب اسم الدواء أو أرسل صورة العبوة\n\n📸 *تعليمات التصوير:*\n• صوّر الوجه الأمامي للعبوة\n• تأكد أن الاسم والتركيز واضحان\n• مثال: 250مغ/5مل أو 100mg/5ml\n• الإضاءة جيدة والصورة واضحة",
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
"rem_saved": "✅ تم الحفظ!\n💊 {drug}\n🕐 {time}\n🔁 {freq}x/يوم",
"no_rems": "📭 لا توجد تذكيرات.",
"rems_title": "📋 *تذكيراتك:*\n\n",
"rem_deleted": "🗑️ تم الحذف.",
"rem_updated": "✅ تم التحديث.",
"rem_not_found": "❌ التذكير غير موجود.",
"alert": "🔔 *تذكير!*\n\n💊 حان وقت: *{drug}*",
"settings": "⚙️ *الإعدادات*",
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
"rem_saved": "✅ Saved!\n💊 {drug}\n🕐 {time}\n🔁 {freq}x/day",
"no_rems": "📭 No reminders yet.",
"rems_title": "📋 *Your Reminders:*\n\n",
"rem_deleted": "🗑️ Deleted.",
"rem_updated": "✅ Updated.",
"rem_not_found": "❌ Reminder not found.",
"alert": "🔔 *Reminder!*\n\n💊 Time to take: *{drug}*",
"settings": "⚙️ *Settings*",
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
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"users": {}, "searches": 0, "child_doses": 0, "reminders": 0, "total_requests": 0}

def save_stats(stats):
    try:
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"stats error: {e}")

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
        "augmentin":"amoxicillin_clavulanate","أوجمنتين":"amoxicillin_clavulanate",
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
                "aspirin":"acetylsalicylic_acid","أسبرين":"acetylsalicylic_acid",
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
            f"🔁 *Child Frequency:* {g('pediatric_frequency_en','pediatric_frequency')}\n"
            f"🧑 *Adult Dose:* {dose_adult()}\n"
            f"🔁 *Adult Frequency:* {g('adult_frequency_en','adult_frequency')}\n"
            f"⚠️ *Max Daily:* {g('max_daily')}\n\n"
            f"🚫 *Contraindications:* {g('contraindications_en','contraindications')}\n"
            f"⚡ *Side Effects:* {g('side_effects_en','side_effects')}\n"
            f"💊 *Interactions:* {g('interactions_en','interactions')}\n\n"
            f"🤰 *Pregnancy:* {g('pregnancy_en','pregnancy')}\n"
            f"🍼 *Lactation:* {g('lactation_en','lactation')}\n"
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
        lines += [f"🍼 *جرعة الطفل - {n}*", f"⚖️ الوزن: {w} كغ", ""]
    else:
        lines += [f"🍼 *Child Dose - {n}*", f"⚖️ Weight: {w} kg", ""]
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
        # استخدام التركيز المحدد من المستخدم
        _user_conc = drug.get("concentration", "")
        if _user_conc and _user_conc != "unknown":
            import re as _re3
            _mc = _re3.search(r"([\d.]+)\s*mg\s*/\s*([\d.]+)\s*ml", _user_conc, _re3.IGNORECASE)
            if _mc: conc = float(_mc.group(1)) / float(_mc.group(2)) * 5
        # استخدام التركيز من الصورة إذا متوفر
        import builtins
        img_conc = getattr(builtins, "_last_concentration", None)
        if img_conc:
            mg_val, ml_val = img_conc
            conc_from_img = (mg_val / ml_val) * 5
            conc = conc_from_img
            builtins._last_concentration = None
            logger.info(f"Using image concentration: {mg_val}mg/{ml_val}ml = {conc}mg/5ml")

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

async def analyze_image(img_bytes, lang):
    if not HTTPX_OK or not ANTHROPIC_API_KEY:
        logger.warning("No API key")
        return ""
    b64 = base64.b64encode(img_bytes).decode()
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
                        {"type": "text", "text": "You are a pharmacist. Read this medicine packaging image carefully. IMPORTANT: Always respond in English only. Find the active ingredient generic name in English. Arabic to English: باراسيتامول=paracetamol, إيبوبروفين/نيوروفين=ibuprofen, أموكسيسيلين=amoxicillin, ميترونيدازول=metronidazole, سيتيريزين=cetirizine, لوراتادين=loratadine, أزيثروميسين=azithromycin, هيوسين=hyoscine_butylbromide, سالبيوتامول=salbutamol, ميتفورمين=metformin, كلاريثروميسين=clarithromycin. Step 1: Find the generic/active ingredient. Brand mappings: Panadol/Calpol/Tylenol=paracetamol, Nurofen/Brufen/Advil/نيوروفين/نيورفين=ibuprofen, Claritin/Claritine=loratadine, Glucophage=metformin, Scobinal/Buscopan/سكوبينال=hyoscine_butylbromide, Anazol/Flagyl/فلاجيل=metronidazole, Zithromax/زيثروماكس=azithromycin, Amoxil/أموكسيل=amoxicillin, Augmentin/أوجمنتين=amoxicillin_clavulanate, Zyrtec/زيرتيك=cetirizine, Ventolin/فنتولين=salbutamol, باراسيتامول/بنادول=paracetamol, إيبوبروفين/نيوروفين=ibuprofen, ميترونيدازول=metronidazole, أموكسيسيلين=amoxicillin, سيتيريزين=cetirizine, لوراتادين=loratadine, ميتفورمين=metformin, سالبيوتامول=salbutamol, كلاريثروميسين=clarithromycin, أزيثروميسين=azithromycin. Step 2: Find the EXACT concentration - look for patterns like: 120mg/5ml, 250mg/5ml, 100mg/5ml, 500mg, 200mg, 400mg/5ml, 125mg/5ml. For paracetamol syrups the common concentrations are 120mg/5ml (infant) or 250mg/5ml (child). For ibuprofen syrups: 100mg/5ml. Look very carefully at all numbers on the packaging. Return ONLY: GENERIC_NAME|CONCENTRATION. Examples: paracetamol|120mg/5ml, ibuprofen|100mg/5ml, metformin|500mg. If concentration truly not visible: GENERIC_NAME|unknown."}
                    ]}]})
        logger.info(f"Image API status: {r.status_code}")
        logger.info(f"Image API response: {r.text[:200]}")
        txt = r.json().get("content", [{}])[0].get("text", "").strip()
        import re as _re
        txt = txt.split("\n")[0].strip()
        logger.info(f"Raw image response: {txt}")
        ARABIC_MAP = {"باراسيتامول":"paracetamol","بنادول":"paracetamol","بانادول":"paracetamol","panadol":"paracetamol","إيبوبروفين":"ibuprofen","نيوروفين":"ibuprofen","nurofen":"ibuprofen","brufen":"ibuprofen","أموكسيسيلين":"amoxicillin","amoxil":"amoxicillin","ميترونيدازول":"metronidazole","فلاجيل":"metronidazole","أزيثروميسين":"azithromycin","زيثروماكس":"azithromycin","سيتيريزين":"cetirizine","زيرتيك":"cetirizine","لوراتادين":"loratadine","كلاريتين":"loratadine","هيوسين":"hyoscine_butylbromide","سكوبينال":"hyoscine_butylbromide","buscopan":"hyoscine_butylbromide","سالبيوتامول":"salbutamol","فنتولين":"salbutamol","ميتفورمين":"metformin","جلوكوفاج":"metformin","كلاريثروميسين":"clarithromycin","كلاسيد":"clarithromycin","بريدنيزولون":"prednisolone","أوندانسيترون":"ondansetron","زوفران":"ondansetron","فيفادول":"paracetamol","فيفا دول":"paracetamol","vifadol":"paracetamol","دومبي":"domperidone","dompy":"domperidone","dompé":"domperidone","سكوبينال":"hyoscine_butylbromide","scobinal":"hyoscine_butylbromide","hyoscine butylbromide":"hyoscine_butylbromide","نيوروفين":"ibuprofen","nurofen for children":"ibuprofen","فنتولين":"salbutamol","ventolin syrup":"salbutamol","salbutamol syrup":"salbutamol","أوجمنتين":"amoxicillin_clavulanate","augmentin":"amoxicillin_clavulanate","كلافوموكس":"amoxicillin_clavulanate","زيناتا":"cefuroxime","زينات":"cefuroxime"}
        for _k, _v in ARABIC_MAP.items():
            if _k in txt or _k.lower() in txt.lower():
                txt = _v
                break
                # بحث ذكي في الكلمات المُرجعة

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
        logger.error(f"Image error: {e}")
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

def load_all_reminders():
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

def get_rems(ctx):
    uid = str(ctx._user_id if hasattr(ctx, "_user_id") else
              ctx.effective_user.id if hasattr(ctx, "effective_user") and ctx.effective_user else "0")
    all_rems = load_all_reminders()
    if uid not in all_rems:
        all_rems[uid] = ctx.user_data.get("reminders", [])
    ctx.user_data["reminders"] = all_rems[uid]
    return ctx.user_data.setdefault("reminders", [])

def save_rems(ctx):
    try:
        uid = str(ctx.effective_user.id) if hasattr(ctx, "effective_user") and ctx.effective_user else "0"
        all_rems = load_all_reminders()
        all_rems[uid] = ctx.user_data.get("reminders", [])
        save_all_reminders(all_rems)
    except Exception as e:
        logger.error(f"save_rems error: {e}")

def fmt_rems(rems, lang):
    if not rems: return tx("no_rems", lang)
    lines = [tx("rems_title", lang)]
    for r in rems:
        suf = "x/يوم" if lang == "ar" else "x/day"
        lines.append(f"🔸 [{r['id']}] 💊 {r['drug']} — 🕐 {r['time']} — 🔁 {r['freq']}{suf}")
    return "\n".join(lines)

async def send_alert(ctx):
    d = ctx.job.data
    msg = tx("alert", d["lang"]).format(drug=d["drug"])
    await ctx.bot.send_message(d["chat_id"], msg, parse_mode=ParseMode.MARKDOWN)
    if os.path.exists(REMINDER_SOUND):
        try:
            with open(REMINDER_SOUND, "rb") as f:
                await ctx.bot.send_audio(d["chat_id"], f)
        except:
            pass

def sched(app, chat_id, drug, time_str, freq, lang):
    try:
        h, m = map(int, time_str.split(":"))
        now = datetime.now(TIMEZONE)
        first_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if first_time <= now:
            from datetime import timedelta
            first_time += timedelta(days=1)
        app.job_queue.run_repeating(
            send_alert,
            interval=3600 * (24 // max(freq, 1)),
            first=first_time,
            data={"chat_id": chat_id, "drug": drug, "lang": lang},
            name=f"rem_{chat_id}_{drug}")
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
        ctx.user_data.clear()
        await u.message.reply_text(tx("welcome", "ar"), reply_markup=kb_lang(), parse_mode=ParseMode.MARKDOWN)
        return STATE_LANGUAGE
    lang = get_lang(ctx)
    await show_main(u.message, lang)
    return STATE_MAIN_MENU

async def start(u, ctx):
    ctx.user_data.clear()
    await u.message.reply_text(tx("welcome", "ar"), reply_markup=kb_lang(), parse_mode=ParseMode.MARKDOWN)
    return STATE_LANGUAGE

async def pick_lang(u, ctx):
    q = u.callback_query; await q.answer()
    ctx.user_data["lang"] = "ar" if q.data == "lang_ar" else "en"
    await show_main(q.message, get_lang(ctx), edit=True)
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
    elif q.data == "m_settings":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(tx("change_lang", lang), callback_data="do_lang")],
            [InlineKeyboardButton(tx("btn_back", lang), callback_data="back")]])
        await q.message.edit_text(tx("settings", lang), reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        return STATE_MAIN_MENU
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
        await u.message.reply_text(tx("img_error", lang), reply_markup=kb_back(lang))
        return STATE_DRUG_SEARCH
    res = search_drugs(name)
    if not res:
        await u.message.reply_text("📸 " + name + chr(10) + chr(10) + tx("not_found", lang), reply_markup=kb_back(lang), parse_mode=ParseMode.MARKDOWN)
        return STATE_DRUG_SEARCH
    track(u, "searches")
    if len(res) == 1:
        await u.message.reply_text("📸 " + name + chr(10) + chr(10) + fmt_drug(res[0], lang), reply_markup=kb_back(lang), parse_mode=ParseMode.MARKDOWN)
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
    res = search_drugs(u.message.text)
    if not res:
        await u.message.reply_text(tx("not_found", lang), reply_markup=kb_back(lang))
        return STATE_DRUG_SEARCH
    if len(res) == 1:
        await u.message.reply_text(fmt_drug(res[0], lang), reply_markup=kb_back(lang), parse_mode=ParseMode.MARKDOWN_V2 if False else ParseMode.MARKDOWN)
        return STATE_DRUG_SEARCH
    ctx.user_data["results"] = res
    btns = [[InlineKeyboardButton(
        str(d.get("name_ar" if lang=="ar" else "name_en", d.get("name_en", "?"))),
        callback_data=f"ds_{i}")] for i, d in enumerate(res)]
    btns.append([InlineKeyboardButton(tx("btn_back", lang), callback_data="back")])
    await u.message.reply_text(tx("multi_results", lang), reply_markup=InlineKeyboardMarkup(btns))
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
    if u.message.photo:
        if not ANTHROPIC_API_KEY:
            await u.message.reply_text(tx("no_api", lang), reply_markup=kb_back(lang))
            return STATE_CHILD_DRUG
        msg = await u.message.reply_text(tx("analyzing", lang))
        photo = u.message.photo[-1]
        f = await photo.get_file()
        img = await f.download_as_bytearray()
        name = await analyze_image(bytes(img), lang)
        await msg.delete()
        if not name:
            await u.message.reply_text(tx("img_error", lang), reply_markup=kb_back(lang))
            return STATE_CHILD_DRUG
        res = search_drugs(name)
        if not res:
            await u.message.reply_text(f"📸 *{name}*\n\n" + tx("not_found", lang),
                reply_markup=kb_back(lang), parse_mode=ParseMode.MARKDOWN)
            return STATE_CHILD_DRUG
        ctx.user_data["child_drug"] = res[0]
        await u.message.reply_text(f"📸 *{name}*\n\n" + tx("weight_prompt", lang),
            reply_markup=kb_back(lang), parse_mode=ParseMode.MARKDOWN)
        return STATE_CHILD_WEIGHT
    res = search_drugs(u.message.text)
    if not res:
        await u.message.reply_text(tx("not_found", lang), reply_markup=kb_back(lang))
        return STATE_CHILD_DRUG
    if len(res) == 1:
        ctx.user_data["child_drug"] = res[0]
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
    lang = get_lang(ctx)
    track(u, "child_doses")
    try:
        w = float(u.message.text.strip().replace(",", "."))
        if not 0.5 <= w <= 150: raise ValueError
    except:
        await u.message.reply_text(tx("bad_weight", lang), reply_markup=kb_back(lang))
        return STATE_CHILD_WEIGHT
    d = ctx.user_data.get("child_drug")
    if not d:
        await show_main(u.message, lang)
        return STATE_MAIN_MENU
    ctx.user_data["child_weight"] = w
    # تراكيز شائعة لكل دواء
    DRUG_CONCS = {
        "paracetamol": ["120mg/5ml", "125mg/5ml", "160mg/5ml", "250mg/5ml"],
        "ibuprofen": ["100mg/5ml", "200mg/5ml"],
        "amoxicillin": ["125mg/5ml", "250mg/5ml"],
        "amoxicillin_clavulanate": ["125mg/5ml", "250mg/5ml", "457mg/5ml"],
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
    msg = "💊 اختر تركيز الشراب:" if lang == "ar" else "💊 Select concentration:"
    await u.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(btns))
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
    drug = ctx.user_data.get("nr_drug", "?")
    time_s = ctx.user_data.get("nr_time", "08:00")
    rems = get_rems(ctx)
    rems.append({"id": len(rems)+1, "drug": drug, "time": time_s, "freq": f})
    save_rems(ctx)
    sched(ctx.application, u.effective_chat.id, drug, time_s, f, lang)
    await u.message.reply_text(tx("rem_saved", lang).format(drug=drug, time=time_s, freq=f),
        reply_markup=kb_remind(lang))
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
    if not ctx.user_data.get("lang"):
        ctx.user_data.clear()
        await u.message.reply_text(tx("welcome", "ar"), reply_markup=kb_lang(), parse_mode=ParseMode.MARKDOWN)
        return STATE_LANGUAGE
    await show_main(u.message, get_lang(ctx))
    return STATE_MAIN_MENU

async def stats_cmd(u, ctx):
    stats = load_stats()
    users = len(stats.get("users", {}))
    searches = stats.get("searches", 0)
    child = stats.get("child_doses", 0)
    rems = stats.get("reminders", 0)
    total = stats.get("total_requests", 0)
    drugs = len(DRUGS_DB)
    lang = get_lang(ctx)
    if lang == "ar":
        lines = [
            "📊 *إحصائيات البوت*", "",
            f"👥 المستخدمون: *{users}*",
            f"💊 عدد الأدوية: *{drugs}*",
            f"🔍 عمليات البحث: *{searches}*",
            f"🍼 جرعات الأطفال: *{child}*",
            f"⏰ التذكيرات المضافة: *{rems}*",
            f"📈 إجمالي الطلبات: *{total}*",
        ]
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
            STATE_LANGUAGE: [
                CallbackQueryHandler(pick_lang, pattern="^lang_")],
            STATE_MAIN_MENU: [
                CallbackQueryHandler(go_back, pattern="^back$"),
                CallbackQueryHandler(main_cb, pattern="^(m_|do_lang|change_lang|pay_)")],
            STATE_BMI_WEIGHT: [
                CallbackQueryHandler(bmi_cb, pattern="^bmi_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, bmi_text)],
            STATE_BMI_DRUG: [
                CallbackQueryHandler(bmi_cb, pattern="^bmi_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, bmi_text)],
            STATE_DRUG_SEARCH: [
                CallbackQueryHandler(go_back, pattern="^back$"),
                CallbackQueryHandler(drug_sel, pattern="^ds_"),
                MessageHandler(filters.PHOTO, drug_search_image),
                MessageHandler(filters.TEXT & ~filters.COMMAND, drug_search)],
            STATE_CHILD_DRUG: [
                CallbackQueryHandler(go_back, pattern="^back$"),
                CallbackQueryHandler(child_sel, pattern="^cs_"),
                MessageHandler(filters.PHOTO, child_input),
                MessageHandler(filters.TEXT & ~filters.COMMAND, child_input)],
            STATE_CHILD_WEIGHT: [
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
            CommandHandler("start", start),
            CommandHandler("stats", stats_cmd),
            MessageHandler(filters.ALL, fallback)],
        allow_reentry=True,
        per_user=True,
        per_chat=True)

async def restore_reminders(app):
    """إعادة جدولة التذكيرات عند بدء التشغيل"""
    all_rems = load_all_reminders()
    count = 0
    for uid, rems in all_rems.items():
        for r in rems:
            try:
                lang = "ar"
                sched(app, int(uid), r["drug"], r["time"], r["freq"], lang)
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
    subs = load_subs()
    uid = str(user_id)
    if uid not in subs:
        return False
    expiry = datetime.fromisoformat(subs[uid]["expiry"])
    return expiry > datetime.now()

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
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(build_conv())
    app.add_handler(CommandHandler("stats", stats_cmd))
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
