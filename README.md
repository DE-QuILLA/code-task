# DE-QUILLA 팀 프로젝트 코드 레포

### 0. Workflow

1. 깃허브에 반영되어야 할 작업이라면, 먼저 Jira에서 티켓을 생성하며 아래와 같은 prefix를 사용합니다.

---

- feat     : 새로운 기능 추가 
- fix      : 디버깅, 버그 수정, 리팩토링 등 코드 수정
- chore    : 잡일성 작업 
- docs     : 문서 관련 작업 
- test     : 테스트 코드 추가 및 수정

---


2. 깃허브에 아래와 같은 브랜치를 이슈를 생성할 때 생성합니다.

---

- 만약 Jira에 생성한 티켓이 다음과 같다면 : `feat-add-login`

- 다음과 같은 브랜치를 생성합니다 : `feat/JIRA-1234-add-login`
    - 1234는 티켓 번호

---

3. 브랜치를 이동하고 작업을 시작해주시면 됩니다.

```bash
git fetch && git checkout code-feat/JIRA-1234-add-login
```


### 1. 개발 환경 설정

##### 1 - 1. Git 설정

- requirements (venv 사용 권장) 설치하기

```bash
pip install -r requirements-dev.txt
```

- pre-commit 훅 초기화 및 git 연동

```bash
pre-commit install
```

- 이후 편하게 코드작업을 시작해주세요.
    - 윈도우 사용자라면 pre-commit-config.yaml의 주석 처리된 내용을 참고해주세요.
    - main, master, dev 등의 브랜치에서는 CI 관련 스크립트가 작동하지 않습니다.
