# airflow_dags 폴더

- airflow, spark(배치) 관련 코드작업을 위한 폴더

- docker-compose yaml을 추후에 변경, 로컬 테스팅 환경으로 활용하실 수 있도록 구성 예정
    - 주의: spark connect 서버를 도입해서 airflow에서 스파크 실행 로그 관측 + 아키텍처 개선을 추구할 예정 => 로컬에서 스파크 코드는 추후 좀 더 세세한 작업 필요
    - Kubernetes Executor 기반이 아니도록 구성할 예정 (각자의 로컬 개발환경에 필요하기엔 너무 무거움) => 따라서 관련 설정 충돌이 있을 수 있음에 주의

- `requirements-airflow` 에서 테스팅 환경에서 돌릴 때 필요한 종속성을 작성
    - 이 파일은 airflow dag 배포 용으로 푸시될 예정

- CD는 git Sync에 의해 배포됨
    - 아래와 같은 옵션을 사용해서 깃 싱크 안정화

```yaml
args:
  - --repo=https://github.com/your-org/airflow-dags.git
  - --branch=main
  - --root=/git
  - --dest=repo
  - --wait=60  # 최소 동기화 주기 30초 (짧게 하면 불안정)
  - --max-sync-failures=5
  - --one-time=false
```
