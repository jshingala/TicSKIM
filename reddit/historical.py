import requests
from config.spot import *
from config.config import *
import pprint
import praw
from datetime import datetime, timezone
import pandas as pd
import re
from collections import defaultdict
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import yfinance as yf
import os
from bs4 import BeautifulSoup
import html
import hashlib


reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    user_agent="python:ticker_skimmer:v1.0",
    read_only=True,
)
vs = SentimentIntensityAnalyzer()
pp = pprint.PrettyPrinter(indent=1, sort_dicts=False)


def get_historic_data(symbol):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={API_KEY}"

    r = requests.get(url)
    data = r.json()
    return data


def scrape_yfinance():
    url = "https://finance.yahoo.com/topic/stock-market-news/"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Connection": "keep-alive",
    }

    response = requests.get(url, headers=headers)
    doc = BeautifulSoup(response.text, "html.parser")
    article_info = {}
    li_tags = doc.find_all("li")
    for li in li_tags:
        h3 = li.find("h3")
        if not h3 or not h3.text.strip():
            continue
        article_title = h3.text.strip()
        sentiment = vs.polarity_scores(article_title)
        span = li.find_all("span", class_="symbol")  # parameter is class_ not class
        source_div = li.find("div", class_="publishing")
        if source_div:
            source_split = source_div.text.split(
                "•"
            )  # outputs something like ["Yahoo", "5 hours ago"] or ["Bloomberg", "yesterday"]
            source_date = calculate_post_date(source_split[-1])
        if h3 and span:
            for ticker in span:
                if ticker.text.strip():
                    ticker_name = ticker.text.strip()
                    if not ticker_name or not source_date:
                        continue
                    title_hash = hashlib.md5(article_title.encode()).hexdigest()[:8]
                    article_id = f"{ticker_name}_yahoo_{source_date}_{title_hash}"
                    stock_data = yf.Ticker(ticker_name)
                    article_info[article_id] = {
                        "Post_ID": article_id,
                        "Ticker": ticker_name,
                        "Title": article_title,
                        "Title_Sentiment": sentiment["compound"],
                        "Title_Sentiment_Positive": sentiment["pos"],
                        "Title_Sentiment_Negative": sentiment["neg"],
                        "Title_Sentiment_Neutral": sentiment["neu"],
                        "Post_Date": source_date,
                        "Upvotes": None,
                        "Num_Comments": None,
                        "Closing_Price": stock_data.history(period="1d", interval="1d")[
                            "Close"
                        ].iloc[0],
                        "Closing_Price_Date": stock_data.history(
                            period="1d", interval="1d"
                        )
                        .index[0]
                        .strftime("%Y-%m-%d"),
                        "Source": source_split[0],
                    }
    df = pd.DataFrame.from_dict(
        article_info,
        orient="index",
        columns=[
            "Post_ID",
            "Ticker",
            "Title",
            "Title_Sentiment",
            "Title_Sentiment_Positive",
            "Title_Sentiment_Negative",
            "Title_Sentiment_Neutral",
            "Post_Date",
            "Upvotes",
            "Num_Comments",
            "Closing_Price",
            "Closing_Price_Date",
            "Source",
        ],
    )
    pp.pprint(df)
    return df


def calculate_post_date(str):
    if "minutes" in str:
        return datetime.now().strftime("Y-%m-%d")
    elif "hours" in str:
        if int(datetime.now().strftime("%H")) - int(str[1:3]) >= 0:
            return datetime.now().strftime("%Y-%m-%d")
    else:
        return None


def search_posts():
    post_data = {}
    subreddits = [
        "wallstreetbets",
        "finance",
        "investing",
        "stocks",
        "StockMarket",
        "SecurityAnalysis",
        "options",
        "daytrading",
        "pennystocks",
        "algotrading",
        "dividends",
        "stockpicks",
        "ValueInvesting",
        "robinhood",
        "stocktwits",
        "weedstocks",
        "cryptocurrencies",
    ]

    for sub in subreddits:
        subreddit = reddit.subreddit(sub)
        print(f"Scraping: {sub}")
        for post in subreddit.top(time_filter="day"):
            post_title = post.title
            post_id = post.id
            num_comments = post.num_comments
            upvotes = post.score
            post_date = datetime.fromtimestamp(
                post.created_utc, tz=timezone.utc
            ).strftime("%Y-%m-%d")
            split_title = post_title.split()

            for token in split_title:
                clean_token = re.sub(r"[^\w]", "", token).upper()
                if clean_token in watchlist or (
                    token.upper() in ambiguous_watchlist and token.startswith("$")
                ):
                    print(f"Found {clean_token} in {post_title} on {post_date}")
                    stock_data = yf.Ticker(clean_token)

                    post_data[post_id] = {
                        "Ticker": clean_token,
                        "Title": post_title,
                        "Title_Sentiment": vs.polarity_scores(post_title)["compound"],
                        "Title_Sentiment_Positive": vs.polarity_scores(post_title)[
                            "pos"
                        ],
                        "Title_Sentiment_Negative": vs.polarity_scores(post_title)[
                            "neg"
                        ],
                        "Title_Sentiment_Neutral": vs.polarity_scores(post_title)[
                            "neu"
                        ],
                        "Post_ID": post_id,
                        "Post_Date": post_date,
                        "Upvotes": upvotes,
                        "Num_Comments": num_comments,
                        "Closing_Price": stock_data.history(period="1d", interval="1d")[
                            "Close"
                        ].iloc[0],
                        "Closing_Price_Date": stock_data.history(
                            period="1d", interval="1d"
                        )
                        .index[0]
                        .strftime("%Y-%m-%d"),
                        "Source": "Reddit",
                    }
    df = pd.DataFrame.from_dict(
        post_data,
        orient="index",
        columns=[
            "Post_ID",
            "Ticker",
            "Title",
            "Title_Sentiment",
            "Title_Sentiment_Positive",
            "Title_Sentiment_Negative",
            "Title_Sentiment_Neutral",
            "Post_Date",
            "Upvotes",
            "Num_Comments",
            "Closing_Price",
            "Closing_Price_Date",
            "Source",
        ],
    )
    df.to_csv("stock_info.csv", index=False)

    return df


def get_master_df(master_path="reddit_data.csv"):
    if os.path.exists(master_path):
        # print("reddit data exists")
        # pp.pprint(pd.read_csv(master_path)) #just making sure the current saved csv is returned correctly
        return pd.read_csv(master_path)
    else:
        return pd.DataFrame()


def join_data(df_today, master_path="stock_info.csv"):
    master_df = get_master_df("reddit_data.csv")
    yfinance_df = scrape_yfinance()
    df_combined = pd.concat(
        [yfinance_df, df_today], ignore_index=True
    )  # combine yfinance df with reddit df
    df_combined = pd.concat(
        [master_df, df_combined], ignore_index=True
    )  # combine previously combined df with whatever is at reddit_data.csv
    df_combined["Post_Date"] = pd.to_datetime(df_combined["Post_Date"], errors="coerce")
    df_combined = df_combined.sort_values(
        "Post_Date", ascending=False
    )  # sort by post_date
    df_combined = df_combined.drop_duplicates(
        subset="Post_ID", keep="first"
    )  # drop duplicate post_id rows

    df_combined.to_csv(master_path, index=False)


def get_hype():
    ticker_count = defaultdict(
        lambda: defaultdict(
            lambda: {
                "Total_Mentions": 0,
                "Total_Upvotes": 0,
                "Total_Comments": 0,
                "Post_IDs": [],
                "Titles": [],
            }
        )
    )
    subreddits = [
        "wallstreetbets",
        "finance",
        "investing",
        "stocks",
        "StockMarket",
        "SecurityAnalysis",
        "options",
        "daytrading",
        "pennystocks",
        "algotrading",
        "dividends",
        "stockpicks",
        "ValueInvesting",
        "robinhood",
        "stocktwits",
        "weedstocks",
        "cryptocurrencies",
    ]

    for sub in subreddits:
        subreddit = reddit.subreddit(sub)
        print(f"Scraping: {sub}")
        for post in subreddit.hot(limit=10000):
            post_title = post.title
            post_id = post.id
            num_comments = post.num_comments
            upvotes = post.score
            post_date = datetime.fromtimestamp(
                post.created_utc, tz=timezone.utc
            ).strftime("%Y-%m-%d")
            split_title = post_title.split()
            for token in split_title:
                clean_token = re.sub(r"[^\w]", "", token).upper()
                if clean_token in watchlist:
                    ticker_data = ticker_count[post_date][clean_token]

                    ticker_data["Titles"].append(post_title)
                    ticker_data["Post_IDs"].append(post_id)
                    ticker_data["Total_Mentions"] += 1
                    ticker_data["Total_Upvotes"] += upvotes
                    ticker_data["Total_Comments"] += num_comments

        # Convert to DataFrame
    all_data = []
    for date, tickers in ticker_count.items():
        for ticker, data in tickers.items():
            all_data.append(
                [
                    date,
                    ticker,
                    data["Total_Mentions"],
                    data["Total_Upvotes"],
                    data["Total_Comments"],
                    ", ".join(data["Post_IDs"]),
                    ", ".join(data["Titles"]),
                ]
            )

    df = pd.DataFrame(
        all_data,
        columns=[
            "Post_Date",
            "Ticker",
            "Total_Mentions",
            "Total_Upvotes",
            "Total_Comments",
            "Post_IDs",
            "Titles",
        ],
    )
    df.to_csv("reddit_hype.csv", index=False)

    print(f"Hype data saved to reddit_hype.csv!")


def get_top_sentiment():
    today = datetime.now().strftime("%Y-%m-%d")
    df = pd.read_csv("stock_info.csv")
    today_df = df[df["Post_Date"] == today]
    today_df.sort_values("Title_Sentiment", ascending=False, inplace=True)
    return today_df[["Ticker", "Title_Sentiment"]][:5]


def main():
    try:
        df_today = search_posts()
        join_data(df_today)
    except KeyboardInterrupt:
        print("Exiting gracefully...")


if __name__ == "__main__":
    main()


# import requests
# from spot import *
# from config import *
# import pprint
# import praw
# from datetime import datetime, timezone
# import pandas as pd
# import re
# reddit = praw.Reddit(
#     client_id=CLIENT_ID,
#     client_secret=CLIENT_SECRET,
#     user_agent="python:ticker_skimmer:v1.0",
#     read_only=True
# )
# pp = pprint.PrettyPrinter(indent=1)
# def get_historic_data(symbol):
#     url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={API_KEY}'
#     r = requests.get(url)
#     data = r.json()
#     return data


# def get_posts(ticker):
#     ticker_count = {}
#     subreddits = [
#     "wallstreetbets", "finance", "investing", "stocks", "StockMarket",
#     "SecurityAnalysis", "options", "daytrading", "pennystocks",
#     "algotrading", "dividends", "stockpicks", "ValueInvesting",
#     "robinhood", "stocktwits", "weedstocks", "cryptocurrencies"
# ]
#     for sub in subreddits:
#         subreddit = reddit.subreddit(sub)
#         for post in subreddit.search(ticker, sort='top', limit=None):
#         #for post in subreddit.top(time_filter='all', limit=None):
#             post_date = datetime.fromtimestamp(post.created_utc, tz=timezone.utc).strftime('%Y-%m-%d')
#             title = post.title
#             title_split = title.split()
#             upvotes = post.score
#             for token in title_split:
#                 if token.startswith('$'):
#                     token = token[1:]
#                 if re.sub(r"[^\w]", "", token) == ticker:
#                     if token not in ticker_count:
#                         ticker_count[token] = {"Ticker": token, "Title": [title], "Post_Date": [post_date], "Upvotes": [upvotes]}
#                     else:
#                         ticker_count[token]["Title"].append(title)
#                         ticker_count[token]["Post_Date"].append(post_date)
#                         ticker_count[token]["Upvotes"].append(upvotes)


#     formatted_data = []
#     for symbol, data in ticker_count.items():
#         for i in range(len(data["Title"])):  # Iterate over all values in lists
#             formatted_data.append({
#                 "Ticker": symbol,
#                 "Title": data["Title"][i],
#                 "Post_Date": data["Post_Date"][i],
#                 "Upvotes": data["Upvotes"][i]
#             })

#     df = pd.DataFrame(formatted_data)
#     df.to_csv(f'{ticker}_reddit_data.csv', index=False)


# def launch(user_input):
#     try:
#         get_posts(user_input)
#     except KeyboardInterrupt:
#         print("Exiting gracefully...")
