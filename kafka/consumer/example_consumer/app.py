from kafka import KafkaConsumer
import json

KAFKA_BROKER = 'kafka-service:9092'
TOPIC = 'user-events'

consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=KAFKA_BROKER,
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='user-event-consumer-group',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

if __name__ == "__main__":
    for message in consumer:
        event = message.value
        print(f"Consumed event: {event}")
        # 여기에 DB 저장, 다른 서비스 호출 등 추가 로직 작성 가능
