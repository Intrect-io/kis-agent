import pandas as pd
from ..core.client import KISClient, API_ENDPOINTS
from typing import Optional, Dict, Any
import logging

"""
account.py - 계좌 정보 조회 전용 모듈

이 모듈은 한국투자증권 OpenAPI를 통해 다음과 같은 기능을 제공합니다:
- 보유 종목 및 잔고 조회
- 현금 매수 가능 금액 조회
- 총 자산 평가 (예수금, 주식, 평가손익 등 포함)

✅ 의존:
- client.py: 모든 API 요청은 이 객체를 통해 수행됩니다.

🔗 연관 모듈:
- stock.py: 종목 단위 시세 및 주문 API 담당
- program.py: 프로그램 매매 추이 및 순매수량 확인
- (전략 관련 모듈은 deprecated되어 제거됨)

💡 사용 예시:
client = KISClient()
account = AccountAPI(client, {"CANO": "12345678", "ACNT_PRDT_CD": "01"})
df = account.get_account_balance()
"""

class AccountAPI:
    def __init__(self, client: KISClient, account_info: Dict[str, str]):
        """Wrapper around KIS account related endpoints.

        Parameters
        ----------
        client : :class:`KISClient`
            Authenticated client instance.
        account_info : dict
            Dictionary with ``CANO`` and ``ACNT_PRDT_CD`` keys. Values are
            usually loaded from ``credit/kis_devlp.yaml``.

        Example
        -------
        >>> account = load_account_info()
        >>> api = AccountAPI(KISClient(), account)
        """
        self.client = client
        self.account = account_info  # { 'CANO': '12345678', 'ACNT_PRDT_CD': '01' }

    def get_account_balance(self) -> Optional[pd.DataFrame]:
        """Return current holdings and profit/loss information.

        Returns
        -------
        Optional[pandas.DataFrame]
            ``output1`` from the API on success.

        Example
        -------
        >>> api.get_account_balance().head()
        """
        res = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/trading/inquire-balance",
            tr_id="TTTC8434R",
            params={
                "CANO": self.account['CANO'],
                "ACNT_PRDT_CD": self.account['ACNT_PRDT_CD'],
                "AFHR_FLPR_YN": "N",
                "OFL_YN": "",
                "INQR_DVSN": "01",
                "UNPR_DVSN": "01",
                "FUND_STTL_ICLD_YN": "N",
                "FNCG_AMT_AUTO_RDPT_YN": "N",
                "PRCS_DVSN": "00",
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": ""
            }
        )
        if res and 'output1' in res:
            return pd.DataFrame(res['output1'])
        return None

    def get_cash_available(self, stock_code: str = "005930") -> Optional[Dict[str, Any]]:
        """Query available cash for purchasing specific stock.

        Args
        ----
        stock_code : str, default "005930"
            Stock code to check purchase availability (default: Samsung Electronics)

        Returns
        -------
        Optional[dict]
            Response JSON with purchase availability information.
            - ord_psbl_cash: Available cash for purchase
            - ord_psbl_sbst: Available substitution amount
            - max_buy_qty: Maximum purchasable quantity

        Example
        -------
        >>> api.get_cash_available("005930")  # Samsung Electronics
        >>> api.get_cash_available("000660")  # SK Hynix
        """
        res = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/trading/inquire-psbl-order",
            tr_id="TTTC8908R",
            params={
                "CANO": self.account['CANO'],
                "ACNT_PRDT_CD": self.account['ACNT_PRDT_CD'],
                "PDNO": stock_code,  # 매수가능조회할 종목코드
                "ORD_UNPR": "0",   # 주문단가 (0으로 설정하면 현재가 기준)
                "ORD_DVSN": "00",  # 지정가
                "CMA_EVLU_AMT_ICLD_YN": "Y",  # CMA평가금액포함여부
                "OVRS_ICLD_YN": "N"  # 해외포함여부
            }
        )
        # JSON 디코드 실패 시 원시 응답 확인을 위한 상세 정보 제공
        if res is not None and res.get('rt_cd') == 'JSON_DECODE_ERROR':
            # 원시 응답 텍스트 확인을 위해 추가 정보 제공
            res["디버깅_정보"] = f"원시 응답 텍스트 확인 필요 (상태코드: {res.get('status_code', 'N/A')})"
        return res

    def get_total_asset(self) -> Optional[Dict[str, Any]]:
        """Query total asset evaluation including cash and stocks.

        Returns
        -------
        Optional[dict]
            JSON structure describing investment account balance.
            - output1: Account summary information
            - output2: Detailed balance information

        Example
        -------
        >>> api.get_total_asset()
        """
        res = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/trading/inquire-account-balance",
            tr_id="CTRP6548R",
            params={
                "CANO": self.account['CANO'],
                "ACNT_PRDT_CD": self.account['ACNT_PRDT_CD'],
                "INQR_DVSN_1": "",  # 조회구분1 (공백입력)
                "BSPR_BF_DT_APLY_YN": ""  # 기준가이전일자적용여부 (공백입력)
            }
        )
        # JSON 디코드 실패 시 원시 응답 확인을 위한 상세 정보 제공
        if res is not None and res.get('rt_cd') == 'JSON_DECODE_ERROR':
            # 원시 응답 텍스트 확인을 위해 추가 정보 제공
            res["디버깅_정보"] = f"원시 응답 텍스트 확인 필요 (상태코드: {res.get('status_code', 'N/A')})"
        return res

    def get_account_order_quantity(self, code: str) -> Optional[Dict]:
        """계좌별 주문 수량 조회"""
        try:
            return self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/trading/inquire-account-order-quantity",
                tr_id="TTTC8434R",
                params={
                    "CANO": self.account['CANO'],
                    "ACNT_PRDT_CD": self.account['ACNT_PRDT_CD'],
                    "PDNO": code,
                    "ORD_UNPR": "0",
                    "CTX_AREA_FK200": "",
                    "CTX_AREA_NK200": ""
                }
            )
        except Exception as e:
            logging.error(f"계좌별 주문 수량 조회 실패: {e}")
            return None

    def get_possible_order_amount(self) -> Optional[Dict]:
        """주문 가능 금액 조회"""
        try:
            return self.client.make_request(
                endpoint=API_ENDPOINTS['INQUIRE_PSBL_ORDER'],
                tr_id="TTTC8908R",
                params={
                    "CANO": self.account['CANO'],
                    "ACNT_PRDT_CD": self.account['ACNT_PRDT_CD'],
                    "PDNO": "",
                    "ORD_UNPR": "0",
                    "ORD_DVSN": "00",
                    "CMA_EVLU_AMT_ICLD_YN": "Y",
                    "OVRS_ICLD_YN": "N"
                }
            )
        except Exception as e:
            logging.error(f"주문 가능 금액 조회 실패: {e}")
            return None

    def order_credit(self, code: str, qty: int, price: int, order_type: str) -> Optional[Dict]:
        """주식주문(신용)"""
        try:
            return self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/trading/order-credit",
                tr_id="TTTC0852U",
                params={
                    "CANO": self.account['CANO'],
                    "ACNT_PRDT_CD": self.account['ACNT_PRDT_CD'],
                    "PDNO": code,
                    "CRDT_TYPE": "21",
                    "LOAN_DT": "",
                    "ORD_DVSN": order_type,
                    "ORD_QTY": str(qty),
                    "ORD_UNPR": str(price)
                }
            )
        except Exception as e:
            logging.error(f"신용 주문 실패: {e}")
            return None

    def order_rvsecncl(self, org_order_no: str, qty: int, price: int, order_type: str, cncl_type: str) -> Optional[Dict]:
        """주식주문(정정취소)"""
        try:
            return self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/trading/order-rvsecncl",
                tr_id="TTTC0803U",
                params={
                    "CANO": self.account['CANO'],
                    "ACNT_PRDT_CD": self.account['ACNT_PRDT_CD'],
                    "KRX_FWDG_ORD_ORGNO": "",
                    "ORGN_ODNO": org_order_no,
                    "ORD_DVSN": order_type,
                    "RVSE_CNCL_DVSN_CD": cncl_type,
                    "ORD_QTY": str(qty),
                    "ORD_UNPR": str(price),
                    "QTY_ALL_ORD_YN": "Y"
                }
            )
        except Exception as e:
            logging.error(f"정정/취소 주문 ��패: {e}")
            return None

    def inquire_psbl_rvsecncl(self) -> Optional[Dict]:
        """주식정정취소가능주문조회"""
        try:
            return self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/trading/inquire-psbl-rvsecncl",
                tr_id="TTTC8036R",
                params={
                    "CANO": self.account['CANO'],
                    "ACNT_PRDT_CD": self.account['ACNT_PRDT_CD'],
                    "CTX_AREA_FK100": "",
                    "CTX_AREA_NK100": "",
                    "INQR_DVSN_1": "1",
                    "INQR_DVSN_2": "0"
                }
            )
        except Exception as e:
            logging.error(f"정정/취소 가능 주문 조회 실패: {e}")
            return None

    def order_resv(self, code: str, qty: int, price: int, order_type: str) -> Optional[Dict]:
        """주식예약주문"""
        try:
            return self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/trading/order-resv",
                tr_id="CTSC0008U",
                params={
                    "CANO": self.account['CANO'],
                    "ACNT_PRDT_CD": self.account['ACNT_PRDT_CD'],
                    "PDNO": code,
                    "ORD_QTY": str(qty),
                    "ORD_UNPR": str(price),
                    "SLL_BUY_DVSN_CD": "02",
                    "ORD_DVSN_CD": order_type,
                    "ORD_OBJT_CBLC_DVSN_CD": "10"
                }
            )
        except Exception as e:
            logging.error(f"예약 주문 실패: {e}")
            return None

    def order_resv_rvsecncl(self, seq: int, qty: int, price: int, order_type: str) -> Optional[Dict]:
        """주식예약주문정정취소"""
        try:
            return self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/trading/order-resv-rvsecncl",
                tr_id="CTSC0013U",
                params={
                    "CANO": self.account['CANO'],
                    "ACNT_PRDT_CD": self.account['ACNT_PRDT_CD'],
                    "PDNO": "",
                    "ORD_QTY": str(qty),
                    "ORD_UNPR": str(price),
                    "SLL_BUY_DVSN_CD": "02",
                    "ORD_DVSN_CD": order_type,
                    "ORD_OBJT_CBLC_DVSN_CD": "10",
                    "RSVN_ORD_SEQ": str(seq)
                }
            )
        except Exception as e:
            logging.error(f"예약 주문 정정/취소 실패: {e}")
            return None

    def order_resv_ccnl(self) -> Optional[Dict]:
        """주식예약주문조회"""
        try:
            return self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/trading/order-resv-ccnl",
                tr_id="CTSC0004R",
                params={
                    "RSVN_ORD_ORD_DT": "",
                    "RSVN_ORD_END_DT": "",
                    "RSVN_ORD_SEQ": "",
                    "TMNL_MDIA_KIND_CD": "00",
                    "CANO": self.account['CANO'],
                    "ACNT_PRDT_CD": self.account['ACNT_PRDT_CD'],
                    "PRCS_DVSN_CD": "0",
                    "CNCL_YN": "Y",
                    "PDNO": "",
                    "SLL_BUY_DVSN_CD": "",
                    "CTX_AREA_FK200": "",
                    "CTX_AREA_NK200": ""
                }
            )
        except Exception as e:
            logging.error(f"예약 주문 조회 실패: {e}")
            return None



# Expose facade class for flat import
__all__ = ['AccountAPI']
