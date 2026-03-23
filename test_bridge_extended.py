#!/usr/bin/env python3
"""
Bridge stdio 확장 테스트 (패키지 임포트 문제 우회)
"""

import sys
import json
import importlib.util
from io import StringIO
import os

# 직접 모듈 로드
def load_module_from_path(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# bridge_protocol 모듈 로드
protocol_path = os.path.join(os.getcwd(), 'kis_agent', 'bridge_protocol.py')
protocol_module = load_module_from_path('bridge_protocol', protocol_path)

# bridge_stdio 모듈 로드
stdio_path = os.path.join(os.getcwd(), 'kis_agent', 'bridge_stdio.py')

# bridge_stdio 내용을 수정해서 로드
with open(stdio_path, 'r') as f:
    stdio_code = f.read()

# 임포트 문제를 우회하기 위해 내용 수정
stdio_code = stdio_code.replace(
    'from kis_agent.bridge_protocol import',
    'from __main__ import'
)

# 필요한 클래스들을 전역에 추가
BridgeRequest = protocol_module.BridgeRequest
BridgeResponse = protocol_module.BridgeResponse
BridgeErrorCode = protocol_module.BridgeErrorCode
BridgeProtocolValidator = protocol_module.BridgeProtocolValidator

# stdio 모듈 실행
exec(stdio_code)

def test_comprehensive():
    print("=== Bridge stdio 종합 테스트 ===")

    # 1. Reader 테스트
    print("\n1. Reader 테스트")

    # 유효한 요청
    valid_request = {
        "id": "test-001",
        "method": "get_price",
        "args": ["005930"],
        "kwargs": {"period": "1d"}
    }

    stdin = StringIO(json.dumps(valid_request) + "\n")
    reader = BridgeStdioReader(stdin)
    request = reader.read_request()

    if request and request.method == "get_price":
        print("✓ 유효한 요청 읽기 성공")
    else:
        print("✗ 유효한 요청 읽기 실패")
        return False

    # 잘못된 JSON
    stdin_bad = StringIO("invalid json\n")
    reader_bad = BridgeStdioReader(stdin_bad)
    bad_request = reader_bad.read_request()

    if bad_request is None:
        print("✓ 잘못된 JSON 적절히 처리")
    else:
        print("✗ 잘못된 JSON 처리 실패")
        return False

    # EOF 테스트
    stdin_eof = StringIO("")
    reader_eof = BridgeStdioReader(stdin_eof)
    eof_request = reader_eof.read_request()

    if eof_request is None:
        print("✓ EOF 적절히 처리")
    else:
        print("✗ EOF 처리 실패")
        return False

    # 2. Writer 테스트
    print("\n2. Writer 테스트")

    stdout = StringIO()
    writer = BridgeStdioWriter(stdout)

    # 성공 응답
    success_resp = BridgeResponse.success(
        request_id="test-001",
        result={"price": 75000, "volume": 1000000}
    )

    if writer.write_response(success_resp):
        output = stdout.getvalue()
        response_data = json.loads(output.strip())
        if response_data["result"]["price"] == 75000:
            print("✓ 성공 응답 쓰기 성공")
        else:
            print("✗ 성공 응답 내용 불일치")
            return False
    else:
        print("✗ 성공 응답 쓰기 실패")
        return False

    # 에러 응답
    stdout2 = StringIO()
    writer2 = BridgeStdioWriter(stdout2)

    error_resp = BridgeResponse.error(
        request_id="test-002",
        code="METHOD_NOT_FOUND",
        message="Unknown method",
        details={"requested_method": "unknown"}
    )

    if writer2.write_response(error_resp):
        output = stdout2.getvalue()
        response_data = json.loads(output.strip())
        if response_data["error"]["code"] == "METHOD_NOT_FOUND":
            print("✓ 에러 응답 쓰기 성공")
        else:
            print("✗ 에러 응답 내용 불일치")
            return False
    else:
        print("✗ 에러 응답 쓰기 실패")
        return False

    # 3. 파이프라인 테스트
    print("\n3. 파이프라인 테스트")

    requests = [
        {"id": "p1", "method": "balance", "args": [], "kwargs": {}},
        {"id": "p2", "method": "price", "args": ["005930"], "kwargs": {}},
        {"id": "p3", "method": "order", "args": ["005930", 10], "kwargs": {"side": "buy"}},
    ]

    stdin_content = "\n".join(json.dumps(req) for req in requests) + "\n"
    stdin_pipeline = StringIO(stdin_content)
    stdout_pipeline = StringIO()

    def test_handler(request):
        handlers = {
            "balance": lambda r: BridgeResponse.success(r.id, {"cash": 1000000, "stocks": {}}),
            "price": lambda r: BridgeResponse.success(r.id, {"code": r.args[0], "price": 75000}),
            "order": lambda r: BridgeResponse.success(r.id, {"order_id": "ORD001", "status": "submitted"})
        }

        handler = handlers.get(request.method)
        if handler:
            return handler(request)
        else:
            return BridgeResponse.error(
                request.id,
                "METHOD_NOT_FOUND",
                f"Method {request.method} not found"
            )

    pipeline = BridgeCommunicationPipeline(stdin_pipeline, stdout_pipeline)
    pipeline.run(test_handler)

    outputs = stdout_pipeline.getvalue().strip().split("\n")
    if len(outputs) == 3:
        print("✓ 파이프라인 다중 요청 처리 성공")

        # 각 응답 검증
        for i, output in enumerate(outputs):
            response_data = json.loads(output)
            expected_id = f"p{i+1}"
            if response_data["id"] == expected_id:
                print(f"  - 응답 {i+1}: ID 일치 ✓")
            else:
                print(f"  - 응답 {i+1}: ID 불일치 ✗")
                return False
    else:
        print(f"✗ 파이프라인 출력 개수 불일치: {len(outputs)} != 3")
        return False

    # 4. 한글 처리 테스트
    print("\n4. 한글 처리 테스트")

    korean_request = {
        "id": "korean-001",
        "method": "search_stock",  # 메서드명은 영문으로
        "args": ["삼성전자"],
        "kwargs": {"시장": "코스피"}
    }

    stdin_kr = StringIO(json.dumps(korean_request, ensure_ascii=False) + "\n")
    stdout_kr = StringIO()

    def korean_handler(request):
        return BridgeResponse.success(
            request.id,
            {
                "종목명": request.args[0] if request.args else None,
                "시장": request.kwargs.get("시장"),
                "코드": "005930",
                "가격": 75000
            }
        )

    pipeline_kr = BridgeCommunicationPipeline(stdin_kr, stdout_kr)
    pipeline_kr.run(korean_handler)

    output_kr = stdout_kr.getvalue().strip()
    if output_kr:
        response_kr = json.loads(output_kr)
        if response_kr["result"]["종목명"] == "삼성전자":
            print("✓ 한글 텍스트 처리 성공")
        else:
            print("✗ 한글 텍스트 처리 실패")
            return False
    else:
        print("✗ 한글 처리 테스트에서 출력 없음")
        return False

    return True

if __name__ == "__main__":
    print("Bridge stdin/stdout 통신 파이프라인 확장 검증\n")

    try:
        success = test_comprehensive()

        print(f"\n=== 최종 검증 결과 ===")
        if success:
            print("✅ 모든 테스트 통과!")
            print("Bridge stdin/stdout 통신 파이프라인이 완전히 구현되었습니다.")
            print("\n구현된 기능:")
            print("- stdin에서 JSON 메시지 읽기 (라인 기반)")
            print("- stdout으로 JSON 응답 송신")
            print("- 메시지 유효성 검증")
            print("- 에러 처리 및 응답")
            print("- 양방향 통신 파이프라인")
            print("- 한글 텍스트 지원")
            print("- 다중 요청 순차 처리")
        else:
            print("❌ 일부 테스트 실패!")

    except Exception as e:
        print(f"❌ 테스트 중 예외 발생: {e}")
        import traceback
        traceback.print_exc()
        success = False

    sys.exit(0 if success else 1)