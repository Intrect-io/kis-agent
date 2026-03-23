# Bridge 메시지 프로토콜 정의

## 개요

Bridge 메시지 프로토콜은 TypeScript CLI와 Python 백엔드 간의 subprocess 통신을 위한 JSON 기반 표준 형식입니다.

- **프로토콜 버전**: 1.0
- **통신 방식**: JSON over stdin/stdout
- **전송 형식**: UTF-8 인코딩

## 요청 메시지 (Request)

### 메시지 구조

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "price",
  "args": ["005930"],
  "kwargs": {
    "daily": true
  }
}
```

### 필드 정의

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `id` | string | ✓ | 요청 고유 식별자 (UUID 형식) |
| `method` | string | ✓ | 호출할 메서드 이름 |
| `args` | array | ✗ | 위치 인자 목록 (기본값: []) |
| `kwargs` | object | ✗ | 키워드 인자 딕셔너리 (기본값: {}) |

### 유효성 검증 규칙

1. **id**: 필수, 문자열, UUID 형식
2. **method**: 필수, 문자열, 패턴 `^[a-zA-Z_][a-zA-Z0-9_]*$`
3. **args**: 배열 (존재하는 경우)
4. **kwargs**: 객체 (존재하는 경우)

### 사용 예시

#### 예시 1: 주식 현재가 조회

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "price",
  "args": ["005930"],
  "kwargs": {}
}
```

응답 기대값:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "result": {
    "stock": {
      "code": "005930",
      "name": "삼성전자",
      "price": 70000,
      "changeRate": 1.5
    }
  },
  "error": null
}
```

#### 예시 2: 계좌 잔고 조회 (옵션 포함)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "method": "balance",
  "kwargs": {
    "holdings": true,
    "include_orders": false
  }
}
```

응답 기대값:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "result": {
    "account": {
      "totalBalance": 1000000,
      "availableBalance": 500000,
      "cashBalance": 50000
    },
    "holdings": [
      {
        "code": "005930",
        "quantity": 10,
        "avgPrice": 65000,
        "currentPrice": 70000
      }
    ]
  },
  "error": null
}
```

#### 예시 3: 직접 API 호출

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "method": "query",
  "kwargs": {
    "endpoint": "GetStockInfo",
    "params": {
      "code": "005930"
    }
  }
}
```

## 응답 메시지 (Response)

### 메시지 구조 (성공)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "result": {
    "stock": {
      "code": "005930",
      "name": "삼성전자"
    }
  },
  "error": null,
  "metadata": {
    "timestamp": "2026-03-24T00:21:38+09:00",
    "notice": "휴장일 — 데이터는 직전 영업일(2026-03-20 금) 기준"
  }
}
```

### 메시지 구조 (에러)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "result": null,
  "error": {
    "code": "INVALID_PARAMS",
    "message": "Invalid stock code",
    "details": {
      "code": "INVALID",
      "reason": "Stock code must be 6 digits"
    }
  },
  "metadata": {
    "timestamp": "2026-03-24T00:21:38+09:00"
  }
}
```

### 필드 정의

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `id` | string | ✓ | 요청 ID (요청과 동일) |
| `result` | any | ✗ | 성공 결과 데이터 (에러 시 null) |
| `error` | object/null | ✗ | 에러 정보 (성공 시 null) |
| `metadata` | object | ✗ | 응답 메타데이터 (선택사항) |

### 에러 필드 정의

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `code` | string | ✓ | 에러 코드 |
| `message` | string | ✓ | 에러 메시지 |
| `details` | object | ✗ | 추가 에러 상세 정보 |

### 에러 코드

| 코드 | 설명 | HTTP 코드 |
|------|------|----------|
| `INVALID_REQUEST` | 요청 형식이 유효하지 않음 | 400 |
| `METHOD_NOT_FOUND` | 요청한 메서드가 존재하지 않음 | 404 |
| `INVALID_PARAMS` | 메서드의 인자가 유효하지 않음 | 400 |
| `INTERNAL_ERROR` | 서버 내부 오류 | 500 |
| `TIMEOUT` | 요청 타임아웃 | 504 |
| `PYTHON_ERROR` | Python 예외 발생 | 500 |

### 유효성 검증 규칙

1. **id**: 필수, 문자열
2. **result와 error**: 최소 하나는 존재해야 함
3. **error가 null이 아닌 경우**: code, message 필수
4. **error.code**: 문자열, 위의 코드 목록 중 하나

## 메타데이터

응답의 `metadata` 필드는 선택사항이며, 응답에 대한 추가 정보를 포함할 수 있습니다.

### 정의된 메타데이터 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| `timestamp` | string | ISO 8601 형식의 응답 시간 |
| `notice` | string | 사용자 알림 메시지 (휴장일, 점검 등) |
| `processingTime` | number | 처리 시간 (밀리초) |
| `version` | string | API 버전 |

### 메타데이터 예시

```json
{
  "metadata": {
    "timestamp": "2026-03-24T00:21:38+09:00",
    "notice": "휴장일 — 데이터는 직전 영업일(2026-03-20 금) 기준",
    "processingTime": 150,
    "version": "1.0"
  }
}
```

## 예외 처리

### Python 측 예외 처리

Python에서 발생한 예외는 다음과 같이 처리됩니다:

```python
try:
    result = agent.get_stock_price(code)
except ValueError as e:
    response = BridgeResponse.error(
        request_id=request.id,
        code="INVALID_PARAMS",
        message=str(e),
        details={"exception_type": "ValueError"}
    )
    print(response.to_json())
except Exception as e:
    response = BridgeResponse.error(
        request_id=request.id,
        code="PYTHON_ERROR",
        message=str(e),
        details={
            "exception_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }
    )
    print(response.to_json())
```

### TypeScript 측 예외 처리

TypeScript에서는 응답 유효성 검증 후 처리합니다:

```typescript
const response = JSON.parse(output) as BridgeResponse;
const [isValid, error] = BridgeProtocolValidator.validateResponse(response);

if (!isValid) {
  console.error("Invalid response format:", error);
  // INVALID_REQUEST 에러로 처리
}

if (response.error) {
  console.error(`[${response.error.code}] ${response.error.message}`);
  // 에러 처리
} else {
  console.log("Success:", response.result);
  // 결과 처리
}
```

## 통신 예시

### 1. 성공적인 요청/응답 흐름

```
TypeScript (CLI)
├─ 요청 생성
│  └─ id: UUID 생성, method: "price", args: ["005930"]
├─ JSON 직렬화
│  └─ {"id":"...", "method":"price", "args":["005930"], "kwargs":{}}
├─ stdin으로 전송
│
Python (subprocess)
├─ JSON 역직렬화
├─ BridgeRequest.from_json() 파싱
├─ 유효성 검증
├─ method 핸들러 실행 (cmd_price)
├─ 결과 처리
├─ BridgeResponse.success() 생성
├─ JSON 직렬화
│  └─ {"id":"...", "result":{...}, "error":null}
├─ stdout으로 전송
│
TypeScript (CLI)
├─ JSON 수신
├─ JSON 역직렬화
├─ BridgeResponse 유효성 검증
├─ 결과 처리
```

### 2. 에러 발생 흐름

```
TypeScript (CLI)
├─ 요청 생성
│  └─ id: UUID 생성, method: "price", args: ["INVALID"]
├─ stdin으로 전송
│
Python (subprocess)
├─ 유효성 검증 실패 또는 method 실행 중 예외 발생
├─ BridgeResponse.error() 생성
│  └─ code: "INVALID_PARAMS" 또는 "PYTHON_ERROR"
│  └─ message: 에러 설명
│  └─ details: 추가 정보
├─ JSON 직렬화
│  └─ {"id":"...", "result":null, "error":{...}}
├─ stdout으로 전송
│
TypeScript (CLI)
├─ 응답에서 error 필드 확인
├─ 에러 처리
└─ 사용자에게 메시지 전달
```

## 구현 위치

### Python 구현
- **파일**: `kis_agent/bridge_protocol.py`
- **클래스**:
  - `BridgeRequest`: 요청 메시지
  - `BridgeResponse`: 응답 메시지
  - `BridgeErrorResponse`: 에러 정보
  - `BridgeProtocolValidator`: 유효성 검증

### TypeScript 구현
- **파일**: `bridge-protocol.ts`
- **타입**:
  - `BridgeRequest`: 요청 메시지
  - `BridgeResponse`: 응답 메시지
  - `BridgeErrorInfo`: 에러 정보
  - `BridgeProtocolValidator`: 유효성 검증
- **헬퍼 함수**:
  - `createBridgeRequest()`: 요청 생성
  - `createSuccessResponse()`: 성공 응답 생성
  - `createErrorResponse()`: 에러 응답 생성
  - `isSuccessResponse()`: 성공 응답 판별
  - `isErrorResponse()`: 에러 응답 판별

## JSON Schema

### 요청 스키마

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Bridge Request",
  "type": "object",
  "required": ["id", "method"],
  "properties": {
    "id": {
      "type": "string",
      "description": "요청 고유 식별자 (UUID)"
    },
    "method": {
      "type": "string",
      "description": "호출할 메서드 이름",
      "pattern": "^[a-zA-Z_][a-zA-Z0-9_]*$"
    },
    "args": {
      "type": "array",
      "description": "위치 인자 목록",
      "default": []
    },
    "kwargs": {
      "type": "object",
      "description": "키워드 인자 딕셔너리",
      "default": {}
    }
  }
}
```

### 응답 스키마

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Bridge Response",
  "type": "object",
  "required": ["id"],
  "properties": {
    "id": {
      "type": "string",
      "description": "요청 ID"
    },
    "result": {
      "description": "성공 결과 데이터"
    },
    "error": {
      "oneOf": [
        {
          "type": "null"
        },
        {
          "type": "object",
          "required": ["code", "message"],
          "properties": {
            "code": {
              "type": "string",
              "enum": [
                "INVALID_REQUEST",
                "METHOD_NOT_FOUND",
                "INVALID_PARAMS",
                "INTERNAL_ERROR",
                "TIMEOUT",
                "PYTHON_ERROR"
              ]
            },
            "message": {
              "type": "string"
            },
            "details": {
              "type": "object"
            }
          }
        }
      ]
    },
    "metadata": {
      "type": "object",
      "description": "응답 메타데이터"
    }
  }
}
```

## 사용 가이드

### Python에서 요청 처리

```python
from kis_agent.bridge_protocol import BridgeRequest, BridgeResponse, BridgeProtocolValidator

# 요청 수신 및 파싱
request_json = input()
request = BridgeRequest.from_json(request_json)

# 유효성 검증
is_valid, error_msg = BridgeProtocolValidator.validate_request(request.to_dict())
if not is_valid:
    response = BridgeResponse.error(
        request_id=request.id,
        code="INVALID_REQUEST",
        message=error_msg
    )
    print(response.to_json())
    exit(1)

# 메서드 실행
try:
    if request.method == "price":
        result = agent.get_stock_price(*request.args, **request.kwargs)
    else:
        raise ValueError(f"Unknown method: {request.method}")

    response = BridgeResponse.success(request.id, result)
except Exception as e:
    response = BridgeResponse.error(
        request.id,
        "PYTHON_ERROR",
        str(e)
    )

print(response.to_json())
```

### TypeScript에서 요청 전송

```typescript
import {
  createBridgeRequest,
  BridgeProtocolValidator,
  isSuccessResponse,
} from "./bridge-protocol";

// 요청 생성 및 검증
const request = createBridgeRequest("price", ["005930"], { daily: true });
const [isValid, error] = BridgeProtocolValidator.validateRequest(request);

if (!isValid) {
  console.error("Invalid request:", error);
  exit(1);
}

// 요청 전송 (stdin을 통해)
const requestJson = JSON.stringify(request);
process.stdin.write(requestJson + "\n");

// 응답 수신 (stdout에서)
const responseJson = response_from_stdin();
const response = JSON.parse(responseJson);

if (isSuccessResponse(response)) {
  console.log("Success:", response.result);
} else {
  console.error(`[${response.error.code}] ${response.error.message}`);
}
```

## 버전 관리

현재 프로토콜 버전: **1.0**

### 향후 버전 계획

- **1.1**: 배치 요청 지원 (여러 메서드를 한 번에 호출)
- **1.2**: 스트리밍 응답 지원 (대용량 데이터)
- **2.0**: WebSocket 지원

## 참고사항

1. **UUID 형식**: 요청 ID는 RFC 4122 UUID 형식을 따릅니다 (예: `550e8400-e29b-41d4-a716-446655440000`)
2. **타임존**: 메타데이터의 타임스탐프는 ISO 8601 형식으로 현지 타임존을 포함합니다 (예: `2026-03-24T00:21:38+09:00`)
3. **인코딩**: 모든 JSON은 UTF-8 인코딩입니다
4. **라인 단위**: 각 메시지는 단일 JSON 객체이며, 개행 문자로 구분됩니다
5. **타임아웃**: 기본 타임아웃은 30초입니다 (설정 가능)
