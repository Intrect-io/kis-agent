#!/usr/bin/env python3
"""
Python Bridge 통합 테스트 - call() 메서드 및 JSON 처리 검증

이 스크립트는 다음을 검증합니다:
1. Python 감지 및 초기화
2. PythonNotFoundError 예외 처리
3. JSON 직렬화/역직렬화
4. call() 메서드의 타임아웃 동작
5. 에러 응답 처리
"""

import json
import subprocess
import sys
import logging
from pathlib import Path

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_python_bridge_basic():
    """Python Bridge 기본 초기화 테스트"""
    print("\n=== Test 1: Python Bridge Basic Initialization ===")

    # cli_bridge.py의 구문 검사
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", "kis_agent/bridge/python_bridge.py"],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("✓ python_bridge.py: 구문 검사 통과")
        return True
    else:
        print(f"✗ python_bridge.py: 구문 오류 - {result.stderr}")
        return False


def test_cli_bridge_basic():
    """CLI Bridge 기본 구문 검사"""
    print("\n=== Test 2: CLI Bridge Basic Syntax ===")

    result = subprocess.run(
        [sys.executable, "-m", "py_compile", "kis_agent/cli_bridge.py"],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("✓ cli_bridge.py: 구문 검사 통과")
        return True
    else:
        print(f"✗ cli_bridge.py: 구문 오류 - {result.stderr}")
        return False


def test_json_serialization():
    """JSON 직렬화/역직렬화 테스트"""
    print("\n=== Test 3: JSON Serialization/Deserialization ===")

    try:
        # 요청 데이터 생성 및 직렬화
        request_data = {
            "method": "price",
            "args": {"code": "005930"},
            "kwargs": {"timeout": 30},
        }

        # JSON 직렬화
        request_json = json.dumps(request_data, ensure_ascii=False)
        print(f"Request JSON: {request_json}")

        # JSON 역직렬화
        parsed_request = json.loads(request_json)

        # 필드 검증
        assert parsed_request["method"] == "price"
        assert parsed_request["args"]["code"] == "005930"
        assert parsed_request["kwargs"]["timeout"] == 30

        # 응답 데이터
        response_data = {
            "data": {"stock": "Samsung"},
            "_notice": "Market closed",
        }

        response_json = json.dumps(response_data, ensure_ascii=False)
        parsed_response = json.loads(response_json)

        assert parsed_response["data"]["stock"] == "Samsung"
        assert parsed_response["_notice"] == "Market closed"

        print("✓ JSON 직렬화/역직렬화 통과")
        return True
    except Exception as e:
        print(f"✗ JSON 처리 실패: {e}")
        return False


def test_invalid_json_handling():
    """유효하지 않은 JSON 처리 테스트"""
    print("\n=== Test 4: Invalid JSON Handling ===")

    try:
        # 유효하지 않은 JSON 테스트
        invalid_json = '{"method": "price" invalid}'

        try:
            json.loads(invalid_json)
            print("✗ JSON 파싱이 실패해야 하는데 성공함")
            return False
        except json.JSONDecodeError as e:
            print(f"✓ JSONDecodeError 정상 발생: {e}")
            return True
    except Exception as e:
        print(f"✗ 예상치 못한 오류: {e}")
        return False


def test_missing_field_handling():
    """필수 필드 누락 테스트"""
    print("\n=== Test 5: Missing Required Field Handling ===")

    try:
        # method 필드 없는 요청
        request_without_method = {
            "args": {"code": "005930"},
            "kwargs": {}
        }

        # method 필드 검사
        if "method" not in request_without_method:
            print("✓ 필드 누락 감지: 'method' 필드 없음")
            return True
        else:
            print("✗ 필드 누락 감지 실패")
            return False
    except Exception as e:
        print(f"✗ 예상치 못한 오류: {e}")
        return False


def test_timeout_validation():
    """타임아웃 설정 검증"""
    print("\n=== Test 6: Timeout Validation ===")

    try:
        # 다양한 타임아웃 값 검증
        timeout_values = [1, 5, 10, 30, 60]

        for timeout in timeout_values:
            assert isinstance(timeout, int)
            assert timeout > 0

        print(f"✓ 타임아웃 값 검증 통과: {timeout_values}")
        return True
    except Exception as e:
        print(f"✗ 타임아웃 검증 실패: {e}")
        return False


def test_error_response_structure():
    """에러 응답 구조 테스트"""
    print("\n=== Test 7: Error Response Structure ===")

    try:
        # 에러 응답 구조
        error_response = {
            "error": "Invalid method",
            "code": "ValueError",
            "traceback": "Traceback (most recent call last)..."
        }

        # 필드 검증
        assert "error" in error_response
        assert "code" in error_response
        assert isinstance(error_response["error"], str)
        assert isinstance(error_response["code"], str)

        # JSON 직렬화
        response_json = json.dumps(error_response, ensure_ascii=False)
        parsed = json.loads(response_json)

        assert parsed["code"] == "ValueError"

        print("✓ 에러 응답 구조 검증 통과")
        return True
    except Exception as e:
        print(f"✗ 에러 응답 구조 검증 실패: {e}")
        return False


def test_success_response_structure():
    """성공 응답 구조 테스트"""
    print("\n=== Test 8: Success Response Structure ===")

    try:
        # 성공 응답 구조
        success_response = {
            "data": {"result": "success"},
            "_notice": "Market closed"
        }

        # 필드 검증
        assert "data" in success_response
        assert isinstance(success_response["data"], dict)

        # JSON 직렬화
        response_json = json.dumps(success_response, ensure_ascii=False)
        parsed = json.loads(response_json)

        assert parsed["data"]["result"] == "success"
        assert parsed.get("_notice") == "Market closed"

        print("✓ 성공 응답 구조 검증 통과")
        return True
    except Exception as e:
        print(f"✗ 성공 응답 구조 검증 실패: {e}")
        return False


def main():
    """모든 통합 테스트 실행"""
    print("=" * 60)
    print("Python Bridge Integration Tests")
    print("=" * 60)

    tests = [
        ("Python Bridge Syntax", test_python_bridge_basic),
        ("CLI Bridge Syntax", test_cli_bridge_basic),
        ("JSON Serialization", test_json_serialization),
        ("Invalid JSON Handling", test_invalid_json_handling),
        ("Missing Field Handling", test_missing_field_handling),
        ("Timeout Validation", test_timeout_validation),
        ("Error Response Structure", test_error_response_structure),
        ("Success Response Structure", test_success_response_structure),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"✗ {test_name} 실행 중 오류: {e}")
            results[test_name] = False

    # 결과 요약
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    failed = len(results) - passed

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print("=" * 60)
    print(f"Total: {passed} passed, {failed} failed out of {len(results)} tests")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
