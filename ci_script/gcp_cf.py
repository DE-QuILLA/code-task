import functions_framework  # GCP Functions용 데코레이터
import requests
import os

# 환경 변수로 깃허브 정보 저장 (보안 위해!)
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_OWNER = os.environ.get("REPO_OWNER")
REPO_NAME = os.environ.get("REPO_NAME")
BASE_BRANCH = "dev"

# 함수 시작
@functions_framework.http
def jira_webhook_to_github_branch(request):
    request_json = request.get_json(silent=True)
    print("📥 받은 데이터:", request_json)

    try:
        # Jira 이슈 정보 가져오기
        issue = request_json["issue"]
        jira_key = issue["key"]                    # ex) JIRA-1234
        summary = issue["fields"]["summary"]       # ex) feat-add-login

        # 브랜치명 만들기 (feat/add-login 등으로 파싱)
        branch_type, description = parse_summary(summary)
        branch_name = f"{branch_type}/{jira_key}-{description}"
        print(f"🔧 브랜치명 생성됨: {branch_name}")

        # 기본 브랜치 SHA 가져오기
        sha = get_branch_sha(BASE_BRANCH)
        print(f"📌 {BASE_BRANCH} 브랜치 SHA: {sha}")

        # 깃허브에 브랜치 생성 요청
        create_branch(branch_name, sha)

        return f"✅ 브랜치 생성 완료: {branch_name}", 200

    except Exception as e:
        print(f"❌ 에러 발생: {str(e)}")
        return f"❌ 에러 발생: {str(e)}", 500

# 요약(summary)에서 타입과 설명을 파싱 (code-feat-add-login → code-feat, add-login)
def parse_summary(summary):
    parts = summary.split("-", 2)

    if len(parts) != 2:
        raise ValueError("Summary 형식이 잘못되었습니다! ex) code-feat-add-login")
    
    branch_type = parts[0].lower()
    description = parts[1].lower().replace(" ", "-")
    return branch_type, description

# 기본 브랜치의 최신 커밋 SHA를 가져옴
def get_branch_sha(branch):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/ref/heads/{branch}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    sha = response.json()["object"]["sha"]
    return sha

# 브랜치 생성
def create_branch(branch_name, sha):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/refs"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "ref": f"refs/heads/{branch_name}",
        "sha": sha
    }
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 201:
        print(f"✅ 브랜치 {branch_name} 생성 성공!")
    else:
        print(f"❌ 브랜치 생성 실패: {response.status_code} - {response.text}")
        raise Exception(f"브랜치 생성 실패: {response.text}")
