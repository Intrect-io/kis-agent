"""
Bridge 메시지 파이프라인 테스트

stdin/stdout을 통한 JSON 메시지 송수신 기능을 테스트합니다.
"""

import json
import io
import sys
import pytest
from kis_agent.bridge_protocol import (
    BridgeRequest,
    BridgeResponse,
    BridgeErrorResponse,
)
from kis_agent.bridge_pipeline import (
    BridgeMessagePipeline,
    MessageReadError,
    MessageWriteError,
)


class TestBridgeMessagePipeline:
    """BridgeMessagePipeline 테스트"""

    def test_receive_valid_request(self, monkeypatch):
        """유효한 요청 수신 테스트"""
        request_json = '{"id": "test-123", "method": "price", "args": ["005930"], "kwargs": {"daily": true}}'
        monkeypatch.setattr("sys.stdin", io.StringIO(request_json + "\n"))

        pipeline = BridgeMessagePipeline()
        request = pipeline.receive_message()

        assert request is not None
        assert request.id == "test-123"
        assert request.method == "price"
        assert request.args == ["005930"]
        assert request.kwargs == {"daily": True}

    def test_receive_minimal_request(self, monkeypatch):
        """최소 필드만 있는 요청 수신 테스트"""
        request_json = '{"id": "test-456", "method": "balance"}'
        monkeypatch.setattr("sys.stdin", io.StringIO(request_json + "\n"))

        pipeline = BridgeMessagePipeline()
        request = pipeline.receive_message()

        assert request is not None
        assert request.id == "test-456"
        assert request.method == "balance"
        assert request.args == []
        assert request.kwargs == {}

    def test_receive_eof(self, monkeypatch):
        """EOF 처리 테스트"""
        monkeypatch.setattr("sys.stdin", io.StringIO(""))

        pipeline = BridgeMessagePipeline()
        request = pipeline.receive_message()

        assert request is None

    def test_receive_empty_line(self, monkeypatch):
        """빈 줄 처리 테스트"""
        monkeypatch.setattr("sys.stdin", io.StringIO("\n"))

        pipeline = BridgeMessagePipeline()
        request = pipeline.receive_message()

        assert request is None

    def test_receive_invalid_json(self, monkeypatch):
        """잘못된 JSON 처리 테스트"""
        monkeypatch.setattr("sys.stdin", io.StringIO('{"id": invalid}\n'))

        pipeline = BridgeMessagePipeline()
        with pytest.raises(MessageReadError, match="JSON 파싱 실패"):
            pipeline.receive_message()

    def test_receive_missing_id(self, monkeypatch):
        """id 필드 누락 처리 테스트"""
        request_json = '{"method": "price"}'
        monkeypatch.setattr("sys.stdin", io.StringIO(request_json + "\n"))

        pipeline = BridgeMessagePipeline()
        with pytest.raises(MessageReadError, match="요청 검증 실패"):
            pipeline.receive_message()

    def test_receive_missing_method(self, monkeypatch):
        """method 필드 누락 처리 테스트"""
        request_json = '{"id": "test-789"}'
        monkeypatch.setattr("sys.stdin", io.StringIO(request_json + "\n"))

        pipeline = BridgeMessagePipeline()
        with pytest.raises(MessageReadError, match="요청 검증 실패"):
            pipeline.receive_message()

    def test_receive_invalid_method_name(self, monkeypatch):
        """잘못된 메서드 이름 처리 테스트"""
        request_json = '{"id": "test-999", "method": "get-price"}'
        monkeypatch.setattr("sys.stdin", io.StringIO(request_json + "\n"))

        pipeline = BridgeMessagePipeline()
        with pytest.raises(MessageReadError, match="요청 검증 실패"):
            pipeline.receive_message()

    def test_send_success_response(self, monkeypatch):
        """성공 응답 전송 테스트"""
        output = io.StringIO()
        monkeypatch.setattr("sys.stdout", output)

        response = BridgeResponse.success(
            request_id="test-123",
            result={"stock": "005930", "price": 70000},
        )

        pipeline = BridgeMessagePipeline()
        pipeline.send_message(response)

        output_str = output.getvalue()
        assert output_str.endswith("\n")

        # JSON 파싱 확인
        data = json.loads(output_str.strip())
        assert data["id"] == "test-123"
        assert data["result"]["stock"] == "005930"
        assert data["error"] is None

    def test_send_error_response(self, monkeypatch):
        """에러 응답 전송 테스트"""
        output = io.StringIO()
        monkeypatch.setattr("sys.stdout", output)

        response = BridgeResponse.error(
            request_id="test-456",
            code="INVALID_PARAMS",
            message="Invalid stock code",
            details={"code": "999999"},
        )

        pipeline = BridgeMessagePipeline()
        pipeline.send_message(response)

        output_str = output.getvalue()
        assert output_str.endswith("\n")

        # JSON 파싱 확인
        data = json.loads(output_str.strip())
        assert data["id"] == "test-456"
        assert data["result"] is None
        assert data["error"]["code"] == "INVALID_PARAMS"
        assert data["error"]["message"] == "Invalid stock code"
        assert data["error"]["details"]["code"] == "999999"

    def test_send_request(self, monkeypatch):
        """요청 전송 테스트"""
        output = io.StringIO()
        monkeypatch.setattr("sys.stdout", output)

        request = BridgeRequest.create(
            method="price",
            args=["005930"],
            kwargs={"daily": True},
        )

        pipeline = BridgeMessagePipeline()
        pipeline.send_request(request)

        output_str = output.getvalue()
        assert output_str.endswith("\n")

        # JSON 파싱 확인
        data = json.loads(output_str.strip())
        assert data["method"] == "price"
        assert data["args"] == ["005930"]
        assert data["kwargs"] == {"daily": True}

    def test_roundtrip_request_response(self, monkeypatch):
        """요청-응답 왕복 테스트"""
        # 요청 전송
        request = BridgeRequest.create(
            method="balance",
            args=["12345"],
        )

        output = io.StringIO()
        monkeypatch.setattr("sys.stdout", output)

        pipeline = BridgeMessagePipeline()
        pipeline.send_request(request)

        # 요청 읽기
        monkeypatch.setattr("sys.stdin", io.StringIO(output.getvalue()))
        received_request = pipeline.receive_message()

        assert received_request.id == request.id
        assert received_request.method == request.method
        assert received_request.args == request.args

        # 응답 전송
        output = io.StringIO()
        monkeypatch.setattr("sys.stdout", output)

        response = BridgeResponse.success(
            request_id=request.id,
            result={"balance": 100000},
        )
        pipeline.send_message(response)

        # 응답 읽기
        response_data = json.loads(output.getvalue().strip())
        assert response_data["id"] == request.id
        assert response_data["result"]["balance"] == 100000


class TestMessageProtocolCompliance:
    """메시지 프로토콜 준수 테스트"""

    def test_request_message_format(self):
        """요청 메시지 형식 테스트"""
        request = BridgeRequest.create(
            method="price",
            args=["005930"],
            kwargs={"daily": True},
            request_id="req-123",
        )

        data = request.to_dict()

        # 필수 필드 확인
        assert "id" in data
        assert "method" in data
        assert data["id"] == "req-123"
        assert data["method"] == "price"

        # 선택 필드 확인
        assert "args" in data
        assert "kwargs" in data

    def test_response_success_format(self):
        """성공 응답 메시지 형식 테스트"""
        response = BridgeResponse.success(
            request_id="req-123",
            result={"data": "value"},
        )

        data = response.to_dict()

        # 필수 필드 확인
        assert "id" in data
        assert data["id"] == "req-123"

        # result와 error 확인
        assert "result" in data
        assert data["result"]["data"] == "value"
        assert "error" in data
        assert data["error"] is None

    def test_response_error_format(self):
        """에러 응답 메시지 형식 테스트"""
        response = BridgeResponse.error(
            request_id="req-456",
            code="INVALID_PARAMS",
            message="Invalid parameter",
        )

        data = response.to_dict()

        # 필수 필드 확인
        assert "id" in data
        assert data["id"] == "req-456"

        # result와 error 확인
        assert "result" in data
        assert data["result"] is None
        assert "error" in data
        assert data["error"]["code"] == "INVALID_PARAMS"
        assert data["error"]["message"] == "Invalid parameter"

    def test_newline_separated_messages(self, monkeypatch):
        """줄바꿈으로 구분된 여러 메시지 처리 테스트"""
        # 3개의 메시지를 줄바꿈으로 구분
        messages = [
            '{"id": "msg-1", "method": "price"}',
            '{"id": "msg-2", "method": "balance"}',
            '{"id": "msg-3", "method": "query"}',
        ]
        input_stream = io.StringIO("\n".join(messages) + "\n")
        monkeypatch.setattr("sys.stdin", input_stream)

        pipeline = BridgeMessagePipeline()

        # 첫 번째 메시지
        req1 = pipeline.receive_message()
        assert req1.id == "msg-1"

        # 두 번째 메시지
        req2 = pipeline.receive_message()
        assert req2.id == "msg-2"

        # 세 번째 메시지
        req3 = pipeline.receive_message()
        assert req3.id == "msg-3"

        # EOF
        req4 = pipeline.receive_message()
        assert req4 is None

    def test_json_serialization_stability(self):
        """JSON 직렬화 안정성 테스트"""
        request = BridgeRequest.create(
            method="test_method",
            args=[1, "string", True, None, {"key": "value"}],
            kwargs={"nested": {"obj": "value"}},
        )

        # 첫 직렬화
        json1 = request.to_json()

        # 역직렬화 후 재직렬화
        request2 = BridgeRequest.from_json(json1)
        json2 = request2.to_json()

        # JSON 문자열이 동일해야 함
        assert json.loads(json1) == json.loads(json2)

    def test_unicode_handling(self, monkeypatch):
        """유니코드 처리 테스트"""
        request_json = '{"id": "test-korean", "method": "query", "args": ["삼성전자"], "kwargs": {"name": "한국전자"}}'
        monkeypatch.setattr("sys.stdin", io.StringIO(request_json + "\n"))

        pipeline = BridgeMessagePipeline()
        request = pipeline.receive_message()

        assert request.args[0] == "삼성전자"
        assert request.kwargs["name"] == "한국전자"

        # 응답도 유니코드 처리 확인
        output = io.StringIO()
        monkeypatch.setattr("sys.stdout", output)

        response = BridgeResponse.success(
            request_id=request.id,
            result={"name": "삼성전자", "type": "대형주"},
        )
        pipeline.send_message(response)

        output_str = output.getvalue()
        data = json.loads(output_str.strip())
        assert data["result"]["name"] == "삼성전자"
        assert data["result"]["type"] == "대형주"
