"""
Bridge stdin/stdout 통신 파이프라인 테스트
"""

import json
import pytest
from io import StringIO
from typing import Any, Dict

from kis_agent.bridge_protocol import BridgeRequest, BridgeResponse, BridgeErrorCode
from kis_agent.bridge_stdio import (
    BridgeStdioReader,
    BridgeStdioWriter,
    BridgeCommunicationPipeline,
)


class TestBridgeStdioReader:
    """BridgeStdioReader 테스트"""

    def test_read_json_line_simple(self):
        """단순 JSON 라인 읽기"""
        stdin = StringIO('{"key": "value"}\n')
        reader = BridgeStdioReader(stdin)
        line = reader.read_json_line()
        assert line == '{"key": "value"}'

    def test_read_json_line_with_newline(self):
        """개행 문자 제거 테스트"""
        stdin = StringIO('{"key": "value"}\r\n')
        reader = BridgeStdioReader(stdin)
        line = reader.read_json_line()
        assert line == '{"key": "value"}'

    def test_read_json_line_eof(self):
        """EOF에서 None 반환"""
        stdin = StringIO("")
        reader = BridgeStdioReader(stdin)
        line = reader.read_json_line()
        assert line is None

    def test_read_request_valid(self):
        """유효한 요청 읽기"""
        request_json = json.dumps({
            "id": "test-123",
            "method": "price",
            "args": ["005930"],
            "kwargs": {"daily": True},
        })
        stdin = StringIO(request_json + "\n")
        reader = BridgeStdioReader(stdin)
        request = reader.read_request()

        assert request is not None
        assert request.id == "test-123"
        assert request.method == "price"
        assert request.args == ["005930"]
        assert request.kwargs == {"daily": True}

    def test_read_request_invalid_json(self):
        """잘못된 JSON"""
        stdin = StringIO("invalid json\n")
        reader = BridgeStdioReader(stdin)
        request = reader.read_request()
        assert request is None

    def test_read_request_missing_method(self):
        """필수 필드 누락"""
        request_json = json.dumps({
            "id": "test-123",
            # method 누락
        })
        stdin = StringIO(request_json + "\n")
        reader = BridgeStdioReader(stdin)
        request = reader.read_request()
        assert request is None

    def test_read_request_invalid_method_name(self):
        """유효하지 않은 메서드 이름"""
        request_json = json.dumps({
            "id": "test-123",
            "method": "invalid-method",  # 하이픈 불가
        })
        stdin = StringIO(request_json + "\n")
        reader = BridgeStdioReader(stdin)
        request = reader.read_request()
        assert request is None


class TestBridgeStdioWriter:
    """BridgeStdioWriter 테스트"""

    def test_write_json_line(self):
        """JSON 라인 송신"""
        stdout = StringIO()
        writer = BridgeStdioWriter(stdout)
        data = {"key": "value"}
        result = writer.write_json_line(data)

        assert result is True
        output = stdout.getvalue()
        assert output == '{"key": "value"}\n'

    def test_write_response_success(self):
        """성공 응답 송신"""
        stdout = StringIO()
        writer = BridgeStdioWriter(stdout)
        response = BridgeResponse.success(
            request_id="test-123",
            result={"status": "ok"},
        )
        result = writer.write_response(response)

        assert result is True
        output = stdout.getvalue()
        response_data = json.loads(output.strip())
        assert response_data["id"] == "test-123"
        assert response_data["result"] == {"status": "ok"}
        assert response_data["error"] is None

    def test_write_response_error(self):
        """에러 응답 송신"""
        stdout = StringIO()
        writer = BridgeStdioWriter(stdout)
        response = BridgeResponse.error(
            request_id="test-456",
            code=BridgeErrorCode.INVALID_PARAMS,
            message="Invalid parameter",
            details={"param": "code"},
        )
        result = writer.write_response(response)

        assert result is True
        output = stdout.getvalue()
        response_data = json.loads(output.strip())
        assert response_data["id"] == "test-456"
        assert response_data["error"]["code"] == "INVALID_PARAMS"
        assert response_data["error"]["message"] == "Invalid parameter"
        assert response_data["error"]["details"]["param"] == "code"

    def test_write_success_shorthand(self):
        """write_success 단축 메서드"""
        stdout = StringIO()
        writer = BridgeStdioWriter(stdout)
        result = writer.write_success(
            request_id="test-789",
            result={"data": "example"},
        )

        assert result is True
        output = stdout.getvalue()
        response_data = json.loads(output.strip())
        assert response_data["id"] == "test-789"
        assert response_data["result"]["data"] == "example"

    def test_write_error_shorthand(self):
        """write_error 단축 메서드"""
        stdout = StringIO()
        writer = BridgeStdioWriter(stdout)
        result = writer.write_error(
            request_id="test-999",
            code="METHOD_NOT_FOUND",
            message="Method not found",
            details={"method": "unknown"},
        )

        assert result is True
        output = stdout.getvalue()
        response_data = json.loads(output.strip())
        assert response_data["id"] == "test-999"
        assert response_data["error"]["code"] == "METHOD_NOT_FOUND"


class TestBridgeCommunicationPipeline:
    """BridgeCommunicationPipeline 통합 테스트"""

    def test_pipeline_single_request_response(self):
        """단일 요청/응답 처리"""
        request_json = json.dumps({
            "id": "req-001",
            "method": "echo",
            "args": ["hello"],
            "kwargs": {},
        })
        stdin = StringIO(request_json + "\n")
        stdout = StringIO()

        def handler(request: BridgeRequest) -> BridgeResponse:
            return BridgeResponse.success(
                request_id=request.id,
                result={"echo": request.args[0] if request.args else None},
            )

        pipeline = BridgeCommunicationPipeline(stdin, stdout)
        pipeline.run(handler)

        output = stdout.getvalue()
        response_data = json.loads(output.strip())
        assert response_data["id"] == "req-001"
        assert response_data["result"]["echo"] == "hello"

    def test_pipeline_error_handling(self):
        """파이프라인 에러 처리"""
        request_json = json.dumps({
            "id": "req-002",
            "method": "divide",
            "args": [10, 0],
            "kwargs": {},
        })
        stdin = StringIO(request_json + "\n")
        stdout = StringIO()

        def handler(request: BridgeRequest) -> BridgeResponse:
            # 의도적 에러
            raise ValueError("Division by zero")

        pipeline = BridgeCommunicationPipeline(stdin, stdout)
        pipeline.run(handler)

        output = stdout.getvalue()
        response_data = json.loads(output.strip())
        assert response_data["id"] == "req-002"
        assert response_data["error"]["code"] == "INTERNAL_ERROR"

    def test_pipeline_send_and_read(self):
        """양방향 통신 (디버깅/테스트용)"""
        stdin = StringIO()
        stdout = StringIO()

        pipeline = BridgeCommunicationPipeline(stdin, stdout)

        # 요청 송신
        request = BridgeRequest.create(
            method="test",
            args=["arg1"],
            kwargs={"key": "value"},
        )
        result = pipeline.send_request(request)
        assert result is True

        # 송신된 데이터 확인
        output = stdout.getvalue()
        request_data = json.loads(output.strip())
        assert request_data["method"] == "test"
        assert request_data["args"] == ["arg1"]
        assert request_data["kwargs"] == {"key": "value"}


class TestBridgeEndToEnd:
    """End-to-end 통합 테스트"""

    def test_multiple_requests(self):
        """여러 요청 순차 처리"""
        requests = [
            {"id": "r1", "method": "get_balance", "args": [], "kwargs": {}},
            {"id": "r2", "method": "get_price", "args": ["005930"], "kwargs": {}},
            {"id": "r3", "method": "get_holding", "args": [], "kwargs": {}},
        ]
        stdin_content = "\n".join(json.dumps(r) for r in requests) + "\n"
        stdin = StringIO(stdin_content)
        stdout = StringIO()

        def handler(request: BridgeRequest) -> BridgeResponse:
            results = {
                "get_balance": {"balance": 1000000},
                "get_price": {"price": 70000},
                "get_holding": {"holding": []},
            }
            result = results.get(request.method, {})
            return BridgeResponse.success(request_id=request.id, result=result)

        pipeline = BridgeCommunicationPipeline(stdin, stdout)
        pipeline.run(handler)

        outputs = stdout.getvalue().strip().split("\n")
        assert len(outputs) == 3

        for i, output in enumerate(outputs):
            response_data = json.loads(output)
            assert response_data["id"] == f"r{i+1}"
            assert response_data["error"] is None
            assert "result" in response_data

    def test_korean_text_handling(self):
        """한글 텍스트 처리"""
        request_json = json.dumps({
            "id": "kr-001",
            "method": "search",
            "args": ["삼성전자"],
            "kwargs": {"market": "코스피"},
        })
        stdin = StringIO(request_json + "\n")
        stdout = StringIO()

        def handler(request: BridgeRequest) -> BridgeResponse:
            return BridgeResponse.success(
                request_id=request.id,
                result={"query": request.args[0], "market": request.kwargs.get("market")},
            )

        pipeline = BridgeCommunicationPipeline(stdin, stdout)
        pipeline.run(handler)

        output = stdout.getvalue()
        response_data = json.loads(output.strip())
        assert response_data["result"]["query"] == "삼성전자"
        assert response_data["result"]["market"] == "코스피"
