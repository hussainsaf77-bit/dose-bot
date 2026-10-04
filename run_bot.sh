python -c "
import time, telebot
from bot import bot

print('🚀 جاري بدء بوت منصة جرعة بنظام الحماية ضد التقطيع...')

while True:
    try:
        bot.polling(none_stop=True, interval=1, timeout=25)
    except Exception as e:
        print(f'⚠️ انقطاع مؤقت في شبكة الهاتف ({e})، جاري إعادة الاتصال خلال 3 ثوانٍ...')
        time.sleep(3)
"
