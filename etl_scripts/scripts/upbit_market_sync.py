import requests
import json
from datetime import datetime

# 업비트 거래쌍 수집
def fetch_upbit_markets():
    url = "https://api.upbit.com/v1/market/all"
    headers = {"Accept": "application/json"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

# 거래쌍 상세 정보 구성
def build_market_info(market_code):
    quote_asset, base_asset = market_code.split('-')
    return {
        "symbol": market_code,
        "baseAsset": base_asset,
        "quoteAsset": quote_asset,
        "status": "active",
        "registered_at": "unknown"
    }

# KRW, USDT 마켓별 거래쌍 필터링
def filter_markets_by_quote(market_list, quote_asset):
    return [m for m in market_list if m['market'].startswith(f"{quote_asset}-")]

# 메모리 기반 데이터 저장 (Redis로 대체 예정)
def save_to_json(data, filepath):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    market_list = fetch_upbit_markets()

    # KRW, USDT 거래쌍 목록
    krw_markets = filter_markets_by_quote(market_list, 'KRW')
    usdt_markets = filter_markets_by_quote(market_list, 'USDT')

    # 상세 정보 딕셔너리 (baseAsset 기준 저장)
    upbit_pairs_krw = {m['market'].split('-')[1]: build_market_info(m['market']) for m in krw_markets}
    upbit_pairs_usdt = {m['market'].split('-')[1]: build_market_info(m['market']) for m in usdt_markets}

    # 로컬 파일로 저장 (Redis Hash 대체용)
    save_to_json(upbit_pairs_krw, 'upbit_pairs_krw.json')
    save_to_json(upbit_pairs_usdt, 'upbit_pairs_usdt.json')

    # Redis 구성 시 사용
    # import redis
    # r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    # for symbol, info in upbit_pairs_krw.items():
    #     r.hset('upbit_pairs_krw', symbol, json.dumps(info))
    # for symbol, info in upbit_pairs_usdt.items():
    #     r.hset('upbit_pairs_usdt', symbol, json.dumps(info))

    # base symbol Set 도출 (나중에는 Redis Set으로 대체)
    upbit_base_symbols_krw = set(upbit_pairs_krw.keys())
    upbit_base_symbols_usdt = set(upbit_pairs_usdt.keys())

    # 업비트의 KRW, USDT 공통 symbol
    upbit_common_pairs = upbit_base_symbols_krw & upbit_base_symbols_usdt

    print(f"[Upbit] KRW 거래쌍 수: {len(upbit_base_symbols_krw)}")
    print(f"[Upbit] USDT 거래쌍 수: {len(upbit_base_symbols_usdt)}")
    print(f"[Upbit] KRW+USDT 공통 symbol 수: {len(upbit_common_pairs)}")

    # 교집합 결과 로컬 저장
    save_to_json(list(upbit_common_pairs), 'upbit_common_pairs.json')

    # Redis 구성 시 사용
    # r.delete('upbit_base_symbols_krw')
    # r.delete('upbit_base_symbols_usdt')
    # r.delete('upbit_common_pairs')
    # if upbit_base_symbols_krw:
    #     r.sadd('upbit_base_symbols_krw', *upbit_base_symbols_krw)
    # if upbit_base_symbols_usdt:
    #     r.sadd('upbit_base_symbols_usdt', *upbit_base_symbols_usdt)
    # if upbit_common_pairs:
    #     r.sadd('upbit_common_pairs', *upbit_common_pairs)

if __name__ == "__main__":
    main()
