import argparse
import json
from datetime import datetime, timedelta

from aiokafka import AIOKafkaProducer
from google.cloud import storage


def get_intervals_between(start: datetime, end: datetime, data_interval: int):
    current = start
    while current <= end:
        yield current
        current += timedelta(minutes=data_interval)


def build_urls_for_datetime(dt: datetime, base_url: str, table_patterns: dict):
    """
    table pattern = filename patterns like [table_name].csv.zip
    """
    timestamp = dt.strftime("%Y%m%d%H%M%S")
    return {
        table: f"{base_url}/{timestamp}{pattern}"
        for table, pattern in table_patterns.items()
    }


def upload_to_gcs(bucket, folder, filename, content, table, ident):
    storage_client = (
        storage.Client.from_service_account_json(ident) if ident else storage.Client()
    )
    bucket = storage_client.bucket(bucket)
    blob_path = f"{folder}/{table}/{filename}"
    blob = bucket.blob(blob_path)
    blob.upload_from_string(content)  # byte type
    return f"gs://{bucket}/{blob_path}"


def parse_datetime(s, format="%Y%m%d%H%M%S"):
    return datetime.strptime(s, format)


def build_kafka_payload(dt, dataset_type, dataset_name, status, **kwargs):
    return {
        "date": dt.strftime("%Y%m%d%H%M%S"),
        dataset_type: dataset_name,
        "status": status,
        **kwargs,
    }


async def send_kafka_signals(messages, kafka_config):
    producer = AIOKafkaProducer(
        bootstrap_servers=kafka_config.kafka_bootstrap_servers,
        value_serializer=lambda payload: json.dumps(payload).encode("utf-8"),
    )
    await producer.start()
    try:
        for message in messages:
            if isinstance(message, dict):  # skip exceptions from gather
                await producer.send_and_wait(kafka_config.kafka_topic, message)
    finally:
        await producer.stop()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stream", action="store_true")
    parser.add_argument("--backfill", action="store_true")
    parser.add_argument("--start", type=str, required=True)
    parser.add_argument("--end", type=str, required=True)
    parser.add_argument("--step-minutes", type=int, default=300)
    return parser.parse_args()
