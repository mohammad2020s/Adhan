from flask import Flask, render_template_string, request
import requests
from datetime import datetime

app = Flask(__name__)

# قائمة المدن المتاحة (الاسم بالعربي : الاسم بالإنجليزي للـ API)
SAUDI_CITIES = {
    "الرياض": "Riyadh",
    "شقراء": "Shaqra",
    "مكة المكرمة": "Makkah",
    "المدينة المنورة": "Madinah",
    "جدة": "Jeddah",
    "الدمام": "Dammam",
    "بريدة": "Buraidah",
    "تبوك": "Tabuk",
    "أبها": "Abha",
    "الطائف": "Taif",
    "حائل": "Hail"
}

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
        .header h1 { color: var(--text-main); font-size: 26px; margin-bottom: 15px; }
        
        /* تصميم قائمة اختيار المدينة */
        .city-form { margin-bottom: 25px; }
        .city-select {
            background-color: var(--card-bg);
            color: var(--text-main);
            border: 2px solid #334155;
            padding: 10px 20px;
            border-radius: 12px;
            font-size: 18px;
            font-family: inherit;
            font-weight: bold;
            outline: none;
            cursor: pointer;
            width: 250px;
            text-align: center;
            appearance: none; /* إخفاء سهم المتصفح الافتراضي */
            -webkit-appearance: none;
            background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2338bdf8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
            background-repeat: no-repeat;
            background-position: left 15px center;
            background-size: 18px;
            transition: all 0.3s ease;
        }
        .city-select:hover, .city-select:focus {
            border-color: var(--accent);
            box-shadow: 0 0 10px var(--accent-glow);
        }
        
        /* تصميم العداد التنازلي */
        .countdown-container {
            background: linear-gradient(145deg, #1e293b, #0f172a);
            border: 1px solid #334155;
            border-radius: 20px;
            padding: 20px;
            text-align: center;
            width: 100%;
            max-width: 320px;
            margin-bottom: 25px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        }
        .countdown-title { color: var(--text-muted); font-size: 16px; margin-bottom: 5px; }
        .countdown-timer { font-size: 42px; font-weight: bold; color: var(--accent); letter-spacing: 2px; }
        .next-prayer-name { font-size: 22px; color: #fff; font-weight: bold; }

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
        .prayer-card span:last-child { color: var(--text-muted); font-size: 18px; direction: ltr; }
        
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
        
        <!-- القائمة المنسدلة لاختيار المدينة -->
        <form method="GET" action="/" id="city-form" class="city-form">
            <select name="city" class="city-select" onchange="document.getElementById('city-form').submit();">
                {% for ar_name, en_name in cities.items() %}
                    <option value="{{ en_name }}" {% if selected_city == en_name %}selected{% endif %}>
                        {{ ar_name }}
                    </option>
                {% endfor %}
            </select>
        </form>
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
            <span>{{ time_12 }}</span>
        </div>
        {% endfor %}
    </div>

    <div class="footer">تم البرمجة باحترافية | Pro Version</div>

    <script>
        const timings24 = {{ timings_24 | tojson }};
        
        function updateCountdown() {
            const now = new Date();
            const currentHours = now.getHours();
            const currentMinutes = now.getMinutes();
            const currentSeconds = now.getSeconds();
            const currentTimeInSeconds = (currentHours * 3600) + (currentMinutes * 60) + currentSeconds;

            let nextPrayerName = "الفجر";
            let nextPrayerTimeInSeconds = 24 * 3600;
            let found = false;

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
                const [fajrH, fajrM] = timings24["الفجر"].split(':').map(Number);
                const fajrSeconds = (fajrH * 3600) + (fajrM * 60);
                diff = ((24 * 3600) - currentTimeInSeconds) + fajrSeconds;
                nextPrayerName = "الفجر";
            } else {
                diff = nextPrayerTimeInSeconds - currentTimeInSeconds;
            }

            const h = Math.floor(diff / 3600);
            const m = Math.floor((diff % 3600) / 60);
            const s = diff % 60;

            const formatNum = (num) => num < 10 ? '0' + num : num;
            
            document.getElementById('timer').innerText = `${formatNum(h)}:${formatNum(m)}:${formatNum(s)}`;
            document.getElementById('next-name').innerText = nextPrayerName;

            document.querySelectorAll('.prayer-card').forEach(card => card.classList.remove('active'));
            const activeCard = document.getElementById('card-' + nextPrayerName);
            if(activeCard) activeCard.classList.add('active');
        }

        setInterval(updateCountdown, 1000);
        updateCountdown();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    # استلام المدينة من الرابط، وإذا لم توجد نضع الرياض كافتراضي
    selected_city_en = request.args.get('city', 'Riyadh')
    
    url = f"http://api.aladhan.com/v1/timingsByCity?city={selected_city_en}&country=Saudi Arabia&method=4"
    try:
        res = requests.get(url).json()
        raw_timings = res["data"]["timings"]
        
        prayers = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
        arabic_names = ["الفجر", "الظهر", "العصر", "المغرب", "العشاء"]
        
        timings_24 = {}
        timings_12 = {}
        
        for en_name, ar_name in zip(prayers, arabic_names):
            time_24 = raw_timings[en_name]
            timings_24[ar_name] = time_24
            
            t_obj = datetime.strptime(time_24, "%H:%M")
            formatted_time = t_obj.strftime("%I:%M %p")
            formatted_time = formatted_time.replace("AM", "ص").replace("PM", "م")
            if formatted_time.startswith("0"):
                formatted_time = formatted_time[1:]
                
            timings_12[ar_name] = formatted_time
            
        return render_template_string(HTML_TEMPLATE, 
                                      timings_12=timings_12, 
                                      timings_24=timings_24,
                                      cities=SAUDI_CITIES,
                                      selected_city=selected_city_en)
    except Exception as e:
        return f"<h2 style='color:red; text-align:center; padding: 50px;'>حدث خطأ في الاتصال بالخادم.</h2>"
@app.route('/shortcut')
def shortcut_api():
    # هذا الرابط مخصص فقط لاختصارات الآيفون
    city = request.args.get('city', 'Riyadh')
    url = f"http://api.aladhan.com/v1/timingsByCity?city={city}&country=Saudi Arabia&method=4"
    
    try:
        res = requests.get(url).json()
        raw_timings = res["data"]["timings"]
        prayers = {
            "الفجر": raw_timings["Fajr"],
            "الظهر": raw_timings["Dhuhr"],
            "العصر": raw_timings["Asr"],
            "المغرب": raw_timings["Maghrib"],
            "العشاء": raw_timings["Isha"]
        }
        
        now = datetime.now()
        current_time_str = now.strftime("%H:%M")
        
        next_prayer = "الفجر"
        next_time_str = prayers["الفجر"]
        
        # البحث عن الصلاة القادمة
        for name, p_time in prayers.items():
            if p_time > current_time_str:
                next_prayer = name
                next_time_str = p_time
                break
                
        # حساب الوقت المتبقي
        now_dt = now
        p_dt = datetime.strptime(next_time_str, "%H:%M").replace(year=now.year, month=now.month, day=now.day)
        
        if p_dt < now_dt: # إذا انتهت صلوات اليوم
            p_dt = p_dt.replace(day=now.day + 1)
            
        diff = p_dt - now_dt
        hours, remainder = divmod(diff.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        # النص الذي سيقرأه الآيفون
        return f"🕌 الصلاة القادمة: {next_prayer}\n⏳ الوقت المتبقي: {hours} ساعة و {minutes} دقيقة"
    except:
        return "حدث خطأ في جلب البيانات"
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
