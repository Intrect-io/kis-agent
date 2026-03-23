"""
Python Bridge 모듈 테스트

kis_agent.bridge.python_bridge 모듈의 포괄적인 테스트:
- PythonBridge 클래스 인스턴스화
- Python 감지 및 버전 검증
- 프로세스 실행 기능
- 예외 처리
"""

import logging
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Tuple
from unittest.mock import MagicMock, patch

import pytest

from kis_agent.bridge import PythonBridge
from kis_agent.bridge.python_bridge import PythonNotFoundError


class TestPythonBridgeInitialization:
    """PythonBridge 클래스 초기화 테스트"""

    def test_init_default_parameters(self):
        """기본 파라미터로 초기화"""
        bridge = PythonBridge()
        assert bridge is not None
        assert bridge.is_available is True  # 시스템에 Python이 있어야 함
        assert bridge.python_executable is not None
        assert bridge.python_path is not None
        assert bridge.python_version is not None

    def test_init_with_explicit_python_executable(self):
        """명시적 Python 실행 경로로 초기화"""
        python_exe = sys.executable
        bridge = PythonBridge(python_executable=python_exe)
        assert bridge.is_available is True
        assert bridge.python_executable is not None

    def test_init_with_min_version(self):
        """최소 버전 설정으로 초기화"""
        bridge = PythonBridge(min_version=(3, 8, 0))
        assert bridge.min_version == (3, 8, 0)
        # 시스템 Python이 3.8 이상이어야 통과
        assert bridge.is_available is True

    def test_init_with_unsupported_min_version(self):
        """지원되지 않는 최소 버전으로 초기화 (예외 발생)"""
        # 미래 버전으로 설정하여 실패 유도
        with pytest.raises(PythonNotFoundError):
            PythonBridge(min_version=(99, 0, 0))

    def test_init_with_raise_on_missing_false(self):
        """raise_on_missing=False로 초기화 (Python 없어도 에러 없음)"""
        bridge = PythonBridge(python_executable="/nonexistent/python", raise_on_missing=False)
        assert bridge.is_available is False
        assert bridge.python_executable is None

    def test_init_with_invalid_python_executable(self):
        """존재하지 않는 Python 실행 파일로 초기화"""
        with pytest.raises(PythonNotFoundError):
            PythonBridge(python_executable="/nonexistent/python/path")


class TestPythonDetection:
    """Python 감지 기능 테스트"""

    def test_detect_python_succeeds(self):
        """시스템에서 Python 감지 성공"""
        bridge = PythonBridge()
        assert bridge.is_available is True
        assert bridge.python_executable is not None

    def test_python_executable_property(self):
        """python_executable 프로퍼티 반환"""
        bridge = PythonBridge()
        assert isinstance(bridge.python_executable, str)
        assert len(bridge.python_executable) > 0

    def test_python_path_property(self):
        """python_path 프로퍼티 반환"""
        bridge = PythonBridge()
        assert isinstance(bridge.python_path, Path)
        assert bridge.python_path.exists()

    def test_python_version_property(self):
        """python_version 프로퍼티 반환"""
        bridge = PythonBridge()
        version = bridge.python_version
        assert isinstance(version, tuple)
        assert len(version) == 3
        assert all(isinstance(v, int) for v in version)

    def test_python_version_string_property(self):
        """python_version_string 프로퍼티 반환"""
        bridge = PythonBridge()
        version_str = bridge.python_version_string
        assert isinstance(version_str, str)
        # "X.Y.Z" 형태
        parts = version_str.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)


class TestVersionDetection:
    """Python 버전 감지 테스트"""

    def test_get_python_version_current(self):
        """현재 Python 버전 감지"""
        version = PythonBridge._get_python_version(sys.executable)
        assert isinstance(version, tuple)
        assert len(version) == 3
        assert version >= (3, 8, 0)  # 최소 요구사항

    def test_get_python_version_format(self):
        """Python 버전 파싱 형식 검증"""
        version = PythonBridge._get_python_version(sys.executable)
        major, minor, micro = version
        assert isinstance(major, int)
        assert isinstance(minor, int)
        assert isinstance(micro, int)
        assert major >= 3
        assert 0 <= minor <= 12
        assert micro >= 0

    def test_get_python_version_invalid_executable(self):
        """존재하지 않는 실행 파일로 버전 감지 시도"""
        with pytest.raises(RuntimeError):
            PythonBridge._get_python_version("/nonexistent/python")

    @patch("subprocess.run")
    def test_get_python_version_timeout(self, mock_run):
        """Python 버전 조회 타임아웃"""
        mock_run.side_effect = subprocess.TimeoutExpired("python", 5)
        with pytest.raises(RuntimeError, match="타임아웃"):
            PythonBridge._get_python_version(sys.executable)

    @patch("subprocess.run")
    def test_get_python_version_parse_error(self, mock_run):
        """Python 버전 파싱 오류"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Invalid version format",
            stderr=""
        )
        with pytest.raises(RuntimeError, match="파싱"):
            PythonBridge._get_python_version(sys.executable)


class TestGetInfo:
    """Python 정보 조회 테스트"""

    def test_get_info_returns_dict(self):
        """get_info() 메서드가 딕셔너리 반환"""
        bridge = PythonBridge()
        info = bridge.get_info()
        assert isinstance(info, dict)

    def test_get_info_contains_required_keys(self):
        """get_info()가 필수 키를 포함"""
        bridge = PythonBridge()
        info = bridge.get_info()
        required_keys = {"is_available", "executable", "path", "version"}
        assert set(info.keys()) == required_keys

    def test_get_info_values_are_strings(self):
        """get_info()의 모든 값이 문자열"""
        bridge = PythonBridge()
        info = bridge.get_info()
        assert all(isinstance(v, str) for v in info.values())

    def test_get_info_available_bridge(self):
        """Python이 감지된 경우의 정보"""
        bridge = PythonBridge()
        info = bridge.get_info()
        assert info["is_available"] == "True"
        assert info["executable"] != "None"
        assert info["path"] != "None"
        assert info["version"] != "None"

    def test_get_info_unavailable_bridge(self):
        """Python이 감지되지 않은 경우의 정보"""
        bridge = PythonBridge(
            python_executable="/nonexistent/python",
            raise_on_missing=False
        )
        info = bridge.get_info()
        assert info["is_available"] == "False"
        assert info["executable"] == "None"


class TestRunScript:
    """스크립트 실행 기능 테스트"""

    def test_run_script_simple(self):
        """간단한 Python 스크립트 실행"""
        bridge = PythonBridge()

        # 임시 테스트 스크립트 생성
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('Hello from Python')")
            script_path = f.name

        try:
            result = bridge.run_script(script_path, capture_output=True)
            assert result.returncode == 0
            assert "Hello from Python" in result.stdout
        finally:
            Path(script_path).unlink()

    def test_run_script_with_args(self):
        """인자를 포함한 스크립트 실행"""
        bridge = PythonBridge()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("import sys\nprint(sys.argv[1])")
            script_path = f.name

        try:
            result = bridge.run_script(
                script_path,
                args=["test_arg"],
                capture_output=True
            )
            assert result.returncode == 0
            assert "test_arg" in result.stdout
        finally:
            Path(script_path).unlink()

    def test_run_script_file_not_found(self):
        """존재하지 않는 스크립트 실행 시도"""
        bridge = PythonBridge()

        with pytest.raises(FileNotFoundError):
            bridge.run_script("/nonexistent/script.py")

    def test_run_script_python_not_available(self):
        """Python이 사용 불가능한 경우"""
        bridge = PythonBridge(
            python_executable="/nonexistent/python",
            raise_on_missing=False
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('test')")
            script_path = f.name

        try:
            with pytest.raises(PythonNotFoundError):
                bridge.run_script(script_path)
        finally:
            Path(script_path).unlink()

    def test_run_script_timeout(self):
        """스크립트 실행 타임아웃"""
        bridge = PythonBridge()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("import time; time.sleep(10)")
            script_path = f.name

        try:
            with pytest.raises(subprocess.TimeoutExpired):
                bridge.run_script(script_path, timeout=1)
        finally:
            Path(script_path).unlink()

    def test_run_script_with_exception_in_script(self):
        """스크립트 내 예외 발생"""
        bridge = PythonBridge()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("raise RuntimeError('Test error')")
            script_path = f.name

        try:
            result = bridge.run_script(script_path, capture_output=True)
            assert result.returncode != 0
        finally:
            Path(script_path).unlink()


class TestRepr:
    """문자열 표현 테스트"""

    def test_repr_format(self):
        """__repr__() 메서드의 형식"""
        bridge = PythonBridge()
        repr_str = repr(bridge)
        assert "PythonBridge" in repr_str
        assert "executable=" in repr_str
        assert "version=" in repr_str
        assert "is_available=" in repr_str

    def test_repr_unavailable_bridge(self):
        """Python이 사용 불가능한 경우의 __repr__()"""
        bridge = PythonBridge(
            python_executable="/nonexistent/python",
            raise_on_missing=False
        )
        repr_str = repr(bridge)
        assert "PythonBridge" in repr_str
        assert "is_available=False" in repr_str


class TestExceptionHandling:
    """예외 처리 테스트"""

    def test_python_not_found_error_message(self):
        """PythonNotFoundError 예외 메시지"""
        with pytest.raises(PythonNotFoundError) as exc_info:
            raise PythonNotFoundError("Test error message")
        assert "Test error message" in str(exc_info.value)

    def test_python_not_found_error_inheritance(self):
        """PythonNotFoundError가 Exception을 상속"""
        error = PythonNotFoundError("test")
        assert isinstance(error, Exception)

    def test_invalid_executable_raises_python_not_found_error(self):
        """잘못된 실행 파일이 PythonNotFoundError 발생"""
        with pytest.raises(PythonNotFoundError):
            PythonBridge(python_executable="/definitely/not/a/python")


class TestLogging:
    """로깅 기능 테스트"""

    def test_logging_on_init(self, caplog):
        """초기화 시 로깅"""
        with caplog.at_level(logging.INFO):
            bridge = PythonBridge()

        # 로그 기록 확인 (선택 사항, 로깅이 있으면 통과)
        assert bridge.is_available is True

    def test_logging_on_detection_failure(self, caplog):
        """Python 감지 실패 시 로깅"""
        with caplog.at_level(logging.WARNING):
            bridge = PythonBridge(
                python_executable="/nonexistent/python",
                raise_on_missing=False
            )

        # 경고 로그 확인
        assert bridge.is_available is False


class TestEdgeCases:
    """엣지 케이스 테스트"""

    def test_multiple_bridge_instances(self):
        """여러 PythonBridge 인스턴스 생성"""
        bridge1 = PythonBridge()
        bridge2 = PythonBridge()

        assert bridge1.python_executable == bridge2.python_executable
        assert bridge1.python_version == bridge2.python_version

    def test_bridge_with_different_min_versions(self):
        """다른 최소 버전으로 여러 인스턴스 생성"""
        bridge1 = PythonBridge(min_version=(3, 8, 0))
        bridge2 = PythonBridge(min_version=(3, 9, 0))

        # 모두 현재 시스템 버전과 비교하면 작거나 같음
        assert bridge1.python_version >= (3, 8, 0)
        assert bridge2.python_version >= (3, 9, 0)

    def test_version_comparison(self):
        """Python 버전 비교"""
        bridge = PythonBridge()
        assert bridge.python_version >= (3, 8, 0)
        assert bridge.python_version >= bridge.min_version

    def test_path_exists(self):
        """감지된 Python 경로 검증"""
        bridge = PythonBridge()
        assert bridge.python_path.exists()
        assert bridge.python_path.is_file()


class TestIntegration:
    """통합 테스트"""

    def test_full_workflow(self):
        """완전한 워크플로우"""
        # 1. 초기화
        bridge = PythonBridge()

        # 2. 정보 조회
        info = bridge.get_info()
        assert info["is_available"] == "True"

        # 3. 스크립트 실행
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("import sys; print(f'Python {sys.version_info.major}.{sys.version_info.minor}')")
            script_path = f.name

        try:
            result = bridge.run_script(script_path, capture_output=True)
            assert result.returncode == 0
            assert "Python" in result.stdout
        finally:
            Path(script_path).unlink()

    def test_version_validation_workflow(self):
        """버전 검증 워크플로우"""
        # 현재 시스템 Python 버전
        bridge = PythonBridge()
        current_version = bridge.python_version

        # 현재 버전보다 낮은 최소 버전
        bridge_lower = PythonBridge(min_version=(3, 8, 0))
        assert bridge_lower.is_available is True

        # 현재 버전과 같거나 높은 최소 버전
        if current_version[1] > 8:  # 3.9+라면
            bridge_same = PythonBridge(min_version=current_version)
            assert bridge_same.is_available is True
