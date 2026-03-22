#!/usr/bin/env python3
"""kis-agent CLI Bridge — subprocess JSON 통신 레이어.

stdin으로 JSON 형식의 명령어를 받아 kis_agent.cli.main 함수들을 호출하고,
stdout으로 JSON 형식의 결과를 반환합니다.

사용법 (subprocess에서):
    echo '{"command": "price", "code": "005930"}' | kis-cli-bridge
    echo '{"command": "balance", "holdings": true}' | kis-cli-bridge
    echo '{"command": "orderbook", "code": "005930"}' | kis-cli-bridge
"""

import argparse
import json
import sys
from io import StringIO
from typing import Any, Dict
from contextlib import redirect_stdout

from kis_agent.cli.main import (
    build_parser,
    cmd_price,
    cmd_balance,
    cmd_orderbook,
    cmd_overseas,
    cmd_futures,
    cmd_query,
    cmd_schema,
)


def json_to_args(command: str, params: Dict[str, Any]) -> argparse.Namespace:
    """JSON 파라미터를 argparse.Namespace로 변환.

    Args:
        command: CLI 명령어 (price, balance, orderbook, 등)
        params: JSON 파라미터 딕셔너리

    Returns:
        argparse.Namespace 객체
    """
    parser = build_parser()

    # 명령어에 맞는 서브파서 선택
    cmd_args = [command]

    # 위치 인자와 옵션 인자 분리
    if command == "price":
        cmd_args.append(params.get("code", ""))
        if params.get("daily"):
            cmd_args.append("--daily")
        if params.get("period"):
            cmd_args.extend(["--period", params["period"]])
        if "days" in params:
            cmd_args.extend(["--days", str(params["days"])])

    elif command == "balance":
        if params.get("holdings"):
            cmd_args.append("--holdings")

    elif command == "orderbook":
        cmd_args.append(params.get("code", ""))

    elif command == "overseas":
        cmd_args.append(params.get("excd", "").upper())
        cmd_args.append(params.get("symb", "").upper())
        if params.get("detail"):
            cmd_args.append("--detail")
        if params.get("daily"):
            cmd_args.append("--daily")
        if "days" in params:
            cmd_args.extend(["--days", str(params["days"])])

    elif command == "futures":
        cmd_args.append(params.get("code", ""))
        if params.get("overseas"):
            cmd_args.append("--overseas")
        if params.get("option"):
            cmd_args.append("--option")
        if params.get("orderbook"):
            cmd_args.append("--orderbook")

    elif command == "query":
        cmd_args.append(params.get("domain", ""))
        cmd_args.append(params.get("method", ""))
        if "args" in params:
            args_list = params["args"]
            if isinstance(args_list, list):
                cmd_args.extend(args_list)

    elif command == "schema":
        if "type" in params:
            cmd_args.append(params["type"])
        if params.get("json"):
            cmd_args.append("--json")

    if params.get("pretty"):
        cmd_args.append("--pretty")

    return parser.parse_args(cmd_args)


def execute_command(command: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """JSON 파라미터로 CLI 명령 실행.

    Args:
        command: CLI 명령어
        params: JSON 파라미터

    Returns:
        {"success": bool, "data": any, "error": str|None}
    """
    try:
        args = json_to_args(command, params)

        # 명령 핸들러 매핑
        handlers = {
            "price": cmd_price,
            "balance": cmd_balance,
            "orderbook": cmd_orderbook,
            "overseas": cmd_overseas,
            "futures": cmd_futures,
            "query": cmd_query,
            "schema": cmd_schema,
        }

        handler = handlers.get(command)
        if not handler:
            return {
                "success": False,
                "error": f"Unknown command: {command}",
                "data": None,
            }

        # stdout 캡처하여 핸들러 실행
        # (일부 핸들러는 print()로 직접 출력함)
        output_buffer = StringIO()
        with redirect_stdout(output_buffer):
            handler(args)

        output = output_buffer.getvalue().strip()
        if output:
            try:
                data = json.loads(output)
                return {
                    "success": True,
                    "data": data,
                    "error": None,
                }
            except json.JSONDecodeError:
                return {
                    "success": True,
                    "data": output,
                    "error": None,
                }

        return {
            "success": True,
            "data": None,
            "error": None,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": None,
        }


def main() -> None:
    """JSON 입력을 받아 CLI 명령어를 실행하고 결과를 JSON으로 반환."""
    try:
        # stdin에서 JSON 읽기
        input_data = json.load(sys.stdin)

        if not isinstance(input_data, dict):
            result = {
                "success": False,
                "error": "Invalid input format. Expected JSON object.",
                "data": None,
            }
            json.dump(result, sys.stdout)
            sys.exit(1)

        command = input_data.get("command")
        if not command:
            result = {
                "success": False,
                "error": "Missing 'command' field in input.",
                "data": None,
            }
            json.dump(result, sys.stdout)
            sys.exit(1)

        # 파라미터 추출 (command 제외)
        params = {k: v for k, v in input_data.items() if k != "command"}

        # 명령 실행
        result = execute_command(command, params)
        json.dump(result, sys.stdout, ensure_ascii=False)

    except json.JSONDecodeError as e:
        result = {
            "success": False,
            "error": f"Invalid JSON: {str(e)}",
            "data": None,
        }
        json.dump(result, sys.stdout)
        sys.exit(1)
    except Exception as e:
        result = {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "data": None,
        }
        json.dump(result, sys.stdout)
        sys.exit(1)


if __name__ == "__main__":
    main()
