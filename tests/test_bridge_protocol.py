"""
Bridge 메시지 프로토콜 유효성 검증 테스트
"""

import pytest
import json
from kis_agent.bridge_protocol import (
    BridgeRequest,
    BridgeResponse,
    BridgeErrorResponse,
    BridgeProtocolValidator,
    BridgeErrorCode,
)


class TestBridgeRequest:
    """BridgeRequest 클래스 테스트"""

    def test_create_request_with_all_fields(self):
        """모든 필드를 포함한 요청 생성"""
        request = BridgeRequest.create(
            method="price",
            args=["005930"],
            kwargs={"daily": True},
            request_id="test-id-123",
        )

        assert request.id == "test-id-123"
        assert request.method == "price"
        assert request.args == ["005930"]
        assert request.kwargs == {"daily": True}

    def test_create_request_with_defaults(self):
        """기본값을 사용한 요청 생성"""
        request = BridgeRequest.create(method="balance")

        assert request.id is not None
        assert request.method == "balance"
        assert request.args == []
        assert request.kwargs == {}

    def test_request_to_dict(self):
        """요청을 딕셔너리로 변환"""
        request = BridgeRequest.create(
            method="price",
            args=["005930"],
            request_id="test-id",
        )

        data = request.to_dict()

        assert data["id"] == "test-id"
        assert data["method"] == "price"
        assert data["args"] == ["005930"]
        assert data["kwargs"] == {}

    def test_request_to_json(self):
        """요청을 JSON으로 변환"""
        request = BridgeRequest.create(
            method="price",
            args=["005930"],
            request_id="test-id",
        )

        json_str = request.to_json()
        parsed = json.loads(json_str)

        assert parsed["id"] == "test-id"
        assert parsed["method"] == "price"
        assert parsed["args"] == ["005930"]

    def test_request_from_dict(self):
        """딕셔너리에서 요청 생성"""
        data = {
            "id": "test-id",
            "method": "balance",
            "args": [],
            "kwargs": {"holdings": True},
        }

        request = BridgeRequest.from_dict(data)

        assert request.id == "test-id"
        assert request.method == "balance"
        assert request.kwargs == {"holdings": True}

    def test_request_from_json(self):
        """JSON에서 요청 생성"""
        json_str = '{"id":"test-id","method":"price","args":["005930"],"kwargs":{}}'

        request = BridgeRequest.from_json(json_str)

        assert request.id == "test-id"
        assert request.method == "price"
        assert request.args == ["005930"]

    def test_request_roundtrip(self):
        """요청 직렬화/역직렬화 왕복 테스트"""
        original = BridgeRequest.create(
            method="query",
            args=["GetStockInfo"],
            kwargs={"code": "005930"},
            request_id="test-id",
        )

        # JSON 변환 후 복원
        json_str = original.to_json()
        restored = BridgeRequest.from_json(json_str)

        assert restored.id == original.id
        assert restored.method == original.method
        assert restored.args == original.args
        assert restored.kwargs == original.kwargs


class TestBridgeResponse:
    """BridgeResponse 클래스 테스트"""

    def test_success_response(self):
        """성공 응답 생성"""
        response = BridgeResponse.success(
            request_id="test-id",
            result={"code": "005930", "name": "삼성전자"},
        )

        assert response.id == "test-id"
        assert response.result == {"code": "005930", "name": "삼성전자"}
        assert response.error is None
        assert response.is_success()
        assert not response.is_error()

    def test_error_response(self):
        """에러 응답 생성"""
        response = BridgeResponse.error(
            request_id="test-id",
            code=BridgeErrorCode.INVALID_PARAMS,
            message="Invalid stock code",
            details={"code": "INVALID"},
        )

        assert response.id == "test-id"
        assert response.result is None
        assert response.error is not None
        assert response.error.code == BridgeErrorCode.INVALID_PARAMS
        assert response.error.message == "Invalid stock code"
        assert not response.is_success()
        assert response.is_error()

    def test_response_to_dict_success(self):
        """성공 응답을 딕셔너리로 변환"""
        response = BridgeResponse.success(
            request_id="test-id",
            result={"data": "value"},
        )

        data = response.to_dict()

        assert data["id"] == "test-id"
        assert data["result"] == {"data": "value"}
        assert data["error"] is None

    def test_response_to_dict_error(self):
        """에러 응답을 딕셔너리로 변환"""
        response = BridgeResponse.error(
            request_id="test-id",
            code="TEST_ERROR",
            message="Test error message",
        )

        data = response.to_dict()

        assert data["id"] == "test-id"
        assert data["result"] is None
        assert data["error"]["code"] == "TEST_ERROR"
        assert data["error"]["message"] == "Test error message"

    def test_response_to_json(self):
        """응답을 JSON으로 변환"""
        response = BridgeResponse.success(
            request_id="test-id",
            result={"data": "value"},
        )

        json_str = response.to_json()
        parsed = json.loads(json_str)

        assert parsed["id"] == "test-id"
        assert parsed["result"] == {"data": "value"}

    def test_response_from_dict_success(self):
        """딕셔너리에서 성공 응답 생성"""
        data = {
            "id": "test-id",
            "result": {"data": "value"},
            "error": None,
        }

        response = BridgeResponse.from_dict(data)

        assert response.is_success()
        assert response.result == {"data": "value"}

    def test_response_from_dict_error(self):
        """딕셔너리에서 에러 응답 생성"""
        data = {
            "id": "test-id",
            "result": None,
            "error": {
                "code": "TEST_ERROR",
                "message": "Test error",
            },
        }

        response = BridgeResponse.from_dict(data)

        assert response.is_error()
        assert response.error.code == "TEST_ERROR"

    def test_response_roundtrip(self):
        """응답 직렬화/역직렬화 왕복 테스트"""
        original = BridgeResponse.success(
            request_id="test-id",
            result={"code": "005930"},
            metadata={"timestamp": "2026-03-24T00:00:00+09:00"},
        )

        # JSON 변환 후 복원
        json_str = original.to_json()
        restored = BridgeResponse.from_json(json_str)

        assert restored.id == original.id
        assert restored.result == original.result
        assert restored.metadata == original.metadata


class TestBridgeProtocolValidator:
    """BridgeProtocolValidator 클래스 테스트"""

    # 요청 검증 테스트
    def test_validate_request_valid(self):
        """유효한 요청 검증"""
        request = {
            "id": "test-id",
            "method": "price",
            "args": ["005930"],
            "kwargs": {},
        }

        is_valid, error = BridgeProtocolValidator.validate_request(request)

        assert is_valid is True
        assert error is None

    def test_validate_request_missing_id(self):
        """ID 필드 누락"""
        request = {
            "method": "price",
        }

        is_valid, error = BridgeProtocolValidator.validate_request(request)

        assert is_valid is False
        assert "id" in error

    def test_validate_request_missing_method(self):
        """메서드 필드 누락"""
        request = {
            "id": "test-id",
        }

        is_valid, error = BridgeProtocolValidator.validate_request(request)

        assert is_valid is False
        assert "method" in error

    def test_validate_request_invalid_id_type(self):
        """ID 타입 오류"""
        request = {
            "id": 123,
            "method": "price",
        }

        is_valid, error = BridgeProtocolValidator.validate_request(request)

        assert is_valid is False
        assert "id" in error

    def test_validate_request_invalid_method_type(self):
        """메서드 타입 오류"""
        request = {
            "id": "test-id",
            "method": 123,
        }

        is_valid, error = BridgeProtocolValidator.validate_request(request)

        assert is_valid is False
        assert "method" in error

    def test_validate_request_invalid_args_type(self):
        """args 타입 오류"""
        request = {
            "id": "test-id",
            "method": "price",
            "args": "not-a-list",
        }

        is_valid, error = BridgeProtocolValidator.validate_request(request)

        assert is_valid is False
        assert "args" in error

    def test_validate_request_invalid_kwargs_type(self):
        """kwargs 타입 오류"""
        request = {
            "id": "test-id",
            "method": "price",
            "kwargs": "not-a-dict",
        }

        is_valid, error = BridgeProtocolValidator.validate_request(request)

        assert is_valid is False
        assert "kwargs" in error

    def test_validate_request_invalid_method_name(self):
        """메서드 이름 패턴 오류"""
        request = {
            "id": "test-id",
            "method": "price-quote",  # 하이픈은 허용 안 됨
        }

        is_valid, error = BridgeProtocolValidator.validate_request(request)

        assert is_valid is False
        assert "invalid characters" in error

    def test_validate_request_valid_method_names(self):
        """유효한 메서드 이름들"""
        valid_names = [
            "price",
            "get_price",
            "_private",
            "Price",
            "PRICE",
            "price123",
            "price_quote_v2",
        ]

        for method_name in valid_names:
            request = {
                "id": "test-id",
                "method": method_name,
            }
            is_valid, _ = BridgeProtocolValidator.validate_request(request)
            assert is_valid is True, f"Method '{method_name}' should be valid"

    # 응답 검증 테스트
    def test_validate_response_valid_success(self):
        """유효한 성공 응답 검증"""
        response = {
            "id": "test-id",
            "result": {"data": "value"},
            "error": None,
        }

        is_valid, error = BridgeProtocolValidator.validate_response(response)

        assert is_valid is True
        assert error is None

    def test_validate_response_valid_error(self):
        """유효한 에러 응답 검증"""
        response = {
            "id": "test-id",
            "result": None,
            "error": {
                "code": "TEST_ERROR",
                "message": "Test error",
            },
        }

        is_valid, error = BridgeProtocolValidator.validate_response(response)

        assert is_valid is True
        assert error is None

    def test_validate_response_missing_id(self):
        """응답 ID 필드 누락"""
        response = {
            "result": {"data": "value"},
        }

        is_valid, error = BridgeProtocolValidator.validate_response(response)

        assert is_valid is False
        assert "id" in error

    def test_validate_response_invalid_id_type(self):
        """응답 ID 타입 오류"""
        response = {
            "id": 123,
            "result": {"data": "value"},
        }

        is_valid, error = BridgeProtocolValidator.validate_response(response)

        assert is_valid is False
        assert "id" in error

    def test_validate_response_missing_result_and_error(self):
        """result와 error 모두 누락"""
        response = {
            "id": "test-id",
        }

        is_valid, error = BridgeProtocolValidator.validate_response(response)

        assert is_valid is False
        assert "result" in error or "error" in error

    def test_validate_response_invalid_error_type(self):
        """error 타입 오류"""
        response = {
            "id": "test-id",
            "result": None,
            "error": "error string",  # 객체여야 함
        }

        is_valid, error = BridgeProtocolValidator.validate_response(response)

        assert is_valid is False

    def test_validate_response_missing_error_code(self):
        """error.code 필드 누락"""
        response = {
            "id": "test-id",
            "error": {
                "message": "Error message",
            },
        }

        is_valid, error = BridgeProtocolValidator.validate_response(response)

        assert is_valid is False
        assert "code" in error

    def test_validate_response_missing_error_message(self):
        """error.message 필드 누락"""
        response = {
            "id": "test-id",
            "error": {
                "code": "TEST_ERROR",
            },
        }

        is_valid, error = BridgeProtocolValidator.validate_response(response)

        assert is_valid is False
        assert "message" in error

    def test_validate_response_invalid_error_code_type(self):
        """error.code 타입 오류"""
        response = {
            "id": "test-id",
            "error": {
                "code": 123,
                "message": "Error message",
            },
        }

        is_valid, error = BridgeProtocolValidator.validate_response(response)

        assert is_valid is False

    def test_validate_response_invalid_error_message_type(self):
        """error.message 타입 오류"""
        response = {
            "id": "test-id",
            "error": {
                "code": "TEST_ERROR",
                "message": 123,
            },
        }

        is_valid, error = BridgeProtocolValidator.validate_response(response)

        assert is_valid is False

    # 엣지 케이스 테스트
    def test_validate_request_with_empty_args_and_kwargs(self):
        """빈 args와 kwargs"""
        request = {
            "id": "test-id",
            "method": "method",
            "args": [],
            "kwargs": {},
        }

        is_valid, error = BridgeProtocolValidator.validate_request(request)

        assert is_valid is True

    def test_validate_response_with_nested_result(self):
        """중첩된 result 구조"""
        response = {
            "id": "test-id",
            "result": {
                "stock": {
                    "code": "005930",
                    "prices": [70000, 69500, 70100],
                },
            },
            "error": None,
        }

        is_valid, error = BridgeProtocolValidator.validate_response(response)

        assert is_valid is True

    def test_validate_response_with_metadata(self):
        """메타데이터 포함"""
        response = {
            "id": "test-id",
            "result": {"data": "value"},
            "error": None,
            "metadata": {
                "timestamp": "2026-03-24T00:00:00+09:00",
                "notice": "Market closed",
            },
        }

        is_valid, error = BridgeProtocolValidator.validate_response(response)

        assert is_valid is True


class TestBridgeErrorResponse:
    """BridgeErrorResponse 클래스 테스트"""

    def test_create_error_response(self):
        """에러 응답 생성"""
        error = BridgeErrorResponse(
            code="TEST_ERROR",
            message="Test error message",
            details={"detail": "value"},
        )

        assert error.code == "TEST_ERROR"
        assert error.message == "Test error message"
        assert error.details == {"detail": "value"}

    def test_error_response_to_dict(self):
        """에러 응답을 딕셔너리로 변환"""
        error = BridgeErrorResponse(
            code="TEST_ERROR",
            message="Test message",
        )

        data = error.to_dict()

        assert data["code"] == "TEST_ERROR"
        assert data["message"] == "Test message"
        assert "details" not in data

    def test_error_response_with_details(self):
        """세부사항 포함 에러 응답"""
        error = BridgeErrorResponse(
            code="TEST_ERROR",
            message="Test message",
            details={"key": "value"},
        )

        data = error.to_dict()

        assert data["details"] == {"key": "value"}

    def test_error_response_from_dict(self):
        """딕셔너리에서 에러 응답 생성"""
        data = {
            "code": "TEST_ERROR",
            "message": "Test message",
            "details": {"key": "value"},
        }

        error = BridgeErrorResponse.from_dict(data)

        assert error.code == "TEST_ERROR"
        assert error.message == "Test message"
        assert error.details == {"key": "value"}


class TestIntegration:
    """통합 테스트"""

    def test_full_request_response_cycle(self):
        """전체 요청/응답 사이클"""
        # 요청 생성 및 직렬화
        request = BridgeRequest.create(
            method="price",
            args=["005930"],
            request_id="integration-test",
        )

        # 요청 검증
        is_valid, _ = BridgeProtocolValidator.validate_request(request.to_dict())
        assert is_valid

        # 요청 JSON 직렬화
        request_json = request.to_json()
        parsed_request = json.loads(request_json)

        # 응답 생성 및 직렬화
        response = BridgeResponse.success(
            request_id=parsed_request["id"],
            result={"code": "005930", "price": 70000},
        )

        # 응답 검증
        is_valid, _ = BridgeProtocolValidator.validate_response(response.to_dict())
        assert is_valid

        # 응답 JSON 직렬화
        response_json = response.to_json()
        parsed_response = json.loads(response_json)

        assert parsed_response["id"] == request.id
        assert parsed_response["result"]["code"] == "005930"

    def test_error_handling_cycle(self):
        """에러 처리 사이클"""
        # 요청 생성
        request = BridgeRequest.create(
            method="price",
            args=["INVALID"],
            request_id="error-test",
        )

        # 응답 생성 (에러)
        response = BridgeResponse.error(
            request_id=request.id,
            code=BridgeErrorCode.INVALID_PARAMS,
            message="Invalid stock code",
            details={"code": "INVALID"},
        )

        # 응답 검증
        is_valid, _ = BridgeProtocolValidator.validate_response(response.to_dict())
        assert is_valid

        # 응답 확인
        assert response.is_error()
        assert response.error.code == BridgeErrorCode.INVALID_PARAMS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
