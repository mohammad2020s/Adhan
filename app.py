from flask import Flask, render_template_string
import requests
from datetime import datetime

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>مواقيت الصلاة | Pro</title>
    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --accent: #38bdf8;
            --accent-glow: rgba(56, 189, 248, 0.4);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .header { text-align: center; margin-bottom: 20px; }
        .header h1 { color: var(--text-main); font-size: 24px; margin-bottom: 5px; }
        .header p { color: var(--text-muted); font-size: 14px; margin-top: 0; }
        
        /* تصميم العداد التنازلي */
        .countdown-container {
            background: linear-gradient(145deg, #1e293b, #0f172a);
            border: 1px solid #334155;
            border-radius: 20px;
            padding: 25px;
            text-align: center;
            width: 100%;
            max-width: 340px;
            margin-bottom: 30px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        }
        .countdown-title { color: var(--text-muted); font-size: 16px; margin-bottom: 10px; }
        .countdown-timer { font-size: 42px; font-weight: bold; color: var(--accent); letter-spacing: 2px; }
        .next-prayer-name { font-size: 22px; color: #fff; margin-top: 5px; font-weight: bold; }

        /* تصميم كروت الصلاة */
        .prayers-list { width: 100%; max-width: 360px; }
        .prayer-card {
            background-color: var(--card-bg);
            border-radius: 15px;
            padding: 18px 25px;
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 20px;
            font-weight: 600;
            transition: all 0.3s ease;
            border: 1px solid transparent;
        }
        .prayer-card span:last-child { color: var(--text-muted); font-size: 18px; }
        
        /* تأثير الصلاة القادمة */
        .prayer-card.active {
            border-color: var(--accent);
            box-shadow: 0 0 15px var(--accent-glow);
            transform: scale(1.02);
        }
        .prayer-card.active span { color: var(--accent); }
        .prayer-card.active span:last-child { color: var(--accent); font-weight: bold; }

        .footer { margin-top: 30px; color: #475569; font-size: 12px; }
    </style>
</head>
<body>

    <div class="header">
        <h1>مواقيت الصلاة</h1>
        <p>مدينة الرياض</p>
    </div>

    <!-- العداد التنازلي -->
    <div class="countdown-container">
        <div class="countdown-title">متبقي على أذان <span id="next-name" class="next-prayer-name">...</span></div>
        <div id="timer" class="countdown-timer">00:00:00</div>
    </div>

    <!-- قائمة الصلوات -->
    <div class="prayers-list">
        {% for name, time_12 in timings_12.items() %}
        <div class="prayer-card" id="card-{{ name }}">
            <span>{{ name }}</span>
            <span dir="ltr">{{ time_12 }}</span>
        </div>
        {% endfor %}
    </div>

    <div class="footer">تم البرمجة باحترافية | Pro Version</div>

    <script>
        // استيراد الأوقات بنظام 24 ساعة من بايثون لاستخدامها في الحسابات
        const timings24 = {{ timings_24 | tojson }};
        
        function updateCountdown() {
            const now = new Date();
            const currentHours = now.getHours();
            const currentMinutes = now.getMinutes();
            const currentSeconds = now.getSeconds();
            const currentTimeInSeconds = (currentHours * 3600) + (currentMinutes * 60) + currentSeconds;

            let nextPrayerName = "الفجر";
            let nextPrayerTimeInSeconds = 24 * 3600; // افتراضياً لليوم التالي
            let found = false;

            // البحث عن الصلاة القادمة
            for (const [name, time] of Object.entries(timings24)) {
                const [h, m] = time.split(':').map(Number);
                const prayerSeconds = (h * 3600) + (m * 60);
                
                if (prayerSeconds > currentTimeInSeconds) {
                    nextPrayerName = name;
                    nextPrayerTimeInSeconds = prayerSeconds;
                    found = true;
                    break;
                }
            }

            let diff;
            if (!found) {
                // إذا انتهت صلوات اليوم، نحسب الوقت حتى فجر اليوم التالي
                const [fajrH, fajrM] = timings24["الفجر"].split(':').map(Number);
                const fajrSeconds = (fajrH * 3600) + (fajrM * 60);
                diff = ((24 * 3600) - currentTimeInSeconds) + fajrSeconds;
                nextPrayerName = "الفجر";
            } else {
                diff = nextPrayerTimeInSeconds - currentTimeInSeconds;
            }

            // تحويل الفارق لـ ساعات، دقائق، ثواني
            const h = Math.floor(diff / 3600);
            const m = Math.floor((diff % 3600) / 60);
            const s = diff % 60;

            // تنسيق الأرقام لتكون بصيغة 00:00:00
            const formatNum = (num) => num < 10 ? '0' + num : num;
            
            // تحديث النصوص في الواجهة
            document.getElementById('timer').innerText = `${formatNum(h)}:${formatNum(m)}:${formatNum(s)}`;
            document.getElementById('next-name').innerText = nextPrayerName;

            // تمييز كرت الصلاة القادمة (إزالة التمييز عن الكل ثم إضافته للجديد)
            document.querySelectorAll('.prayer-card').forEach(card => card.classList.remove('active'));
            const activeCard = document.getElementById('card-' + nextPrayerName);
            if(activeCard) activeCard.classList.add('active');
        }

        // تحديث العداد كل ثانية
        setInterval(updateCountdown, 1000);
        updateCountdown(); // تشغيل فوري عند فتح الصفحة
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    url = "http://api.aladhan.com/v1/timingsByCity?city=Riyadh&country=Saudi Arabia&method=4"
    try:
        res = requests.get(url).json()
        raw_timings = res["data"]["timings"]
        
        prayers = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
        arabic_names = ["الفجر", "الظهر", "العصر", "المغرب", "العشاء"]
        
        timings_24 = {}
        timings_12 = {}
        
        for en_name, ar_name in zip(prayers, arabic_names):
            time_24 = raw_timings[en_name]
            # حفظ وقت 24 ساعة للعمليات الحسابية في الجافاسكربت
            timings_24[ar_name] = time_24
            
            # تحويل الوقت لصيغة 12 ساعة (ص/م) للعرض الاحترافي
            t_obj = datetime.strptime(time_24, "%H:%M")
            formatted_time = t_obj.strftime("%I:%M %p")
            # استبدال AM و PM بالعربي
            formatted_time = formatted_time.replace("AM", "ص").replace("PM", "م")
            # إزالة الصفر الذي يسبق الساعة إن وجد (مثلاً 03 تصير 3)
            if formatted_time.startswith("0"):
                formatted_time = formatted_time[1:]
                
            timings_12[ar_name] = formatted_time
            
        return render_template_string(HTML_TEMPLATE, timings_12=timings_12, timings_24=timings_24)
    except Exception as e:
        return f"<h2 style='color:red; text-align:center; padding: 50px;'>حدث خطأ في الاتصال بالخادم.</h2>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
