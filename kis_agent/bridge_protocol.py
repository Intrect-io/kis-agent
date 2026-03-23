"""
Bridge 메시지 프로토콜 정의

JSON 기반 request/response 메시지 형식을 정의합니다.
TypeScript CLI와 Python 백엔드 간의 subprocess 통신을 위한 표준 형식입니다.

메시지 형식:
- Request: { id: str, method: str, args: list, kwargs: dict }
- Response: { id: str, result: any, error: null } 또는 { id: str, result: null, error: { code: str, message: str } }
"""

import re
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Union
from enum import Enum
import uuid
import json


class BridgeMessageType(str, Enum):
    """Bridge 메시지 타입"""
    REQUEST = "request"
    RESPONSE = "response"
    ERROR = "error"


class BridgeErrorCode(str, Enum):
    """Bridge 에러 코드"""
    INVALID_REQUEST = "INVALID_REQUEST"
    METHOD_NOT_FOUND = "METHOD_NOT_FOUND"
    INVALID_PARAMS = "INVALID_PARAMS"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    TIMEOUT = "TIMEOUT"
    PYTHON_ERROR = "PYTHON_ERROR"


@dataclass
class BridgeRequest:
    """
    Bridge 요청 메시지

    Attributes:
        id: 요청 고유 식별자 (UUID)
        method: 호출할 메서드 이름 (e.g., "price", "balance", "query")
        args: 위치 인자 목록
        kwargs: 키워드 인자 딕셔너리
    """
    id: str
    method: str
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        method: str,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> "BridgeRequest":
        """
        BridgeRequest 인스턴스 생성

        Args:
            method: 메서드 이름
            args: 위치 인자 (기본값: [])
            kwargs: 키워드 인자 (기본값: {})
            request_id: 요청 ID (기본값: UUID 자동 생성)

        Returns:
            BridgeRequest 인스턴스
        """
        return cls(
            id=request_id or str(uuid.uuid4()),
            method=method,
            args=args or [],
            kwargs=kwargs or {},
        )

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)

    def to_json(self) -> str:
        """JSON 문자열로 변환"""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BridgeRequest":
        """딕셔너리에서 인스턴스 생성"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            method=data["method"],
            args=data.get("args", []),
            kwargs=data.get("kwargs", {}),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "BridgeRequest":
        """JSON 문자열에서 인스턴스 생성"""
        return cls.from_dict(json.loads(json_str))


@dataclass
class BridgeErrorResponse:
    """
    Bridge 에러 응답

    Attributes:
        code: 에러 코드
        message: 에러 메시지
        details: 추가 에러 상세 정보 (선택사항)
    """
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        result = {
            "code": self.code,
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BridgeErrorResponse":
        """딕셔너리에서 인스턴스 생성"""
        return cls(
            code=data["code"],
            message=data["message"],
            details=data.get("details"),
        )


@dataclass
class BridgeResponse:
    """
    Bridge 응답 메시지

    Attributes:
        id: 요청 ID (요청과 동일)
        result: 성공 결과 데이터 (에러 시 None)
        error: 에러 정보 (성공 시 None)
        metadata: 응답 메타데이터 (선택사항)
    """
    id: str
    result: Optional[Any] = None
    error: Optional[BridgeErrorResponse] = None
    metadata: Optional[Dict[str, Any]] = None

    def is_success(self) -> bool:
        """성공 응답 여부"""
        return self.error is None and self.result is not None

    def is_error(self) -> bool:
        """에러 응답 여부"""
        return self.error is not None

    @classmethod
    def success(
        cls,
        request_id: str,
        result: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "BridgeResponse":
        """성공 응답 생성"""
        return cls(
            id=request_id,
            result=result,
            error=None,
            metadata=metadata,
        )

    @classmethod
    def error(
        cls,
        request_id: str,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "BridgeResponse":
        """에러 응답 생성"""
        return cls(
            id=request_id,
            result=None,
            error=BridgeErrorResponse(
                code=code,
                message=message,
                details=details,
            ),
            metadata=metadata,
        )

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        result = {
            "id": self.id,
            "result": self.result,
            "error": self.error.to_dict() if self.error else None,
        }
        if self.metadata:
            result["metadata"] = self.metadata
        return result

    def to_json(self) -> str:
        """JSON 문자열로 변환"""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BridgeResponse":
        """딕셔너리에서 인스턴스 생성"""
        error = None
        if data.get("error"):
            error = BridgeErrorResponse.from_dict(data["error"])

        return cls(
            id=data["id"],
            result=data.get("result"),
            error=error,
            metadata=data.get("metadata"),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "BridgeResponse":
        """JSON 문자열에서 인스턴스 생성"""
        return cls.from_dict(json.loads(json_str))


class BridgeProtocolValidator:
    """Bridge 메시지 프로토콜 검증"""

    @staticmethod
    def validate_request(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        요청 메시지 유효성 검증

        Args:
            data: 검증할 딕셔너리

        Returns:
            (유효성, 에러 메시지) 튜플
        """
        # 필수 필드 확인
        if "id" not in data:
            return False, "Missing required field: 'id'"

        if "method" not in data:
            return False, "Missing required field: 'method'"

        # 타입 확인
        if not isinstance(data["id"], str):
            return False, "'id' must be a string"

        if not isinstance(data["method"], str):
            return False, "'method' must be a string"

        if "args" in data and not isinstance(data["args"], list):
            return False, "'args' must be a list"

        if "kwargs" in data and not isinstance(data["kwargs"], dict):
            return False, "'kwargs' must be a dict"

        # 메서드 이름 유효성 (영문자, 숫자, 언더스코어만 허용)
        # 패턴: [a-zA-Z_][a-zA-Z0-9_]*
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", data["method"]):
            return False, "'method' contains invalid characters"

        return True, None

    @staticmethod
    def validate_response(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        응답 메시지 유효성 검증

        Args:
            data: 검증할 딕셔너리

        Returns:
            (유효성, 에러 메시지) 튜플
        """
        # 필수 필드 확인
        if "id" not in data:
            return False, "Missing required field: 'id'"

        if not isinstance(data["id"], str):
            return False, "'id' must be a string"

        # result와 error 중 하나는 있어야 함
        has_result = "result" in data
        has_error = "error" in data

        if not (has_result or has_error):
            return False, "Response must have either 'result' or 'error'"

        # error 필드 유효성
        if has_error and data["error"] is not None:
            if not isinstance(data["error"], dict):
                return False, "'error' must be a dict or null"

            if "code" not in data["error"]:
                return False, "'error' missing required field: 'code'"

            if "message" not in data["error"]:
                return False, "'error' missing required field: 'message'"

            if not isinstance(data["error"]["code"], str):
                return False, "'error.code' must be a string"

            if not isinstance(data["error"]["message"], str):
                return False, "'error.message' must be a string"

        return True, None


# 프로토콜 스키마 정의 (문서화용)
BRIDGE_PROTOCOL_SCHEMA = {
    "version": "1.0",
    "description": "Bridge 메시지 프로토콜",
    "request": {
        "type": "object",
        "required": ["id", "method"],
        "properties": {
            "id": {
                "type": "string",
                "description": "요청 고유 식별자 (UUID)",
            },
            "method": {
                "type": "string",
                "description": "호출할 메서드 이름 (e.g., price, balance, query)",
                "pattern": "^[a-zA-Z_][a-zA-Z0-9_]*$",
            },
            "args": {
                "type": "array",
                "description": "위치 인자 목록",
                "default": [],
            },
            "kwargs": {
                "type": "object",
                "description": "키워드 인자 딕셔너리",
                "default": {},
            },
        },
    },
    "response": {
        "type": "object",
        "required": ["id"],
        "properties": {
            "id": {
                "type": "string",
                "description": "요청 ID (요청과 동일)",
            },
            "result": {
                "description": "성공 결과 데이터 (에러 시 null)",
                "default": None,
            },
            "error": {
                "type": ["object", "null"],
                "description": "에러 정보 (성공 시 null)",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "에러 코드",
                        "enum": [
                            "INVALID_REQUEST",
                            "METHOD_NOT_FOUND",
                            "INVALID_PARAMS",
                            "INTERNAL_ERROR",
                            "TIMEOUT",
                            "PYTHON_ERROR",
                        ],
                    },
                    "message": {
                        "type": "string",
                        "description": "에러 메시지",
                    },
                    "details": {
                        "type": "object",
                        "description": "추가 에러 상세 정보 (선택사항)",
                    },
                },
                "required": ["code", "message"],
            },
            "metadata": {
                "type": "object",
                "description": "응답 메타데이터 (선택사항)",
            },
        },
    },
}


if __name__ == "__main__":
    # 예시: 요청 생성 및 검증
    request = BridgeRequest.create(
        method="price",
        args=["005930"],
        kwargs={"daily": True},
    )
    print("Request:")
    print(request.to_json())
    print()

    # 예시: 응답 생성 및 검증
    response = BridgeResponse.success(
        request_id=request.id,
        result={
            "stock": {
                "code": "005930",
                "name": "삼성전자",
                "price": 70000,
            },
        },
    )
    print("Response (Success):")
    print(response.to_json())
    print()

    # 예시: 에러 응답
    error_response = BridgeResponse.error(
        request_id=request.id,
        code="INVALID_PARAMS",
        message="Invalid stock code",
        details={"code": "005930", "reason": "Stock code not found"},
    )
    print("Response (Error):")
    print(error_response.to_json())
    print()

    # 유효성 검증
    print("Validation:")
    is_valid, error_msg = BridgeProtocolValidator.validate_request(request.to_dict())
    print(f"Request validation: {is_valid}")
    if error_msg:
        print(f"  Error: {error_msg}")

    is_valid, error_msg = BridgeProtocolValidator.validate_response(response.to_dict())
    print(f"Response validation: {is_valid}")
    if error_msg:
        print(f"  Error: {error_msg}")
