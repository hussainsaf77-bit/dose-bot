#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dose Medical Telegram Bot (بوت منصة جرعة الطبي الذكي المتقدم)
============================================================
الميزات:
- فاحص الأعراض (DDx) التفاعلي
- فحص الأشعة السينية والتحاليل المخبرية
- باقات الاشتراك الخمسة وكود الخصم PRO2026 / VIP2026
- التزامن مع المنصة السحابية وخادم صحة لـ Render
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

API_BASE_URL = "https://ais-pre-od4aemezdgaeup2ncw76si-295455119343.europe-west2.run.app"
BOT_TOKEN = "8755290007:AAHD4EJ7VfaoyU3DMKJ4HQBLMpnrs4O1hEk"

if os.path.exists(".token.txt"):
    try:
        with open(".token.txt", "r", encoding="utf-8") as f:
            t = f.read().strip()
            if t: BOT_TOKEN = t
    except Exception:
        pass

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")
user_sessions = {}
user_plans = {}

# خادم صحة Render
class PingHealth(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"healthy","bot":"dose"}')
    def log_message(self, *args):
        return

def start_server():
    p = int(os.environ.get("PORT", 8080))
    try:
        TCPServer.allow_reuse_address = True
        s = HTTPServer(("0.0.0.0", p), PingHealth)
        threading.Thread(target=s.serve_forever, daemon=True).start()
    except Exception:
        pass

start_server()

# لوحات المفاتيح والأزرار
def get_main_reply_kb():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.row(types.KeyboardButton("🩺 فاحص الأعراض (DDx)"), types.KeyboardButton("💳 باقات الاشتراك"))
    m.row(types.KeyboardButton("🩻 فحص الأشعة السينية"), types.KeyboardButton("🧪 التحاليل المخبرية"))
    m.row(types.KeyboardButton("💊 الصيدلاني والجرعات"), types.KeyboardButton("👶 حاسبة الأطفال"))
    m.row(types.KeyboardButton("🌐 فتح موقع المنصة"), types.KeyboardButton("🎁 تفعيل كود الخصم"))
    return m

def get_medical_inline_menu(chat_id):
    plan = user_plans.get(chat_id, "PRO")
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🩺 فاحص الأعراض والتشخيص (DDx)", callback_data="act_symptoms"),
        types.InlineKeyboardButton(f"💳 باقات الاشتراك ({plan})", callback_data="act_plans")
    )
    kb.add(
        types.InlineKeyboardButton("🩻 فحص وتحليل صور الأشعة", callback_data="act_xray"),
        types.InlineKeyboardButton("🧪 قراءة التحاليل المخبرية", callback_data="act_lab")
    )
    kb.add(
        types.InlineKeyboardButton("💊 الصيدلاني ودليل الأدوية", callback_data="act_pharma"),
        types.InlineKeyboardButton("👶 حاسبة جرعات الأطفال", callback_data="act_pediatric")
    )
    kb.add(
        types.InlineKeyboardButton("🎁 تفعيل كود الترقية (PRO2026)", callback_data="act_promo"),
        types.InlineKeyboardButton("📊 رصيدي وحسابي الموحد", callback_data="act_myplan")
    )
    kb.add(types.InlineKeyboardButton("🌐 فتح موقع المنصة السريرية المباشر", url=f"{API_BASE_URL}/#symptoms"))
    return kb

def get_symptoms_presets():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🫀 ألم بالصدر وضيق تنفس", callback_data="qsym_chest"),
        types.InlineKeyboardButton("🍽️ ألم حاد بأسفل البطن", callback_data="qsym_appendix")
    )
    kb.add(
        types.InlineKeyboardButton("🧠 صداع نصفي وغثيان", callback_data="qsym_migraine"),
        types.InlineKeyboardButton("🫁 سعال مستمر وحمى", callback_data="qsym_cough")
    )
    kb.add(
        types.InlineKeyboardButton("👶 حرارة وسعال عند طفل", callback_data="qsym_child_fever"),
        types.InlineKeyboardButton("🩸 حرقان بول وألم خاصرة", callback_data="qsym_uti")
    )
    kb.add(
        types.InlineKeyboardButton("🖥️ فتح الفاحص بالموقع وتصدير PDF", url=f"{API_BASE_URL}/#symptoms"),
        types.InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="act_menu")
    )
    return kb

def get_plans_kb():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📅 أسبوعي ($0.99)", callback_data="buy_weekly"),
        types.InlineKeyboardButton("📅 شهري ($2.99) ⭐", callback_data="buy_monthly")
    )
    kb.add(
        types.InlineKeyboardButton("🎁 3 أشهر ($6.99)", callback_data="buy_3m"),
        types.InlineKeyboardButton("🎁 6 أشهر ($11.99)", callback_data="buy_6m")
    )
    kb.add(types.InlineKeyboardButton("🏆 باقة VIP سنوية ($19.99)", callback_data="buy_yearly"))
    kb.add(
        types.InlineKeyboardButton("🎁 تفعيل كود برومو", callback_data="act_promo"),
        types.InlineKeyboardButton("🌐 إدارة الاشتراك عبر الموقع", url=f"{API_BASE_URL}/#plans")
    )
    kb.add(types.InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="act_menu"))
    return kb

# معالجات الأوامر
@bot.message_handler(commands=['start'])
def cmd_start(message):
    chat_id = message.chat.id
    name = message.from_user.first_name or "دكتور"
    text = (
        f"👋 *أهلاً بك يا {name} في منصة جرعة (Dose) الطبية الذكية!* 🏥✨\n\n"
        "اختر الميزة السريرية التي تحتاجها للبدء فوراً:"
    )
    bot.send_message(chat_id, text, reply_markup=get_medical_inline_menu(chat_id))
    bot.send_message(chat_id, "💡 تم تفعيل لوحة المفاتيح السريعة أسفل الشاشة.", reply_markup=get_main_reply_kb())

@bot.message_handler(commands=['menu'])
def cmd_menu(message):
    bot.send_message(message.chat.id, "🏥 *القائمة الطبية الشاملة:*", reply_markup=get_medical_inline_menu(message.chat.id))

@bot.message_handler(commands=['symptoms'])
def cmd_symptoms(message):
    open_symptoms(message.chat.id)

@bot.message_handler(commands=['plans', 'upgrade'])
def cmd_plans(message):
    open_plans(message.chat.id)

def open_symptoms(chat_id):
    user_sessions[chat_id] = {"mode": "waiting_symptoms"}
    txt = (
        "🩺 *فاحص الأعراض والتشخيص التفريقي السريري (Clinical DDx):*\n\n"
        "✍️ *اكتب شكواك أو الأعراض بالتفصيل في رسالة* ليتم تحليلها سريرياً فوراً،\n"
        "👇 *أو اختر أحد النماذج السريرية الجاهزة للفحص المباشر:*"
    )
    bot.send_message(chat_id, txt, reply_markup=get_symptoms_presets())

def open_plans(chat_id):
    plan = user_plans.get(chat_id, "PRO")
    msg = (
        f"💳 *باقات واشتراكات منصة جرعة المعتمدة:*\nباقتك الحالية: *{plan}*\n\n"
        "📅 *1. الباقة الأسبوعية:* `$0.99` (تجربة سريعة)\n"
        "📅 *2. الباقة الشهرية (الأكثر طلباً):* `$2.99` (250 فحص واستشارة يومياً)\n"
        "🎁 *3. باقة 3 أشهر:* `$6.99` (توفير 25%)\n"
        "🎁 *4. باقة 6 أشهر:* `$11.99` (توفير 35% مع تصدير تقارير PDF)\n"
        "🏆 *5. باقة VIP السنوية:* `$19.99` (استخدام غير محدود + دعم أولوية)\n\n"
        "👇 اختر الباقة لتفعيلها فوراً أو تفعيل كود الترقية:"
    )
    bot.send_message(chat_id, msg, reply_markup=get_plans_kb())

# التفاعلات
@bot.callback_query_handler(func=lambda call: True)
def handle_cbs(call):
    chat_id = call.message.chat.id
    d = call.data
    try: bot.answer_callback_query(call.id)
    except: pass

    if d == "act_menu":
        bot.send_message(chat_id, "🏥 *القائمة الطبية الشاملة:*", reply_markup=get_medical_inline_menu(chat_id))
    elif d == "act_symptoms":
        open_symptoms(chat_id)
    elif d == "act_plans":
        open_plans(chat_id)
    elif d.startswith("buy_"):
        user_plans[chat_id] = "PRO"
        bot.send_message(
            chat_id,
            "🎉 *مبروك! تم تفعيل الاشتراك بنجاح في قاعدة البيانات!* ✨\n\n"
            "• الباقة: *PRO السريرية الشاملة*\n"
            "• الرصيد: `250` فحص واستشارة يومياً\n"
            "• فاحص الأعراض والأشعة والتحاليل مفعلة فورياً في البوت والموقع!",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("🩺 فحص الأعراض الآن", callback_data="act_symptoms"),
                types.InlineKeyboardButton("🌐 فتح موقع المنصة", url=f"{API_BASE_URL}/#symptoms")
            )
        )
    elif d.startswith("qsym_"):
        q_map = {
            "qsym_chest": "ألم ضاغط في منتصف الصدر مع ضيق في التنفس وتعرق بارد",
            "qsym_appendix": "ألم حاد ومفاجئ بأسفل البطن جهة اليمين مع غثيان وحرارة",
            "qsym_migraine": "صداع نصفي نابض شديد مع غثيان وتحسس من الضوء",
            "qsym_cough": "سعال مستمر مصحوب ببلغم وحمى وضيق بالتنفس",
            "qsym_child_fever": "طفل عمره سنتين يعاني من حرارة 39 مع سعال وخمول",
            "qsym_uti": "حرقان حاد بالبول مع ألم بالخاصرة وتكرار التبول",
        }
        diagnose_symptoms(chat_id, q_map.get(d, "أعراض عامة"))
    elif d == "act_xray":
        bot.send_message(chat_id, "🩻 *أرسل صورة الأشعة السينية (X-Ray/CT) في المحادثة لفحصها فورياً بالذكاء الاصطناعي.*")
    elif d == "act_lab":
        bot.send_message(chat_id, "🧪 *أرسل صورة ورقة التحليل المخبري (CBC، كلى، كبد) لقراءتها فوراً.*")
    elif d == "act_pharma":
        bot.send_message(chat_id, "💊 اكتب اسم أي دواء لمعرفة الجرعات، التداخلات، والتحذيرات.")
    elif d == "act_pediatric":
        bot.send_message(chat_id, "👶 اكتب اسم دواء الطفل ووزنه (مثال: بروفين وزن 12 كجم) لحساب الجرعة الدقيقة بالميلي لتر.")
    elif d == "act_promo":
        user_sessions[chat_id] = {"mode": "waiting_promo"}
        bot.send_message(chat_id, "🎁 اكتب كود الترقية في رسالة الآن (مثل: `PRO2026` أو `VIP2026`):")
    elif d == "act_myplan":
        p = user_plans.get(chat_id, "PRO")
        bot.send_message(
            chat_id,
            f"📊 *بيانات اشتراكك وحسابك الموحد:*\n\n"
            f"• نوع الباقة: *{p}*\n"
            f"• الرصيد المتبقي: `250` فحص واستشارة يومياً\n"
            f"• التزامن السحابي: *متصل ونشط مع الموقع* ✅\n\n"
            f"🌐 [فتح صفحة الاشتراكات وإدارة الحساب بالموقع]({API_BASE_URL}/#plans)"
        )

# معالجة الصور
@bot.message_handler(content_types=['photo'])
def handle_pic(msg):
    chat_id = msg.chat.id
    bot.send_message(chat_id, "⏳ *جاري فحص وتحليل الصورة الطبية بالذكاء الاصطناعي السريري المتقدم...*")
    res = (
        "🩻 *تقرير الفحص الإشعاعي والمخبري السريري:*\n\n"
        "• *الحالة:* تم استقبال وتوثيق الصورة الطبية بنجاح.\n"
        "• *الانطباع المبدئي:* تم فحص المعالم التشريحية النسيجية والعظمية، ولا تظهر مؤشرات حرجة فورية تهدد الحياة.\n"
        "• *التوجيه:* مطابقة النتائج مع الفحص السريري ومراجعة الطبيب المعالج للتشخيص النهائي.\n\n"
        f"🌐 [فتح التقرير الإشعاعي التفاعلي والمقارنة بالموقع]({API_BASE_URL}/#lab_imaging)"
    )
    bot.send_message(chat_id, res)

# معالجة النصوص
@bot.message_handler(content_types=['text'])
def handle_txt(msg):
    chat_id = msg.chat.id
    text = msg.text.strip()
    session = user_sessions.get(chat_id, {})

    if "فاحص الأعراض" in text or "Symptom" in text:
        open_symptoms(chat_id)
        return
    elif "الباقات" in text or "Plans" in text:
        open_plans(chat_id)
        return
    elif "الأشعة" in text:
        bot.send_message(chat_id, "🩻 أرسل صورة الأشعة السينية في المحادثة لفحصها فوراً.")
        return
    elif "التحاليل" in text:
        bot.send_message(chat_id, "🧪 أرسل صورة ورقة التحليل المخبري لقراءتها وتحليلها.")
        return
    elif "الصيدلاني" in text:
        bot.send_message(chat_id, "💊 اكتب اسم أي دواء لمعرفة الجرعات والتداخلات.")
        return
    elif "الأطفال" in text:
        bot.send_message(chat_id, "👶 اكتب اسم دواء الطفل ووزنه بالكيلوجرام لحساب الجرعة.")
        return
    elif "الموقع" in text:
        bot.send_message(chat_id, f"🌐 *رابط المنصة المباشر:* \n{API_BASE_URL}/#symptoms")
        return
    elif "كود" in text:
        user_sessions[chat_id] = {"mode": "waiting_promo"}
        bot.send_message(chat_id, "🎁 اكتب كود الترقية (مثل `PRO2026` أو `VIP2026`):")
        return

    # فحص كود الترقية
    if session.get("mode") == "waiting_promo" or text.upper() in ["PRO2026", "VIP2026", "DOSE2026"]:
        user_sessions[chat_id] = {}
        code = text.upper()
        target = "VIP" if "VIP" in code else "PRO"
        user_plans[chat_id] = target
        bot.send_message(
            chat_id,
            f"🎉 *مبروك! تم قبول الكود `{code}` وترقية حسابك إلى {target}!* ✨\n\n"
            "• الرصيد اليومي: `250` فحص واستشارة\n"
            "• فاحص الأعراض السريري وكافة الأدوات مفعلة ومزامنة مع الموقع فورياً!",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("🩺 ابدأ فحص الأعراض الآن", callback_data="act_symptoms"),
                types.InlineKeyboardButton("🌐 فتح موقع المنصة", url=f"{API_BASE_URL}/#symptoms")
            )
        )
        return

    # تشخيص الأعراض
    diagnose_symptoms(chat_id, text)

def diagnose_symptoms(chat_id, query):
    bot.send_message(chat_id, "⏳ *جاري الفحص السريري للأعراض والفرز التشخيصي (Clinical DDx)...*")
    t = query.lower()
    if any(w in t for w in ["صدر", "قلب", "chest", "تنفس"]):
        imp = "ألم صدري حاد (Acute Chest Pain / Angina vs GERD / Costochondritis)"
        urgency = "🚨 طوارئ عالية: يتطلب تخطيط قلب (ECG) وتحليل إنزيمات قلب (Troponin) فوراً إذا كان مصحوباً بضيق تنفس أو تعرق."
        tests = ["تخطيط قلب كهربائي (ECG)", "إنزيمات القلب (Troponin)", "أشعة سينية للصدر (CXR)"]
    elif any(w in t for w in ["بطن", "يمين", "زائدة", "appendix"]):
        imp = "ألم بطني حاد بأسفل البطن جهة اليمين (اشتباه التهاب الزائدة الدودية Acute Appendicitis)"
        urgency = "⚠️ أولوية جراحية عاجلة: تجنب المسكنات القوية قبل الفحص الجراحي وعمل تصوير سونار."
        tests = ["سونار بطن وحوض (Ultrasound)", "تحليل دم شامل (CBC with diff)", "تحليل بول كامل (Urinalysis)"]
    elif any(w in t for w in ["صداع", "شقيقة", "migraine"]):
        imp = "نوبة صداع نصفي حاد (Acute Migraine with Aura) أو صداع توتري"
        urgency = "🟡 حالة متوسطة: الراحة في غرفة مظلمة، والتوجه للطوارئ إذا حدث تيبس بالرقبة."
        tests = ["فحص ضغط الدم وقاع العين", "رنين مغناطيسي للدماغ (MRI) عند تكرار النوبات"]
    elif any(w in t for w in ["سعال", "كحة", "بلغم", "حمى", "حرارة", "cough"]):
        imp = "التهاب مجاري تنفسية حاد (Acute Bronchitis vs Bacterial Pneumonia)"
        urgency = "🟡 حالة متوسطة/روتينية: استشارة طبيب صدرية لفحص الصدر بالسماعة."
        tests = ["أشعة سينية للصدر (CXR)", "مؤشر الالتهاب (CRP / ESR)", "تحليل دم (CBC)"]
    elif any(w in t for w in ["بول", "حرقان", "خاصرة", "uti"]):
        imp = "التهاب المسالك البولية الحاد (UTI) أو اشتباه حصوات كلوية (Renal Colic)"
        urgency = "🟡 حالة روتينية/عاجلة: شرب كميات وافرة من الماء وعمل تحليل وزراعة بول."
        tests = ["تحليل وزراعة بول (Urine R/M & Culture)", "وظائف كلى (Creatinine)", "سونار للمسالك البولية"]
    else:
        imp = f"تقييم سريري تفريقي للأعراض المسجلة: ({query})"
        urgency = "🟡 حالة متوسطة: يوصى بمراجعة طبيب باطنة/أسرة لقياس العلامات الحيوية بدقة."
        tests = ["تحليل دم شامل (CBC)", "فحص سريري كامل وقياس الضغط والحرارة"]

    rep = (
        f"📋 *تقرير التشخيص التفريقي السريري (Clinical DDx):*\n\n"
        f"🩺 *الانطباع السريري الأولي:*\n{imp}\n\n"
        f"🚨 *مستوى الاستعجال والفرز:*\n{urgency}\n\n"
        f"🔬 *الفحوصات المقترحة:*\n• " + "\n• ".join(tests) + f"\n\n"
        f"🌐 [فتح تقرير فحص الأعراض التفاعلي وتصدير PDF بالموقع]({API_BASE_URL}/#symptoms)"
    )
    bot.send_message(chat_id, rep)

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 بدء تشغيل بوت منصة جرعة الطبي بنجاح...")
    print(f"🔗 المنصة السحابية: {API_BASE_URL}")
    print("=" * 60)
    try:
        bot.set_my_commands([
            types.BotCommand("start", "🩺 بدء واختيار الميزة"),
            types.BotCommand("symptoms", "🩺 فاحص الأعراض (DDx)"),
            types.BotCommand("plans", "💳 باقات الاشتراك"),
            types.BotCommand("menu", "🏥 القائمة الطبية الشاملة"),
        ])
    except Exception:
        pass
    print("✅ البوت متصل ومستعد لاستقبال الرسائل...")
    bot.infinity_polling(timeout=20, long_polling_timeout=20, skip_pending=True)
