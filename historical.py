import requests
from spot import *
from config import *
import pprint
import praw
from datetime import datetime, timezone
import pandas as pd
import re
reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    user_agent="python:ticker_skimmer:v1.0",
    read_only=True
)
pp = pprint.PrettyPrinter(indent=1)
def get_historic_data(symbol):
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={API_KEY}'
    r = requests.get(url)
    data = r.json()
    return data


def get_posts(ticker):
    ticker_count = {}
    subreddits = [
    "wallstreetbets", "finance", "investing", "stocks", "StockMarket", 
    "SecurityAnalysis", "options", "daytrading", "pennystocks",
    "algotrading", "dividends", "stockpicks", "ValueInvesting", 
    "robinhood", "stocktwits", "weedstocks", "cryptocurrencies"
]
    for sub in subreddits:
        subreddit = reddit.subreddit(sub)
        for post in subreddit.search(ticker, sort='top', limit=None):
        #for post in subreddit.top(time_filter='all', limit=None):
            post_date = datetime.fromtimestamp(post.created_utc, tz=timezone.utc).strftime('%Y-%m-%d')
            title = post.title
            title_split = title.split()
            upvotes = post.score
            for token in title_split:
                if token.startswith('$'):
                    token = token[1:]
                if re.sub(r"[^\w]", "", token) == ticker:
                    if token not in ticker_count:
                        ticker_count[token] = {"Ticker": token, "Title": [title], "Post_Date": [post_date], "Upvotes": [upvotes]}
                    else:
                        ticker_count[token]["Title"].append(title)
                        ticker_count[token]["Post_Date"].append(post_date)
                        ticker_count[token]["Upvotes"].append(upvotes)


    formatted_data = []
    for symbol, data in ticker_count.items():
        for i in range(len(data["Title"])):  # Iterate over all values in lists
            formatted_data.append({
                "Ticker": symbol,
                "Title": data["Title"][i],
                "Post_Date": data["Post_Date"][i],
                "Upvotes": data["Upvotes"][i]
            })

    df = pd.DataFrame(formatted_data)
    df.to_csv(f'{ticker}_reddit_data.csv', index=False)


def launch(user_input):
    try:
        get_posts(user_input)
    except KeyboardInterrupt:
        print("Exiting gracefully...")