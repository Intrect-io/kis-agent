# 🔍 pykis 코드 리뷰 리포트

**생성일시**: 2025-12-03 11:35:21
**프로젝트**: pykis
**프로젝트 경로**: /home/unohee/dev/tools/pykis
**리뷰 타입**: full

---

## 📋 1. Make Audit 결과

```
[2025-12-03 11:35:01] 📋 프로젝트 감사 실행 중...
[2025-12-03 11:35:01]   → Makefile 없음: 기본 감사 수행
⚠️ ISSUES FOUND
```

---

## 🔄 2. Git 변경사항

### 최근 커밋 (24시간)
```

```

### 수정된 파일
```
pykis/account/api.py
pykis/core/agent.py
pykis/core/auth.py
pykis/core/base_api.py
pykis/core/client.py
pykis/core/exceptions.py
pykis/core/rate_limiter.py
pykis/program/trade.py
pykis/responses/__init__.py
pykis/responses/account.py
pykis/responses/order.py
pykis/responses/stock.py
pykis/stock/api_facade.py
pykis/stock/interest.py
pykis/stock/investor.py
pykis/stock/investor_api.py
pykis/stock/price_api.py
pykis/utils/__init__.py
pykis/utils/sector_code.py
tests/integration/test_stock_api_integration.py
```

### 스테이지되지 않은 변경
```
 M pykis/account/api.py
 M pykis/core/agent.py
 M pykis/core/auth.py
 M pykis/core/base_api.py
 M pykis/core/client.py
 M pykis/core/exceptions.py
 M pykis/core/rate_limiter.py
 M pykis/program/trade.py
 M pykis/responses/__init__.py
 M pykis/responses/account.py
 M pykis/responses/order.py
 M pykis/responses/stock.py
 M pykis/stock/api_facade.py
 M pykis/stock/interest.py
 M pykis/stock/investor.py
 M pykis/stock/investor_api.py
 M pykis/utils/__init__.py
 M pykis/utils/sector_code.py
 M tests/integration/test_stock_api_integration.py
 M tests/test_cache_integration.py
 M tests/test_cache_ttl.py
 M tests/test_exception_handling.py
 M tests/test_inquire_daily_ccld.py
 M tests/test_new_apis_integration_251010.py
 M tests/unit/test_account_api.py
 M tests/unit/test_agent_facade_delegation.py
 M tests/unit/test_agent_order_api.py
 M tests/unit/test_auth.py
 M tests/unit/test_client.py
 M tests/unit/test_pagination.py
```

---

## 🤖 3. Claude Code 리뷰

[2025-12-03 11:35:09] 🤖 Claude Code 리뷰 실행 중 (type: full)...
[2025-12-03 11:35:09] Claude 실행: timeout=600s, tools=--tools Read,Grep,Glob
[2025-12-03 11:35:21] ⚠️ Claude Code 오류 (exit code: 1)
Claude Code 실행 오류 (exit code: 1)

---

## 🔧 4. Lint 검사 결과

### Ruff
```
warning: The top-level linter settings are deprecated in favour of their counterparts in the `lint` section. Please update the following options in `pykis-mcp-server/pyproject.toml`:
  - 'ignore' -> 'lint.ignore'
  - 'select' -> 'lint.select'
  - 'per-file-ignores' -> 'lint.per-file-ignores'
docs/api_reference/account_complete.py:8:1: I001 [*] Import block is un-sorted or un-formatted
docs/api_reference/account_complete.py:8:20: F401 [*] `typing.List` imported but unused
docs/api_reference/stock_complete.py:8:1: I001 [*] Import block is un-sorted or un-formatted
docs/api_reference/stock_complete.py:8:20: F401 [*] `typing.List` imported but unused
examples/StockMonitor.py:13:1: E402 Module level import not at top of file
examples/StockMonitor.py:14:1: E402 Module level import not at top of file
examples/export_trading_history.py:54:5: F821 Undefined name `KISClient`
examples/export_trading_history.py:83:20: F821 Undefined name `agent`
examples/export_trading_history.py:104:20: F821 Undefined name `agent`
examples/export_trading_history.py:123:20: F821 Undefined name `agent`
examples/export_trading_history.py:143:44: F821 Undefined name `agent`
examples/export_trading_history.py:185:20: F821 Undefined name `agent`
examples/index_tickprice_example.py:57:14: F821 Undefined name `agent`
examples/index_tickprice_example.py:78:14: F821 Undefined name `agent`
examples/index_tickprice_example.py:99:14: F821 Undefined name `agent`
examples/list_interest_groups.py:15:1: E402 Module level import not at top of file
examples/minute_candle_crawler.py:66:9: E722 Do not use bare `except`
examples/minute_candle_crawler.py:106:17: E722 Do not use bare `except`
examples/pykis.ipynb:cell 21:9:13: F821 Undefined name `KisWebSocket`
examples/run.py:49:1: E402 Module level import not at top of file
examples/run.py:53:1: E402 Module level import not at top of file
examples/run.py:125:20: E701 Multiple statements on one line (colon)
examples/run.py:169:20: E701 Multiple statements on one line (colon)
examples/run.py:176:20: E701 Multiple statements on one line (colon)
examples/run.py:331:28: E701 Multiple statements on one line (colon)
examples/run.py:362:24: E701 Multiple statements on one line (colon)
examples/test_helpers.py:204:9: E722 Do not use bare `except`
examples/test_interest_stocks.py:13:1: E402 Module level import not at top of file
examples/test_interest_stocks.py:50:19: F541 [*] f-string without any placeholders
examples/test_interest_stocks.py:65:19: F541 [*] f-string without any placeholders
examples/test_interest_stocks.py:69:23: F541 [*] f-string without any placeholders
examples/test_pbar_tratio_with_chart.py:36:22: F401 `pandas` imported but unused; consider using `importlib.util.find_spec` to test for availability
examples/test_pbar_tratio_with_chart.py:37:23: F401 `seaborn` imported but unused; consider using `importlib.util.find_spec` to test for availability
pykis-mcp-server/src/pykis_mcp_server/__main__.py:2:1: I001 [*] Import block is un-sorted or un-formatted
pykis-mcp-server/src/pykis_mcp_server/config.py:2:1: I001 [*] Import block is un-sorted or un-formatted
pykis-mcp-server/src/pykis_mcp_server/errors.py:2:1: I001 [*] Import block is un-sorted or un-formatted
pykis-mcp-server/src/pykis_mcp_server/server.py:2:1: I001 [*] Import block is un-sorted or un-formatted
pykis-mcp-server/src/pykis_mcp_server/server.py:2:8: F401 [*] `asyncio` imported but unused
pykis-mcp-server/src/pykis_mcp_server/server.py:45:13: B904 Within an `except` clause, raise exceptions with `raise ... from err` or `raise ... from None` to distinguish them from errors in exception handling
pykis-mcp-server/src/pykis_mcp_server/server.py:70:13: B904 Within an `except` clause, raise exceptions with `raise ... from err` or `raise ... from None` to distinguish them from errors in exception handling
pykis-mcp-server/src/pykis_mcp_server/server.py:75:1: I001 [*] Import block is un-sorted or un-formatted
pykis-mcp-server/src/pykis_mcp_server/server.py:76:5: F401 [*] `.tools.stock_tools` imported but unused
pykis-mcp-server/src/pykis_mcp_server/server.py:77:5: F401 [*] `.tools.account_tools` imported but unused
pykis-mcp-server/src/pykis_mcp_server/server.py:78:5: F401 [*] `.tools.order_tools` imported but unused
pykis-mcp-server/src/pykis_mcp_server/server.py:79:5: F401 [*] `.tools.investor_tools` imported but unused
pykis-mcp-server/src/pykis_mcp_server/server.py:80:5: F401 [*] `.tools.utility_tools` imported but unused
```

### Black
```
would reformat /home/unohee/dev/tools/pykis/examples/run.py
would reformat /home/unohee/dev/tools/pykis/pykis-mcp-server/src/pykis_mcp_server/tools/orchestration_tools.py
would reformat /home/unohee/dev/tools/pykis/pykis-mcp-server/src/pykis_mcp_server/tools/investor_tools.py
would reformat /home/unohee/dev/tools/pykis/tests/unit/test_base_api.py
would reformat /home/unohee/dev/tools/pykis/tests/unit/test_client.py
would reformat /home/unohee/dev/tools/pykis/tests/unit/test_stock_price_api.py
would reformat /home/unohee/dev/tools/pykis/pykis/core/agent.py

Oh no! 💥 💔 💥
54 files would be reformatted, 91 files would be left unchanged.
```

---

## 📊 5. 요약

- **Audit 상태**: [2025-12-03
- **리포트 위치**: `/home/unohee/dev/tools/pykis/reports/code_review/review_20251203_113501.md`
- **다음 리뷰**: 내일 09:00 (평일)

---

*이 리포트는 Claude Code 자동 리뷰 시스템에 의해 생성되었습니다.*
