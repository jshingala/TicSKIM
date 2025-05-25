import requests
import json
from config.config import BIZTOC_API_KEY


class BIZTOC:
    def __init__(self):
        self.base_url = "https://biztoc.p.rapidapi.com"
        self.headers = {
            "x-rapidapi-key": BIZTOC_API_KEY,
            "x-rapidapi-host": "biztoc.p.rapidapi.com",
        }

    def search_ticker(self, ticker):
        url = f"{self.base_url}/search"
        querystring = {"q": ticker}
        response = requests.get(url, headers=self.headers, params=querystring)
        formatted_data = json.dumps(response.json(), indent=5)
        return formatted_data

    def latest(self):
        url = f"{self.base_url}/news/latest"
        response = requests.get(url, headers=self.headers)
        formatted_data = json.dumps(response.json(), indent=5)
        return formatted_data

    def search_source(self, source):
        url = f"{self.base_url}/news/source/{source}"
        response = requests.get(url, headers=self.headers)
        formatted_data = json.dumps(response.json(), indent=5)
        return formatted_data

    def list_sources(self):
        url = f"{self.base_url}/sources"
        response = requests.get(url, headers=self.headers)
        formatted_data = json.dumps(response.json(), indent=5)
        return formatted_data
