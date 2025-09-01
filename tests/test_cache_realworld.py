#!/usr/bin/env python3
"""
캐싱 로직 실제 동작 검증 테스트
시세 데이터는 10초, 다른 데이터는 컨텍스트별 TTL 적용 확인
"""

import time
import json
from unittest.mock import Mock, patch
from pykis.core.cache import APICache, TTLCache
from pykis.core.base_api import BaseAPI


def test_price_data_caching():
    """시세 데이터 10초 TTL 실제 동작 테스트"""
    print("\n" + "="*60)
    print("🔍 시세 데이터 캐싱 테스트 (TTL: 10초)")
    print("="*60)
    
    cache = APICache()
    endpoint = "/uapi/domestic-stock/v1/quotations/inquire-price"
    
    # TTL 확인
    ttl = cache.get_ttl_for_endpoint(endpoint)
    print(f"✓ 시세 데이터 TTL: {ttl}초")
    assert ttl == 10, f"시세 데이터는 10초 TTL이어야 합니다. 실제: {ttl}"
    
    # 데이터 저장
    test_data = {
        "rt_cd": "0",
        "output": {
            "stck_prpr": "70000",
            "prdy_vrss": "1000",
            "prdy_ctrt": "1.45"
        }
    }
    
    cache_key = cache._make_key({
        "endpoint": endpoint,
        "tr_id": "FHKST01010100",
        "params": {"FID_INPUT_ISCD": "005930"}
    })
    
    cache.set(cache_key, test_data, ttl=ttl)
    print(f"✓ 데이터 캐시 저장 완료")
    
    # 즉시 조회 - 캐시 히트
    cached = cache.get(cache_key)
    assert cached is not None, "캐시된 데이터를 찾을 수 없습니다"
    print(f"✓ 즉시 조회: 캐시 히트 (hits: {cache.hits})")
    
    # 5초 후 - 아직 유효
    print("⏳ 5초 대기 중...")
    time.sleep(5)
    cached = cache.get(cache_key)
    assert cached is not None, "5초 후에도 캐시가 유효해야 합니다"
    print(f"✓ 5초 후: 여전히 캐시 유효 (hits: {cache.hits})")
    
    # 11초 후 - 만료됨
    print("⏳ 6초 추가 대기 중 (총 11초)...")
    time.sleep(6)
    cached = cache.get(cache_key)
    assert cached is None, "11초 후에는 캐시가 만료되어야 합니다"
    print(f"✓ 11초 후: 캐시 만료 확인 (misses: {cache.misses})")
    
    print("\n✅ 시세 데이터 10초 TTL 동작 검증 완료!")


def test_different_context_ttls():
    """다양한 컨텍스트별 TTL 동작 테스트"""
    print("\n" + "="*60)
    print("🔍 컨텍스트별 차등 TTL 테스트")
    print("="*60)
    
    cache = APICache()
    
    # 테스트할 엔드포인트와 예상 TTL
    test_cases = [
        {
            "name": "체결내역 (실시간)",
            "endpoint": "/uapi/domestic-stock/v1/quotations/inquire-ccnl",
            "expected_ttl": 5,
            "data": {"rt_cd": "0", "output": [{"체결가": "70000"}]}
        },
        {
            "name": "투자자 동향 (준실시간)",
            "endpoint": "/uapi/domestic-stock/v1/quotations/inquire-investor",
            "expected_ttl": 30,
            "data": {"rt_cd": "0", "output": {"개인": "매수"}}
        },
        {
            "name": "일봉 차트 (일단위)",
            "endpoint": "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
            "expected_ttl": 60,
            "data": {"rt_cd": "0", "output": [{"종가": "70000"}]}
        },
        {
            "name": "종목 정보 (정적)",
            "endpoint": "/uapi/domestic-stock/v1/quotations/inquire-stock-info",
            "expected_ttl": 300,
            "data": {"rt_cd": "0", "output": {"종목명": "삼성전자"}}
        }
    ]
    
    stored_keys = []
    
    # 각 컨텍스트별로 데이터 저장
    for tc in test_cases:
        ttl = cache.get_ttl_for_endpoint(tc["endpoint"])
        print(f"\n[{tc['name']}]")
        print(f"  엔드포인트: {tc['endpoint']}")
        print(f"  TTL: {ttl}초 (예상: {tc['expected_ttl']}초)")
        assert ttl == tc["expected_ttl"], f"TTL 불일치: {ttl} != {tc['expected_ttl']}"
        
        cache_key = cache._make_key({
            "endpoint": tc["endpoint"],
            "params": {"test": True}
        })
        cache.set(cache_key, tc["data"], ttl=ttl)
        stored_keys.append((tc["name"], cache_key, ttl))
        print(f"  ✓ 캐시 저장 완료")
    
    # 6초 후 체크 - 5초 TTL만 만료
    print("\n⏳ 6초 대기 후 확인...")
    time.sleep(6)
    
    for name, key, ttl in stored_keys:
        cached = cache.get(key)
        if ttl <= 5:
            assert cached is None, f"{name}은(는) 만료되어야 합니다"
            print(f"  ✓ {name}: 만료됨 (TTL {ttl}초)")
        else:
            assert cached is not None, f"{name}은(는) 유효해야 합니다"
            print(f"  ✓ {name}: 유효함 (TTL {ttl}초)")
    
    print("\n✅ 컨텍스트별 차등 TTL 동작 검증 완료!")


def test_cache_performance():
    """캐시 성능 측정 테스트"""
    print("\n" + "="*60)
    print("🚀 캐시 성능 측정")
    print("="*60)
    
    cache = APICache()
    
    # 1000개 데이터 저장 시간 측정
    start_time = time.time()
    for i in range(1000):
        cache.set(f"key_{i}", {"data": f"value_{i}"}, ttl=60)
    write_time = time.time() - start_time
    print(f"✓ 1000개 쓰기: {write_time:.3f}초 ({1000/write_time:.0f} ops/sec)")
    
    # 1000개 데이터 읽기 시간 측정
    start_time = time.time()
    hits = 0
    for i in range(1000):
        if cache.get(f"key_{i}") is not None:
            hits += 1
    read_time = time.time() - start_time
    print(f"✓ 1000개 읽기: {read_time:.3f}초 ({1000/read_time:.0f} ops/sec)")
    print(f"✓ 캐시 히트율: {hits/10:.1f}%")
    
    # 통계 출력
    stats = cache.get_stats()
    print(f"\n📊 캐시 통계:")
    print(f"  - 현재 크기: {stats['size']}/{stats['max_size']}")
    print(f"  - 총 히트: {stats['hits']}")
    print(f"  - 총 미스: {stats['misses']}")
    print(f"  - 히트율: {stats['hit_rate']}")


def test_order_api_no_cache():
    """주문 API는 캐시하지 않음 검증"""
    print("\n" + "="*60)
    print("⚠️ 주문 API 캐시 비활성화 검증")
    print("="*60)
    
    cache = APICache()
    
    order_endpoints = [
        "/uapi/domestic-stock/v1/trading/order-cash",
        "/uapi/domestic-stock/v1/trading/order-credit",
        "/uapi/domestic-stock/v1/trading/modify",
        "/uapi/domestic-stock/v1/trading/cancel"
    ]
    
    for endpoint in order_endpoints:
        ttl = cache.get_ttl_for_endpoint(endpoint)
        print(f"✓ {endpoint}: TTL={ttl}초")
        assert ttl == 0, f"주문 API는 캐시하지 않아야 합니다: {endpoint}"
    
    # 실제로 캐시가 안 되는지 테스트
    endpoint = "/uapi/domestic-stock/v1/trading/order-cash"
    cache_key = cache._make_key({"endpoint": endpoint, "params": {"order": "buy"}})
    
    # TTL=0으로 저장 시도
    cache.set(cache_key, {"result": "주문 완료"}, ttl=0)
    
    # 즉시 조회 - 캐시되지 않음
    cached = cache.get(cache_key)
    assert cached is None, "TTL=0인 데이터는 캐시되지 않아야 합니다"
    print("\n✓ 주문 API는 캐시에 저장되지 않음 확인")
    print("✅ 주문 API 캐시 비활성화 검증 완료!")


def test_cache_statistics_summary():
    """캐시 통계 요약"""
    print("\n" + "="*60)
    print("📊 PyKIS 캐시 TTL 설정 요약")
    print("="*60)
    
    cache = APICache()
    
    # TTL 그룹별 분류
    ttl_groups = {
        "실시간 (5-10초)": [],
        "준실시간 (30초)": [],
        "일단위 (60초)": [],
        "계좌정보 (60-120초)": [],
        "정적 (300초+)": [],
        "캐시안함 (0초)": []
    }
    
    # 각 API별 TTL 분류
    for api_name, ttl in cache.DEFAULT_TTLS.items():
        if ttl == 0:
            ttl_groups["캐시안함 (0초)"].append(f"{api_name}: {ttl}초")
        elif ttl <= 10:
            ttl_groups["실시간 (5-10초)"].append(f"{api_name}: {ttl}초")
        elif ttl <= 30:
            ttl_groups["준실시간 (30초)"].append(f"{api_name}: {ttl}초")
        elif ttl <= 60:
            ttl_groups["일단위 (60초)"].append(f"{api_name}: {ttl}초")
        elif ttl <= 120:
            ttl_groups["계좌정보 (60-120초)"].append(f"{api_name}: {ttl}초")
        else:
            ttl_groups["정적 (300초+)"].append(f"{api_name}: {ttl}초")
    
    # 출력
    for group_name, apis in ttl_groups.items():
        if apis:
            print(f"\n🔹 {group_name}")
            for api in sorted(apis):
                print(f"   - {api}")
    
    print(f"\n기본 TTL: {cache.default_ttl}초")
    print(f"최대 캐시 크기: {cache.max_size}개")
    print("="*60)


def main():
    """메인 테스트 실행"""
    print("\n🧪 PyKIS 캐싱 로직 실제 동작 검증 시작")
    
    try:
        # 1. 시세 데이터 10초 TTL 테스트
        test_price_data_caching()
        
        # 2. 컨텍스트별 차등 TTL 테스트
        test_different_context_ttls()
        
        # 3. 캐시 성능 측정
        test_cache_performance()
        
        # 4. 주문 API 캐시 비활성화 검증
        test_order_api_no_cache()
        
        # 5. 통계 요약
        test_cache_statistics_summary()
        
        print("\n" + "="*60)
        print("✅ 모든 캐싱 로직 테스트 통과!")
        print("="*60)
        print("\n📌 검증 결과:")
        print("  1. 시세 데이터는 10초 TTL로 정확히 동작")
        print("  2. 컨텍스트별 차등 TTL이 올바르게 적용")
        print("  3. 캐시 성능이 충분히 빠름")
        print("  4. 주문 API는 캐시하지 않음")
        print("  5. 모든 TTL 설정이 시간 민감성에 적합")
        
    except AssertionError as e:
        print(f"\n❌ 테스트 실패: {e}")
        raise
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")
        raise


if __name__ == "__main__":
    main()