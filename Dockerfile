FROM python:3.9-slim

# تحديث حزم النظام وتثبيت المكتبات الحديثة والمستقرة لمعالجة الصور
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# نسخ وتثبيت مكتبات بايثون
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي ملفات المشروع بالكامل
COPY . .

# فتح بورت التشغيل الافتراضي لـ Render
EXPOSE 10000

# تشغيل التطبيق عبر خادم gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:10000", "app:app"]