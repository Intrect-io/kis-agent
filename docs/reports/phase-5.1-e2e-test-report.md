# Phase 5.1 E2E 테스트 보고서

**작성일**: 2025-12-18
**관련 이슈**: INT-111 (PyKIS V2 업데이트), INT-139 (E2E 테스트)
**상태**: 진행 중 (버그 수정 완료, 검증 대기)

---

## 1. 개요

MCP 서버의 통합 도구(Consolidated Tools)에 대한 E2E 테스트를 수행하여 실제 API 연동 상태를 검증했습니다.

## 2. 테스트 환경

```yaml
MCP Server: pykis-local (FastMCP 2.0 STDIO)
Agent: PyKIS Agent (account: 68867843)
Rate Limiter: 18 RPS / 900 RPM
Tools: 124개 (18 consolidated + 106 legacy)
```

## 3. E2E 테스트 결과

### 3.1 성공한 도구들 (8/12 테스트)

| 도구명 | 유형 | 테스트 케이스 | 결과 |
|--------|------|--------------|------|
| `stock_quote` | 통합 | detail (005930) | ✅ 성공 - 삼성전자 107,600원 |
| `stock_chart` | 통합 | daily_30 (005930) | ✅ 성공 - 30일 일봉 데이터 |
| `investor_flow` | 통합 | stock (005930) | ✅ 성공 - 투자자별 매매동향 |
| `account_query` | 통합 | balance | ✅ 성공 - 22개 포지션 조회 |
| `index_data` | 통합 | current (KOSPI) | ✅ 성공 - KOSPI 3994.51 |
| `broker_trading` | 통합 | current (005930) | ✅ 성공 - 증권사별 매매동향 |
| `get_stock_price` | 레거시 | 005930 | ✅ 성공 - 동일 결과 |
| `get_market_rankings` | 레거시 | volume | ✅ 성공 (결과 empty) |

### 3.2 실패한 도구들 (4/12 테스트)

| 도구명 | 유형 | 에러 메시지 | 근본 원인 |
|--------|------|------------|----------|
| `market_ranking` | 통합 | "Unknown error" | api_facade ↔ market_api 파라미터 불일치 |
| `get_volume_rank` | 레거시 | "Unknown error" | 동일 원인 |
| `get_fluctuation_rank` | 레거시 | "Unknown error" | 동일 원인 |
| `get_top_gainers` | 레거시 | 인자 개수 오류 | 함수 시그니처 불일치 |

## 4. 발견된 버그 및 수정

### 4.1 [버그 1] 에러 메시지에 rt_cd/msg_cd 미표시

**증상**: API 오류 시 "Unknown error"만 표시되어 디버깅 어려움

**원인**: `validate_api_response()`에서 `msg1`이 비어있을 때 fallback 메시지가 불친절함

**수정 (errors.py:171-176)**:
```python
# Before
error = APIError(f"{operation} failed: {msg1 or 'Unknown error'}", ...)

# After
if msg1:
    error_message = msg1
else:
    error_message = f"rt_cd={rt_cd}, msg_cd={msg_cd}"
error = APIError(f"{operation} failed: {error_message}", ...)
```

**상태**: ✅ 코드 수정 완료 (MCP 서버 재시작 후 검증 필요)

### 4.2 [버그 2] market_ranking 파라미터 불일치

**증상**: `market_ranking` 통합 도구 호출 시 항상 실패

**원인 분석**:
1. MCP 도구가 `agent.get_fluctuation_rank(market, sign)` 호출
2. Agent가 `stock_api.get_fluctuation_rank(fid_cond_mrkt_div_code, ...)` 전달
3. api_facade가 FID 파라미터를 market_api에 위치 인자로 전달
4. market_api.get_fluctuation_rank는 `(market="ALL", count="50", ...)` 기대
5. 결과적으로 `count="0"`으로 설정되어 0개 결과 요청

**수정 (consolidated_tools.py:218-310)**:
- api_facade 경유 대신 `market_api._make_request_dict()` 직접 호출
- 올바른 API 엔드포인트와 파라미터 사용
- 시장 코드/input_iscd 매핑 로직 추가

**상태**: ✅ 코드 수정 완료 (MCP 서버 재시작 후 검증 필요)

## 5. 테스트 자동화 결과

```
pytest pykis-mcp-server/tests/test_consolidated_tools.py
================== 26 passed in 6.94s ===================
```

모든 단위 테스트 통과 확인.

## 6. 수정된 파일

| 파일 | 변경 내용 |
|------|----------|
| `pykis-mcp-server/src/pykis_mcp_server/errors.py` | rt_cd/msg_cd 에러 메시지 표시 개선 |
| `pykis-mcp-server/src/pykis_mcp_server/tools/consolidated_tools.py` | market_ranking 직접 API 호출로 변경 |

## 7. 다음 단계

### 즉시 필요 작업
1. **MCP 서버 재시작** - 코드 변경사항 적용 필요
2. **버그 수정 검증** - 재시작 후 market_ranking 재테스트
3. **에러 메시지 검증** - rt_cd/msg_cd 표시 확인

### 후속 작업 (Phase 5.2, 5.3)
- [ ] IDE/Agent 호환성 테스트 (INT-140)
- [ ] CHANGELOG 및 마이그레이션 가이드 (INT-141)

## 8. 참고: PyKIS API 계층 구조 이슈

E2E 테스트 중 발견된 아키텍처 문제:

```
Agent.get_fluctuation_rank(fid_params)
    ↓
api_facade.get_fluctuation_rank(fid_params)
    ↓ (위치 인자로 전달)
market_api.get_fluctuation_rank(user_friendly_params)  ← 불일치!
```

**권장 사항**:
1. api_facade에서 FID → user-friendly 파라미터 매핑 로직 추가
2. 또는 market_api에 raw FID 파라미터 버전 메서드 추가
3. 장기적으로 일관된 API 설계 필요

---

**작성자**: Claude Code
**검토자**: -
