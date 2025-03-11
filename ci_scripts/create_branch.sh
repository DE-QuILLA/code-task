#!/bin/bash

# 지라 티켓 넘버와 타입 입력
read -p "브랜치를 분기 할 원본 브랜치를 입력하세요 ()" ORIGIN_BRANCH
read -p "티켓 타입을 입력하세요 (feat, fix, chore 등): " TYPE
read -p "티켓 번호를 입력하세요 (예: 123): " NUMBER
read -p "브랜치 설명을 입력하세요 (예: add-login-api): " DESC

# 브랜치 네임 생성
PROJECT_ID=DEQ
BRANCH_NAME="${TYPE}/${PROJECT_ID}-${NUMBER}-${DESC}"

# 원본 브랜치로 전환
git swtich "$ORIGIN_BRANCH"

# 브랜치 생성 및 전환
git checkout -b "$BRANCH_NAME"

echo "✅ 브랜치가 생성되었습니다: $BRANCH_NAME"
