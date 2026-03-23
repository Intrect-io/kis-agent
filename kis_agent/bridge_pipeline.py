"""
Bridge 통신 파이프라인

stdin으로 JSON 메시지를 수신하고, stdout으로 응답을 전송합니다.
메시지는 줄바꿈 기반으로 구분됩니다.

사용 예:
    pipeline = BridgeMessagePipeline()
    while True:
        request = pipeline.receive_message()
        if request is None:
            break
        response = process(request)
        pipeline.send_message(response)
"""

import sys
import json
import logging
from typing import Optional, Dict, Any
from kis_agent.bridge_protocol import BridgeRequest, BridgeResponse, BridgeProtocolValidator


logger = logging.getLogger(__name__)


class MessageReadError(Exception):
    """메시지 읽기 실패 예외"""
    pass


class MessageWriteError(Exception):
    """메시지 쓰기 실패 예외"""
    pass


class BridgeMessagePipeline:
    """
    Bridge JSON 메시지 통신 파이프라인

    stdin/stdout을 통해 JSON 메시지를 주고받습니다.
    메시지는 줄바꿈(\n)으로 구분되며, 각 메시지는 유효한 JSON이어야 합니다.
    """

    def __init__(self, debug: bool = False):
        """
        파이프라인 초기화

        Args:
            debug: 디버그 모드 활성화 여부
        """
        self.debug = debug
        if debug:
            logging.basicConfig(level=logging.DEBUG)

    def receive_message(self) -> Optional[BridgeRequest]:
        """
        stdin에서 JSON 메시지를 한 줄 읽어서 BridgeRequest로 변환

        메시지 형식: {"id": "...", "method": "...", "args": [...], "kwargs": {...}}

        Returns:
            BridgeRequest 인스턴스 또는 EOF인 경우 None

        Raises:
            MessageReadError: JSON 파싱 실패 또는 유효성 검증 실패
        """
        try:
            line = sys.stdin.readline()

            # EOF 처리
            if not line:
                return None

            # 줄바꿈 제거
            line = line.rstrip('\n\r')

            if not line:
                return None

            if self.debug:
                logger.debug(f"Received raw message: {line}")

            # JSON 파싱
            try:
                data = json.loads(line)
            except json.JSONDecodeError as e:
                raise MessageReadError(f"JSON 파싱 실패: {e}")

            # 프로토콜 검증
            is_valid, error_msg = BridgeProtocolValidator.validate_request(data)
            if not is_valid:
                raise MessageReadError(f"요청 검증 실패: {error_msg}")

            # BridgeRequest 생성
            request = BridgeRequest.from_dict(data)

            if self.debug:
                logger.debug(f"Parsed request: id={request.id}, method={request.method}")

            return request

        except (IOError, OSError) as e:
            raise MessageReadError(f"stdin 읽기 실패: {e}")

    def send_message(self, response: BridgeResponse) -> None:
        """
        stdout으로 BridgeResponse를 JSON 메시지로 전송

        메시지는 줄바꿈으로 끝납니다.

        Args:
            response: 전송할 BridgeResponse 인스턴스

        Raises:
            MessageWriteError: JSON 직렬화 실패 또는 쓰기 실패
        """
        try:
            # 프로토콜 검증
            is_valid, error_msg = BridgeProtocolValidator.validate_response(response.to_dict())
            if not is_valid:
                raise MessageWriteError(f"응답 검증 실패: {error_msg}")

            # JSON 직렬화
            message = response.to_json()

            if self.debug:
                logger.debug(f"Sending response: {message}")

            # stdout으로 전송 (줄바꿈 포함)
            print(message, flush=True)

        except (IOError, OSError) as e:
            raise MessageWriteError(f"stdout 쓰기 실패: {e}")

    def send_request(self, request: BridgeRequest) -> None:
        """
        stdout으로 BridgeRequest를 JSON 메시지로 전송

        메시지는 줄바꿈으로 끝납니다.

        Args:
            request: 전송할 BridgeRequest 인스턴스

        Raises:
            MessageWriteError: JSON 직렬화 실패 또는 쓰기 실패
        """
        try:
            # 프로토콜 검증
            is_valid, error_msg = BridgeProtocolValidator.validate_request(request.to_dict())
            if not is_valid:
                raise MessageWriteError(f"요청 검증 실패: {error_msg}")

            # JSON 직렬화
            message = request.to_json()

            if self.debug:
                logger.debug(f"Sending request: {message}")

            # stdout으로 전송 (줄바꿈 포함)
            print(message, flush=True)

        except (IOError, OSError) as e:
            raise MessageWriteError(f"stdout 쓰기 실패: {e}")


def demo_pipeline():
    """파이프라인 데모

    stdin에서 요청을 받아서 stdout으로 응답을 보냅니다.
    간단한 에코 서버처럼 동작합니다.
    """
    pipeline = BridgeMessagePipeline(debug=True)

    try:
        while True:
            # 요청 수신
            request = pipeline.receive_message()
            if request is None:
                break

            print(f"Received request: {request.method}({request.args}, {request.kwargs})", file=sys.stderr)

            # 간단한 에코 응답
            if request.method == "echo":
                result = {
                    "method": request.method,
                    "args": request.args,
                    "kwargs": request.kwargs,
                }
                response = BridgeResponse.success(request.id, result)
            elif request.method == "error":
                response = BridgeResponse.error(
                    request.id,
                    "INVALID_PARAMS",
                    "Test error message",
                    details={"test": "details"}
                )
            else:
                response = BridgeResponse.error(
                    request.id,
                    "METHOD_NOT_FOUND",
                    f"Unknown method: {request.method}"
                )

            # 응답 전송
            pipeline.send_message(response)

    except MessageReadError as e:
        print(f"Message read error: {e}", file=sys.stderr)
        sys.exit(1)
    except MessageWriteError as e:
        print(f"Message write error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    demo_pipeline()
