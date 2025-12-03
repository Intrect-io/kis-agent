#!/bin/bash
# =============================================================================
# Claude Code 자동 코드 리뷰 스크립트
# =============================================================================
# 목적: 매일 정해진 시간에 Claude Code로 코드 리뷰 수행
# 생성일: 2025-12-01
# 사용법: ./scripts/claude_code_review.sh [--full | --quick | --security]
# 크론 예시: 0 9 * * 1-5 /home/unohee/dev/STONKS/scripts/claude_code_review.sh
# =============================================================================

set -e

# === 설정 ===
PROJECT_ROOT="/home/unohee/dev/STONKS"
REPORT_DIR="${PROJECT_ROOT}/reports/code_review"
LOG_DIR="${PROJECT_ROOT}/logs"
VENV_PATH="${HOME}/RTX_ENV/bin/activate"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DATE_ONLY=$(date +"%Y-%m-%d")

# 리포트 파일
REPORT_FILE="${REPORT_DIR}/review_${TIMESTAMP}.md"
SUMMARY_FILE="${REPORT_DIR}/latest_summary.md"
LOG_FILE="${LOG_DIR}/claude_code_review_${DATE_ONLY}.log"

# === 함수 정의 ===

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

ensure_dirs() {
    mkdir -p "$REPORT_DIR"
    mkdir -p "$LOG_DIR"
}

# Make audit 실행
run_make_audit() {
    log "📋 Make audit 실행 중..."
    cd "$PROJECT_ROOT"

    # audit 결과 캡처
    AUDIT_OUTPUT=$(source "$VENV_PATH" && make audit 2>&1) || true
    echo "$AUDIT_OUTPUT" >> "$LOG_FILE"

    # 결과 분석
    if echo "$AUDIT_OUTPUT" | grep -q "✅ 종합 감사 완료!"; then
        AUDIT_STATUS="✅ PASSED"
    else
        AUDIT_STATUS="⚠️ ISSUES FOUND"
    fi

    echo "$AUDIT_STATUS"
}

# Git 변경사항 분석
analyze_git_changes() {
    log "🔍 Git 변경사항 분석 중..."
    cd "$PROJECT_ROOT"

    # 최근 커밋 (24시간 이내)
    RECENT_COMMITS=$(git log --since="24 hours ago" --oneline 2>/dev/null | head -10)

    # 수정된 파일
    MODIFIED_FILES=$(git diff --name-only HEAD~5 2>/dev/null | head -20)

    # 스테이지되지 않은 변경
    UNSTAGED_CHANGES=$(git status --short 2>/dev/null | head -30)

    echo "RECENT_COMMITS:
$RECENT_COMMITS

MODIFIED_FILES:
$MODIFIED_FILES

UNSTAGED_CHANGES:
$UNSTAGED_CHANGES"
}

# Claude Code 리뷰 실행
run_claude_review() {
    local REVIEW_TYPE="${1:-quick}"
    log "🤖 Claude Code 리뷰 실행 중 (type: $REVIEW_TYPE)..."
    cd "$PROJECT_ROOT"

    # 최근 변경된 파일 목록 (Claude가 참조할 수 있도록)
    local CHANGED_FILES=$(git diff --name-only HEAD~5 2>/dev/null | grep -E '\.(py|ts|tsx)$' | head -10)
    local STAGED_FILES=$(git diff --cached --name-only 2>/dev/null | grep -E '\.(py|ts|tsx)$' | head -5)

    case "$REVIEW_TYPE" in
        full)
            # 전체 리뷰: 도구 사용 허용, 타임아웃 연장
            TIMEOUT=600
            TOOLS="--tools Read,Grep,Glob"
            PROMPT="프로젝트 코드 리뷰를 수행해줘. 다음 영역을 검사해:

1. **Python 코드 품질** (src/ 디렉토리):
   - src/api/ 엔드포인트 검사
   - src/services/ 서비스 레이어 검사

2. **TypeScript 코드 품질** (real-time-dashboard/frontend/src/):
   - 컴포넌트 구조 확인

3. **보안 취약점**: 하드코딩된 시크릿, SQL 인젝션 가능성

4. **최근 변경 파일 집중 검토**:
${CHANGED_FILES}

마크다운 형식으로 간결한 리포트를 작성해줘. 각 이슈는 파일경로:라인번호 형식으로 표시."
            ;;
        security)
            TIMEOUT=480
            TOOLS="--tools Read,Grep,Glob"
            PROMPT="보안 중심 코드 리뷰를 수행해줘:

1. **하드코딩된 시크릿 검색**: API 키, 비밀번호, 토큰
2. **SQL 인젝션 취약점**: f-string 또는 format()으로 SQL 쿼리 구성하는 코드
3. **경로 탐색 취약점**: 사용자 입력을 파일 경로에 직접 사용하는 코드
4. **XSS 취약점**: 프론트엔드에서 dangerouslySetInnerHTML 사용

src/ 디렉토리와 real-time-dashboard/frontend/src/ 디렉토리를 검사해.
마크다운 형식으로 발견된 이슈만 간결하게 보고해."
            ;;
        quick|*)
            TIMEOUT=180
            TOOLS=""  # 빠른 리뷰는 도구 없이
            PROMPT="다음 Git 변경사항을 기반으로 빠른 코드 리뷰를 해줘:

변경된 파일:
${CHANGED_FILES}

스테이지된 파일:
${STAGED_FILES}

각 파일에 대해:
1. 명백한 버그나 논리적 오류
2. 타입 안전성 문제
3. 에러 핸들링 누락

간결하게 3-5개 핵심 이슈만 마크다운으로 보고해."
            ;;
    esac

    # Claude Code 실행
    if command -v claude &> /dev/null; then
        log "Claude 실행: timeout=${TIMEOUT}s, tools=${TOOLS:-none}"

        # 도구 사용 여부에 따라 명령어 구성
        if [ -n "$TOOLS" ]; then
            REVIEW_OUTPUT=$(timeout "$TIMEOUT" claude -p $TOOLS "$PROMPT" 2>&1) || {
                local EXIT_CODE=$?
                if [ $EXIT_CODE -eq 124 ]; then
                    log "⚠️ Claude Code 시간 초과 (${TIMEOUT}초)"
                    REVIEW_OUTPUT="Claude Code 실행 시간 초과 (${TIMEOUT}초). --quick 모드를 시도하거나 타임아웃을 늘려주세요."
                else
                    log "⚠️ Claude Code 오류 (exit code: $EXIT_CODE)"
                    REVIEW_OUTPUT="Claude Code 실행 오류 (exit code: $EXIT_CODE)"
                fi
            }
        else
            REVIEW_OUTPUT=$(timeout "$TIMEOUT" claude -p "$PROMPT" 2>&1) || {
                local EXIT_CODE=$?
                if [ $EXIT_CODE -eq 124 ]; then
                    log "⚠️ Claude Code 시간 초과 (${TIMEOUT}초)"
                    REVIEW_OUTPUT="Claude Code 실행 시간 초과 (${TIMEOUT}초)"
                else
                    log "⚠️ Claude Code 오류 (exit code: $EXIT_CODE)"
                    REVIEW_OUTPUT="Claude Code 실행 오류 (exit code: $EXIT_CODE)"
                fi
            }
        fi
    else
        REVIEW_OUTPUT="Claude Code CLI가 설치되지 않았습니다. npm install -g @anthropic-ai/claude-code"
    fi

    echo "$REVIEW_OUTPUT"
}

# Lint 검사 실행
run_lint_check() {
    log "🔧 Lint 검사 실행 중..."
    cd "$PROJECT_ROOT"

    source "$VENV_PATH"

    # Ruff 검사
    RUFF_OUTPUT=$(ruff check src/ --output-format=concise 2>&1 | head -50) || true

    # Black 검사
    BLACK_OUTPUT=$(black --check src/ 2>&1 | tail -10) || true

    echo "RUFF:
$RUFF_OUTPUT

BLACK:
$BLACK_OUTPUT"
}

# 리포트 생성
generate_report() {
    local AUDIT_RESULT="$1"
    local GIT_CHANGES="$2"
    local CLAUDE_REVIEW="$3"
    local LINT_RESULT="$4"

    log "📝 리포트 생성 중..."

    cat > "$REPORT_FILE" << EOF
# 🔍 STONKS 코드 리뷰 리포트

**생성일시**: $(date '+%Y-%m-%d %H:%M:%S')
**프로젝트**: STONKS Real-time Trading Dashboard
**리뷰 타입**: ${REVIEW_MODE:-quick}

---

## 📋 1. Make Audit 결과

\`\`\`
${AUDIT_RESULT}
\`\`\`

---

## 🔄 2. Git 변경사항

### 최근 커밋 (24시간)
\`\`\`
$(echo "$GIT_CHANGES" | sed -n '/RECENT_COMMITS:/,/MODIFIED_FILES:/p' | grep -v 'RECENT_COMMITS:\|MODIFIED_FILES:')
\`\`\`

### 수정된 파일
\`\`\`
$(echo "$GIT_CHANGES" | sed -n '/MODIFIED_FILES:/,/UNSTAGED_CHANGES:/p' | grep -v 'MODIFIED_FILES:\|UNSTAGED_CHANGES:')
\`\`\`

### 스테이지되지 않은 변경
\`\`\`
$(echo "$GIT_CHANGES" | sed -n '/UNSTAGED_CHANGES:/,$p' | grep -v 'UNSTAGED_CHANGES:')
\`\`\`

---

## 🤖 3. Claude Code 리뷰

${CLAUDE_REVIEW}

---

## 🔧 4. Lint 검사 결과

### Ruff
\`\`\`
$(echo "$LINT_RESULT" | sed -n '/RUFF:/,/BLACK:/p' | grep -v 'RUFF:\|BLACK:')
\`\`\`

### Black
\`\`\`
$(echo "$LINT_RESULT" | sed -n '/BLACK:/,$p' | grep -v 'BLACK:')
\`\`\`

---

## 📊 5. 요약

- **Audit 상태**: ${AUDIT_RESULT%% *}
- **리포트 위치**: \`${REPORT_FILE}\`
- **다음 리뷰**: 내일 09:00 (평일)

---

*이 리포트는 Claude Code 자동 리뷰 시스템에 의해 생성되었습니다.*
EOF

    # 최신 요약 파일 업데이트
    cp "$REPORT_FILE" "$SUMMARY_FILE"

    log "✅ 리포트 생성 완료: $REPORT_FILE"
}

# Telegram 알림 (선택사항)
send_notification() {
    local STATUS="$1"
    local MESSAGE="$2"

    # Telegram 봇 설정이 있는 경우에만 실행
    if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d chat_id="$TELEGRAM_CHAT_ID" \
            -d text="🔍 STONKS 코드 리뷰 완료

상태: $STATUS
시간: $(date '+%Y-%m-%d %H:%M')

$MESSAGE" \
            -d parse_mode="Markdown" > /dev/null 2>&1 || true
    fi
}

# === 메인 실행 ===

main() {
    REVIEW_MODE="${1:-quick}"

    log "=========================================="
    log "🚀 STONKS 코드 리뷰 시작 (mode: $REVIEW_MODE)"
    log "=========================================="

    ensure_dirs

    # 1. Make audit 실행
    AUDIT_RESULT=$(run_make_audit)

    # 2. Git 변경사항 분석
    GIT_CHANGES=$(analyze_git_changes)

    # 3. Lint 검사
    LINT_RESULT=$(run_lint_check)

    # 4. Claude Code 리뷰 (선택적)
    if [ "$REVIEW_MODE" != "--skip-claude" ]; then
        CLAUDE_REVIEW=$(run_claude_review "$REVIEW_MODE")
    else
        CLAUDE_REVIEW="Claude Code 리뷰 스킵됨"
    fi

    # 5. 리포트 생성
    generate_report "$AUDIT_RESULT" "$GIT_CHANGES" "$CLAUDE_REVIEW" "$LINT_RESULT"

    # 6. 알림 전송
    if echo "$AUDIT_RESULT" | grep -q "PASSED"; then
        send_notification "✅ PASSED" "모든 검사 통과"
    else
        send_notification "⚠️ ISSUES" "일부 이슈 발견 - 리포트 확인 필요"
    fi

    log "=========================================="
    log "✅ 코드 리뷰 완료"
    log "리포트: $REPORT_FILE"
    log "=========================================="
}

# 인자 파싱
case "${1:-}" in
    --full)
        main "full"
        ;;
    --security)
        main "security"
        ;;
    --quick)
        main "quick"
        ;;
    --skip-claude)
        main "--skip-claude"
        ;;
    --help|-h)
        echo "사용법: $0 [--full | --quick | --security | --skip-claude]"
        echo ""
        echo "옵션:"
        echo "  --full        전체 코드 리뷰 (시간 소요)"
        echo "  --quick       빠른 리뷰 (기본값)"
        echo "  --security    보안 중심 리뷰"
        echo "  --skip-claude Claude Code 리뷰 스킵 (audit + lint만)"
        echo "  --help        이 도움말 표시"
        exit 0
        ;;
    *)
        main "quick"
        ;;
esac
