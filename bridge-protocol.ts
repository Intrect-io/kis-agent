/**
 * Bridge 메시지 프로토콜 정의 (TypeScript)
 *
 * JSON 기반 request/response 메시지 형식을 정의합니다.
 * TypeScript CLI와 Python 백엔드 간의 subprocess 통신을 위한 표준 형식입니다.
 *
 * 메시지 형식:
 * - Request: { id: string, method: string, args: any[], kwargs: Record<string, any> }
 * - Response: { id: string, result: any, error: null } 또는 { id: string, result: null, error: { code: string, message: string } }
 */

/**
 * Bridge 메시지 타입
 */
export enum BridgeMessageType {
  REQUEST = "request",
  RESPONSE = "response",
  ERROR = "error",
}

/**
 * Bridge 에러 코드
 */
export enum BridgeErrorCode {
  INVALID_REQUEST = "INVALID_REQUEST",
  METHOD_NOT_FOUND = "METHOD_NOT_FOUND",
  INVALID_PARAMS = "INVALID_PARAMS",
  INTERNAL_ERROR = "INTERNAL_ERROR",
  TIMEOUT = "TIMEOUT",
  PYTHON_ERROR = "PYTHON_ERROR",
}

/**
 * Bridge 요청 메시지
 *
 * @property id - 요청 고유 식별자 (UUID)
 * @property method - 호출할 메서드 이름 (e.g., "price", "balance", "query")
 * @property args - 위치 인자 목록 (기본값: [])
 * @property kwargs - 키워드 인자 딕셔너리 (기본값: {})
 */
export interface BridgeRequest {
  id: string;
  method: string;
  args?: any[];
  kwargs?: Record<string, any>;
}

/**
 * Bridge 에러 정보
 *
 * @property code - 에러 코드
 * @property message - 에러 메시지
 * @property details - 추가 에러 상세 정보 (선택사항)
 */
export interface BridgeErrorInfo {
  code: string;
  message: string;
  details?: Record<string, any>;
}

/**
 * Bridge 응답 메시지
 *
 * @property id - 요청 ID (요청과 동일)
 * @property result - 성공 결과 데이터 (에러 시 null)
 * @property error - 에러 정보 (성공 시 null)
 * @property metadata - 응답 메타데이터 (선택사항)
 */
export interface BridgeResponse {
  id: string;
  result?: any;
  error?: BridgeErrorInfo | null;
  metadata?: Record<string, any>;
}

/**
 * Bridge 프로토콜 유효성 검증 클래스
 */
export class BridgeProtocolValidator {
  /**
   * 요청 메시지 유효성 검증
   *
   * @param data - 검증할 객체
   * @returns [유효성, 에러 메시지] 튜플
   */
  static validateRequest(data: unknown): [boolean, string | null] {
    if (typeof data !== "object" || data === null) {
      return [false, "Request must be an object"];
    }

    const obj = data as Record<string, unknown>;

    // 필수 필드 확인
    if (!("id" in obj)) {
      return [false, "Missing required field: 'id'"];
    }

    if (!("method" in obj)) {
      return [false, "Missing required field: 'method'"];
    }

    // 타입 확인
    if (typeof obj.id !== "string") {
      return [false, "'id' must be a string"];
    }

    if (typeof obj.method !== "string") {
      return [false, "'method' must be a string"];
    }

    if ("args" in obj && !Array.isArray(obj.args)) {
      return [false, "'args' must be an array"];
    }

    if ("kwargs" in obj && (typeof obj.kwargs !== "object" || obj.kwargs === null || Array.isArray(obj.kwargs))) {
      return [false, "'kwargs' must be an object"];
    }

    // 메서드 이름 유효성 (영문자, 숫자, 언더스코어만 허용)
    if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(obj.method)) {
      return [false, "'method' contains invalid characters"];
    }

    return [true, null];
  }

  /**
   * 응답 메시지 유효성 검증
   *
   * @param data - 검증할 객체
   * @returns [유효성, 에러 메시지] 튜플
   */
  static validateResponse(data: unknown): [boolean, string | null] {
    if (typeof data !== "object" || data === null) {
      return [false, "Response must be an object"];
    }

    const obj = data as Record<string, unknown>;

    // 필수 필드 확인
    if (!("id" in obj)) {
      return [false, "Missing required field: 'id'"];
    }

    if (typeof obj.id !== "string") {
      return [false, "'id' must be a string"];
    }

    // result와 error 중 하나는 있어야 함
    const hasResult = "result" in obj;
    const hasError = "error" in obj;

    if (!hasResult && !hasError) {
      return [false, "Response must have either 'result' or 'error'"];
    }

    // error 필드 유효성
    if (hasError && obj.error !== null && obj.error !== undefined) {
      if (typeof obj.error !== "object" || Array.isArray(obj.error)) {
        return [false, "'error' must be an object or null"];
      }

      const error = obj.error as Record<string, unknown>;

      if (!("code" in error)) {
        return [false, "'error' missing required field: 'code'"];
      }

      if (!("message" in error)) {
        return [false, "'error' missing required field: 'message'"];
      }

      if (typeof error.code !== "string") {
        return [false, "'error.code' must be a string"];
      }

      if (typeof error.message !== "string") {
        return [false, "'error.message' must be a string"];
      }
    }

    return [true, null];
  }
}

/**
 * Bridge 요청 생성 헬퍼
 */
export function createBridgeRequest(
  method: string,
  args: any[] = [],
  kwargs: Record<string, any> = {},
  id: string = crypto.randomUUID()
): BridgeRequest {
  return {
    id,
    method,
    args: args.length > 0 ? args : undefined,
    kwargs: Object.keys(kwargs).length > 0 ? kwargs : undefined,
  };
}

/**
 * Bridge 성공 응답 생성 헬퍼
 */
export function createSuccessResponse(
  id: string,
  result: any,
  metadata?: Record<string, any>
): BridgeResponse {
  return {
    id,
    result,
    error: null,
    metadata,
  };
}

/**
 * Bridge 에러 응답 생성 헬퍼
 */
export function createErrorResponse(
  id: string,
  code: string,
  message: string,
  details?: Record<string, any>,
  metadata?: Record<string, any>
): BridgeResponse {
  return {
    id,
    result: null,
    error: {
      code,
      message,
      details,
    },
    metadata,
  };
}

/**
 * 응답이 성공인지 확인
 */
export function isSuccessResponse(response: BridgeResponse): boolean {
  return response.error === null && response.result !== undefined;
}

/**
 * 응답이 에러인지 확인
 */
export function isErrorResponse(response: BridgeResponse): boolean {
  return response.error !== null && response.error !== undefined;
}

/**
 * Bridge 프로토콜 스키마 (JSON Schema 형식)
 */
export const BRIDGE_PROTOCOL_SCHEMA = {
  version: "1.0",
  description: "Bridge 메시지 프로토콜",
  request: {
    type: "object",
    required: ["id", "method"],
    properties: {
      id: {
        type: "string",
        description: "요청 고유 식별자 (UUID)",
      },
      method: {
        type: "string",
        description: "호출할 메서드 이름 (e.g., price, balance, query)",
        pattern: "^[a-zA-Z_][a-zA-Z0-9_]*$",
      },
      args: {
        type: "array",
        description: "위치 인자 목록",
        default: [],
      },
      kwargs: {
        type: "object",
        description: "키워드 인자 딕셔너리",
        default: {},
      },
    },
  },
  response: {
    type: "object",
    required: ["id"],
    properties: {
      id: {
        type: "string",
        description: "요청 ID (요청과 동일)",
      },
      result: {
        description: "성공 결과 데이터 (에러 시 null)",
        default: null,
      },
      error: {
        type: ["object", "null"],
        description: "에러 정보 (성공 시 null)",
        properties: {
          code: {
            type: "string",
            description: "에러 코드",
            enum: [
              "INVALID_REQUEST",
              "METHOD_NOT_FOUND",
              "INVALID_PARAMS",
              "INTERNAL_ERROR",
              "TIMEOUT",
              "PYTHON_ERROR",
            ],
          },
          message: {
            type: "string",
            description: "에러 메시지",
          },
          details: {
            type: "object",
            description: "추가 에러 상세 정보 (선택사항)",
          },
        },
        required: ["code", "message"],
      },
      metadata: {
        type: "object",
        description: "응답 메타데이터 (선택사항)",
      },
    },
  },
};

/**
 * 예시: 요청과 응답 생성 및 검증
 */
export function exampleUsage() {
  // 요청 생성
  const request = createBridgeRequest("price", ["005930"], { daily: true });
  console.log("Request:", JSON.stringify(request, null, 2));

  // 요청 검증
  const [isValidRequest, requestError] = BridgeProtocolValidator.validateRequest(request);
  console.log(`Request valid: ${isValidRequest}`, requestError ? `(${requestError})` : "");

  // 성공 응답 생성
  const successResponse = createSuccessResponse(request.id, {
    stock: {
      code: "005930",
      name: "삼성전자",
      price: 70000,
    },
  });
  console.log("Success Response:", JSON.stringify(successResponse, null, 2));

  // 응답 검증
  const [isValidResponse, responseError] = BridgeProtocolValidator.validateResponse(
    successResponse
  );
  console.log(`Response valid: ${isValidResponse}`, responseError ? `(${responseError})` : "");

  // 에러 응답 생성
  const errorResponse = createErrorResponse(
    request.id,
    BridgeErrorCode.INVALID_PARAMS,
    "Invalid stock code",
    { code: "005930", reason: "Stock code not found" }
  );
  console.log("Error Response:", JSON.stringify(errorResponse, null, 2));
}
