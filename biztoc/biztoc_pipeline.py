from biztoc.biztoc_client import BIZTOC
from config.spot import watchlist, ambiguous_watchlist
from biztoc.biztoc_transform import *
import json

bt = BIZTOC()


def biztoc_search_watchlist(ticker):
    try:
        print(f"Querying biztoc api for {ticker}...")
        data = bt.search_ticker(ticker)
        parsed = json.loads(data)
        with open(f"data/{ticker}_biztoc.json", "w") as f:
            print(f"Creating json file with response data for {ticker}")
            json.dump(parsed, f, indent=5)
    except Exception as e:
        print(e)


def locate_file(ticker):
    path = f"data/{ticker}_biztoc.json"

    if not os.path.exists(path):
        print(f"[WARN] file path not found: {path}")
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            print(f"Searched for and found json file for {ticker}")
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to read {path}: {e}")
        return None


def main():  # ran out of api calls on PARA
    try:
        for ticker in watchlist:
            biztoc_search_watchlist(ticker)
            data = locate_file(ticker)
            if data:
                convert_to_csv(data, ticker)
    except KeyboardInterrupt:
        print("Exiting gracefully...")


if __name__ == "__main__":
    main()
