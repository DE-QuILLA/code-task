# 외부 라이브러리
from fastapi import FastAPI
from contextlib import asynccontextmanager

# config 모델
from kraken_modules.config_models import (
    KrakenStandardLoggerConfigModel,
    KrakenRedisClientConfigModel,
    KrakenActiveSymbolManagerConfigModel,
    KrakenKafkaClientConfigModel,
    ALL_WEBSOCKET_CLIENT_CONFIG_MODELS,
)

# 내부 활용 객체
from kraken_modules.logging import KrakenStdandardLogger
from kraken_modules.managers import (
    KrakenProducerStatusManager,
    KrakenActiveSymbolManager,
    KrakenWebSocketClientManager,
)
from kraken_modules.clients import (
    KrakenKafkaClient,
    KrakenWebSocketClient,
    KrakenRedisClient,
)


@asynccontextmanager
async def lifespan(
    kraken_fast_api_app: FastAPI, api_level_logger: KrakenStdandardLogger
):
    try:
        # 1. STATUS MANAGER
        api_level_logger.info_start("상태 매니저 초기화")
        kraken_status_manager: KrakenProducerStatusManager = (
            KrakenProducerStatusManager()
        )
        api_level_logger.info_start("상태 매니저 초기화")

        # 2. REDIS CLIENT
        api_level_logger.info_start("Redis Client 연결")
        redis_config = KrakenRedisClientConfigModel(
            redis_url="redis://redis-master.redis.svc.cluster.local:6379/0",
            retry_num=5,
            retry_delay=2,
            conn_timeout=10,
            component_name="REDIS CLIENT",
        )
        redis_client = KrakenRedisClient(
            config=redis_config, status_manager=kraken_status_manager
        )
        await redis_client.initialize_redis_client()
        api_level_logger.info_success(f"Redis Client 연결")

        # 3. ACTIVE PAIR MANAGER
        api_level_logger.info_start("Redis에서 거래쌍 정보 초기화")
        active_pair_manager_config = KrakenActiveSymbolManagerConfigModel(
            redis_key="kraken:active_pair",  # 필요 시 수정
            component_name="ACTIVE PAIR MANAGER",
            retry_num=5,
            retry_delay=2,
            conn_timeout=20,
        )
        active_pair_manager = KrakenActiveSymbolManager(
            redis_client=redis_client,
            config=active_pair_manager_config,
        )
        await active_pair_manager.initialize_active_pair_manager()
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
            conn_timeout=20,
        )
        kafka_client = KrakenKafkaClient(
            config=kafka_client_config, status_manager=kraken_status_manager
        )
        await kafka_client.initialize_kafka_client()
        api_level_logger.info_success("Kafka Client 연결")

        # 5. WEBSOCKET CLIENT들
        api_level_logger.info_start("웹소켓 클라이언트 초기화")
        websocket_client_config_list = []
        for config in ALL_WEBSOCKET_CLIENT_CONFIG_MODELS:
            websocket_client_config_list.append(config())
        api_level_logger.info_success("웹소켓 클라이언트 초기화")

        api_level_logger.info_start("웹소켓 매니저 초기화")
        websocket_manager = KrakenWebSocketClientManager(
            client_config_list=websocket_client_config_list,
            status_manager=kraken_status_manager,
            kafka_client=kafka_client,
            active_pair_manager=active_pair_manager,
        )
        await websocket_manager.initialize_clients_manager()
        api_level_logger.info_success("웹소켓 매니저 초기화")

        api_level_logger.info_start("Producer 전체 동작")
        kraken_fast_api_app.state.websocket_manager = websocket_manager
        kraken_fast_api_app.state.status_manager = kraken_status_manager
        await kraken_fast_api_app.websocket_manager.start_all()
        yield {
            "status": "successfully started",
            "status_code": await kraken_fast_api_app.state.status_manager.get_all_component_health_status(),
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
        lifespan=lifespan,
    )
    api_level_logger.info_success("Fast API 앱 부팅")

    @kraken_fast_api_app.post("/reload")
    async def reload():
        """reload 엔드포인트 - Redis의 변경 사항을 reload"""
        try:
            api_level_logger.info_start(
                "/reload endpoint로 요청 발생, Redis에서 상태 정보 갱신"
            )
            await kraken_fast_api_app.state.websocket_manager.reload_symbols()
            api_level_logger.info_success(
                f"/reload endpoint로 요청 발생, Redis에서 상태 정보 갱신"
            )
            return {
                "method": "reload",
                "status": "success",
            }
        except Exception as e:
            return {
                "method": "reload",
                "status": "failed",
                "error": f"{e}",
            }

    @kraken_fast_api_app.get("/health", tags=["Monitoring"])
    async def health():
        return await kraken_fast_api_app.state.status_manager.get_all_component_status()

    return kraken_fast_api_app


if __name__ == "__main__":
    api_level_logger: KrakenStdandardLogger = KrakenStdandardLogger(
        logger_name="FAST API APP"
    )
    kraken_fast_api_app = create_app(api_level_logger=api_level_logger)
