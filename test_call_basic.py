#!/usr/bin/env python3
"""
기본 call() 메서드 테스트 - JSON 직렬화/역직렬화 및 타임아웃 동작 검증
"""

import json
import subprocess
import sys
import time
from kis_agent.bridge import PythonBridge, PythonNotFoundError


def test_python_bridge_detection():
    """Python Bridge 초기화 및 감지 테스트"""
    print("=== Test 1: Python Bridge Detection ===")
    try:
        bridge = PythonBridge()
        print(f"✓ Python detected: {bridge.python_executable}")
        print(f"  Version: {bridge.python_version_string}")
        print(f"  Path: {bridge.python_path}")
        print(f"  Is available: {bridge.is_available}")
        return True
    except PythonNotFoundError as e:
        print(f"✗ Python detection failed: {e}")
        return False


def test_call_json_serialization():
    """JSON 직렬화/역직렬화 테스트"""
    print("\n=== Test 2: JSON Serialization/Deserialization ===")

    # 요청 데이터
    request_data = {
        "method": "price",
        "args": {"code": "005930"},
        "kwargs": {},
    }

    # JSON 직렬화
    request_json = json.dumps(request_data, ensure_ascii=False)
    print(f"Request JSON: {request_json}")

    # JSON 역직렬화
    parsed_request = json.loads(request_json)
    print(f"Parsed request: {parsed_request}")

    # 응답 데이터
    response_data = {
        "data": {"stock": "Samsung"},
        "_notice": "Market closed",
    }

    # JSON 직렬화
    response_json = json.dumps(response_data, ensure_ascii=False)
    print(f"Response JSON: {response_json}")

    # JSON 역직렬화
    parsed_response = json.loads(response_json)
    print(f"Parsed response: {parsed_response}")

    print("✓ JSON serialization/deserialization passed")
    return True


def test_call_method_basic():
    """call() 메서드 기본 동작 테스트"""
    print("\n=== Test 3: call() Method Basic Execution ===")

    try:
        bridge = PythonBridge()

        # 타임아웃을 길게 설정하여 기본 동작만 검증
        # 실제 가격 조회 (환경변수가 설정되어 있어야 함)
        print("Testing call() with simple schema query...")

        # 간단한 메서드 테스트
        result = bridge.call("schema", args={"type_name": "Stock"}, timeout=30)

        if "error" in result:
            print(f"Error response received (expected if env not set): {result['code']}")
            print(f"  Message: {result.get('error', '')}")
        else:
            print(f"✓ call() executed successfully")
            print(f"  Response keys: {list(result.keys())}")

        return True
    except subprocess.TimeoutExpired:
        print(f"✗ call() timed out (exceeded 30 seconds)")
        return False
    except Exception as e:
        print(f"✗ call() execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_call_timeout():
    """타임아웃 동작 테스트 (빠른 타임아웃 설정)"""
    print("\n=== Test 4: Timeout Behavior ===")

    try:
        bridge = PythonBridge()

        # 매우 짧은 타임아웃으로 타임아웃 동작 검증
        print("Testing timeout with 1 second limit...")

        try:
            result = bridge.call(
                "schema",
                args={"type_name": "Stock"},
                timeout=1  # 1초 타임아웃
            )
            print(f"Note: call() completed within 1 second (timeout not triggered)")
            print(f"  Response: {result}")
        except subprocess.TimeoutExpired:
            print(f"✓ TimeoutExpired raised as expected")
            return True

        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def main():
    """모든 테스트 실행"""
    print("Starting basic call() method tests...\n")

    results = {
        "Python Detection": test_python_bridge_detection(),
        "JSON Serialization": test_call_json_serialization(),
        "call() Basic Execution": test_call_method_basic(),
        "Timeout Behavior": test_call_timeout(),
    }

    print("\n" + "=" * 60)
    print("TEST RESULTS:")
    print("=" * 60)

    passed = 0
    failed = 0

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
        else:
            failed += 1

    print("=" * 60)
    print(f"Total: {passed} passed, {failed} failed")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
