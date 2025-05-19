# 외부 라이브러리
from fastapi import FastAPI
from contextlib import asynccontextmanager

# config 모델
from kraken_modules.config_models.kraken_standarad_logger_config_model import KrakenStandardLoggerConfigModel
from kraken_modules.config_models.kraken_redis_client_configs import KrakenRedisClientConfigModel
from kraken_modules.config_models.kraken_active_pair_manager_config_model import KrakenActivePairManagerConfigModel
from kraken_modules.config_models.kraken_kafka_client_configs import KrakenKafkaClientConfigModel
from kraken_modules.config_models.kraken_websocket_client_configs import ALL_WEBSOCKET_CLIENT_CONFIG_MODELS

# 내부 활용 객체
from kraken_modules.logging.kraken_stdout_logger import KrakenStdandardLogger
from kraken_modules.managers.kraken_producer_status_manager import KrakenProducerStatusManager
from kraken_modules.clients.kraken_redis_client import KrakenRedisClient
from kraken_modules.managers.kraken_active_pair_manager import KrakenActivePairManager
from kraken_modules.clients.kraken_kafka_client import KrakenKafkaClient
from kraken_modules.clients.kraken_websocket_client import KrakenWebSocketClient
from kraken_modules.managers.kraken_websocket_client_manager import KrakenWebSocketClientManager
# from kraken_modules.config_models.kraken_standarad_logger_config_model import KrakenStandardLoggerConfigModel
# from kraken_modules.logging.kraken_stdout_logger import KrakenStdandardLogger
# from kraken_modules.config_models.kraken_websocket_client_configs import ALL_WEBSOCKET_CLIENT_CONFIG_MODELS

# from kraken_modules.utils.enums.kraken_producer_status_code_enum import KrakenProducerStatusCodeEnum
# from kraken_modules.clients.kraken_kafka_client import KrakenKafkaClient
# from kraken_modules.managers.kraken_active_pair_manager import KrakenActivePairDataModel, KrakrenActivePairManager
# from kraken_modules.clients.kraken_redis_client import KrakenRedisClient
# from kraken_modules.managers.kraken_producer_status_manager import KrakenProducerStatusManager
# from kraken_modules.clients.config_models.kraken_redis_client_configs import KrakenActivePairRedisClientConfigModel
# import logging

# from kraken_producer_core.kraken_websocket_manager import KrakenWebSocketManager
# from kafka.kraken_kafka_client import KrakenKafkaClient
# from manager.kraken_active_pair_manager import KrakenActivePairManager
# from store.kraken_redis_client import KrakenRedisClient




@asynccontextmanager
async def lifespan(kraken_fast_api_app: FastAPI, api_level_logger: KrakenStdandardLogger):
    try:
        # 1. STATUS MANAGER
        api_level_logger.info_start("상태 매니저 초기화")
        kraken_status_manager: KrakenProducerStatusManager = KrakenProducerStatusManager()
        api_level_logger.info_start("상태 매니저 초기화")

        # 2. REDIS CLIENT
        api_level_logger.info_start("Redis Client 연결")
        redis_config = KrakenRedisClientConfigModel(
            redis_url="redis://redis-master.redis.svc.cluster.local:6379/0",
            retry_num=5,
            retry_delay=2,
            conn_timeout=10,
            component_name="REDIS CLIENT"
        )
        redis_client = KrakenRedisClient(config=redis_config, status_manager=kraken_status_manager)
        await redis_client.initialize_redis_client()
        api_level_logger.info_success(f"Redis Client 연결")

        # 3. ACTIVE PAIR MANAGER
        api_level_logger.info_start("Redis에서 거래쌍 정보 초기화")
        active_pair_manager_config = KrakenActivePairManagerConfigModel(
            redis_key="kraken:active_pair",  # 필요 시 수정
            component_name="ACTIVE PAIR MANAGER",
            retry_num=5,
            retry_delay=2,
            conn_timeout=20,
        )
        active_pair_manager = KrakenActivePairManager(redis_client=redis_client, config=active_pair_manager_config,)
        active_pair_manager.initialize_active_pair_manager()
        api_level_logger.info_success("Redis에서 거래쌍 정보 초기화")

        # 4. KAFKA CLIENT
        api_level_logger.info_start("Kafka Client 연결")
        kafka_client_config = KrakenKafkaClientConfigModel(
            bootstrap_server="de-quilla-kafka-cluster.kafka-1.9092",
            health_topic_name="__kafka_health_check",
            status_manager=kraken_status_manager,
            acks="1",  # NOTE: 변경될 여지 있음
            retry_num=5,
            retry_delay=2,
            conn_timeout=20,)
        kafka_client = KrakenKafkaClient(config=kafka_client_config, status_manager=kraken_status_manager)
        kafka_client.initialize_kafka_client()
        api_level_logger.info_success("Kafka Client 연결")

        # 5. WEBSOCKET CLIENT들
        api_level_logger.info_start("웹소켓 클라이언트 초기화")
        websocket_client_config_list = []
        for config in ALL_WEBSOCKET_CLIENT_CONFIG_MODELS:
            websocket_client_config_list.append(config)
        api_level_logger.info_success("웹소켓 클라이언트 초기화")

        api_level_logger.info_start("웹소켓 매니저 초기화")
        websocket_manager = KrakenWebSocketClientManager(
            client_config_list=websocket_client_config_list,
            status_manager=kraken_status_manager,
            kafka_client=kafka_client,
            active_pair_manager=active_pair_manager
        )
        websocket_manager.init_clients_manager()
        api_level_logger.info_success("웹소켓 매니저 초기화")

        api_level_logger.info_start("Producer 전체 동작")
        kraken_fast_api_app.state.websocket_manager = websocket_manager
        kraken_fast_api_app.state.status_manager = kraken_status_manager
        await kraken_fast_api_app.websocket_manager.start_all()
        yield {
            "status": "successfully started",
            "status_code": await kraken_fast_api_app.state.status_manager.get_all_component_health_status()
            }
    except Exception as e:
        api_level_logger.exception_common(error=e, description="시작 실패")
        raise
    finally:
        api_level_logger.info_start("Kraken Producer 전체 종료")
        await kraken_fast_api_app.websocket_manager.stop_all()
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
