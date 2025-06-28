# Unused:
# from enum import Enum
# Config.CONCURRENCY.name, .value
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


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
    # hard-coding field() leads to shared fields across instances!!!
    cols_to_keep: Dict[str, List[str]] = field(
        default_factory=lambda: {
            "events": [
                "GlobalEventID",
                "Day",
                "FractionDate",
                "Actor1Name",
                "Actor1Type1Code",
                "Actor2Name",
                "Actor2Type1Code",
                "Actor1Geo_Type",
                "Actor1Geo_Fullname",
                "Actor1Geo_Lat",
                "Actor1Geo_Long",
                "Actor2Geo_Type",
                "Actor2Geo_Fullname",
                "Actor2Geo_Lat",
                "Actor2Geo_Long",
                "ActionGeo_Type",
                "ActionGeo_Fullname",
                "ActionGeo_Lat",
                "ActionGeo_Long",
                "DATEADDED",
                "SOURCEURL",
            ],
            "mentions": [
                "GlobalEventID",
                "EventTimeDate",
                "MentionTimeDate",
                "MentionType",
                "MentionIdentifier",
                "SentenceID",
                "Actor1CharOffset",
                "Actor2CharOffset",
                "ActionCharOffset",
                "MentionDocLen",
                "MentionDocTone",
            ],
            "gkg": [
                "GKGRECORDID",
                "V2.1DATE",
                "V2SOURCECOLLECTIONIDENTIFIER",
                "V2SOURCECOMMONNAME",
                "V2DOCUMENTIDENTIFIER",
                "V2.1COUNTS",
                "V2ENHANCEDTHEMES",
                "V2ENHANCEDLOCATIONS",
                "V2ENHANCEDPERSONS",
                "V2ENHANCEDORGANIZATIONS",
                "V1.5TONE",
                "V2.1ENHANCEDDATES",
                "V2GCAM",
                "V2.1QUOTATIONS",
                "V2.1ALLNAMES",
                "V2.1AMOUNTS",
            ],
        }
    )
