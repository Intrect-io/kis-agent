# Bridge 메시지 프로토콜 구현 완료

## 개요

kis-agent 프로젝트의 Bridge 메시지 프로토콜이 완전히 정의되고 구현되었습니다. JSON 기반 request/response 형식으로 TypeScript CLI와 Python 백엔드 간의 통신을 표준화합니다.

## 구현 내용

### 1. Python 구현 (`kis_agent/bridge_protocol.py`, 443줄)

**클래스:**
- `BridgeRequest`: 요청 메시지 정의 및 직렬화/역직렬화
- `BridgeResponse`: 응답 메시지 정의 및 직렬화/역직렬화
- `BridgeErrorResponse`: 에러 정보 구조화
- `BridgeProtocolValidator`: 요청/응답 유효성 검증

**주요 기능:**
- UUID 기반 요청 ID 자동 생성
- 메서드명 정규식 검증 (`^[a-zA-Z_][a-zA-Z0-9_]*$`)
- JSON 직렬화/역직렬화 (with `asdict()`)
- 타입 안전성 (dataclass 기반)
- 메타데이터 지원 (timestamp, notice 등)

**사용 예시:**
```python
# 요청 생성
request = BridgeRequest.create(
    method="price",
    args=["005930"],
    kwargs={"daily": True}
)

# 응답 생성 (성공)
response = BridgeResponse.success(
    request_id=request.id,
    result={"code": "005930", "price": 70000}
)

# 응답 생성 (에러)
error_response = BridgeResponse.error(
    request_id=request.id,
    code="INVALID_PARAMS",
    message="Invalid stock code"
)

# 유효성 검증
is_valid, error_msg = BridgeProtocolValidator.validate_request(request.to_dict())
```

### 2. TypeScript 구현 (`bridge-protocol.ts`, 369줄)

**타입/인터페이스:**
- `BridgeRequest`: 요청 메시지 타입
- `BridgeResponse`: 응답 메시지 타입
- `BridgeErrorInfo`: 에러 정보 타입
- `BridgeMessageType`: 메시지 타입 enum
- `BridgeErrorCode`: 에러 코드 enum

**클래스:**
- `BridgeProtocolValidator`: 요청/응답 유효성 검증

**헬퍼 함수:**
- `createBridgeRequest()`: 요청 생성
- `createSuccessResponse()`: 성공 응답 생성
- `createErrorResponse()`: 에러 응답 생성
- `isSuccessResponse()`: 성공 응답 판별
- `isErrorResponse()`: 에러 응답 판별

**사용 예시:**
```typescript
// 요청 생성 및 검증
const request = createBridgeRequest("price", ["005930"], { daily: true });
const [isValid, error] = BridgeProtocolValidator.validateRequest(request);

// 응답 처리
const response = JSON.parse(responseJson);
if (isSuccessResponse(response)) {
  console.log("Success:", response.result);
} else if (isErrorResponse(response)) {
  console.error(`[${response.error.code}] ${response.error.message}`);
}
```

### 3. 문서화 (`docs/bridge-protocol.md`, 531줄)

포괄적인 프로토콜 명세서 포함:
- 메시지 구조 및 필드 정의
- 유효성 검증 규칙
- 에러 코드 및 처리 방법
- 사용 가이드 및 예시
- JSON Schema 정의
- 통신 흐름도

### 4. 테스트 (`tests/test_bridge_protocol.py`, 657줄)

**테스트 범위:**
- 요청/응답 생성 및 직렬화
- 유효성 검증 (필수 필드, 타입 확인)
- 메서드명 정규식 검증
- JSON 왕복 변환 (roundtrip)
- 엣지 케이스 처리
- 통합 테스트

**테스트 수:** 45개

## 프로토콜 사양

### 요청 메시지 (Request)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "price",
  "args": ["005930"],
  "kwargs": {}
}
```

**필드:**
- `id` (string, 필수): UUID
- `method` (string, 필수): 메서드명 (패턴: `^[a-zA-Z_][a-zA-Z0-9_]*$`)
- `args` (array, 선택): 위치 인자
- `kwargs` (object, 선택): 키워드 인자

### 응답 메시지 (Response)

#### 성공 응답

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
    "timestamp": "2026-03-24T00:21:38+09:00"
  }
}
```

#### 에러 응답

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

**필드:**
- `id` (string, 필수): 요청 ID
- `result` (any, 선택): 성공 데이터
- `error` (object/null, 선택): 에러 정보
  - `code` (string): 에러 코드
  - `message` (string): 에러 메시지
  - `details` (object, 선택): 추가 정보
- `metadata` (object, 선택): 응답 메타데이터

## 에러 코드

| 코드 | 설명 |
|------|------|
| `INVALID_REQUEST` | 요청 형식 오류 |
| `METHOD_NOT_FOUND` | 메서드 미존재 |
| `INVALID_PARAMS` | 인자 오류 |
| `INTERNAL_ERROR` | 서버 내부 오류 |
| `TIMEOUT` | 타임아웃 |
| `PYTHON_ERROR` | Python 예외 |

## 주요 검증 규칙

### 요청 검증
✓ `id` 필드 필수 (string)
✓ `method` 필드 필수 (string, 영문/숫자/언더스코어만)
✓ `args` 필드는 배열이어야 함
✓ `kwargs` 필드는 객체여야 함

### 응답 검증
✓ `id` 필드 필수
✓ `result` 또는 `error` 중 최소 하나 필수
✓ `error.code`, `error.message` 필수 (error가 있을 때)
✓ 모든 필드 타입 검증

## 구현 품질

- **코드 라인 수**: 2,000줄 (4 파일)
- **테스트 커버리지**: 45개 테스트 (검증, 직렬화, 통합)
- **타입 안정성**: Python (dataclass), TypeScript (interface/enum)
- **문서화**: 완전한 마크다운 문서 + JSON Schema
- **정규식**: 메서드명 엄격 검증

## 파일 위치

```
kis-agent/
├── kis_agent/
│   └── bridge_protocol.py         # Python 구현
├── bridge-protocol.ts              # TypeScript 구현
├── docs/
│   └── bridge-protocol.md          # 프로토콜 명세
└── tests/
    └── test_bridge_protocol.py     # 검증 테스트
```

## 다음 단계

1. **CLI 통합**: TypeScript CLI에서 bridge_protocol.ts 사용
2. **Python 핸들러 통합**: `kis_agent/cli/main.py`에서 BridgeRequest/Response 사용
3. **E2E 테스트**: subprocess 통신 통합 테스트
4. **배포 준비**: 문서화 및 버전 관리

## 기술 사양

- **프로토콜 버전**: 1.0
- **전송 형식**: JSON over stdin/stdout
- **인코딩**: UTF-8
- **타임존**: ISO 8601 + 타임존 (예: +09:00)
- **타임아웃**: 30초 (기본값, 설정 가능)

---

**생성일**: 2026-03-24
**상태**: ✅ 완료
**신뢰도**: 95%
