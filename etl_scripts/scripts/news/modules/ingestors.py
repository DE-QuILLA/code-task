import asyncio
import io
import zipfile
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

from aiohttp import ClientSession, ClientTimeout

from modules.configs import GDELTIngestConfig, IngestionConfig
from modules.helpers import (
    build_kafka_payload,
    build_urls_for_datetime,
    get_intervals_between,
    parse_datetime,
    upload_to_gcs,
)
from modules.logger import LoggingMixin


class FileUnavailableError(Exception):
    pass


class RetryableDownloadError(Exception):
    pass


class Ingestor(LoggingMixin, ABC):
    def __init__(self, config: IngestionConfig, log_config: dict = None):
        super().__init__(log_config)
        self.config = config

    @abstractmethod
    async def execute(self, start, end):
        pass

    @abstractmethod
    async def fetch(self, session, url, semaphore):
        pass

    @abstractmethod
    async def process(
        self, dt: datetime, table, url, session, semaphore: asyncio.Semaphore
    ):
        pass


class GDELTIngestor(Ingestor):
    def __init__(self, config: GDELTIngestConfig, log_config: dict = None):
        super().__init__(config, log_config)
        self.config: GDELTIngestConfig = config

    async def fetch(self, session: ClientSession, url: str, semaphore):
        """
        Fetches a csv.zip table from a complete url, upholding semaphore limits.

        Params
        ------
        session: An aiohttp client session
        """
        async with semaphore:
            try:
                async with session.get(
                    url, timeout=ClientTimeout(total=self.config.download_timeout)
                ) as resp:
                    if resp.status == 404:
                        raise FileUnavailableError(f"File not found: {url}")
                    if resp.status != 200:
                        raise RetryableDownloadError(
                            f"Unexpected status {resp.status} for {url}"
                        )
                    zip_bytes = await resp.read()
                    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
                        for filename in z.namelist():
                            content = z.read(filename)
                            return filename.lower(), content
            except asyncio.TimeoutError:
                raise RetryableDownloadError(f"Timeout while downloading {url}")

    async def process(self, dt, table, url, session, semaphore):
        """
        Fetch-Upload-Signal
        """
        filename, content = await self.fetch(session, url, semaphore)
        # # # # # # # # # # # # # # # # # # # # # # # # # # # #
        # INSERT SPARK JOB HERE. CALL self.config.cols_to_keep #
        # # # # # # # # # # # # # # # # # # # # # # # # # # # #
        gcs_uri = upload_to_gcs(
            self.config.gcs_bucket_name,
            self.config.gcs_folder,
            filename,
            content,
            table,
            self.config.ident,
        )
        self.logger.info(f"[DONE] {table} @ {dt} -> {gcs_uri}")
        return build_kafka_payload(
            dt, "table", table, "ingestion:done", {"gcs_uri": gcs_uri}
        )

    # NOTE: Overloading is heresy in python?! Dang...
    # NOTE: A method is also an object, and attribute of a class in python
    # NOTE: so overloading them would be like assigning--
    # NOTE: which doesn't make sense for methods, conceptually.
    # NOTE: The typing.overload is for duct typing.
    # NOTE: If we must, we can implement a single dispatch method or bring in the lambda
    # NOTE: but apparently this is the most pythonic way:
    async def execute(self, start, end):
        """
        Business as usual.
        """
        semaphore = asyncio.Semaphore(self.config.concurrency)
        async with ClientSession() as session:
            tasks = []
            for dt in get_intervals_between(start, end, self.config.data_interval):
                urls = build_urls_for_datetime(
                    dt, self.config.base_url, self.config.table_patterns
                )
                for table, url in urls.items():
                    tasks.append(self.process(dt, table, url, session, semaphore))
            return await asyncio.gather(*tasks, return_exceptions=True)

    async def backfill(self, start, end):
        """
        Runs backfill for historical
        """
        semaphore = asyncio.Semaphore(self.config.concurrency)
        all_results = []
        async with ClientSession() as session:
            current = start
            while current <= end:
                chunk_end = min(
                    current + timedelta(minutes=self.config.step_minutes), end
                )
                chunk_tasks = []
                for dt in get_intervals_between(
                    current, chunk_end, self.config.data_interval
                ):
                    urls = build_urls_for_datetime(
                        dt, self.config.base_url, self.config.table_patterns
                    )
                    for table, url in urls.items():
                        chunk_tasks.append(
                            self.process(dt, table, url, session, semaphore)
                        )
                self.logger.info(
                    f"[CHUNK] {current} → {chunk_end} | {len(chunk_tasks)} tasks"
                )
                results = await asyncio.gather(*chunk_tasks, return_exceptions=True)
                all_results.extend(results)
                current = chunk_end + timedelta(minutes=self.config.data_interval)
        return all_results
