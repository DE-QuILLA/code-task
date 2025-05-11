from kafka import KafkaProducer
import json
import time
import random

KAFKA_BROKER = 'kafka-service:9092'
TOPIC = 'user-events'

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

if __name__ == "__main__":
    while True:
        user_event = {
            'user_id': random.randint(1, 1000),
            'event_type': random.choice(['click', 'purchase', 'logout']),
            'timestamp': time.time()
        }

        producer.send(TOPIC, user_event)
        print(f"Produced event: {user_event}")

        time.sleep(2)
