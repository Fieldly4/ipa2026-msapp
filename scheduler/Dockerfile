FROM python:3.14-slim

WORKDIR /app

# คัดลอกไฟล์ requirements.txt และติดตั้ง dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอกไฟล์ทั้งหมดในโฟลเดอร์ scheduler เข้ามาใน Container
COPY . .

# สั่งรันโปรแกรมหลัก (scheduler.py)
CMD ["python", "scheduler.py"]
