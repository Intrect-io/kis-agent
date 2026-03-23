"""
Bridge stdin/stdout 통신 파이프라인

stdin에서 JSON 메시지를 읽고, stdout으로 JSON 응답을 송신합니다.
라인 기반 파싱, 버퍼링 처리, 직렬화를 제공합니다.
"""

import sys
import json
import logging
from typing import Any, Dict, Optional, Callable
from io import TextIOBase

from kis_agent.bridge_protocol import (
    BridgeRequest,
    BridgeResponse,
    BridgeErrorCode,
    BridgeProtocolValidator,
)

logger = logging.getLogger(__name__)


class BridgeStdioReader:
    """stdin에서 JSON 메시지를 읽는 리더"""

    def __init__(self, stdin: Optional[TextIOBase] = None):
        """
        초기화

        Args:
            stdin: 입력 스트림 (기본값: sys.stdin)
        """
        self.stdin = stdin or sys.stdin
        self._line_buffer = ""

    def read_json_line(self) -> Optional[str]:
        """
        stdin에서 한 줄을 읽음 (블로킹)

        Returns:
            JSON 문자열, 또는 EOF인 경우 None
        """
        try:
            line = self.stdin.readline()
            if not line:
                return None
            return line.rstrip("\n\r")
        except (IOError, OSError) as e:
            logger.error(f"Failed to read from stdin: {e}")
            return None

    def read_request(self) -> Optional[BridgeRequest]:
        """
        stdin에서 BridgeRequest를 읽음

        Returns:
            BridgeRequest 인스턴스, 또는 읽기 실패 시 None
        """
        json_line = self.read_json_line()
        if json_line is None:
            return None

        try:
            data = json.loads(json_line)
            is_valid, error_msg = BridgeProtocolValidator.validate_request(data)
            if not is_valid:
                logger.error(f"Invalid request: {error_msg}")
                return None

            request = BridgeRequest.from_dict(data)
            return request
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to create BridgeRequest: {e}")
            return None


class BridgeStdioWriter:
    """stdout으로 JSON 메시지를 송신하는 라이터"""

    def __init__(self, stdout: Optional[TextIOBase] = None):
        """
        초기화

        Args:
            stdout: 출력 스트림 (기본값: sys.stdout)
        """
        self.stdout = stdout or sys.stdout

    def write_json_line(self, obj: Any) -> bool:
        """
        stdout에 JSON을 한 줄로 송신 (라인 기반)

        Args:
            obj: JSON 직렬화 가능한 객체

        Returns:
            성공 여부
        """
        try:
            json_str = json.dumps(obj, ensure_ascii=False)
            self.stdout.write(json_str + "\n")
            self.stdout.flush()
            return True
        except (IOError, OSError) as e:
            logger.error(f"Failed to write to stdout: {e}")
            return False
        except TypeError as e:
            logger.error(f"Failed to serialize to JSON: {e}")
            return False

    def write_response(self, response: BridgeResponse) -> bool:
        """
        stdout에 BridgeResponse를 송신

        Args:
            response: BridgeResponse 인스턴스

        Returns:
            성공 여부
        """
        try:
            is_valid, error_msg = BridgeProtocolValidator.validate_response(
                response.to_dict()
            )
            if not is_valid:
                logger.error(f"Invalid response: {error_msg}")
                return False

            return self.write_json_line(response.to_dict())
        except Exception as e:
            logger.error(f"Failed to write response: {e}")
            return False

    def write_success(self, request_id: str, result: Any) -> bool:
        """
        stdout에 성공 응답을 송신

        Args:
            request_id: 요청 ID
            result: 결과 데이터

        Returns:
            성공 여부
        """
        response = BridgeResponse.success(request_id=request_id, result=result)
        return self.write_response(response)

    def write_error(
        self,
        request_id: str,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        stdout에 에러 응답을 송신

        Args:
            request_id: 요청 ID
            code: 에러 코드
            message: 에러 메시지
            details: 추가 상세 정보

        Returns:
            성공 여부
        """
        response = BridgeResponse.error(
            request_id=request_id,
            code=code,
            message=message,
            details=details,
        )
        return self.write_response(response)


class BridgeCommunicationPipeline:
    """stdin/stdout 양방향 통신 파이프라인"""

    def __init__(
        self,
        stdin: Optional[TextIOBase] = None,
        stdout: Optional[TextIOBase] = None,
    ):
        """
        초기화

        Args:
            stdin: 입력 스트림 (기본값: sys.stdin)
            stdout: 출력 스트림 (기본값: sys.stdout)
        """
        self.reader = BridgeStdioReader(stdin)
        self.writer = BridgeStdioWriter(stdout)

    def run(self, handler: Callable[[BridgeRequest], BridgeResponse]) -> None:
        """
        메인 루프: stdin에서 읽고 처리하고 stdout으로 응답 송신

        Args:
            handler: 요청을 처리하고 응답을 반환하는 핸들러 함수
                     Callable[[BridgeRequest], BridgeResponse]
        """
        while True:
            request = self.reader.read_request()
            if request is None:
                logger.info("stdin closed or EOF reached")
                break

            try:
                response = handler(request)
                self.writer.write_response(response)
            except Exception as e:
                logger.error(f"Unhandled exception in handler: {e}")
                error_response = BridgeResponse.error(
                    request_id=request.id,
                    code=BridgeErrorCode.INTERNAL_ERROR,
                    message=str(e),
                )
                self.writer.write_response(error_response)

    def send_request(self, request: BridgeRequest) -> bool:
        """
        요청을 stdout에 송신 (디버깅/테스트용)

        Args:
            request: BridgeRequest 인스턴스

        Returns:
            성공 여부
        """
        return self.writer.write_json_line(request.to_dict())

    def read_response(self) -> Optional[BridgeResponse]:
        """
        stdin에서 응답을 읽음 (디버깅/테스트용)

        Returns:
            BridgeResponse 인스턴스, 또는 읽기 실패 시 None
        """
        json_line = self.reader.read_json_line()
        if json_line is None:
            return None

        try:
            data = json.loads(json_line)
            is_valid, error_msg = BridgeProtocolValidator.validate_response(data)
            if not is_valid:
                logger.error(f"Invalid response: {error_msg}")
                return None

            response = BridgeResponse.from_dict(data)
            return response
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to create BridgeResponse: {e}")
            return None


if __name__ == "__main__":
    # 간단한 echo 테스트: 요청을 받으면 그대로 응답
    def echo_handler(request: BridgeRequest) -> BridgeResponse:
        """테스트용 echo 핸들러"""
        return BridgeResponse.success(
            request_id=request.id,
            result={"method": request.method, "args": request.args, "kwargs": request.kwargs},
        )

    pipeline = BridgeCommunicationPipeline()
    pipeline.run(echo_handler)
