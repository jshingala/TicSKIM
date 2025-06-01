import requests
from config.config import ALPHAVANTAGE_API_KEY
import json


class ALPHAVANTAGE:
    def __init__(self):

        self.url = "https://www.alphavantage.co/query"

    def search_ticker(
        self, ticker, limit=100, sort="RELEVANCE", function="NEWS_SENTIMENT"
    ):
        params = {
            "function": function.upper(),
            "tickers": ticker,
            "limit": limit,
            "sort": sort.upper(),
            "apikey": ALPHAVANTAGE_API_KEY,
        }
        response = requests.get(self.url, params=params)
        data = response.json()
        formatted_data = json.dumps(data, indent=5)
        return formatted_data
