#!/data/data/com.termux/files/usr/bin/sh
while true; do
    cd ~/dose-bot
    python bot.py
    echo "إعادة تشغيل بعد 5 ثوان..."
    sleep 5
done
