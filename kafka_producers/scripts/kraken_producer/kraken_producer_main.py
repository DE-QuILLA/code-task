from fastapi import FastAPI
from contextlib import asynccontextmanager
from kraken_modules.config_models.kraken_standarad_logger_config_model import KrakenStandardLoggerConfigModel
from kraken_modules.logging.kraken_stdout_logger import KrakenStdandardLogger
from kraken_modules.clients.config_models.kraken_websocket_client_configs import ALL_WEBSOCKET_CLIENT_CONFIG_MODELS
from kraken_modules.utils.enums.kraken_producer_status_code_enum import KrakenProducerStatusCodeEnum
from kraken_modules.clients.kraken_kafka_client import KrakenKafkaClient
from kraken_modules.managers.kraken_active_pair_manager import KrakenActivePairDataModel, KrakrenActivePairManager
from kraken_modules.clients.kraken_redis_client import KrakenRedisClient
from kraken_modules.managers.kraken_producer_status_manager import KrakenProducerStatusManager
from kraken_modules.clients.config_models.kraken_redis_client_configs import KrakenActivePairRedisClientConfigModel
import logging

# from kraken_producer_core.kraken_websocket_manager import KrakenWebSocketManager
# from kafka.kraken_kafka_client import KrakenKafkaClient
# from manager.kraken_active_pair_manager import KrakenActivePairManager
# from store.kraken_redis_client import KrakenRedisClient




@asynccontextmanager
async def lifespan(kraken_fast_api_app: FastAPI, api_level_logger: KrakenStdandardLogger):
    try:
        api_level_logger.info_start("상태 매니저 초기화")
        websocket_manager = KrakenProducerStatusManager(kafka_client, active_pair_manager, ALL_WEBSOCKET_CLIENT_CONFIG_MODELS)
        api_level_logger.info_start("상태 매니저 초기화")

        api_level_logger.info_start("Redis Client 연결")
        redis_client = KrakenRedisClient(KrakenActivePairRedisClientConfigModel().input_params)
        api_level_logger.info_success(f"Redis Client 연결")

        api_level_logger.info_start("Redis에서 거래쌍 정보 초기화")
        active_pair_manager = KrakrenActivePairManager(redis_client)
        active_pair_manager.get_current_active_pairs()
        api_level_logger.info_success("Redis에서 거래쌍 정보 초기화")

        api_level_logger.info_start("Kafka Client 연결")
        kafka_client = KrakenKafkaClient()
        api_level_logger.info_success("Kafka Client 연결")

        api_level_logger.info_start("웹소켓 매니저 초기화")
        websocket_manager = KrakenWebSocketManager(kafka_client, active_pair_manager, ALL_WEBSOCKET_CLIENT_CONFIG_MODELS)
        api_level_logger.info_success("웹소켓 매니저 초기화")

        api_level_logger.info_start("웹소켓 매니저 초기화")
        kraken_fast_api_app.state.websocket_manager: KrakenWebSocketManager = websocket_manager
        kraken_fast_api_app.state.health_status = KrakenProducerStatusCodeEnum.STARTED
        await kraken_fast_api_app.websocket_manager.start()
        yield {
            "status": "successfully started",
            "status_code": kraken_fast_api_app.state.websocket_manager.get_all_health_status()
            }
    except Exception as e:
        api_level_logger.exception_common(error=e, description="시작 실패")
        raise
    finally:
        api_level_logger.info_start("Kraken Producer 전체 종료")
        await kraken_fast_api_app.websocket_manager.stop()
        api_level_logger.info_success(f"Kraken Producer 전체 종료")

def create_app(api_level_logger: KrakenStdandardLogger):
    api_level_logger.info_start("Fast API 앱 부팅")
    kraken_fast_api_app = FastAPI(
        title="Kraken Producer Fast-api app",
        description="크라켄 웹소켓 기반 카프카 프로듀서",
        version="0.0.1",
        lifespan=lifespan
    )
    api_level_logger.info_success("Fast API 앱 부팅")

    @kraken_fast_api_app.post("/reload")
    async def reload():
        """reload 엔드포인트 - Redis의 변경 사항을 reload"""
        try:
            api_level_logger.info_start("/reload endpoint로 요청 발생, Redis에서 상태 정보 갱신")
            await kraken_fast_api_app.state.websocket_manager.reload_symbols()
            api_level_logger.info_success(f"/reload endpoint로 요청 발생, Redis에서 상태 정보 갱신")
            return {
                "status": "reloaded",
                "status_code": "",
                }
        except Exception as e:
            return {"error": f"{e}"}
    
    @kraken_fast_api_app.get("/health", tags=["Monitoring"])
    async def health():
        return kraken_fast_api_app.state.websocket_manager.get_health()

    return kraken_fast_api_app


if __name__=="__main__":
    api_level_logger_config = KrakenStandardLoggerConfigModel(logger_name = "FAST API APP",)
    api_level_logger: KrakenStdandardLogger = KrakenStdandardLogger.from_config(config_model=api_level_logger_config)
    kraken_fast_api_app = create_app(api_level_logger=api_level_logger)
