import os
import json
import pika
from datetime import datetime, timezone

from pymongo import MongoClient
from netmiko import ConnectHandler

# =========================
# Environment
# =========================

RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_USER = os.environ.get("RABBITMQ_USER", "admin")
RABBITMQ_PASS = os.environ.get("RABBITMQ_PASS", "rabbitmq")

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://mongo:27017/")
DB_NAME = os.environ.get("DB_NAME")


# =========================
# MongoDB
# =========================

mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]

results_collection = db["router_results"]


# =========================
# SSH Router
# =========================


def connect_router(router):
    router_id = router.get("_id")
    ip = router.get("ip") or router.get("IP")
    username = router.get("username") or router.get("User")
    password = router.get("password") or router.get("Pass")

    print(f"[Worker1] Connecting to {router_id} ({ip})")

    device = {
        "device_type": "cisco_ios",
        "host": ip,
        "username": username,
        "password": password,
        "conn_timeout": 10,
        "auth_timeout": 10,
        "banner_timeout": 10,
    }

    connection = ConnectHandler(**device)

    print(f"[Worker1] Connected to {router_id}")

    # ใช้ TextFSM
    result = connection.send_command(
        "show ip interface brief", use_textfsm=True
    )

    connection.disconnect()

    print(f"[Worker1] Command completed on {router_id}")

    return result


# =========================
# RabbitMQ Consumer
# =========================


def callback(ch, method, properties, body):

    try:
        print("\n================================")
        print("[Worker1] Message received")
        print(body)
        print("================================")

        # แปลง JSON message
        router = json.loads(body)

        ip = router.get("ip") or router.get("IP")

        # SSH + show command
        result = connect_router(router)

        # เก็บผลลง MongoDB ตามโครงสร้างที่กำหนด
        document = {
            "router_ip": ip,
            "timestamp": datetime.now(timezone.utc),
            "interfaces": result,
        }

        results_collection.insert_one(document)

        print(f"[Worker1] Result saved to MongoDB for IP: {ip}")

        # ยืนยันว่า message สำเร็จ
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:

        print(f"[Worker1] ERROR: {e}")

        # ปล่อย message ไม่สำเร็จ (ไม่นำกลับเข้า Queue)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


# =========================
# Main
# =========================


def main():

    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)

    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST, credentials=credentials
    )

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    # ต้องตรงกับ Scheduler
    channel.exchange_declare(exchange="jobs", exchange_type="direct")

    channel.queue_declare(queue="router_jobs")

    channel.queue_bind(
        queue="router_jobs", exchange="jobs", routing_key="check_interfaces"
    )

    # รับทีละ 1 message
    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(queue="router_jobs", on_message_callback=callback)

    print("[Worker1] Waiting for messages...")
    print("[Worker1] Queue: router_jobs")

    channel.start_consuming()


if __name__ == "__main__":
    main()
