from fastapi import FastAPI
from contextlib import asynccontextmanager
from kraken_modules.clients.config_models.kraken_websocket_client_configs import ALL_WEBSOCKET_CLIENT_CONFIG_MODELS
from kraken_modules.utils.logging.kraken_stdout_logger import get_stdout_logger, get_error_msg, get_start_info_msg, get_success_info_msg
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


api_level_logger: logging.Logger = get_stdout_logger("FAST API APP LEVEL Logger")


@asynccontextmanager
async def lifespan(kraken_fast_api_app: FastAPI):
    kraken_fast_api_app.state.health_status = KrakenProducerStatusCodeEnum.NOT_STARTED
    try:
        api_level_logger.info(get_start_info_msg("Redis Client 연결"))
        redis_client = KrakenRedisClient(KrakenActivePairRedisClientConfigModel().input_params)
        api_level_logger.info(get_success_info_msg(f"Redis Client 연결 성공!"))

        api_level_logger.info(get_start_info_msg("Redis에서 거래쌍 정보 초기화"))
        active_pair_manager = KrakrenActivePairManager(redis_client)
        active_pair_manager.get_current_active_pairs()
        api_level_logger.info(get_success_info_msg("Redis에서 거래쌍 정보 초기화"))

        api_level_logger.info(get_start_info_msg("Kafka Client 연결"))
        kafka_client = KrakenKafkaClient()
        api_level_logger.info(get_success_info_msg("Kafka Client 연결"))

        api_level_logger.info(get_start_info_msg("웹소켓 매니저 초기화"))
        websocket_manager = KrakenWebSocketManager(kafka_client, active_pair_manager, ALL_WEBSOCKET_CLIENT_CONFIG_MODELS)
        api_level_logger.info(get_success_info_msg("웹소켓 매니저 초기화"))

        api_level_logger.info(get_start_info_msg("상태 매니저 초기화"))
        websocket_manager = KrakenProducerStatusManager(kafka_client, active_pair_manager, ALL_WEBSOCKET_CLIENT_CONFIG_MODELS)
        api_level_logger.info(get_success_info_msg("상태 매니저 초기화"))

        api_level_logger.info("웹소켓 매니저 초기화 중!")
        kraken_fast_api_app.state.websocket_manager: KrakenWebSocketManager = websocket_manager
        kraken_fast_api_app.state.health_status = KrakenProducerStatusCodeEnum.STARTED
        await kraken_fast_api_app.websocket_manager.start()
        yield {
            "status": "successfully started",
            "status_code": kraken_fast_api_app.state.websocket_manager.get_all_health_status()
            }
    except Exception as e:
        api_level_logger.exception(get_error_msg(e))
        raise
    finally:
        api_level_logger.info(f"Kraken Producer 종료 시작!")
        await kraken_fast_api_app.websocket_manager.stop()
        api_level_logger.info(f"Kraken Producer 정상 종료!")

def create_app():
    api_level_logger.info("Kraken Kafka Producer - Fast API 앱 기동!")
    kraken_fast_api_app = FastAPI(
        title="Kraken Producer Fast-api app",
        description="크라켄 웹소켓 기반 카프카 프로듀서",
        version="0.0.1",
        lifespan=lifespan
    )
    api_level_logger.info("Kraken Kafka Producer - Fast API 앱 기동 완료!")

    @kraken_fast_api_app.post("/reload")
    async def reload():
        """reload 엔드포인트 - Redis의 변경 사항을 reload"""
        try:
            api_level_logger.info(f"/reload endpoint로 요청 발생, Redis에서 상태 정보 갱신!")
            await kraken_fast_api_app.state.websocket_manager.reload_symbols()
            api_level_logger.info(f"/reload endpoint로 요청 발생, Redis에서 상태 정보 갱신 완료!")
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
    kraken_fast_api_app = create_app()
