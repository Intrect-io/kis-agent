# Setup Project Agents

프로젝트별 최적화된 에이전트를 자동 생성하는 스킬입니다.

## 목적

전역 에이전트 대신 프로젝트 컨텍스트에 최적화된 에이전트를 `.claude/agents/`에 설정하여:
- 불필요한 컨텍스트 소비 방지
- 프로젝트 특성에 맞는 전문가 에이전트 활용
- 팀 전체가 동일한 에이전트 공유 (git으로 체크인)

## 실행 단계

### 1. 프로젝트 분석
다음 정보를 수집하세요:
- 프로젝트 언어 (Python, TypeScript, Go 등)
- 프레임워크 (Django, FastAPI, React 등)
- 주요 작업 (API 개발, 테스트, 데이터 분석 등)
- 프로젝트 규칙 (CLAUDE.md, README.md 참고)

### 2. 전역 에이전트 비활성화
```bash
if [ -d ~/.claude/agents ]; then
    mv ~/.claude/agents ~/.claude/agents.disabled
    echo "✅ 전역 에이전트 비활성화 완료"
fi
```

### 3. 프로젝트 에이전트 디렉토리 생성
```bash
mkdir -p .claude/agents
```

### 4. 에이전트 생성

프로젝트 타입에 따라 3-5개 전문 에이전트를 생성하세요.

#### Python API 프로젝트 예시
- **tester**: 단위 테스트 작성, 커버리지 향상
- **api-designer**: API 엔드포인트 추가
- **reviewer**: 코드 리뷰, 규칙 준수 검증

#### Frontend 프로젝트 예시
- **component-builder**: React 컴포넌트 작성
- **style-expert**: CSS/Tailwind 스타일링
- **reviewer**: 접근성, 성능, 코드 품질 검증

#### Data Science 프로젝트 예시
- **data-analyst**: 데이터 분석, 시각화
- **model-trainer**: 머신러닝 모델 학습
- **notebook-cleaner**: Jupyter 노트북 정리

### 5. 에이전트 템플릿

각 에이전트는 다음 구조를 따릅니다:

```markdown
---
name: agent-name
description: 에이전트 설명 (Claude가 언제 사용할지 판단)
tools: Read, Grep, Glob, Write, Edit, Bash
model: sonnet
permissionMode: default
---

# 에이전트 역할

당신은 [프로젝트]의 [역할] 전문가입니다.

## 프로젝트 컨텍스트

- **프로젝트**: [이름]
- **기술 스택**: [언어/프레임워크]
- **주요 작업**: [작업 유형]
- **프로젝트 규칙**: [CLAUDE.md 참고]

## 핵심 원칙

1. [원칙 1]
2. [원칙 2]
3. [원칙 3]

## 작업 플로우

### 1. [단계 1]
설명...

### 2. [단계 2]
설명...

## 호출 예시

\```
[agent-name] agent를 사용해서 [작업]을 해줘
\```
```

### 6. 검증

에이전트가 올바르게 생성되었는지 확인:
```bash
ls -la .claude/agents/
```

각 에이전트 파일이 존재하고 frontmatter가 올바른지 확인하세요.

### 7. 사용법

에이전트는 자동으로 로드됩니다. 다음과 같이 사용:
```
tester agent를 사용해서 커버리지를 올려줘
api-designer agent로 새 엔드포인트를 추가해줘
reviewer agent로 최근 변경사항을 리뷰해줘
```

## 프로젝트별 에이전트 예시

### Python API 프로젝트 (FastAPI, Django)
```markdown
---
name: api-tester
description: API 테스트 작성 전문가
tools: Read, Write, Edit, Bash
---

당신은 API 테스트를 작성하는 전문가입니다.

- pytest fixture 활용
- Mock 기반 단위 테스트
- Integration test 작성
- 70% 커버리지 목표
```

### Frontend 프로젝트 (React, Vue)
```markdown
---
name: component-builder
description: React 컴포넌트 작성 전문가
tools: Read, Write, Edit
---

당신은 React 컴포넌트를 작성하는 전문가입니다.

- TypeScript 타입 정의
- Props validation
- Accessible HTML
- Tailwind CSS 스타일링
```

### Data Science 프로젝트
```markdown
---
name: data-analyst
description: 데이터 분석 전문가
tools: Read, Write, Bash
---

당신은 데이터 분석 전문가입니다.

- pandas, numpy 활용
- matplotlib, seaborn 시각화
- 통계 분석
- Jupyter 노트북 작성
```

## 베스트 프랙티스

1. **3-5개 에이전트**: 너무 많으면 오히려 혼란
2. **명확한 역할 분담**: 각 에이전트의 책임 명확히
3. **프로젝트 규칙 포함**: CLAUDE.md 내용 참조
4. **Git 체크인**: 팀 전체가 동일한 에이전트 사용
5. **정기 업데이트**: 프로젝트 변화에 따라 에이전트도 업데이트

## 주의사항

- 전역 에이전트는 `~/.claude/agents.disabled`로 백업됨
- 복구하려면: `mv ~/.claude/agents.disabled ~/.claude/agents`
- 프로젝트 에이전트가 전역 에이전트보다 우선순위 높음

## 자동화 스크립트

이 스킬을 다른 프로젝트에서도 사용하려면:

1. 이 파일을 복사: `cp .claude/commands/setup-project-agents.md ../other-project/.claude/commands/`
2. Claude에서 실행: `/setup-project-agents`
3. 프로젝트 분석 후 자동으로 에이전트 생성

---

**이 스킬을 실행하면 프로젝트에 맞는 에이전트가 자동 생성됩니다.**
