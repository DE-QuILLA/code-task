# init

"""
Custom Exception 객체들을 모은 모듈
-
"""

# 0. Exception 없는 성공을 나타내는 객체(종료코드 매핑에 사용)
from .kraken_success import KrakenScriptSuccess

# 1. 전체적인 설정
from .kraken_custom_err import ALL_CUSTOM_EXCEPTIONS
from .kraken_custom_err import KrakenBaseETLException

# 2. Redis Client
from .kraken_custom_err import KrakenRedisClientConnectionException
from .kraken_custom_err import KrakenRedisClientCanNotCloseException

# 3. REST Client
from .kraken_custom_err import KrakenRESTClientHTTPException

# 4. REST API Collector
from .kraken_custom_err import KrakenErrorInAPIResponseException
from .kraken_custom_err import KrakenAPIResponseNoDataException
from .kraken_custom_err import KrakenAPIResponseValueException
from .kraken_custom_err import KrakenProducerAPICallFailException
