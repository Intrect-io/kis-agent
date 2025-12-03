import pytest

from pykis.core.agent import Agent
from pykis.core.client import API_ENDPOINTS, KISClient


@pytest.fixture
def mock_make_request(monkeypatch):
    calls = []

    def _fake_make_request(
        self,
        endpoint: str,
        tr_id: str,
        params: dict,
        retries: int = 0,
        method: str = "GET",
    ):
        calls.append({"endpoint": endpoint, "tr_id": tr_id, "params": params})
        return {"rt_cd": "0", "msg1": "OK", "output": {}}

    monkeypatch.setattr(KISClient, "make_request", _fake_make_request, raising=True)
    # 토큰 초기화 경로 완전 우회
    monkeypatch.setattr(KISClient, "_initialize_token", lambda self: None, raising=True)
    return calls


@pytest.fixture(autouse=True)
def mock_agent_token_flow(monkeypatch):
    """Agent._ensure_valid_token 경로 우회: read_token은 존재, auth는 no-op."""
    monkeypatch.setattr(
        "pykis.core.agent.read_token",
        lambda path=None, app_key=None: {"access_token": "dummy"},
    )
    monkeypatch.setattr(
        "pykis.core.agent.auth",
        lambda config=None, svr="prod", product=None, url=None: None,
    )
    monkeypatch.setenv("PYKIS_SILENT", "1")


def _new_agent() -> Agent:
    return Agent(
        app_key="k",
        app_secret="s",
        account_no="12345678",
        account_code="01",
        base_url="https://openapivts.koreainvestment.com:29443",
    )


def test_agent_inquire_price_delegates_to_price_api(mock_make_request):
    agent = _new_agent()
    resp = agent.inquire_price("005930")

    assert resp is not None and resp.get("rt_cd") == "0"
    last = mock_make_request[-1]
    assert last["tr_id"] == "FHKST01010100"
    assert last["endpoint"] == API_ENDPOINTS["INQUIRE_PRICE"]
    assert last["params"]["FID_INPUT_ISCD"] == "005930"


def test_agent_inquire_ccnl_delegates_to_price_api(mock_make_request):
    agent = _new_agent()
    resp = agent.inquire_ccnl("005930")

    assert resp is not None and resp.get("rt_cd") == "0"
    last = mock_make_request[-1]
    assert last["tr_id"] == "FHKST01010300"
    assert last["endpoint"] == API_ENDPOINTS["INQUIRE_CCNL"]
    assert last["params"]["FID_INPUT_ISCD"] == "005930"
