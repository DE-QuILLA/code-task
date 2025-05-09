import requests
import json
import logging
from pathlib import Path

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

def fetch_all_markets():
    url = "https://api.upbit.com/v1/market/all"
    headers = {"Accept": "application/json"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def extract_usdt_base_symbols(market_data):
    base_symbols = {
        market["market"].split("-")[1]
        for market in market_data
        if market["market"].startswith("USDT-")
    }
    return sorted(base_symbols)

def save_to_json(symbols, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(symbols, f, indent=2, ensure_ascii=False)

def main():
    setup_logging()

    output_path = Path("data/markets/upbit_usdt_pairs.json")

    logging.info("Fetching market data from Upbit...")
    market_data = fetch_all_markets()

    logging.info("Extracting base symbols from USDT pairs...")
    base_symbols = extract_usdt_base_symbols(market_data)

    logging.info("Saving base symbols to JSON file: %s", output_path)
    save_to_json(base_symbols, output_path)

    logging.info("Saved %d USDT base symbols successfully.", len(base_symbols))

if __name__ == "__main__":
    main()
