# Unused:
# from enum import Enum
# Config.CONCURRENCY.name, .value
import os
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class Config:
    ident: Optional[str] = None


@dataclass
class KafkaConfig(Config):
    bootstrap: str = field(
        default_factory=lambda: os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
    )
    topic: str = field(
        default_factory=lambda: os.getenv("KAFKA_TOPIC", "gdelt-ingestion")
    )  # temp


@dataclass
class IngestionConfig(Config):
    gcs_bucket_name: str = field(
        default_factory=lambda: os.getenv("GCS_BUCKET", "default-bucket")
    )
    gcs_folder: str = "default-dir"
    concurrency: int = 5
    download_timeout: int = 30
    step_minutes: int = 300
    data_interval: int = 15


@dataclass
class GDELTIngestConfig(IngestionConfig):
    base_url: str = "http://data.gdeltproject.org/gdeltv2"
    table_patterns: Dict[str, str] = field(
        default_factory=lambda: {
            "events": ".export.CSV.zip",
            "mentions": ".mentions.CSV.zip",
            "gkg": ".gkg.csv.zip",
        }
    )
