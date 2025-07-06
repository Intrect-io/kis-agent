import os
from dataclasses import dataclass
from dotenv import dotenv_values

@dataclass
class KISConfig:
    """API 인증 및 계좌 정보를 관리하는 설정 클래스"""

    APP_KEY: str = ""
    APP_SECRET: str = ""
    BASE_URL: str = ""
    ACCOUNT_NO: str = ""
    ACCOUNT_CODE: str = ""

    def __init__(self, env_path: str = ".env", app_key: str = None, app_secret: str = None, base_url: str = None, account_no: str = None, account_code: str = None):
        """
        설정을 초기화합니다.
        인자가 제공되면 직접 사용하고, 그렇지 않으면 .env 파일에서 로드합니다.
        """
        # 인자가 하나라도 제공되면 직접 설정을 적용
        if any(arg is not None for arg in [app_key, app_secret, base_url, account_no, account_code]):
            self.APP_KEY = app_key or ""
            self.APP_SECRET = app_secret or ""
            self.BASE_URL = base_url or ""
            self.ACCOUNT_NO = account_no or ""
            self.ACCOUNT_CODE = account_code or ""
        else:
            if not os.path.exists(env_path):
                raise FileNotFoundError(
                    f"'{env_path}' 파일을 찾을 수 없습니다. '.env.example' 파일을 복사하여 설정 후 사용하세요."
                )
            
            config = dotenv_values(dotenv_path=env_path)

            self.APP_KEY = config.get("KIS_APP_KEY") or ""
            self.APP_SECRET = config.get("KIS_APP_SECRET") or ""
            self.BASE_URL = config.get("KIS_BASE_URL") or ""
            self.ACCOUNT_NO = config.get("KIS_ACCOUNT_NO") or ""
            self.ACCOUNT_CODE = config.get("KIS_ACCOUNT_CODE") or ""
        
        self._validate()

    @property
    def account_stock(self) -> str:
        """계좌 번호 반환"""
        return self.ACCOUNT_NO

    @property
    def account_product(self) -> str:
        """계좌 상품 코드 반환"""
        return self.ACCOUNT_CODE

    def _validate(self) -> None:
        if not all([self.APP_KEY, self.APP_SECRET, self.BASE_URL, self.ACCOUNT_NO, self.ACCOUNT_CODE]):
            raise ValueError("필수 설정 값이 누락되었습니다. .env 파일의 내용을 확인하세요.")

__all__ = ["KISConfig"]
