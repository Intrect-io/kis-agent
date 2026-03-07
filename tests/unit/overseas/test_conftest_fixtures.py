"""
conftest.py fixture 검증 테스트

모든 overseas 테스트 fixture가 올바르게 작동하는지 확인합니다.
"""

from unittest.mock import Mock

import pytest

from kis_agent.core.client import KISClient
from kis_agent.overseas.api_facade import OverseasStockAPI


class TestConfFixtures:
    """conftest.py의 fixture 검증"""

    def test_mock_client_fixture(self, mock_client):
        """mock_client fixture 검증"""
        assert isinstance(mock_client, Mock)
        assert "authorization" in mock_client.headers
        assert "appkey" in mock_client.headers
        assert "appsecret" in mock_client.headers
        assert mock_client.domain == "https://openapi.koreainvestment.com:9443"

    def test_account_info_fixture(self, account_info):
        """account_info fixture 검증"""
        assert isinstance(account_info, dict)
        assert "CANO" in account_info
        assert "ACNT_PRDT_CD" in account_info
        assert account_info["CANO"] == "12345678"
        assert account_info["ACNT_PRDT_CD"] == "01"

    def test_overseas_exchange_codes_fixture(self, overseas_exchange_codes):
        """overseas_exchange_codes fixture 검증"""
        assert isinstance(overseas_exchange_codes, dict)
        assert "NAS" in overseas_exchange_codes
        assert "NYS" in overseas_exchange_codes
        assert "HKS" in overseas_exchange_codes
        assert overseas_exchange_codes["NAS"]["currency"] == "USD"
        assert overseas_exchange_codes["HKS"]["country"] == "홍콩"

    def test_sample_price_response_fixture(self, sample_price_response):
        """sample_price_response fixture 검증"""
        assert isinstance(sample_price_response, dict)
        assert sample_price_response["rt_cd"] == "0"
        assert "output" in sample_price_response
        assert "last" in sample_price_response["output"]
        assert sample_price_response["output"]["last"] == "150.25"

    def test_sample_daily_price_response_fixture(self, sample_daily_price_response):
        """sample_daily_price_response fixture 검증"""
        assert isinstance(sample_daily_price_response, dict)
        assert "output1" in sample_daily_price_response
        assert isinstance(sample_daily_price_response["output1"], list)
        assert len(sample_daily_price_response["output1"]) == 2

    def test_sample_balance_response_fixture(self, sample_balance_response):
        """sample_balance_response fixture 검증"""
        assert isinstance(sample_balance_response, dict)
        assert "output1" in sample_balance_response
        assert isinstance(sample_balance_response["output1"], list)
        assert sample_balance_response["output1"][0]["ovrs_excg_cd"] == "NAS"

    def test_sample_order_response_fixture(self, sample_order_response):
        """sample_order_response fixture 검증"""
        assert isinstance(sample_order_response, dict)
        assert "output" in sample_order_response
        assert "odno" in sample_order_response["output"]
        assert sample_order_response["output"]["odno"] == "12345678"

    def test_sample_ranking_response_fixture(self, sample_ranking_response):
        """sample_ranking_response fixture 검증"""
        assert isinstance(sample_ranking_response, dict)
        assert "output" in sample_ranking_response
        assert isinstance(sample_ranking_response["output"], list)
        assert len(sample_ranking_response["output"]) == 2

    def test_overseas_api_fixture(self, overseas_api):
        """overseas_api fixture 검증"""
        assert isinstance(overseas_api, OverseasStockAPI)
        assert overseas_api.client is not None
        assert overseas_api.account is not None
        assert "CANO" in overseas_api.account
        assert hasattr(overseas_api, "price_api")
        assert hasattr(overseas_api, "account_api")
        assert hasattr(overseas_api, "order_api")
        assert hasattr(overseas_api, "ranking_api")
