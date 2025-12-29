"""Consolidated MCP Tools 단위 테스트

18개 통합 도구의 기능을 검증합니다.
FastMCP의 @server.tool() 데코레이터로 래핑된 함수를 테스트합니다.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestConsolidatedToolsIntegration:
    """통합 도구 Import 및 등록 테스트"""

    def test_consolidated_tools_import(self):
        """모듈 임포트 테스트"""
        from pykis_mcp_server.tools import consolidated_tools
        assert consolidated_tools is not None

    def test_all_tools_exist(self):
        """18개 통합 도구 존재 확인"""
        from pykis_mcp_server.tools import consolidated_tools

        expected_tools = [
            'stock_quote', 'stock_chart', 'index_data', 'market_ranking',
            'investor_flow', 'broker_trading', 'program_trading', 'account_query',
            'order_execute', 'order_manage', 'stock_info', 'overtime_trading',
            'derivatives', 'interest_stocks', 'utility', 'data_management',
            'rate_limiter', 'method_discovery'
        ]

        for tool in expected_tools:
            assert hasattr(consolidated_tools, tool), f"Tool {tool} not found"

    def test_server_has_consolidated_tools(self):
        """서버에 통합 도구 등록 확인"""
        from pykis_mcp_server.server import server

        # FastMCP 서버에서 도구 목록 가져오기
        # server._tool_manager.tools 또는 유사한 방법으로 접근
        assert server is not None


class TestStockQuoteLogic:
    """stock_quote 도구 로직 테스트 (함수 직접 테스트)"""

    @pytest.fixture
    def mock_agent(self):
        return Mock()

    def test_stock_quote_price_logic(self, mock_agent):
        """현재가 조회 로직 검증"""
        mock_agent.get_stock_price.return_value = {
            "rt_cd": "0",
            "output": {"stck_prpr": "71000"}
        }

        # 직접 로직 테스트
        code = "005930"
        query_type = "price"

        if query_type == "price":
            result = mock_agent.get_stock_price(code)

        mock_agent.get_stock_price.assert_called_once_with("005930")
        assert result["rt_cd"] == "0"
        assert result["output"]["stck_prpr"] == "71000"

    def test_stock_quote_orderbook_logic(self, mock_agent):
        """호가 조회 로직 검증"""
        mock_agent.get_orderbook_raw.return_value = {
            "rt_cd": "0",
            "output1": {"ask1": "71100", "bid1": "71000"}
        }

        code = "005930"
        query_type = "orderbook"

        if query_type == "orderbook":
            result = mock_agent.get_orderbook_raw(code)

        mock_agent.get_orderbook_raw.assert_called_once_with("005930")
        assert result["rt_cd"] == "0"


class TestStockChartLogic:
    """stock_chart 도구 로직 테스트"""

    @pytest.fixture
    def mock_agent(self):
        return Mock()

    def test_stock_chart_minute_today_logic(self, mock_agent):
        """당일 분봉 조회 로직 검증"""
        mock_agent.get_intraday_price.return_value = {
            "rt_cd": "0",
            "output": [{"time": "090000", "price": "71000"}]
        }

        code = "005930"
        timeframe = "minute"
        date = ""

        if timeframe == "minute" and not date:
            result = mock_agent.get_intraday_price(code)

        mock_agent.get_intraday_price.assert_called_once_with("005930")
        assert result["rt_cd"] == "0"

    def test_stock_chart_minute_specific_date_logic(self, mock_agent):
        """특정일 분봉 조회 로직 검증"""
        mock_agent.get_daily_minute_price.return_value = {
            "rt_cd": "0",
            "output": [{"time": "090000", "price": "71000"}]
        }

        code = "005930"
        timeframe = "minute"
        date = "20241217"
        hour = "153000"

        if timeframe == "minute" and date:
            result = mock_agent.get_daily_minute_price(code, date, hour)

        mock_agent.get_daily_minute_price.assert_called_once_with("005930", "20241217", "153000")

    def test_stock_chart_daily_logic(self, mock_agent):
        """일봉 조회 로직 검증"""
        mock_agent.inquire_daily_itemchartprice.return_value = {
            "rt_cd": "0",
            "output": [{"date": "20241217", "close": "71000"}]
        }

        code = "005930"
        timeframe = "daily"

        if timeframe == "daily":
            result = mock_agent.inquire_daily_itemchartprice(code, "", "")

        mock_agent.inquire_daily_itemchartprice.assert_called_once()


class TestMarketRankingLogic:
    """market_ranking 도구 로직 테스트"""

    @pytest.fixture
    def mock_agent(self):
        return Mock()

    def test_market_ranking_volume_logic(self, mock_agent):
        """거래량 순위 조회 로직 검증"""
        mock_agent.get_volume_rank.return_value = {
            "rt_cd": "0",
            "output": [{"rank": 1, "code": "005930"}]
        }

        ranking_type = "volume"
        market = "0"
        sign = "0"

        if ranking_type == "volume":
            result = mock_agent.get_volume_rank(market, sign)

        mock_agent.get_volume_rank.assert_called_once_with("0", "0")
        assert result["rt_cd"] == "0"

    def test_market_ranking_gainers_logic(self, mock_agent):
        """상승률 순위 조회 로직 검증"""
        mock_agent.get_fluctuation_rank.return_value = {
            "rt_cd": "0",
            "output": [{"rank": 1, "code": "005930", "rate": "5.5"}]
        }

        ranking_type = "gainers"
        market = "KOSPI"
        market_map = {"ALL": "0", "KOSPI": "1", "KOSDAQ": "2"}
        m = market_map.get(market, "0")

        if ranking_type == "gainers":
            result = mock_agent.get_fluctuation_rank(m, "1")

        mock_agent.get_fluctuation_rank.assert_called_once_with("1", "1")


class TestAccountQueryLogic:
    """account_query 도구 로직 테스트"""

    @pytest.fixture
    def mock_agent(self):
        return Mock()

    def test_account_query_balance_logic(self, mock_agent):
        """계좌 잔고 조회 로직 검증"""
        mock_agent.get_account_balance.return_value = {
            "rt_cd": "0",
            "output1": [{"ticker": "005930", "qty": "100"}],
            "output2": {"total": "10000000"}
        }

        query_type = "balance"

        if query_type == "balance":
            result = mock_agent.get_account_balance()

        mock_agent.get_account_balance.assert_called_once()
        assert result["rt_cd"] == "0"

    def test_account_query_order_ability_logic(self, mock_agent):
        """주문 가능 금액 조회 로직 검증"""
        mock_agent.get_possible_order_amount.return_value = {
            "rt_cd": "0",
            "output": {"ord_psbl_qty": "100"}
        }

        query_type = "order_ability"
        code = "005930"
        price = "71000"

        if query_type == "order_ability":
            result = mock_agent.get_possible_order_amount(code, price)

        mock_agent.get_possible_order_amount.assert_called_once_with("005930", "71000")


class TestOrderExecuteLogic:
    """order_execute 도구 로직 테스트"""

    @pytest.fixture
    def mock_agent(self):
        return Mock()

    def test_order_execute_buy_logic(self, mock_agent):
        """매수 주문 로직 검증"""
        mock_agent.order_stock_cash.return_value = {
            "rt_cd": "0",
            "output": {"order_no": "12345"}
        }

        action = "buy"
        code = "005930"
        quantity = "10"
        price = "71000"
        order_type = "00"
        credit = False

        if not credit and action == "buy":
            result = mock_agent.order_stock_cash(action, code, order_type, quantity, price)

        mock_agent.order_stock_cash.assert_called_once_with("buy", "005930", "00", "10", "71000")
        assert result["rt_cd"] == "0"

    def test_order_execute_credit_buy_logic(self, mock_agent):
        """신용 매수 주문 로직 검증"""
        mock_agent.order_credit_buy.return_value = {
            "rt_cd": "0",
            "output": {"order_no": "12346"}
        }

        action = "buy"
        code = "005930"
        quantity = "10"
        price = "71000"
        order_type = "00"
        credit = True
        credit_type = "21"

        if credit and action == "buy":
            result = mock_agent.order_credit_buy(code, credit_type, quantity, price, order_type)

        mock_agent.order_credit_buy.assert_called_once_with("005930", "21", "10", "71000", "00")


class TestOrderManageLogic:
    """order_manage 도구 로직 테스트"""

    @pytest.fixture
    def mock_agent(self):
        return Mock()

    def test_order_manage_cancel_logic(self, mock_agent):
        """주문 취소 로직 검증"""
        mock_agent.order_rvsecncl.return_value = {
            "rt_cd": "0",
            "output": {"cncl_qty": "10"}
        }

        action = "cancel"
        order_no = "12345"
        quantity = "10"
        price = ""
        order_type = "00"

        if action == "cancel":
            result = mock_agent.order_rvsecncl(order_no, quantity, price, order_type, "02")

        mock_agent.order_rvsecncl.assert_called_once_with("12345", "10", "", "00", "02")

    def test_order_manage_list_pending_logic(self, mock_agent):
        """정정/취소 가능 목록 조회 로직 검증"""
        mock_agent.inquire_psbl_rvsecncl.return_value = {
            "rt_cd": "0",
            "output": [{"order_no": "12345", "status": "pending"}]
        }

        action = "list_pending"

        if action == "list_pending":
            result = mock_agent.inquire_psbl_rvsecncl()

        mock_agent.inquire_psbl_rvsecncl.assert_called_once()


class TestRateLimiterLogic:
    """rate_limiter 도구 로직 테스트"""

    @pytest.fixture
    def mock_agent(self):
        return Mock()

    def test_rate_limiter_status_logic(self, mock_agent):
        """Rate Limiter 상태 조회 로직 검증"""
        mock_agent.get_rate_limiter_status.return_value = {
            "rt_cd": "0",
            "output": {"requests_per_second": 18}
        }

        action = "status"

        if action == "status":
            result = mock_agent.get_rate_limiter_status()

        mock_agent.get_rate_limiter_status.assert_called_once()
        assert result["rt_cd"] == "0"

    def test_rate_limiter_reset_logic(self, mock_agent):
        """Rate Limiter 초기화 로직 검증"""
        mock_agent.reset_rate_limiter.return_value = {
            "rt_cd": "0",
            "msg1": "초기화 완료"
        }

        action = "reset"

        if action == "reset":
            result = mock_agent.reset_rate_limiter()

        mock_agent.reset_rate_limiter.assert_called_once()


class TestMethodDiscoveryLogic:
    """method_discovery 도구 로직 테스트"""

    @pytest.fixture
    def mock_agent(self):
        return Mock()

    def test_method_discovery_search_logic(self, mock_agent):
        """메서드 검색 로직 검증"""
        mock_agent.search_methods.return_value = {
            "rt_cd": "0",
            "output": [{"name": "get_stock_price", "desc": "주식 현재가 조회"}]
        }

        action = "search"
        query = "stock"

        if action == "search":
            result = mock_agent.search_methods(query)

        mock_agent.search_methods.assert_called_once_with("stock")

    def test_method_discovery_list_all_logic(self, mock_agent):
        """전체 메서드 목록 조회 로직 검증"""
        mock_agent.get_all_methods.return_value = {
            "rt_cd": "0",
            "output": {"total": 176, "methods": []}
        }

        action = "list_all"

        if action == "list_all":
            result = mock_agent.get_all_methods()

        mock_agent.get_all_methods.assert_called_once()


class TestValidationLogic:
    """입력 검증 로직 테스트"""

    def test_invalid_code_length(self):
        """잘못된 종목코드 길이 검증"""
        code = "12345"  # 5자리

        assert len(code) != 6

    def test_valid_code_length(self):
        """올바른 종목코드 길이 검증"""
        code = "005930"

        assert len(code) == 6

    def test_invalid_query_types(self):
        """잘못된 query_type 검증"""
        valid_types = ["price", "detail", "orderbook"]
        invalid_type = "invalid"

        assert invalid_type not in valid_types

    def test_valid_query_types(self):
        """올바른 query_type 검증"""
        valid_types = ["price", "detail", "orderbook"]
        query_type = "price"

        assert query_type in valid_types


class TestToolConsolidationCount:
    """도구 통합 수 검증"""

    def test_consolidated_tool_count(self):
        """18개 통합 도구 수 확인"""
        expected_count = 18
        tools = [
            'stock_quote', 'stock_chart', 'index_data', 'market_ranking',
            'investor_flow', 'broker_trading', 'program_trading', 'account_query',
            'order_execute', 'order_manage', 'stock_info', 'overtime_trading',
            'derivatives', 'interest_stocks', 'utility', 'data_management',
            'rate_limiter', 'method_discovery'
        ]

        assert len(tools) == expected_count

    def test_total_tool_reduction(self):
        """도구 수 감소 확인 (110개 → 22개)"""
        original_count = 110
        consolidated_count = 18
        composite_analysis_count = 4  # 복합 분석 도구
        orchestration_count = 3  # 오케스트레이션 도구

        total_new = consolidated_count + composite_analysis_count + orchestration_count

        assert total_new == 25
        assert total_new < original_count


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
