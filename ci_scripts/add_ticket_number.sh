#!/usr/bin/env bash

if [ -z "$BRANCHES_TO_SKIP" ]; then
  BRANCHES_TO_SKIP=(main master develop release)  # 제외할 브랜치 목록
fi

PROJECT_ID=DEQ  # 우리 프로젝트 이름

BRANCH_NAME=$(git symbolic-ref --short HEAD)
BRANCH_NAME="${BRANCH_NAME##*/}"

JIRA_ID=$(echo "$BRANCH_NAME" | grep -oE "$PROJECT_ID-[0-9]+")

BRANCH_EXCLUDED=$(printf "%s\n" "${BRANCHES_TO_SKIP[@]}" | grep -c "^$BRANCH_NAME$")

COMMIT_MSG_HEAD=$(head -n 1 "$1")

if [[ "$COMMIT_MSG_HEAD" == *:* ]]; then
  PREFIX=$(echo "$COMMIT_MSG_HEAD" | cut -d: -f1)  
  REMAINING_MSG=$(echo "$COMMIT_MSG_HEAD" | cut -d: -f2- | sed 's/^ //')
else
  PREFIX=""
  REMAINING_MSG="$COMMIT_MSG_HEAD"
fi

if [ -n "$JIRA_ID" ] && [ "$BRANCH_EXCLUDED" -eq 0 ] && ! [[ "$REMAINING_MSG" == "$JIRA_ID"* ]]; then
  if [ -n "$PREFIX" ]; then
    sed -i.bak -e "1s/^$COMMIT_MSG_HEAD/$PREFIX: $JIRA_ID $REMAINING_MSG/" "$1"
  else
    sed -i.bak -e "1s/^/$JIRA_ID /" "$1"
  fi
fi
