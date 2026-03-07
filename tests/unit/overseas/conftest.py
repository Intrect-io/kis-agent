"""
해외주식 API 테스트 설정 모듈

overseas API 전용 fixture 및 mock 설정을 제공합니다.
"""

from unittest.mock import MagicMock, Mock

import pytest

from kis_agent.core.client import KISClient
from kis_agent.core.config import KISConfig


@pytest.fixture
def mock_client():
    """
    해외주식 API 테스트용 Mock KISClient

    Returns:
        Mock: KISClient의 mock 객체
    """
    client = Mock(spec=KISClient)

    # 기본 속성 설정
    client.headers = {
        "authorization": "mock_token",
        "appkey": "mock_appkey",
        "appsecret": "mock_appsecret",
    }
    client.domain = "https://openapi.koreainvestment.com:9443"

    return client


@pytest.fixture
def account_info():
    """
    테스트용 계좌 정보

    Returns:
        dict: 계좌 정보 딕셔너리
    """
    return {
        "CANO": "12345678",  # 계좌번호
        "ACNT_PRDT_CD": "01",  # 계좌상품코드
    }


@pytest.fixture
def overseas_exchange_codes():
    """
    지원하는 해외거래소 코드

    Returns:
        dict: 거래소 코드별 정보
    """
    return {
        "NAS": {"name": "NASDAQ", "country": "미국", "currency": "USD"},
        "NYS": {"name": "NYSE", "country": "미국", "currency": "USD"},
        "AMS": {"name": "AMEX", "country": "미국", "currency": "USD"},
        "HKS": {"name": "홍콩증권거래소", "country": "홍콩", "currency": "HKD"},
        "TSE": {"name": "도쿄증권거래소", "country": "일본", "currency": "JPY"},
        "SHS": {"name": "상해증권거래소", "country": "중국", "currency": "CNY"},
        "SZS": {"name": "심천증권거래소", "country": "중국", "currency": "CNY"},
        "HSX": {"name": "호치민증권거래소", "country": "베트남", "currency": "VND"},
        "HNX": {"name": "하노이증권거래소", "country": "베트남", "currency": "VND"},
    }


@pytest.fixture
def sample_price_response():
    """
    해외주식 시세 조회 응답 샘플

    Returns:
        dict: API 응답 형식의 샘플 데이터
    """
    return {
        "rt_cd": "0",
        "msg_cd": "00000000",
        "msg1": "정상처리",
        "output": {
            "acpt_tmrd": "150000",  # 체결시각
            "last": "150.25",  # 현재가
            "clpr": "150.00",  # 전일종가
            "diff": "0.25",  # 전일대비
            "rate": "0.17",  # 등락률
            "time": "150000",
            "highd52w": "200.00",  # 52주 최고
            "lowd52w": "100.00",  # 52주 최저
        },
    }


@pytest.fixture
def sample_daily_price_response():
    """
    해외주식 기간별 시세 조회 응답 샘플

    Returns:
        dict: API 응답 형식의 샘플 데이터
    """
    return {
        "rt_cd": "0",
        "msg_cd": "00000000",
        "msg1": "정상처리",
        "output1": [
            {
                "yd_clpr": "150.00",  # 전일종가
                "prv_vrss": "0.25",  # 전일대비
                "prv_vrss_rate": "0.17",  # 등락률
                "opnprc": "149.75",  # 시가
                "hgpr": "151.00",  # 고가
                "lwpr": "149.50",  # 저가
                "clpr": "150.25",  # 종가
                "vol": "1000000",  # 거래량
                "trd_amt": "150250000",  # 거래대금
            },
            {
                "yd_clpr": "149.50",
                "prv_vrss": "0.50",
                "prv_vrss_rate": "0.33",
                "opnprc": "149.00",
                "hgpr": "150.50",
                "lwpr": "148.75",
                "clpr": "150.00",
                "vol": "950000",
                "trd_amt": "142500000",
            },
        ],
        "output2": {
            "ctx_area_fk200": "",  # 연속조회 검색조건
            "ctx_area_nk200": "",  # 연속조회 키
        },
    }


@pytest.fixture
def sample_balance_response():
    """
    해외주식 잔고 조회 응답 샘플

    Returns:
        dict: API 응답 형식의 샘플 데이터
    """
    return {
        "rt_cd": "0",
        "msg_cd": "00000000",
        "msg1": "정상처리",
        "output1": [
            {
                "ovrs_excg_cd": "NAS",  # 거래소 코드
                "ovrs_item_code": "AAPL",  # 종목코드
                "item_name": "Apple Inc",  # 종목명
                "hldg_qty": "100",  # 보유수량
                "ord_psbl_qty": "100",  # 주문가능수량
                "frcr_evalu_pfls": "5000.00",  # 외화평가손익
                "evalu_pfls_rt": "3.50",  # 평가손익률
                "frcr_buy_amt_smry1": "150000.00",  # 외화매입금액합
                "frcr_evalu_amt1": "155000.00",  # 외화평가금액합
            }
        ],
        "output2": {
            "dnca_tot_amt": "500000.00",  # 원화합계금액
            "frcr_tot_evalu_pfls": "15000.00",  # 외화총평가손익
            "tot_evalu_pfls_rt": "3.20",  # 총평가손익률
        },
    }


@pytest.fixture
def sample_order_response():
    """
    해외주식 주문 응답 샘플

    Returns:
        dict: API 응답 형식의 샘플 데이터
    """
    return {
        "rt_cd": "0",
        "msg_cd": "00000000",
        "msg1": "정상처리",
        "output": {
            "odno": "12345678",  # 주문번호
            "ord_tmd": "150000",  # 주문시각
        },
    }


@pytest.fixture
def sample_ranking_response():
    """
    해외주식 순위 조회 응답 샘플

    Returns:
        dict: API 응답 형식의 샘플 데이터
    """
    return {
        "rt_cd": "0",
        "msg_cd": "00000000",
        "msg1": "정상처리",
        "output": [
            {
                "rank": "1",
                "shcode": "NAS.NVDA",
                "hname": "NVIDIA Corporation",
                "vs_diff": "1000000",  # 전일대비
                "diff_rate": "5.50",  # 등락률
            },
            {
                "rank": "2",
                "shcode": "NAS.AAPL",
                "hname": "Apple Inc",
                "vs_diff": "500000",
                "diff_rate": "3.30",
            },
        ],
    }


@pytest.fixture
def overseas_api(mock_client, account_info):
    """
    테스트용 OverseasStockAPI 인스턴스

    Args:
        mock_client: 테스트용 Mock KISClient
        account_info: 테스트용 계좌 정보

    Returns:
        OverseasStockAPI: 테스트 준비된 API 인스턴스
    """
    from kis_agent.overseas.api_facade import OverseasStockAPI

    api = OverseasStockAPI(
        client=mock_client,
        account_info=account_info,
        enable_cache=False,
        _from_agent=True,
    )

    return api
