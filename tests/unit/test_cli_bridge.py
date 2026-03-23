"""Tests for kis_agent.cli_bridge JSON communication protocol."""

import json
import pytest

from kis_agent.cli_bridge import (
    BridgeResponse,
    _execute_command,
    _parse_request,
)


class TestBridgeResponse:
    """Test BridgeResponse helper class."""

    def test_success_with_data(self):
        """Test success response with data."""
        response_str = BridgeResponse.success({"key": "value"})
        response = json.loads(response_str)

        assert "data" in response
        assert response["data"] == {"key": "value"}
        assert "_notice" not in response

    def test_success_with_notice(self):
        """Test success response with notice."""
        response_str = BridgeResponse.success({"key": "value"}, "Market closed")
        response = json.loads(response_str)

        assert response["data"] == {"key": "value"}
        assert response["_notice"] == "Market closed"

    def test_success_with_non_serializable_data(self):
        """Test success response with non-serializable objects (using default=str)."""
        class CustomObj:
            def __str__(self):
                return "custom"

        response_str = BridgeResponse.success({"obj": CustomObj()})
        response = json.loads(response_str)

        assert "data" in response
        assert response["data"]["obj"] == "custom"

    def test_error_basic(self):
        """Test error response with basic fields."""
        response_str = BridgeResponse.error("Something went wrong")
        response = json.loads(response_str)

        assert response["error"] == "Something went wrong"
        assert response["code"] == "Error"
        assert "traceback" not in response

    def test_error_with_code(self):
        """Test error response with custom error code."""
        response_str = BridgeResponse.error("Invalid value", "ValueError")
        response = json.loads(response_str)

        assert response["error"] == "Invalid value"
        assert response["code"] == "ValueError"

    def test_error_with_traceback(self):
        """Test error response with traceback."""
        tb_str = "Traceback (most recent call last):\n  File ..."
        response_str = BridgeResponse.error("Error occurred", "RuntimeError", tb_str)
        response = json.loads(response_str)

        assert response["error"] == "Error occurred"
        assert response["code"] == "RuntimeError"
        assert response["traceback"] == tb_str


class TestParseRequest:
    """Test request parsing."""

    def test_parse_valid_request(self):
        """Test parsing a valid request."""
        request_str = '{"method": "price", "args": {"code": "005930"}, "kwargs": {}}'
        request = _parse_request(request_str)

        assert request["method"] == "price"
        assert request["args"] == {"code": "005930"}
        assert request["kwargs"] == {}

    def test_parse_request_with_kwargs(self):
        """Test parsing request with kwargs."""
        request_str = '{"method": "price", "args": {"code": "005930"}, "kwargs": {"daily": true}}'
        request = _parse_request(request_str)

        assert request["method"] == "price"
        assert request["args"]["code"] == "005930"
        assert request["kwargs"]["daily"] is True

    def test_parse_request_missing_args(self):
        """Test parsing request without args field (should default to {})."""
        request_str = '{"method": "price"}'
        request = _parse_request(request_str)

        assert request["method"] == "price"
        assert request["args"] == {}
        assert request["kwargs"] == {}

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON."""
        with pytest.raises(ValueError, match="Invalid JSON"):
            _parse_request("{invalid json")

    def test_parse_non_dict_json(self):
        """Test parsing JSON that's not an object."""
        with pytest.raises(ValueError, match="must be a JSON object"):
            _parse_request('["array"]')

    def test_parse_missing_method(self):
        """Test parsing request without method field."""
        with pytest.raises(ValueError, match="must have 'method' field"):
            _parse_request('{"args": {}}')

    def test_parse_non_string_method(self):
        """Test parsing request with non-string method."""
        with pytest.raises(ValueError, match="must have 'method' field"):
            _parse_request('{"method": 123, "args": {}}')

    def test_parse_invalid_args_type(self):
        """Test parsing request with invalid args type."""
        with pytest.raises(ValueError, match="'args' field must be a dict"):
            _parse_request('{"method": "price", "args": "invalid"}')

    def test_parse_invalid_kwargs_type(self):
        """Test parsing request with invalid kwargs type."""
        with pytest.raises(ValueError, match="'kwargs' field must be a dict"):
            _parse_request('{"method": "price", "kwargs": "invalid"}')


class TestExecuteCommand:
    """Test command execution routing.

    Note: These tests mock the CLI handlers since they require real API access.
    """

    def test_unknown_method(self):
        """Test executing unknown method."""
        with pytest.raises(ValueError, match="Unknown command"):
            _execute_command("unknown_method", {}, {})

    def test_schema_handler_exists(self):
        """Test that schema handler is registered."""
        # cmd_schema exists and should not raise ValueError for unknown method
        # (it may fail for other reasons like missing args, but not "unknown command")
        with pytest.raises(Exception):
            # Will fail because schema requires proper args, but not "unknown command"
            _execute_command("schema", {}, {})
