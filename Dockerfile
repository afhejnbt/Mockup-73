FROM python:3.9-slim

# تثبيت المكتبات النظامية الأساسية لمعالجة الصور
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# نسخ وتثبيت مكتبات بايثون
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي ملفات المشروع بالكامل إلى السيرفر
COPY . .

# فتح البورت 7860 وهو البورت الافتراضي لـ Hugging Face
EXPOSE 7860

# تشغيل الباك إند عبر خادم gunicorn المستقر
CMD ["gunicorn", "-b", "0.0.0.0:7860", "app:app"]