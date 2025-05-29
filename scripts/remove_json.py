from config.spot import watchlist
import os

"""
script to remove unnecessary json files after they are converted to csv
"""


def cleanup(ticker):
    path = f"data/{ticker}_biztoc.json"
    if os.path.exists(path):
        try:
            os.remove(path)
            print(f"Successfully removed {path}")
        except Exception as e:
            print(e)
    else:
        print(f"{path} does not exist")


def main():
    for ticker in watchlist:
        cleanup(ticker)


if __name__ == "__main__":
    main()
