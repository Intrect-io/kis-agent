# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Agents

PyKIS uses **project-specific agents** optimized for this codebase. These agents are stored in `.claude/agents/` and are shared with the team via git.

### Available Agents

1. **pykis-tester** - Test coverage specialist
   - Boost test coverage from 52% → 70%+
   - Mock-based unit testing
   - pytest fixtures and edge cases
   - Usage: `pykis-tester agent를 사용해서 stock_price_api.py 커버리지를 올려줘`

2. **pykis-api-designer** - API integration expert
   - Add new Korea Investment API endpoints
   - Generate TypedDict response models
   - Apply Facade pattern
   - Korean docstring generation
   - Usage: `pykis-api-designer로 TR_ID FHKST03010100 API를 추가해줘`

3. **pykis-reviewer** - Code review specialist
   - Verify project rules (Korean docstrings, TypedDict, etc.)
   - Performance and security checks
   - Critical/Warning/Suggestion classification
   - Usage: `pykis-reviewer로 최근 변경사항을 리뷰해줘`

### Why Project Agents?

- **Context efficiency**: Only load relevant knowledge for PyKIS
- **Team consistency**: All developers use the same agents
- **Customizable**: Tailored to PyKIS patterns (Facade, TypedDict, Korean docs)
- **Version controlled**: Agents evolve with the project

### Reusable Skill

The `/setup-project-agents` skill can be used in other projects to automatically generate project-specific agents. See `.claude/commands/setup-project-agents.md` for details.

## Task Master AI Instructions
**Import Task Master's development workflow commands and guidelines, treat as if import is in the main CLAUDE.md file.**
@./.taskmaster/CLAUDE.md

## Project Overview

**PyKIS** is a high-performance Python wrapper for Korea Investment & Securities (한국투자증권) OpenAPI. It provides comprehensive trading functionality for Korean stock markets (KOSPI, KOSDAQ, NXT), domestic futures/options (KOSPI200), and overseas futures/options with intelligent caching, rate limiting, real-time WebSocket data streaming, and TypedDict response models for type safety.

### Key Statistics
- **382 tests** passing with 52% code coverage
- **214 methods** with 100% type hinting
- **114 TypedDict** response models for API responses
- **Python 3.8-3.12** support with CI/CD on all versions
- **38 new API endpoints** for futures/options trading

## Architecture Overview

### Core Design Pattern: Facade + Delegation

The codebase uses a **Facade pattern with intelligent delegation** to organize API functionality:

```
Agent (Top-level Facade)
├── StockAPI (Package Facade - pykis.stock.StockAPI)
│   ├── StockPriceAPI (Price & quote data)
│   ├── StockMarketAPI (Market rankings & trends)
│   └── StockInvestorAPI (Investor trends & analytics)
├── AccountAPI (Account balance & queries)
├── ProgramTradeAPI (Program trading analytics)
├── InterestStockAPI (Interest stock management)
├── Futures (Domestic futures/options - pykis.futures.Futures)
│   ├── FuturesPriceAPI (11 price/quote methods)
│   ├── FuturesAccountAPI (6 account methods)
│   ├── FuturesOrderAPI (6 order methods)
│   ├── FuturesCodeGenerator (Contract code generation)
│   └── FuturesHistoricalAPI (Historical minute bars)
├── OverseasFutures (Overseas futures/options - pykis.overseas_futures.OverseasFutures)
│   ├── OverseasFuturesPriceAPI (8 price methods)
│   ├── OverseasFuturesAccountAPI (9 account methods)
│   └── OverseasFuturesOrderAPI (2 order methods)
└── WebSocket (Real-time data streaming)
```

**IMPORTANT**: The file `pykis/stock/api.py` contains legacy `StockAPI` with a DEPRECATION NOTICE. The actual facade is in `pykis/stock/__init__.py` which delegates to specialized APIs. When working with stock-related code:
- Use `from pykis.stock import StockAPI` (the facade)
- The facade auto-delegates via `__getattr__` to child APIs
- Avoid modifying `pykis/stock/api.py` directly

### Key Components

1. **Agent (pykis/core/agent.py)**: Main entry point combining all APIs
2. **KISClient (pykis/core/client.py)**: Low-level HTTP client with 100+ endpoint definitions
3. **RateLimiter (pykis/core/rate_limiter.py)**: Adaptive rate limiting (18 RPS / 900 RPM empirically tested)
4. **TTLCache (pykis/core/cache.py)**: Thread-safe caching with 5s default TTL
5. **Auth (pykis/core/auth.py)**: OAuth2 token management with automatic refresh
6. **WebSocket (pykis/websocket/)**: Real-time data streaming with subscription management

### Response Type System

All API responses use TypedDict for type safety and IDE autocomplete:
- **pykis/responses/stock.py**: Stock price, orderbook, minute/daily price responses
- **pykis/responses/account.py**: Account balance, order history responses
- **pykis/responses/order.py**: Order execution, modification, cancellation responses
- **pykis/responses/futures.py**: Domestic futures/options responses (27 TypedDicts)
- **pykis/responses/overseas_futures.py**: Overseas futures/options responses (30 TypedDicts)
- **pykis/responses/common.py**: BaseResponse and shared types

Example:
```python
from pykis.responses.stock import StockPriceResponse

def get_stock_price(code: str) -> Optional[StockPriceResponse]:
    # response['output']['stck_prpr'] is fully typed
    ...
```

## Development Commands

### Environment Setup

```bash
# Activate virtual environment (recommended)
source ~/RTX_ENV/bin/activate

# Install development dependencies
pip install -e ".[dev,all]"

# Install with WebSocket support only
pip install -e ".[websocket]"
```

### Testing

```bash
# Run all unit tests (excludes integration tests requiring credentials)
pytest tests/ -v --cov=pykis

# Run tests for a specific module
pytest tests/unit/test_agent.py -v

# Run a single test
pytest tests/unit/test_agent.py::test_function_name -v

# Run with coverage report
pytest tests/ -v --cov=pykis --cov-report=html --cov-report=term-missing

# View HTML coverage report
open htmlcov/index.html  # or just navigate to htmlcov/index.html

# Run integration tests (requires real credentials in .env)
RUN_LIVE_TESTS=1 pytest tests/integration/ -v

# Run tests excluding integration and credential tests
pytest -v -m "not integration and not requires_credentials"
```

### Code Quality Tools

```bash
# Run all linting and formatting checks
ruff check pykis tests
ruff format pykis tests
black pykis tests
isort pykis tests

# Auto-fix issues
ruff check pykis tests --fix
black pykis tests
isort pykis tests

# Type checking (library only, tests not type-strict)
mypy pykis

# Security scan
bandit -r pykis -f json -o bandit_report.json
```

### CI/CD Pipeline

The project uses GitHub Actions with 5 jobs:
1. **test**: Runs on Python 3.8, 3.9, 3.10, 3.11, 3.12 in parallel
2. **lint**: Ruff, Black, isort, Flake8, MyPy checks
3. **security**: Trivy vulnerability scanning
4. **build**: Package building with setuptools
5. **deploy**: Automatic PyPI deployment on version tags

## Korean Language Philosophy

**PyKIS intentionally uses Korean docstrings** for several critical reasons:

1. **API Field Name Matching**: Korea Investment & Securities API responses use Korean field names like `stck_prpr` (주식 현재가). Korean docstrings allow direct 1:1 mapping with official API documentation.

2. **Error Message Matching**: API errors return Korean messages (`"주문가능수량이 부족합니다"`). Korean docstrings enable instant cross-referencing during debugging.

3. **Target Audience**: The API is Korea-specific and serves primarily Korean developers. Practical usability trumps international conventions in this context.

Example:
```python
"""
주식 현재가 조회

Returns:
    - output.stck_prpr: 주식 현재가  ← Matches API field exactly
    - output.prdy_vrss: 전일 대비
"""
```

**Do not translate docstrings to English unless explicitly requested by the user.**

## Rate Limiting & Performance

### Empirically Tested Limits (2025.09.21)

- **Official API Spec**: 20 RPS / 1000 RPM
- **Safe Operating Limits**: 18 RPS / 900 RPM (used in production)
- **Minimum Request Interval**: 50ms
- **Cache Hit Rate**: 80-95% (drastically reduces API calls)
- **Adaptive Backoff**: Automatically slows down on errors

### RateLimiter Usage

```python
limiter = RateLimiter(
    requests_per_second=18,
    requests_per_minute=900,
    enable_adaptive=True
)

wait_time = limiter.acquire(priority=1)  # 0=normal, 1=important, 2=urgent
# Make API call
limiter.report_success()  # or report_error() on failure
```

### Cache System

- **Default TTL**: 5 seconds for price data (balances real-time vs. API load)
- **Thread-safe**: Uses RLock for concurrent access
- **Auto-cleanup**: Removes expired entries when max_size reached
- **Statistics**: Tracks hit/miss rates via `get_stats()`

## Common Development Tasks

### Adding a New API Endpoint

1. Add endpoint definition to `pykis/core/client.py` in `API_ENDPOINTS` dict
2. Create method in appropriate API class (e.g., `StockPriceAPI`, `AccountAPI`)
3. Define TypedDict response in `pykis/responses/` if needed
4. Update `__all__` in relevant `__init__.py`
5. Add unit tests in `tests/unit/`
6. Update CHANGELOG.md

Example structure:
```python
# In pykis/stock/price_api.py
def new_api_method(self, param: str) -> Optional[NewResponseType]:
    """
    새로운 API 메서드

    Args:
        param: 파라미터 설명

    Returns:
        NewResponseType: 응답 구조
            - output.field1: 필드1 설명
    """
    return self.client.fetch_data(
        endpoint=API_ENDPOINTS["NEW_ENDPOINT"],
        tr_id="TRXXXXXX",
        params={"param": param}
    )
```

### Working with WebSocket

WebSocket implementation is in `pykis/websocket/`:
- **ws_agent.py**: Main WebSocket agent (recommended for new code)
- **client.py**: Legacy WebSocket client (maintained for compatibility)
- **enhanced_client.py**: Enhanced client with better error handling

To start WebSocket:
```python
from pykis import Agent

agent = Agent(...)
ws_client = agent.websocket(
    stock_codes=["005930", "035420"],
    enable_index=True,
    enable_program_trading=True
)

import asyncio
asyncio.run(ws_client.start())
```

### Testing with Credentials

1. Create `.env` file with:
```
KIS_APP_KEY=your_key
KIS_APP_SECRET=your_secret
KIS_ACCOUNT_NO=your_account
KIS_ACCOUNT_CODE=01
KIS_BASE_URL=https://openapi.koreainvestment.com:9443
```

2. Run tests:
```bash
RUN_LIVE_TESTS=1 pytest tests/integration/ -v
```

3. Mark credential-dependent tests:
```python
@pytest.mark.requires_credentials
def test_with_real_api():
    ...
```

## MCP Server

PyKIS includes an **MCP (Model Context Protocol) server** in `pykis-mcp-server/` that exposes 58 tools for Claude and other AI assistants. Configuration in `.mcp.json`:

```json
{
  "mcpServers": {
    "pykis-local": {
      "command": "python",
      "args": ["-m", "pykis_mcp_server"],
      "env": {
        "KIS_APP_KEY": "...",
        "KIS_SECRET": "...",
        ...
      }
    }
  }
}
```

## Important Files

- **pyproject.toml**: Package metadata, dependencies, tool configs
- **CHANGELOG.md**: Version history and feature changes
- **.github/workflows/ci-cd.yml**: Complete CI/CD pipeline definition
- **docs/architecture/websocket-architecture.md**: WebSocket system design (C4 diagrams)
- **docs/architecture/futures-architecture.md**: Futures API architecture (C4 diagrams)
- **docs/architecture/futures-api-mapping.md**: Futures API endpoint mapping
- **docs/architecture/futures-response-models.md**: Futures TypedDict models
- **docs/RATE_LIMITER_GUIDE.md**: Detailed rate limiter documentation
- **examples/**: Usage examples for various features
- **examples/futures_code_generator_example.py**: Futures contract code generation examples

## Testing Philosophy

- **Unit tests** mock API responses and test logic in isolation
- **Integration tests** use real API credentials (marked with `@pytest.mark.requires_credentials`)
- **Coverage target**: 52% current, aiming for 70%+ (prioritize core modules)
- **Test naming**: `test_<module>_<function>_<scenario>.py`

High-priority coverage areas:
- `pykis/core/`: 70%+ target (auth, client, rate_limiter)
- `pykis/stock/`: 60%+ target
- `pykis/account/`: 60%+ target
- `pykis/websocket/`: Currently 64%, maintain or improve

## Common Pitfalls

1. **Stock API Import**: Always use `from pykis.stock import StockAPI` (facade), not `from pykis.stock.api import StockAPI` (legacy)
2. **Korean Field Names**: API responses use Korean-based field names like `stck_prpr`, `prdy_vrss` - keep docstrings Korean
3. **Rate Limiting**: Use 18 RPS / 900 RPM, not the official 20/1000 spec (empirically safer)
4. **Cache TTL**: Default 5s is optimized for price data - adjust per use case
5. **TypedDict Usage**: All new API methods should return TypedDict responses for IDE support
6. **Test Markers**: Use `@pytest.mark.integration` and `@pytest.mark.requires_credentials` appropriately
7. **Futures Code Format**: Use `101S03` format (product+series+month), not year-based codes
8. **Futures Account**: Futures APIs require account_code="03" (선물옵션 계좌)

## Version Information

- Current version: **1.2.0** (in `pyproject.toml` and `pykis/responses/__init__.py`)
- Package version in `pykis/__init__.py`: **0.1.22** (legacy compatibility)
- Update both when releasing

## Additional Resources

- Official API Portal: https://apiportal.koreainvestment.com
- Package on PyPI: https://pypi.org/project/pykis/
- GitHub Issues: https://github.com/unohee/pykis/issues
