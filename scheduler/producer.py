import os
import pika

def produce(host, body):
    user = os.environ.get("RABBITMQ_USER", "admin")
    password = os.environ.get("RABBITMQ_PASS", "rabbitmq")

    # กำหนด Authentication สำหรับ RabbitMQ
    credentials = pika.PlainCredentials(user, password)
    parameters = pika.ConnectionParameters(host=host, credentials=credentials)

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    channel.exchange_declare(exchange="jobs", exchange_type="direct")
    channel.queue_declare(queue="router_jobs")
    channel.queue_bind(queue="router_jobs", exchange="jobs", 
                       routing_key="check_interfaces")

    channel.basic_publish(exchange="jobs", 
                          routing_key="check_interfaces", body=body)

    connection.close()

if __name__ == "__main__":
    rabbitmq_host = os.environ.get("RABBITMQ_HOST", "rabbitmq")
    produce(rabbitmq_host, "192.168.1.44")
