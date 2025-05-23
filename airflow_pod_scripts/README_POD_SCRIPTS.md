# airflow_pod_scripts 폴더

- airflow가 띄우는 별도 pod에서 실행할 코드 작성 폴더

- 해당 내용은 도커 헙, ECR 과 같은 컨테이너 이미지 레포로 푸시되고 이를 다시 POD 생성 시 풀받아 사용

- airflow에서는 dag의 실행 관련 내용만! 실제 api 호출, 크롤링 등은 여기서!

- 모듈 아래 utils를 나눈 기준
    - utils 아래에는 서로 종속성이 없는 최소한의 단위의 기능을 모듈화
    - utils 밖의 kraken_modules 에 있는 파일은 utils 하위의 기능을 사용하여 구현