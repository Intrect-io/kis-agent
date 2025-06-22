# Changelog

모든 주요 변경사항이 이 파일에 기록됩니다.

## [0.1.4] - 2024-06-22

### 수정됨
- 체결강도 관련 API 통합 및 정리
  - `get_volume_power` 메서드 중복 제거 및 통합
  - 올바른 API 엔드포인트 및 TR 코드 적용 (`/uapi/domestic-stock/v1/ranking/volume-power`, `FHPST01680000`)
  - 용어 통일: "거래량 파워" → "체결강도"로 변경
  - 거래량 급증도 관련 기능 제거 (존재하지 않는 API)

- 프로그램 매매 API 개선
  - 종목별 프로그램 매매와 시장 전체 프로그램 매매 API 분리
  - `get_program_trade_daily_summary`: 종목별 기능 유지
  - `get_program_trade_market_daily`: 새로운 시장 전체 API 추가
  - 올바른 엔드포인트 적용

- 등락률 순위 API 수정
  - `get_market_fluctuation` 메서드를 올바른 국내주식 등락률 순위 API로 수정
  - 엔드포인트: `/uapi/domestic-stock/v1/ranking/fluctuation`, TR: `FHPST01700000`

- 계좌 API 정리
  - 주문가능금액조회 엔드포인트 수정
  - `client.py`에 `INQUIRE_PSBL_ORDER` 상수 추가
  - 존재하지 않는 `get_total_evaluation` 메서드 제거

### 개선됨
- 분석 로직 독립화
  - `get_pgm_trade` 메서드를 `examples/program_trade_analysis.py`로 분리
  - `ProgramTradeAnalyzer` 클래스로 분석 기능 캡슐화
  - API와 분석 로직의 명확한 분리

- 조건검색 관련 버그 수정
  - `logger` 미정의 오류 수정: `logger` → `logging`으로 변경
  - 무한 재귀 호출 문제 해결: `get_condition_stocks_dict`에서 직접 API 호출하도록 수정

- Strategy 모듈 완전 제거
  - deprecated된 strategy 관련 import 및 메서드 모두 제거
  - `pykis/core/agent.py`에서 strategy 관련 코드 정리
  - `tests/integration/test_strategy.py` 파일 삭제

### 추가됨
- 종합 테스트 노트북 확장
  - 50개 이상의 메서드에 대한 포괄적인 테스트 추가
  - 계좌, 주식, 시장, 프로그램 매매, 조건검색 등 모든 영역 커버
  - 에러 처리 및 경계 조건 테스트 포함
  - 성능 및 캐싱 테스트 추가

### 제거됨
- 중복된 `get_volume_power` 메서드들 제거
- 존재하지 않는 거래량 급증도 API 관련 코드 제거
- Strategy 모듈 및 관련 의존성 완전 제거
- 미사용 및 잘못된 API 메서드들 정리

## [0.1.3] - 2024-06-19

### 변경됨
- ProgramTradeAPI 클래스 중복 제거 및 통합
  - `pykis/program/api.py`, `pykis/program/trade.py`, `pykis/stock/program_trade.py`의 중복 클래스 통합
  - 모든 import를 `pykis.program.trade`로 통일
  - deprecated 파일들에 안내 메시지 추가

### 개선됨
- 메서드명 개선
  - `get_program_trade_summary` → `get_program_trade_by_stock`으로 변경
  - 메서드명이 실제 기능과 일치하도록 수정
- `get_program_trade_by_stock`이 실제 API를 직접 호출하도록 수정
  - 종목별프로그램매매추이(체결) API 직접 호출
  - 날짜 파라미터 지원 추가

### 문서화
- README.md 업데이트
  - 프로그램 매매 관련 메서드 목록 업데이트
  - 사용 예시에 프로그램 매매 관련 예시 추가

## [0.1.2] - 2024-06-16

### 변경됨
- 프로젝트명을 `kis-agent`에서 `pykis`로 변경
- 패키지 구조 개선
  - `src` 디렉토리 제거
  - 메인 모듈을 `pykis`로 변경
- 클래스명 변경
  - `KIS_Agent` → `Agent`
  - `KISClient` → `Client`

## [0.1.1] - 2024-06-15

### 추가됨
- Postman 컬렉션의 모든 엔드포인트 구현
  - 국내주식: 휴장일, 기본정보, 재무제표, 투자의견 등
  - 국내주식: 체결강도 랭킹(거래량 파워) API 구현 및 정상 동작 확인
  - 해외주식: 시세, 뉴스, 권리정보 등
  - 채권: 시세 조회
  - 시장 분석: 거래량/등락률/수익률 순위 등

### 개선됨
- 로깅 시스템 개선
  - 각 API 호출에 대한 상세한 로깅 추가
  - 에러 메시지 한글화
  - 로그 포맷 통일화
- 국내주식 엔드포인트 실제 테스트 결과, 대부분 정상 동작함을 확인 (일부 미지원/폐지 API 및 파라미터 오류 등은 실제 서비스 상태에 따라 다를 수 있음)

### 변경됨
- `market.py` 구조 개선
  - 메서드명 표준화
  - 파라미터 타입 힌트 추가
  - 반환값 타입 명시

### 문서화
- 모든 API 메서드에 상세한 docstring 추가
  - 목적, 파라미터, 반환값 설명
  - 사용 예시 포함
  - 예외 처리 정보 추가

## [0.1.0] - 2025-06-11

### 추가됨
- 한국투자증권 OpenAPI 연동을 위한 기본 모듈 구조 구현
  - `core`: API 클라이언트, 인증, 설정 관리
  - `account`: 계좌 잔고 및 주문 관리
  - `stock`: 주식 시세 및 주문 처리
  - `program`: 프로그램 매매 정보 조회
  - `strategy`: 전략 실행 및 모니터링

### 개선됨
- 모든 모듈 및 클래스에 상세한 docstring 추가
  - 모듈 레벨: 목적, 기능, 의존성, 연관 모듈, 사용 예시
  - 클래스 레벨: 목적, 속성, 사용 예시
  - 메서드 레벨: 목적, 매개변수, 반환값, 주의사항, 사용 예시

### 변경됨
- `program_trade.py`의 메서드명 변경
  - `get_program_trade_detail` → `get_program_trade_period_detail`
  - `get_program_trade_ratio` → `get_pgm_trade`

### 제거됨
- `scripts/convert_yaml_to_env.py`: 사용하지 않는 스크립트 제거

### 보안
- API 키 및 인증 정보를 환경 변수로 관리하도록 변경
- 민감한 정보가 포함된 파일들을 .gitignore에 추가

### 문서화
- 각 모듈의 README.md 파일 추가
- API 사용 예시 및 설명 추가
- 코드 주석 개선 및 한글화

### 기술적 부채
- `program_trade.py`의 주석 처리된 `get_program_trade_summary` 메서드 재구현 필요
- 일부 API 응답 처리 로직 개선 필요
- 에러 처리 및 재시도 로직 보완 필요 