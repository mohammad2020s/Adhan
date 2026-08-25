from flask import Flask, render_template_string
import requests

app = Flask(__name__)

# هذا كود HTML و CSS لتصميم واجهة الموقع بشكل جميل ومناسب للجوال
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>مواقيت الصلاة</title>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background-color: #121212; 
            color: #ffffff; 
            text-align: center; 
            padding: 20px; 
            margin: 0; 
        }
        h1 { color: #4caf50; margin-bottom: 5px;}
        p.date { color: #888; font-size: 14px; margin-bottom: 25px; }
        .prayer-card { 
            background-color: #1e1e1e; 
            padding: 15px 25px; 
            margin: 12px auto; 
            border-radius: 12px; 
            max-width: 320px; 
            display: flex; 
            justify-content: space-between; 
            font-size: 22px; 
            font-weight: bold;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        .prayer-name { color: #a0c4ff; }
        .footer { margin-top: 40px; font-size: 12px; color: #555; }
    </style>
</head>
<body>
    <h1>مواقيت الصلاة - الرياض</h1>
    <p class="date">تاريخ اليوم: {{ date }}</p>
    
    {% for name, time in timings.items() %}
    <div class="prayer-card">
        <span class="prayer-name">{{ name }}</span>
        <span>{{ time }}</span>
    </div>
    {% endfor %}
    
    <div class="footer">تطبيق ويب لـ أوقات الصلاة</div>
</body>
</html>
"""

@app.route('/')
def index():
    # إعدادات الرياض كمثال (مضبوطة على تقويم أم القرى)
    city = "Riyadh"
    country = "Saudi Arabia"
    method = 4
    url = f"http://api.aladhan.com/v1/timingsByCity?city={city}&country={country}&method={method}"
    
    try:
        res = requests.get(url).json()
        timings_data = res["data"]["timings"]
        date_today = res["data"]["date"]["readable"]
        
        # استخراج الأوقات الخمسة
        timings = {
            "الفجر": timings_data["Fajr"],
            "الظهر": timings_data["Dhuhr"],
            "العصر": timings_data["Asr"],
            "المغرب": timings_data["Maghrib"],
            "العشاء": timings_data["Isha"]
        }
        
        return render_template_string(HTML_TEMPLATE, timings=timings, date=date_today)
    except:
        return "<h2 style='color:red; text-align:center;'>حدث خطأ في جلب الأوقات، يرجى تحديث الصفحة.</h2>"

# هذا السطر مهم لتشغيل السيرفر
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
