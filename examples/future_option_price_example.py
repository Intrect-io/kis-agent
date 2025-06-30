#!/usr/bin/env python3
"""
선물옵션 시세 조회 예제

이 예제는 Pykis를 사용하여 선물옵션 시세를 조회하는 방법을 보여줍니다.
"""

import os
import sys

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pykis import KISClient, StockAPI

def main():
    """선물옵션 시세 조회 예제"""
    
    # KISClient 초기화
    client = KISClient()
    
    # StockAPI 초기화 (계좌 정보는 선택사항)
    stock_api = StockAPI(client, {})
    
    print("선물옵션 시세 조회")
    print("=" * 50)
    
    # 1. 지수선물 시세 조회 (기본값)
    print("\n1. 지수선물 시세 조회 (기본값: 101S09)")
    result = stock_api.get_future_option_price()
    
    if result and result.get('rt_cd') == '0':
        output = result.get('output2') or result.get('output3') or result.get('output', {})
        if output:
            print(f"종목명: {output.get('hts_kor_isnm', 'N/A')}")
            print(f"현재가: {output.get('bstp_nmix_prpr', 'N/A')}")
            print(f"전일대비: {output.get('bstp_nmix_prdy_vrss', 'N/A')}")
            print(f"등락률: {output.get('bstp_nmix_prdy_ctrt', 'N/A')}%")
        else:
            print("데이터가 없습니다.")
    else:
        print(f"조회 실패: {result.get('msg1', '알 수 없는 오류') if result else '응답 없음'}")
    
    # 2. 다른 지수선물 종목 조회 (현재 거래되는 종목)
    print("\n2. 다른 지수선물 종목 조회 (101S12)")
    result = stock_api.get_future_option_price(
        market_div_code="F",      # 지수선물
        input_iscd="101S12"       # 2024년 12월 만기 선물
    )
    
    if result and result.get('rt_cd') == '0':
        output = result.get('output2') or result.get('output3') or result.get('output', {})
        if output:
            print(f"종목명: {output.get('hts_kor_isnm', 'N/A')}")
            print(f"현재가: {output.get('bstp_nmix_prpr', 'N/A')}")
            print(f"전일대비: {output.get('bstp_nmix_prdy_vrss', 'N/A')}")
            print(f"등락률: {output.get('bstp_nmix_prdy_ctrt', 'N/A')}%")
        else:
            print("데이터가 없습니다.")
    else:
        print(f"조회 실패: {result.get('msg1', '알 수 없는 오류') if result else '응답 없음'}")
    
    # 3. 지수옵션 시세 조회 (현재 거래되는 종목)
    print("\n3. 지수옵션 시세 조회 (201S12370)")
    result = stock_api.get_future_option_price(
        market_div_code="O",      # 지수옵션
        input_iscd="201S12370"    # 2024년 12월 만기 콜옵션
    )
    
    if result and result.get('rt_cd') == '0':
        output = result.get('output2') or result.get('output3') or result.get('output', {})
        if output:
            print(f"종목명: {output.get('hts_kor_isnm', 'N/A')}")
            print(f"현재가: {output.get('bstp_nmix_prpr', 'N/A')}")
            print(f"전일대비: {output.get('bstp_nmix_prdy_vrss', 'N/A')}")
            print(f"등락률: {output.get('bstp_nmix_prdy_ctrt', 'N/A')}%")
        else:
            print("데이터가 없습니다.")
    else:
        print(f"조회 실패: {result.get('msg1', '알 수 없는 오류') if result else '응답 없음'}")
    
    # 4. 시장분류코드 정보
    print("\n4. 시장분류코드 정보")
    market_codes = {
        "F": "지수선물",
        "O": "지수옵션", 
        "JF": "주식선물",
        "JO": "주식옵션"
    }
    
    print("사용 가능한 시장분류코드:")
    for code, name in market_codes.items():
        print(f"  {code}: {name}")
    
    print("\n5. 종목코드 형식 안내")
    print("선물 종목코드: 6자리 (예: 101S03, 101S06, 101S09)")
    print("옵션 종목코드: 9자리 (예: 201S03370, 201S03380)")

if __name__ == "__main__":
    main() 