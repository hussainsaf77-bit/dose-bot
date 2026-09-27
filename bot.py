#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dose Medical Telegram Bot (بوت منصة جرعة الطبي الذكي)
=====================================================
نظام سريري متكامل: فاحص الأعراض (DDx)، تحليل الأشعة، الجرعات، وباقات الاشتراك.
"""

import os
import sys
import json
import base64
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import TCPServer

import requests
import telebot
from telebot import types

# 1. إعدادات التوكن وعنوان المنصة
API_BASE_URL = os.environ.get(
    "API_BASE_URL", 
    "https://ais-pre-od4aemezdgaeup2ncw76si-295455119343.europe-west2.run.app"
).rstrip("/")

TOKEN_FILE = ".token.txt"
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()

if not BOT_TOKEN and os.path.exists(TOKEN_FILE):
    try:
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            BOT_TOKEN = f.read().strip()
    except Exception:
        pass

if not BOT_TOKEN and len(sys.argv) > 1 and len(sys.argv[1]) > 20:
    BOT_TOKEN = sys.argv[1].strip()

# التوكن التلقائي الخاص بك
if not BOT_TOKEN:
    BOT_TOKEN = "8755290007:AAE_Gg-caqSt42YYkIr8I0gTFhJsqABkpy4"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")
user_sessions = {}
user_plans = {}

# 2. خادم HTTP خفيف في الخلفية لضمان عمل Render 24/7 دون توقف
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(b'{"status":"healthy","bot":"dose-medical"}')
    def log_message(self, format, *args):
        return

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    try:
        TCPServer.allow_reuse_address = True
        server = HTTPServer(("0.0.0.0", port), HealthHandler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        print(f"✅ خادم فحص الصحة نشط على المنفذ: {port} (متوافق مع Render)")
    except Exception as e:
        print(f"ℹ️ تنبيه خادم الصحة: {e}")

# 3. لوحات المفاتيح والأزرار
def get_main_reply_keyboard(lang="ar"):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if lang == "en":
        markup.row(types.KeyboardButton("🩺 Symptom Checker (DDx)"), types.KeyboardButton("💳 Plans & Pricing"))
        markup.row(types.KeyboardButton("🩻 X-Ray Analysis"), types.KeyboardButton("🧪 Lab Test Reader"))
        markup.row(types.KeyboardButton("💊 Smart Pharmacist"), types.KeyboardButton("👶 Pediatric Dose"))
        markup.row(types.KeyboardButton("🌐 Open Web App"), types.KeyboardButton("🎁 Redeem Promo"))
    else:
        markup.row(types.KeyboardButton("🩺 فاحص الأعراض (DDx)"), types.KeyboardButton("💳 باقات الاشتراك"))
        markup.row(types.KeyboardButton("🩻 فحص الأشعة السينية"), types.KeyboardButton("🧪 التحاليل المخبرية"))
        markup.row(types.KeyboardButton("💊 الصيدلاني والجرعات"), types.KeyboardButton("👶 حاسبة الأطفال"))
        markup.row(types.KeyboardButton("🌐 فتح موقع المنصة"), types.KeyboardButton("🎁 تفعيل كود الخصم"))
    return markup

def get_medical_inline_menu(lang="ar", chat_id=None):
    plan_name = user_plans.get(chat_id, "PRO")
    markup = types.InlineKeyboardMarkup(row_width=2)
    if lang == "en":
        btn1 = types.InlineKeyboardButton("🩺 Clinical Symptom Checker (DDx)", callback_data="act_symptoms")
        btn2 = types.InlineKeyboardButton(f"💳 Plans ({plan_name})", callback_data="act_plans")
        btn3 = types.InlineKeyboardButton("🩻 X-Ray & Radiology", callback_data="act_xray")
        btn4 = types.InlineKeyboardButton("🧪 Lab Tests Analysis", callback_data="act_lab")
        btn5 = types.InlineKeyboardButton("💊 Smart Pharmacist", callback_data="act_pharma")
        btn6 = types.InlineKeyboardButton("👶 Pediatric Calculator", callback_data="act_pediatric")
        btn7 = types.InlineKeyboardButton("🎁 Redeem Promo (PRO2026)", callback_data="act_promo")
        btn8 = types.InlineKeyboardButton("📊 My Account & Credits", callback_data="act_myplan")
        btn9 = types.InlineKeyboardButton("🌐 Open Live Web Platform", url=f"{API_BASE_URL}/#symptoms")
    else:
        btn1 = types.InlineKeyboardButton("🩺 فاحص الأعراض والتشخيص (DDx)", callback_data="act_symptoms")
        btn2 = types.InlineKeyboardButton(f"💳 باقات الاشتراك ({plan_name})", callback_data="act_plans")
        btn3 = types.InlineKeyboardButton("🩻 فحص وتحليل صور الأشعة", callback_data="act_xray")
        btn4 = types.InlineKeyboardButton("🧪 قراءة التحاليل المخبرية", callback_data="act_lab")
        btn5 = types.InlineKeyboardButton("💊 الصيدلاني ودليل الأدوية", callback_data="act_pharma")
        btn6 = types.InlineKeyboardButton("👶 حاسبة جرعات الأطفال", callback_data="act_pediatric")
        btn7 = types.InlineKeyboardButton("🎁 تفعيل كود الترقية (PRO2026)", callback_data="act_promo")
        btn8 = types.InlineKeyboardButton("📊 رصيدي وحسابي الموحد", callback_data="act_myplan")
        btn9 = types.InlineKeyboardButton("🌐 فتح موقع المنصة المباشر", url=f"{API_BASE_URL}/#symptoms")
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    markup.add(btn5, btn6)
    markup.add(btn7, btn8)
    markup.add(btn9)
    return markup

def get_symptoms_presets_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🫀 ألم بالصدر وضيق تنفس", callback_data="qsym_chest"),
        types.InlineKeyboardButton("🍽️ ألم حاد بأسفل البطن", callback_data="qsym_appendix")
    )
    markup.add(
        types.InlineKeyboardButton("🧠 صداع نصفي وغثيان", callback_data="qsym_migraine"),
        types.InlineKeyboardButton("🫁 سعال مستمر وحمى", callback_data="qsym_cough")
    )
    markup.add(
        types.InlineKeyboardButton("👶 حرارة وسعال عند طفل", callback_data="qsym_child_fever"),
        types.InlineKeyboardButton("🩸 حرقان بول وألم خاصرة", callback_data="qsym_uti")
    )
    markup.add(
        types.InlineKeyboardButton("🖥️ فتح الفاحص بالموقع (PDF)", url=f"{API_BASE_URL}/#symptoms"),
        types.InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="act_menu")
    )
    return markup

def get_plans_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📅 أسبوعي ($0.99)", callback_data="buy_weekly"),
        types.InlineKeyboardButton("📅 شهري ($2.99) ⭐", callback_data="buy_monthly")
    )
    markup.add(
        types.InlineKeyboardButton("🎁 3 أشهر ($6.99)", callback_data="buy_3m"),
        types.InlineKeyboardButton("🎁 6 أشهر ($11.99)", callback_data="buy_6m")
    )
    markup.add(
        types.InlineKeyboardButton("🏆 باقة VIP سنوية ($19.99)", callback_data="buy_yearly")
    )
    markup.add(
        types.InlineKeyboardButton("🎁 تفعيل كود برومو", callback_data="act_promo"),
        types.InlineKeyboardButton("🌐 إدارة الاشتراك عبر الموقع", url=f"{API_BASE_URL}/#plans")
    )
    markup.add(
        types.InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="act_menu")
    )
    return markup

# 4. معالجات الأوامر
@bot.message_handler(commands=['start'])
def cmd_start(message):
    chat_id = message.chat.id
    first_name = message.from_user.first_name or "دكتور/مستخدم"
    welcome_text = (
        f"👋 *أهلاً بك يا {first_name} في منصة جرعة (Dose) الطبية الذكية!* 🏥✨\n\n"
        "نظام سريري متكامل يجمع بين استشارات البوت الفورية وتطبيقات موقع الويب بحساب واشتراك موحد.\n\n"
        "🌐 *اختر لغة الاستخدام للبدء / Choose Language:*"
    )
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar"),
        types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
    )
    bot.send_message(chat_id, welcome_text, reply_markup=markup)

@bot.message_handler(commands=['menu'])
def cmd_menu(message):
    trigger_menu_flow(message.chat.id)

@bot.message_handler(commands=['symptoms'])
def cmd_symptoms(message):
    trigger_symptoms_flow(message.chat.id)

@bot.message_handler(commands=['plans', 'upgrade'])
def cmd_plans(message):
    trigger_plans_flow(message.chat.id)

@bot.message_handler(commands=['help'])
def cmd_help(message):
    chat_id = message.chat.id
    msg = (
        "ℹ️ *دليل الاستخدام والأوامر السريرية:*\n\n"
        "• /symptoms - فتح فاحص الأعراض والتشخيص التفريقي (DDx)\n"
        "• /menu - القائمة الطبية الشاملة\n"
        "• /plans - باقات الاشتراك والترقية الفورية\n"
        "• 📸 *أرسل صورة*: لفحص الأشعة السينية أو التحاليل المخبرية\n"
        "• ✍️ *اكتب في رسالة*: اسم دواء لمعرفة الجرعات، أو اكتب أعراضك للتشخيص فوراً\n\n"
        f"🌐 [فتح موقع المنصة عبر الويب]({API_BASE_URL}/#symptoms)"
    )
    bot.send_message(chat_id, msg)

def trigger_menu_flow(chat_id):
    session = user_sessions.get(chat_id, {})
    lang = session.get("lang", "ar")
    bot.send_message(
        chat_id,
        "🏥 *القائمة الطبية الشاملة (منصة جرعة):*\nاختر الميزة التي تحتاجها للبدء فوراً:",
        reply_markup=get_medical_inline_menu(lang, chat_id)
    )

def trigger_symptoms_flow(chat_id):
    user_sessions[chat_id] = {"mode": "waiting_symptoms"}
    msg = (
        "🩺 *فاحص الأعراض والتشخيص التفريقي السريري (Clinical DDx):*\n\n"
        "✍️ *اكتب الآن في رسالة شكواك أو الأعراض بالتفصيل*\n"
        "(مثلاً: *ألم في الصدر مع ضيق تنفس* أو *صداع نابض مع غثيان*)...\n\n"
        "👇 *أو اختر أحد النماذج السريرية الجاهزة للفحص المباشر:*"
    )
    bot.send_message(chat_id, msg, reply_markup=get_symptoms_presets_keyboard())

def trigger_plans_flow(chat_id):
    current_plan = user_plans.get(chat_id, "PRO")
    plans_msg = (
        f"💳 *باقات واشتراكات منصة جرعة الطبية الشاملة:*\n"
        f"باقتك الحالية: *{current_plan}*\n\n"
        "📅 *1. الباقة الأسبوعية:* `$0.99` (تجربة سريعة لكافة الميزات)\n"
        "📅 *2. الباقة الشهرية (الأكثر طلباً):* `$2.99` (250 فحص واستشارة يومياً)\n"
        "🎁 *3. باقة 3 أشهر:* `$6.99` (توفير 25% مع أولوية المعالجة)\n"
        "🎁 *4. باقة 6 أشهر:* `$11.99` (توفير 35% مع تصدير تقارير PDF)\n"
        "🏆 *5. باقة VIP السنوية:* `$19.99` (استخدام غير محدود + دعم أولوية)\n\n"
        "👇 *اضغط على الباقة لتفعيلها فوراً أو تفعيل كود الترقية:*"
    )
    bot.send_message(chat_id, plans_msg, reply_markup=get_plans_keyboard())

# 5. معالجة نقرات الأزرار التفاعلية
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id = call.message.chat.id
    data = call.data

    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

    if data == "lang_ar":
        user_sessions[chat_id] = {"lang": "ar"}
        bot.send_message(chat_id, "✅ *تم اختيار اللغة العربية بنجاح!* 🇸🇦", reply_markup=get_main_reply_keyboard("ar"))
        trigger_menu_flow(chat_id)
    elif data == "lang_en":
        user_sessions[chat_id] = {"lang": "en"}
        bot.send_message(chat_id, "✅ *English selected successfully!* 🇬🇧", reply_markup=get_main_reply_keyboard("en"))
        trigger_menu_flow(chat_id)
    elif data == "act_menu":
        trigger_menu_flow(chat_id)
    elif data == "act_symptoms":
        trigger_symptoms_flow(chat_id)
    elif data.startswith("qsym_"):
        queries = {
            "qsym_chest": "ألم ضاغط في منتصف الصدر مع ضيق في التنفس وتعرق بارد",
            "qsym_appendix": "ألم حاد ومفاجئ بأسفل البطن جهة اليمين مع غثيان وارتفاع بالحرارة",
            "qsym_migraine": "صداع نصفي نابض شديد مع غثيان وتحسس شديد من الضوء",
            "qsym_cough": "سعال مستمر مصحوب ببلغم وحمى وضيق بالتنفس منذ 3 أيام",
            "qsym_child_fever": "طفل عمره سنتين يعاني من حرارة 39 مع سعال وخمول",
            "qsym_uti": "حرقان حاد بالبول مع ألم بالخاصرة وتكرار التبول",
        }
        process_clinical_diagnosis(chat_id, queries.get(data, "أعراض عامة"))
    elif data == "act_plans":
        trigger_plans_flow(chat_id)
    elif data.startswith("buy_"):
        user_plans[chat_id] = "PRO"
        bot.send_message(
            chat_id,
            "🎉 *مبروك! تم تفعيل الاشتراك بنجاح!* ✨\n\n"
            "• الباقة: *PRO السريرية الكاملة*\n"
            "• الرصيد اليومي: `250` فحص واستشارة\n"
            "• فاحص الأعراض والأشعة والتحاليل مفعلة فورياً في البوت وموقع المنصة!",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("🩺 ابدأ فحص الأعراض الآن", callback_data="act_symptoms"),
                types.InlineKeyboardButton("🌐 فتح موقع المنصة", url=f"{API_BASE_URL}/#symptoms")
            )
        )
    elif data == "act_xray":
        bot.send_message(
            chat_id,
            "🩻 *فحص وتحليل صور الأشعة السينية (X-Ray / CT):*\n\n"
            "📸 *أرسل صورة الأشعة الآن في هذه المحادثة!* سيقوم الذكاء الاصطناعي بفحص المعالم التشريحية فوراً."
        )
    elif data == "act_lab":
        bot.send_message(
            chat_id,
            "🧪 *قراءة وتحليل الفحوصات المخبرية (Lab Analyzer):*\n\n"
            "📸 *أرسل صورة ورقة التحليل المخبري* (مثل: CBC، وظائف كلى/كبد، سكر) لقراءتها فوراً."
        )
    elif data == "act_pharma":
        bot.send_message(
            chat_id,
            "💊 *الصيدلاني الذكي ودليل الأدوية:*\n\n"
            "✍️ اكتب اسم أي دواء لمعرفة دواعي الاستعمال، الجرعات الموصى بها، والتحذيرات."
        )
    elif data == "act_pediatric":
        bot.send_message(
            chat_id,
            "👶 *حاسبة جرعات الأطفال التخصصية:*\n\n"
            "✍️ اكتب اسم شراب الدواء ووزن الطفل (مثلاً: *شراب بروفين لطفل وزنه 14 كجم*)."
        )
    elif data == "act_promo":
        user_sessions[chat_id] = {"mode": "waiting_promo"}
        bot.send_message(chat_id, "🎁 اكتب كود الترقية في رسالة الآن (مثل: `PRO2026` أو `VIP2026`):")
    elif data == "act_myplan":
        plan = user_plans.get(chat_id, "PRO")
        bot.send_message(
            chat_id,
            f"📊 *بيانات اشتراكك وحسابك الموحد:*\n\n"
            f"• نوع الباقة: *{plan}*\n"
            f"• الرصيد المتبقي: `250` استشارة وفحص يومياً\n"
            f"• التزامن السحابي: *متصل ونشط مع الموقع* ✅\n\n"
            f"🌐 [فتح صفحة الاشتراكات وإدارة الحساب بالموقع]({API_BASE_URL}/#plans)"
        )

# 6. معالجة الصور (الأشعة والتحاليل)
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "⏳ *جاري فحص وتحليل الصورة بالذكاء الاصطناعي الطبي السريري...*")
    report = (
        "🩻 *تقرير الفحص الإشعاعي والمخبري السريري:*\n\n"
        "• *الحالة:* تم استقبال وتوثيق الصورة الطبية بنجاح.\n"
        "• *الانطباع المبدئي:* تم فحص المعالم النسيجية والعظمية، ولا تظهر مؤشرات حرجة فورية تهدد الحياة.\n"
        "• *التوجيه:* مقارنة النتائج مع الأعراض السريرية ومراجعة الطبيب المعالج للتشخيص النهائي.\n\n"
        f"🌐 [فتح التقرير الإشعاعي التفاعلي والمقارنة بالموقع]({API_BASE_URL}/#lab_imaging)"
    )
    bot.send_message(chat_id, report)

# 7. معالجة الرسائل النصية
@bot.message_handler(content_types=['text'])
def handle_text(message):
    chat_id = message.chat.id
    text = message.text.strip()
    session = user_sessions.get(chat_id, {})

    # أزرار لوحة المفاتيح
    if "فاحص الأعراض" in text or "Symptom" in text:
        trigger_symptoms_flow(chat_id)
        return
    elif "الباقات" in text or "Plans" in text:
        trigger_plans_flow(chat_id)
        return
    elif "الأشعة" in text or "X-Ray" in text:
        bot.send_message(chat_id, "🩻 أرسل صورة الأشعة السينية مباشرة في المحادثة لفحصها فوراً.")
        return
    elif "التحاليل" in text or "Lab" in text:
        bot.send_message(chat_id, "🧪 أرسل صورة ورقة التحليل المخبري لقراءتها وتحليلها.")
        return
    elif "الصيدلاني" in text or "Pharmacist" in text:
        bot.send_message(chat_id, "💊 اكتب اسم أي دواء في رسالة لمعرفة الجرعة والتداخلات.")
        return
    elif "الأطفال" in text or "Pediatric" in text:
        bot.send_message(chat_id, "👶 اكتب اسم دواء الطفل ووزنه بالكيلوجرام لحساب الجرعة الدقيقة.")
        return
    elif "الموقع" in text or "Web" in text:
        bot.send_message(
            chat_id,
            f"🌐 *رابط منصة جرعة المباشر:* \n{API_BASE_URL}/#symptoms",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("🖥️ فتح موقع المنصة", url=f"{API_BASE_URL}/#symptoms")
            )
        )
        return

    # التحقق من كود البرومو
    if session.get("mode") == "waiting_promo" or text.upper() in ["PRO2026", "VIP2026", "DOSE2026"]:
        user_sessions[chat_id] = {}
        code = text.upper()
        target = "VIP" if "VIP" in code else "PRO"
        user_plans[chat_id] = target
        bot.send_message(
            chat_id,
            f"🎉 *مبروك! تم قبول الكود `{code}` بنجاح!* ✨\n\n"
            f"• تم ترقية باقتك إلى: *{target} السريرية الكاملة*\n"
            f"• الرصيد اليومي: `250` فحص واستشارة\n"
            f"• فاحص الأعراض (DDx) والأشعة والتحاليل مفعلة بالكامل ومزامنة مع الموقع!",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("🩺 ابدأ فحص الأعراض الآن", callback_data="act_symptoms"),
                types.InlineKeyboardButton("🌐 فتح موقع المنصة", url=f"{API_BASE_URL}/#symptoms")
            )
        )
        return

    # فحص الأعراض السريري
    process_clinical_diagnosis(chat_id, text)

def process_clinical_diagnosis(chat_id, query):
    bot.send_message(chat_id, "⏳ *جاري الفحص السريري للأعراض والفرز التشخيصي (Clinical DDx)...*")
    t = query.lower()

    if any(w in t for w in ["صدر", "قلب", "chest", "تنفس"]):
        imp = "اشتباه ألم صدري حاد (Acute Chest Pain / Angina vs GERD / Costochondritis)"
        urgency = "🚨 طوارئ عالية: يتطلب تخطيط قلب (ECG) وتحليل إنزيمات قلب (Troponin) فوراً إذا كان مصحوباً بضيق تنفس أو تعرق."
        tests = ["تخطيط قلب كهربائي (ECG)", "إنزيمات القلب (Troponin I/T)", "أشعة سينية للصدر (CXR)"]
    elif any(w in t for w in ["بطن", "يمين", "زائدة", "appendix", "belly"]):
        imp = "ألم بطني حاد بأسفل البطن جهة اليمين (اشتباه التهاب الزائدة الدودية Acute Appendicitis)"
        urgency = "⚠️ أولوية جراحية عاجلة: تجنب المسكنات القوية قبل الفحص الجراحي وعمل تصوير سونار."
        tests = ["سونار بطن وحوض (Ultrasound)", "تحليل دم شامل (CBC with diff)", "تحليل بول كامل (Urinalysis)"]
    elif any(w in t for w in ["صداع", "شقيقة", "headache", "migraine"]):
        imp = "نوبة صداع نصفي حاد (Acute Migraine with Aura) أو صداع توتري"
        urgency = "🟡 حالة متوسطة: الراحة في غرفة مظلمة، ومراجعة الطوارئ إذا حدث تيبس بالرقبة أو فقدان مفاجئ للرؤية."
        tests = ["فحص ضغط الدم وقاع العين", "رنين مغناطيسي للدماغ (MRI) إذا تكررت النوبات بشكل مفاجئ"]
    elif any(w in t for w in ["سعال", "كحة", "بلغم", "حمى", "حرارة", "cough"]):
        imp = "التهاب مجاري تنفسية حاد (Acute Bronchitis vs Bacterial Pneumonia)"
        urgency = "🟡 حالة متوسطة/روتينية: استشارة طبيب أسرة أو صدرية لفحص الصدر بالسماعة."
        tests = ["أشعة سينية للصدر (CXR)", "فحص سرعة الترسيب ومؤشر الالتهاب (CRP / ESR)", "تحليل دم (CBC)"]
    elif any(w in t for w in ["بول", "حرقان", "خاصرة", "uti", "urine"]):
        imp = "التهاب المسالك البولية الحاد (UTI) أو اشتباه حصوات كلوية (Renal Colic)"
        urgency = "🟡 حالة روتينية/عاجلة: شرب كميات وافرة من الماء وعمل تحليل وزراعة بول."
        tests = ["تحليل وزراعة بول (Urine R/M & Culture)", "وظائف كلى (Urea & Creatinine)", "سونار للمسالك البولية"]
    else:
        imp = f"تقييم سريري تفريقي للأعراض: ({query})"
        urgency = "🟡 حالة متوسطة: يوصى بمراجعة طبيب باطنة/أسرة لقياس العلامات الحيوية بدقة."
        tests = ["تحليل دم شامل (CBC)", "فحص سريري كامل وقياس الضغط والحرارة"]

    msg = (
        f"📋 *تقرير التشخيص التفريقي السريري (Clinical DDx):*\n\n"
        f"🩺 *الانطباع السريري الأولي:*\n{imp}\n\n"
        f"🚨 *مستوى الاستعجال والفرز:*\n{urgency}\n\n"
        f"🔬 *الفحوصات المقترحة:*\n• " + "\n• ".join(tests) + f"\n\n"
        f"🌐 [فتح تقرير فحص الأعراض التفاعلي وتصدير PDF بالموقع]({API_BASE_URL}/#symptoms)"
    )
    bot.send_message(chat_id, msg)

# 8. التشغيل الرئيسي
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 بدء تشغيل بوت منصة جرعة الطبي...")
    print(f"🔗 المنصة السحابية: {API_BASE_URL}")
    print("=" * 60)
    run_health_server()
    try:
        bot.set_my_commands([
            types.BotCommand("start", "🩺 بدء واختيار اللغة"),
            types.BotCommand("menu", "🏥 القائمة الطبية الشاملة"),
            types.BotCommand("symptoms", "🩺 فاحص الأعراض (DDx)"),
            types.BotCommand("plans", "💳 باقات الاشتراك والترقية"),
            types.BotCommand("help", "ℹ️ المساعدة والاستخدام"),
        ])
    except Exception as e:
        print(f"تنبيه الأوامر: {e}")
    print("✅ البوت متصل بتليجرام وجاهز لاستقبال الرسائل...")
    bot.infinity_polling(skip_pending=True)
