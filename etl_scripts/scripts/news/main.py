import asyncio
import logging

from modules.configs import GDELTIngestConfig, KafkaConfig
from modules.helpers import parse_args, parse_datetime, send_kafka_signals
from modules.ingestors import GDELTIngestor

if __name__ == "__main__":
    args = parse_args()
    start = parse_datetime(args.start)
    end = parse_datetime(args.end)

    # TODO: Ingestor SA key json needed. ident should be a path -> bake into dockerfile
    # TODO: Need confirmation on GCS bucket env var name & folder name
    # TODO: Gather exception backfill loop is needed
    # TODO: Kafka-related vars? What to do?
    # TODO: Upload to GCS could be more generalized
    # TODO: Uh... the DAG?
    config = GDELTIngestConfig(
        ident="key.json", gcs_folder="gdelt", step_minutes=args.step_minutes
    )
    kafka_config = KafkaConfig(ident="key.json", bootstrap="", topic="")
    log_config = {"level": logging.DEBUG}
    ingestor = GDELTIngestor(config=config, log_config=log_config)
    results = []

    if args.stream:
        results = asyncio.run(ingestor.execute(start, end))
    elif args.backfill:
        results = asyncio.run(ingestor.backfill(start, end))

    # What am I, half-producer, half-scrapper?
    # NOTE: Conceptualizing. DO NOT BE ALARMED IF IT WORKS 😂... AS IF ...
    if results:
        asyncio.run(send_kafka_signals(results, kafka_config))
