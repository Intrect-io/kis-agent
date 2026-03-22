"""kis_agent.cli_bridge 모듈 테스트."""

import argparse
import json
import sys
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

from kis_agent.cli_bridge import execute_command, json_to_args, main


class TestJsonToArgs:
    """json_to_args 함수 테스트."""

    def test_price_command_with_code(self):
        """price 명령어 - 기본 코드 입력."""
        result = json_to_args("price", {"code": "005930"})
        assert isinstance(result, argparse.Namespace)
        assert result.code == "005930"

    def test_price_command_with_daily_flag(self):
        """price 명령어 - daily 플래그."""
        result = json_to_args("price", {"code": "005930", "daily": True})
        assert result.daily is True

    def test_price_command_with_period(self):
        """price 명령어 - period 옵션."""
        result = json_to_args("price", {"code": "005930", "period": "1h"})
        assert result.period == "1h"

    def test_price_command_with_days(self):
        """price 명령어 - days 옵션."""
        result = json_to_args("price", {"code": "005930", "days": 10})
        assert result.days == 10

    def test_balance_command_default(self):
        """balance 명령어 - 기본값."""
        result = json_to_args("balance", {})
        assert isinstance(result, argparse.Namespace)

    def test_balance_command_with_holdings(self):
        """balance 명령어 - holdings 플래그."""
        result = json_to_args("balance", {"holdings": True})
        assert result.holdings is True

    def test_orderbook_command(self):
        """orderbook 명령어."""
        result = json_to_args("orderbook", {"code": "005930"})
        assert result.code == "005930"

    def test_overseas_command_basic(self):
        """overseas 명령어 - 기본값."""
        result = json_to_args("overseas", {"excd": "nas", "symb": "aapl"})
        assert result.excd == "NAS"
        assert result.symb == "AAPL"

    def test_overseas_command_with_options(self):
        """overseas 명령어 - detail, daily 플래그."""
        result = json_to_args(
            "overseas", {"excd": "nyse", "symb": "goog", "detail": True, "daily": True}
        )
        assert result.excd == "NYSE"
        assert result.symb == "GOOG"
        assert result.detail is True
        assert result.daily is True

    def test_futures_command_basic(self):
        """futures 명령어 - 기본값."""
        result = json_to_args("futures", {"code": "CLM26"})
        assert result.code == "CLM26"

    def test_futures_command_with_flags(self):
        """futures 명령어 - overseas, option, orderbook 플래그."""
        result = json_to_args(
            "futures",
            {"code": "CLM26", "overseas": True, "option": True, "orderbook": True},
        )
        assert result.code == "CLM26"
        assert result.overseas is True
        assert result.option is True
        assert result.orderbook is True

    def test_query_command(self):
        """query 명령어."""
        result = json_to_args(
            "query", {"domain": "stock", "method": "price_info", "args": ["arg1", "arg2"]}
        )
        assert result.domain == "stock"
        assert result.method == "price_info"

    def test_schema_command_default(self):
        """schema 명령어 - 기본값."""
        result = json_to_args("schema", {})
        assert isinstance(result, argparse.Namespace)

    def test_schema_command_with_type(self):
        """schema 명령어 - type 지정."""
        result = json_to_args("schema", {"type": "stock"})
        assert result.type == "stock"

    def test_pretty_flag_common(self):
        """모든 명령어에서 pretty 플래그 지원."""
        result = json_to_args("price", {"code": "005930", "pretty": True})
        assert result.pretty is True


class TestExecuteCommand:
    """execute_command 함수 테스트."""

    @patch("kis_agent.cli_bridge.cmd_price")
    def test_execute_price_command_success(self, mock_cmd_price):
        """price 명령어 - 성공."""
        mock_cmd_price.return_value = None

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            with patch("kis_agent.cli_bridge.redirect_stdout"):
                result = execute_command("price", {"code": "005930"})

        assert result["success"] is True
        assert result["error"] is None

    @patch("kis_agent.cli_bridge.cmd_balance")
    def test_execute_balance_command_success(self, mock_cmd_balance):
        """balance 명령어 - 성공."""
        mock_cmd_balance.return_value = None

        with patch("kis_agent.cli_bridge.redirect_stdout"):
            result = execute_command("balance", {})

        assert result["success"] is True

    @patch("kis_agent.cli_bridge.cmd_orderbook")
    def test_execute_orderbook_command_success(self, mock_cmd_orderbook):
        """orderbook 명령어 - 성공."""
        mock_cmd_orderbook.return_value = None

        with patch("kis_agent.cli_bridge.redirect_stdout"):
            result = execute_command("orderbook", {"code": "005930"})

        assert result["success"] is True

    def test_execute_unknown_command(self):
        """알 수 없는 명령어."""
        with pytest.raises(SystemExit):
            result = execute_command("unknown_cmd", {})
            # argparse가 알 수 없는 서브명령어에 대해 SystemExit을 발생시킴

    @patch("kis_agent.cli_bridge.cmd_price")
    def test_execute_command_exception(self, mock_cmd_price):
        """명령어 실행 중 예외."""
        mock_cmd_price.side_effect = ValueError("Test error")

        with patch("kis_agent.cli_bridge.redirect_stdout"):
            result = execute_command("price", {"code": "005930"})

        assert result["success"] is False
        assert "Test error" in result["error"]

    @patch("kis_agent.cli_bridge.cmd_price")
    def test_execute_command_json_output(self, mock_cmd_price):
        """JSON 형식의 출력 결과."""
        json_output = '{"price": 70000, "code": "005930"}'

        def side_effect(args):
            print(json_output)

        mock_cmd_price.side_effect = side_effect

        result = execute_command("price", {"code": "005930"})

        assert result["success"] is True
        assert result["data"] == {"price": 70000, "code": "005930"}

    @patch("kis_agent.cli_bridge.cmd_price")
    def test_execute_command_text_output(self, mock_cmd_price):
        """텍스트 형식의 출력 결과."""
        text_output = "Price: 70000\nCode: 005930"

        def side_effect(args):
            print(text_output)

        mock_cmd_price.side_effect = side_effect

        result = execute_command("price", {"code": "005930"})

        assert result["success"] is True
        assert result["data"] == text_output


class TestMain:
    """main 함수 테스트."""

    @patch("kis_agent.cli_bridge.execute_command")
    def test_main_valid_input(self, mock_execute):
        """유효한 JSON 입력."""
        mock_execute.return_value = {
            "success": True,
            "data": {"price": 70000},
            "error": None,
        }

        json_input = '{"command": "price", "code": "005930"}'

        with patch("sys.stdin", StringIO(json_input)):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                main()
                output = mock_stdout.getvalue()
                result = json.loads(output)
                assert result["success"] is True

    def test_main_invalid_json(self):
        """잘못된 JSON 입력."""
        invalid_json = "not a json"

        with patch("sys.stdin", StringIO(invalid_json)):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                with patch("sys.exit"):
                    main()
                    output = mock_stdout.getvalue()
                    result = json.loads(output)
                    assert result["success"] is False
                    assert "Invalid JSON" in result["error"]

    def test_main_not_dict_input(self):
        """딕셔너리가 아닌 JSON 입력."""
        invalid_input = '["not", "a", "dict"]'

        with patch("sys.stdin", StringIO(invalid_input)):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                try:
                    main()
                except SystemExit:
                    pass
                output = mock_stdout.getvalue().strip()
                # JSON 전에 있는 문자들 제거
                start_idx = output.find('{')
                if start_idx != -1:
                    output = output[start_idx:]
                result = json.loads(output)
                assert result["success"] is False
                assert "Expected JSON object" in result["error"]

    def test_main_missing_command(self):
        """command 필드 누락."""
        invalid_input = '{"code": "005930"}'

        with patch("sys.stdin", StringIO(invalid_input)):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                try:
                    main()
                except SystemExit:
                    pass
                output = mock_stdout.getvalue().strip()
                # JSON 전에 있는 문자들 제거
                start_idx = output.find('{')
                if start_idx != -1:
                    output = output[start_idx:]
                result = json.loads(output)
                assert result["success"] is False
                assert "Missing 'command' field" in result["error"]

    @patch("kis_agent.cli_bridge.execute_command")
    def test_main_command_execution(self, mock_execute):
        """명령어 실행 및 파라미터 전달."""
        mock_execute.return_value = {
            "success": True,
            "data": None,
            "error": None,
        }

        json_input = '{"command": "balance", "holdings": true}'

        with patch("sys.stdin", StringIO(json_input)):
            with patch("sys.stdout", new_callable=StringIO):
                main()

        mock_execute.assert_called_once_with("balance", {"holdings": True})

    @patch("kis_agent.cli_bridge.execute_command")
    def test_main_ensure_ascii_false(self, mock_execute):
        """한글 포함 출력 (ensure_ascii=False)."""
        mock_execute.return_value = {
            "success": True,
            "data": {"message": "테스트 메시지"},
            "error": None,
        }

        json_input = '{"command": "price", "code": "005930"}'

        with patch("sys.stdin", StringIO(json_input)):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                main()
                output = mock_stdout.getvalue()
                result = json.loads(output)
                assert result["data"]["message"] == "테스트 메시지"


class TestIntegration:
    """통합 테스트."""

    @patch("kis_agent.cli_bridge.cmd_price")
    def test_json_to_args_and_execute_flow(self, mock_cmd_price):
        """json_to_args와 execute_command의 통합 흐름."""
        mock_cmd_price.return_value = None

        params = {"code": "005930", "daily": True, "period": "1h"}
        args = json_to_args("price", params)

        assert args.code == "005930"
        assert args.daily is True
        assert args.period == "1h"

    @patch("kis_agent.cli_bridge.execute_command")
    def test_main_to_execute_command_flow(self, mock_execute):
        """main 함수에서 execute_command로의 흐름."""
        mock_execute.return_value = {
            "success": True,
            "data": {"result": "success"},
            "error": None,
        }

        json_input = json.dumps({
            "command": "price",
            "code": "005930",
            "daily": True,
        })

        with patch("sys.stdin", StringIO(json_input)):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                main()
                output = mock_stdout.getvalue()
                result = json.loads(output)

                assert result["success"] is True
                assert result["data"]["result"] == "success"

                # execute_command가 올바른 인자로 호출되었는지 확인
                mock_execute.assert_called_once_with(
                    "price",
                    {"code": "005930", "daily": True}
                )
