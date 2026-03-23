"""
Python Bridge 클래스 - Python 설치 감지 및 프로세스 실행 관리

이 모듈은 kis-agent가 외부 Python 프로세스와 통신할 수 있도록
Python 설치 감지, 버전 확인, 프로세스 실행 기능을 제공합니다.
"""

import logging
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 모듈 레벨 로거
_logger = logging.getLogger(__name__)


class PythonNotFoundError(Exception):
    """Python 설치를 찾을 수 없을 때 발생하는 예외"""

    pass


class PythonBridge:
    """
    Python 프로세스 관리 및 브릿지 클래스

    기능:
    - Python 설치 감지 (python3, python, pythonX.Y)
    - Python 버전 확인 및 검증
    - 외부 Python 스크립트 실행
    - 프로세스 리소스 관리
    """

    # 지원하는 Python 명령어 (우선순위 순서)
    PYTHON_EXECUTABLES = [
        "python3",          # 기본 (권장)
        "python3.11",
        "python3.10",
        "python3.9",
        "python3.8",
        "python",           # 폴백 (Windows 등)
    ]

    def __init__(
        self,
        min_version: Tuple[int, int, int] = (3, 8, 0),
        python_executable: Optional[str] = None,
        raise_on_missing: bool = True,
    ):
        """
        PythonBridge 초기화

        Args:
            min_version: 최소 Python 버전 (기본: 3.8.0)
            python_executable: 특정 Python 실행 경로 (지정하면 자동 감지 스킵)
            raise_on_missing: Python을 찾을 수 없으면 예외 발생 여부

        Raises:
            PythonNotFoundError: Python을 찾을 수 없고 raise_on_missing=True인 경우
        """
        self.min_version = min_version
        self.raise_on_missing = raise_on_missing
        self._python_executable: Optional[str] = None
        self._python_version: Optional[Tuple[int, int, int]] = None
        self._python_path: Optional[Path] = None

        # Python 실행 경로 결정
        if python_executable:
            try:
                self._set_python_executable(python_executable)
            except RuntimeError as e:
                msg = str(e)
                if self.raise_on_missing:
                    raise PythonNotFoundError(msg) from e
                _logger.warning(msg)
        else:
            self._detect_python()

        if self._python_executable is None:
            msg = "Python 설치를 찾을 수 없습니다"
            if self.raise_on_missing:
                raise PythonNotFoundError(msg)
            _logger.warning(msg)

    def _detect_python(self) -> None:
        """
        시스템에서 사용 가능한 Python 실행 파일 감지

        PYTHON_EXECUTABLES 리스트의 우선순위 순서로 탐색합니다.
        찾은 첫 번째 Python을 사용합니다.
        """
        for executable in self.PYTHON_EXECUTABLES:
            path = shutil.which(executable)
            if path:
                _logger.debug(f"Python 감지: {executable} -> {path}")
                try:
                    self._set_python_executable(executable)
                    return
                except RuntimeError as e:
                    _logger.debug(f"{executable} 검증 실패: {e}")
                    continue

        _logger.warning(
            f"사용 가능한 Python을 찾을 수 없습니다. "
            f"시도한 실행 파일: {', '.join(self.PYTHON_EXECUTABLES)}"
        )

    def _set_python_executable(self, executable: str) -> None:
        """
        Python 실행 파일 설정 및 검증

        Args:
            executable: Python 실행 파일 이름 또는 전체 경로

        Raises:
            RuntimeError: Python 버전이 최소 버전보다 낮거나 버전 확인에 실패한 경우
        """
        # 실행 파일 경로 확인
        path = shutil.which(executable)
        if not path:
            raise RuntimeError(f"Python 실행 파일 '{executable}'을(를) 찾을 수 없습니다")

        # Python 버전 확인
        try:
            version = self._get_python_version(path)
        except RuntimeError as e:
            raise RuntimeError(f"Python 버전 확인 실패 ({executable}): {e}") from e

        # 최소 버전 검증
        if version < self.min_version:
            raise RuntimeError(
                f"Python 버전 {version}은(는) 최소 버전 {self.min_version}보다 낮습니다"
            )

        self._python_executable = executable
        self._python_path = Path(path)
        self._python_version = version
        _logger.info(
            f"Python 설정 완료: {self._python_executable} "
            f"(v{version[0]}.{version[1]}.{version[2]}) -> {self._python_path}"
        )

    @staticmethod
    def _get_python_version(python_executable: str) -> Tuple[int, int, int]:
        """
        Python 버전 조회

        Args:
            python_executable: Python 실행 파일 경로

        Returns:
            버전 튜플 (major, minor, micro)

        Raises:
            RuntimeError: Python 버전 조회 실패
        """
        try:
            result = subprocess.run(
                [python_executable, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                raise RuntimeError(f"실행 오류: {result.stderr}")

            # "Python 3.8.0" 형태 파싱
            version_str = result.stdout.strip().split()[-1]
            parts = version_str.split(".")
            if len(parts) < 2:
                raise RuntimeError(f"버전 형식 파싱 실패: {version_str}")

            major = int(parts[0])
            minor = int(parts[1])
            micro = int(parts[2]) if len(parts) > 2 else 0

            return (major, minor, micro)

        except subprocess.TimeoutExpired:
            raise RuntimeError("Python 버전 조회 타임아웃 (5초)")
        except (ValueError, IndexError) as e:
            raise RuntimeError(f"버전 파싱 오류: {e}") from e
        except Exception as e:
            raise RuntimeError(f"예상치 못한 오류: {e}") from e

    @property
    def is_available(self) -> bool:
        """Python이 감지되었는지 여부"""
        return self._python_executable is not None

    @property
    def python_executable(self) -> Optional[str]:
        """감지된 Python 실행 파일 이름"""
        return self._python_executable

    @property
    def python_path(self) -> Optional[Path]:
        """감지된 Python 실행 파일의 절대 경로"""
        return self._python_path

    @property
    def python_version(self) -> Optional[Tuple[int, int, int]]:
        """감지된 Python 버전 (major, minor, micro)"""
        return self._python_version

    @property
    def python_version_string(self) -> Optional[str]:
        """감지된 Python 버전 문자열"""
        if self._python_version:
            major, minor, micro = self._python_version
            return f"{major}.{minor}.{micro}"
        return None

    def get_info(self) -> Dict[str, Optional[str]]:
        """
        Python 감지 정보 조회

        Returns:
            Python 정보를 담은 딕셔너리:
            - is_available: Python 감지 여부
            - executable: 실행 파일 이름
            - path: 절대 경로
            - version: 버전 문자열
        """
        return {
            "is_available": str(self.is_available),
            "executable": self.python_executable or "None",
            "path": str(self.python_path) if self.python_path else "None",
            "version": self.python_version_string or "None",
        }

    def run_script(
        self,
        script_path: str,
        args: Optional[List[str]] = None,
        timeout: int = 30,
        capture_output: bool = False,
    ) -> subprocess.CompletedProcess:
        """
        Python 스크립트 실행 (기초 구현)

        Args:
            script_path: 실행할 Python 스크립트 경로
            args: 스크립트에 전달할 인자 리스트
            timeout: 실행 타임아웃 (초 단위, 기본: 30)
            capture_output: stdout/stderr 캡처 여부

        Returns:
            subprocess.CompletedProcess 객체

        Raises:
            PythonNotFoundError: Python을 찾을 수 없는 경우
            FileNotFoundError: 스크립트 파일이 없는 경우
            subprocess.TimeoutExpired: 타임아웃 발생
        """
        if not self.is_available:
            raise PythonNotFoundError("사용 가능한 Python을 찾을 수 없습니다")

        script = Path(script_path)
        if not script.exists():
            raise FileNotFoundError(f"스크립트 파일을 찾을 수 없습니다: {script_path}")

        # 명령어 구성
        cmd = [self._python_executable, str(script)]
        if args:
            cmd.extend(args)

        _logger.debug(f"스크립트 실행: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                timeout=timeout,
                capture_output=capture_output,
                text=True,
            )
            return result
        except subprocess.TimeoutExpired as e:
            _logger.error(f"스크립트 실행 타임아웃 ({timeout}초): {script_path}")
            raise

    def __repr__(self) -> str:
        """Python Bridge 객체의 문자열 표현"""
        return (
            f"PythonBridge(executable={self.python_executable!r}, "
            f"version={self.python_version_string!r}, "
            f"is_available={self.is_available})"
        )
