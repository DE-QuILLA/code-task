# init

"""
내부적으로 사용하는 커스텀 래퍼를 작성하는 모듈
- custom_retry: 고차함수 형식으로 작성된 retry 로직을 추가하는 래퍼 함수
    - logger를 동적으로 받기 위해 decorator가 아닌 고차 함수 형식 채택
"""

from .retry_wrapper_function import custom_retry
