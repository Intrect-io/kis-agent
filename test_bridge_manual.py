#!/usr/bin/env python3
"""
Bridge stdio 수동 테스트
"""

import sys
import json
from io import StringIO

# 직접 임포트 (패키지 임포트 문제 우회)
sys.path.append('.')

# bridge_protocol과 bridge_stdio를 직접 로드
from kis_agent.bridge_protocol import (
    BridgeRequest,
    BridgeResponse,
    BridgeProtocolValidator,
    BridgeErrorCode
)

from kis_agent.bridge_stdio import (
    BridgeStdioReader,
    BridgeStdioWriter,
    BridgeCommunicationPipeline
)

def test_basic_functionality():
    print("=== Bridge stdio 기본 기능 테스트 ===")

    # 1. JSON 라인 읽기 테스트
    request_data = {
        "id": "test-123",
        "method": "price",
        "args": ["005930"],
        "kwargs": {"daily": True}
    }
    request_json = json.dumps(request_data)

    stdin = StringIO(request_json + "\n")
    reader = BridgeStdioReader(stdin)

    request = reader.read_request()
    if request:
        print(f"✓ JSON 읽기 성공: {request.method}({request.args}) - ID: {request.id}")
    else:
        print("✗ JSON 읽기 실패")
        return False

    # 2. JSON 라인 쓰기 테스트
    stdout = StringIO()
    writer = BridgeStdioWriter(stdout)

    response = BridgeResponse.success(
        request_id=request.id,
        result={"price": 70000, "currency": "KRW"}
    )

    success = writer.write_response(response)
    if success:
        output = stdout.getvalue()
        response_data = json.loads(output.strip())
        print(f"✓ JSON 쓰기 성공: ID={response_data['id']}, result={response_data['result']}")
    else:
        print("✗ JSON 쓰기 실패")
        return False

    # 3. 에러 응답 테스트
    stdout2 = StringIO()
    writer2 = BridgeStdioWriter(stdout2)

    error_response = BridgeResponse.error(
        request_id=request.id,
        code=BridgeErrorCode.INVALID_PARAMS,
        message="Invalid stock code",
        details={"code": "005930", "reason": "Not found"}
    )

    success = writer2.write_response(error_response)
    if success:
        output = stdout2.getvalue()
        response_data = json.loads(output.strip())
        print(f"✓ 에러 응답 성공: code={response_data['error']['code']}")
    else:
        print("✗ 에러 응답 실패")
        return False

    return True

def test_pipeline():
    print("\n=== 파이프라인 통신 테스트 ===")

    # 요청 데이터
    requests = [
        {"id": "req-1", "method": "get_balance", "args": [], "kwargs": {}},
        {"id": "req-2", "method": "get_price", "args": ["005930"], "kwargs": {}},
        {"id": "req-3", "method": "invalid_method", "args": [], "kwargs": {}}
    ]

    stdin_content = "\n".join(json.dumps(req) for req in requests) + "\n"
    stdin = StringIO(stdin_content)
    stdout = StringIO()

    def handler(request: BridgeRequest) -> BridgeResponse:
        """테스트용 핸들러"""
        if request.method == "get_balance":
            return BridgeResponse.success(
                request_id=request.id,
                result={"balance": 1000000, "currency": "KRW"}
            )
        elif request.method == "get_price":
            stock_code = request.args[0] if request.args else "Unknown"
            return BridgeResponse.success(
                request_id=request.id,
                result={"code": stock_code, "price": 70000}
            )
        else:
            return BridgeResponse.error(
                request_id=request.id,
                code=BridgeErrorCode.METHOD_NOT_FOUND,
                message=f"Method '{request.method}' not found"
            )

    # 파이프라인 실행
    pipeline = BridgeCommunicationPipeline(stdin, stdout)
    pipeline.run(handler)

    # 결과 검증
    outputs = stdout.getvalue().strip().split("\n")
    print(f"✓ 처리된 응답 개수: {len(outputs)}")

    for i, output in enumerate(outputs):
        response_data = json.loads(output)
        request_id = response_data["id"]

        if response_data.get("error"):
            print(f"  {i+1}. {request_id}: ERROR - {response_data['error']['code']}")
        else:
            result = response_data.get("result", {})
            print(f"  {i+1}. {request_id}: SUCCESS - {result}")

    return len(outputs) == 3

def test_korean_text():
    print("\n=== 한글 텍스트 처리 테스트 ===")

    request_data = {
        "id": "kr-001",
        "method": "search_stock",
        "args": ["삼성전자"],
        "kwargs": {"market": "코스피"}
    }

    stdin = StringIO(json.dumps(request_data, ensure_ascii=False) + "\n")
    stdout = StringIO()

    def kr_handler(request: BridgeRequest) -> BridgeResponse:
        stock_name = request.args[0] if request.args else "Unknown"
        market = request.kwargs.get("market", "Unknown")

        return BridgeResponse.success(
            request_id=request.id,
            result={
                "name": stock_name,
                "market": market,
                "code": "005930",
                "full_name": f"{stock_name} (코스피)"
            }
        )

    pipeline = BridgeCommunicationPipeline(stdin, stdout)
    pipeline.run(kr_handler)

    output = stdout.getvalue()
    response_data = json.loads(output.strip())

    if response_data["result"]["name"] == "삼성전자":
        print(f"✓ 한글 처리 성공: {response_data['result']}")
        return True
    else:
        print("✗ 한글 처리 실패")
        return False

if __name__ == "__main__":
    print("Bridge stdin/stdout 통신 파이프라인 검증\n")

    success = True

    try:
        success &= test_basic_functionality()
        success &= test_pipeline()
        success &= test_korean_text()

        print(f"\n=== 검증 결과 ===")
        if success:
            print("✓ 모든 테스트 통과! Bridge stdin/stdout 통신 파이프라인이 정상 작동합니다.")
        else:
            print("✗ 일부 테스트 실패!")

    except Exception as e:
        print(f"✗ 테스트 중 예외 발생: {e}")
        import traceback
        traceback.print_exc()
        success = False

    sys.exit(0 if success else 1)