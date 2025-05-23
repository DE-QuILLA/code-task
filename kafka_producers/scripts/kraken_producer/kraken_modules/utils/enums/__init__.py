# init

"""
Producer 내부적으로 사용하는 Enum 클래스를 작성하는 모듈
- KrakenProducerExitCodeEnum: Producer가 종료될 때 발생하는 종료 코드의 명세 작성
- KrakenProducerStatusCodeEnum: 각 컴포넌트의 상태를 표현하는 코드 명세 작성
- EXCEPTION_TO_EXIT_CODE, get_exitcode_from_exception: 각각 커스텀 Exception 객체 별 종료 코드와 매핑 / 해당 매핑을 가져오는 헬퍼 함수
"""

from .kraken_exit_code_enum import KrakenProducerExitCodeEnum
from .kraken_producer_status_code_enum import KrakenProducerStatusCodeEnum
from ..mappings.map_exceptions_to_exit_code import (
    EXCEPTION_TO_EXIT_CODE,
    get_exitcode_from_exception,
)
