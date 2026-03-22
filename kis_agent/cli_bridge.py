#!/usr/bin/env python3
"""kis-agent CLI Bridge — subprocess JSON 통신 레이어.

stdin으로 JSON 형식의 명령어를 받아 kis_agent.cli.main 함수들을 호출하고,
stdout으로 JSON 형식의 결과를 반환합니다.

사용법 (subprocess에서):
    echo '{"command": "price", "code": "005930"}' | kis-cli-bridge
    echo '{"command": "balance", "holdings": true}' | kis-cli-bridge
    echo '{"command": "orderbook", "code": "005930"}' | kis-cli-bridge
"""

import json
import sys
from typing import Any, Dict

from kis_agent.cli.main import main as cli_main


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

        # 추후 구현: JSON을 argparse 형식으로 변환하여 CLI 호출
        # 현재는 기본 구조만 제공
        command = input_data.get("command")

        if not command:
            result = {
                "success": False,
                "error": "Missing 'command' field in input.",
                "data": None,
            }
            json.dump(result, sys.stdout)
            sys.exit(1)

        # TODO: CLI 명령어 매핑 및 실행
        result = {
            "success": True,
            "command": command,
            "data": None,
        }
        json.dump(result, sys.stdout)

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
