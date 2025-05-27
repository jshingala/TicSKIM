from config.spot import *
from config.config import *
import pprint
import praw
from datetime import datetime, timezone, timedelta
import pandas as pd
import re
from collections import defaultdict
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import yfinance as yf
import os
from bs4 import BeautifulSoup
import hashlib


reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    user_agent="python:ticker_skimmer:v1.0",
    read_only=True,
)
vs = SentimentIntensityAnalyzer()
pp = pprint.PrettyPrinter(indent=1, sort_dicts=False)


def search_reddit_posts(
    timeframe="all",
):  # accepted time filters are 'all', 'year', 'month', 'week', 'day', 'hour'
    assert timeframe in [
        "all",
        "year",
        "month",
        "week",
        "day",
        "hour",
    ], "Invalid timeframe. Acceptable time filters are: 'all', 'year', 'month', 'week', 'day', 'hour'"
    post_data = {}

    for sub in subreddits:
        subreddit = reddit.subreddit(sub)
        print(f"Scraping: {sub}")
        for post in subreddit.top(time_filter=timeframe):
            post_title = post.title
            post_id = post.id
            num_comments = post.num_comments
            upvotes = post.score
            post_date = datetime.fromtimestamp(post.created_utc, tz=timezone.utc).date()
            start_date = post_date
            end_date = post_date + timedelta(days=1)
            split_title = post_title.split()
            num_loopbacks = 0

            for token in split_title:
                clean_token = re.sub(r"[^\w]", "", token).upper()
                if clean_token in watchlist or (
                    token.upper() in ambiguous_watchlist and token.startswith("$")
                ):
                    print(f"Found {clean_token} in {post_title} on {post_date}")
                    unique_post_id = f"{post_id}_{clean_token}"
                    stock_data = yf.Ticker(clean_token).history(
                        period="1d",  # Example: "1d", "5d", "1mo", "3mo", "1y", "5y", "max"
                        interval="1d",  # Example: "1m", "2m", "5m", "15m", "1h", "1d", etc.
                        start=start_date.strftime(
                            "%Y-%m-%d"
                        ),  # Start date as string or datetime
                        end=end_date.strftime("%Y-%m-%d"),  # End date (exclusive)
                        auto_adjust=True,  # Adjust prices for splits/dividends
                        actions=False,
                    )
                    while stock_data.empty and num_loopbacks < 10:
                        start_date -= timedelta(days=1)
                        end_date = start_date + timedelta(days=1)
                        stock_data = yf.Ticker(clean_token).history(
                            period="1d",  # Example: "1d", "5d", "1mo", "3mo", "1y", "5y", "max"
                            interval="1d",  # Example: "1m", "2m", "5m", "15m", "1h", "1d", etc.
                            start=start_date.strftime(
                                "%Y-%m-%d"
                            ),  # Start date as string or datetime
                            end=end_date.strftime("%Y-%m-%d"),  # End date (exclusive)
                            auto_adjust=True,  # Adjust prices for splits/dividends
                            actions=False,
                        )
                        num_loopbacks += 1
                    if not stock_data.empty:
                        post_data[unique_post_id] = {
                            "Ticker": clean_token,
                            "Title": post_title,
                            "Title_Sentiment": vs.polarity_scores(post_title)[
                                "compound"
                            ],
                            "Title_Sentiment_Positive": vs.polarity_scores(post_title)[
                                "pos"
                            ],
                            "Title_Sentiment_Negative": vs.polarity_scores(post_title)[
                                "neg"
                            ],
                            "Title_Sentiment_Neutral": vs.polarity_scores(post_title)[
                                "neu"
                            ],
                            "Post_ID": unique_post_id,
                            "Raw_Post_ID": post_id,
                            "Post_Date": start_date,
                            "Upvotes": upvotes,
                            "Num_Comments": num_comments,
                            "Closing_Price": stock_data["Close"].iloc[0],
                            "Closing_Price_Date": end_date.strftime("%Y-%m-%d"),
                            "Subreddit": sub,
                            "Source": "Reddit",
                        }
    df = pd.DataFrame.from_dict(
        post_data,
        orient="index",
        columns=[
            "Post_ID",
            "Raw_Post_ID",
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
            "Subreddit",
            "Source",
        ],
    )
    df.to_csv("data/stock_info.csv", index=False)

    return df


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
    df = pd.read_csv("data/stock_info.csv")
    today_df = df[df["Post_Date"] == today]
    today_df.sort_values("Title_Sentiment", ascending=False, inplace=True)
    return today_df[["Ticker", "Title_Sentiment"]][:5]


def get_master_df(master_path="data/stock_info.csv"):
    if os.path.exists(master_path):
        print("found master_path")
        # print("reddit data exists")
        # pp.pprint(pd.read_csv(master_path)) #just making sure the current saved csv is returned correctly
        return pd.read_csv(master_path)
    else:
        return pd.DataFrame()


def join_data(various, master_path="data/reddit_data.csv"):
    master_df = get_master_df(master_path)
    df_combined = pd.concat(
        [various, master_df], ignore_index=True
    )  # combine yfinance df with reddit df
    # df_combined["Post_Date"] = pd.to_datetime(df_combined["Post_Date"], errors="coerce")
    df_combined["Post_Date"] = pd.to_datetime(df_combined["Post_Date"], errors="coerce")
    df_combined = df_combined.sort_values(
        "Post_Date", ascending=False
    )  # sort by post_date
    df_combined = df_combined.drop_duplicates(
        subset="Post_ID", keep="first"
    )  # drop duplicate post_id rows

    df_combined.to_csv("data/reddit_data.csv", index=False)


def create_historical_df():
    for tf in timeframes[: len(timeframes)]:
        various = search_reddit_posts(tf)
        join_data(various)


def main():
    try:
        search_reddit_posts()
        create_historical_df()
        daily_df = search_reddit_posts("day")
        join_data(daily_df)
        # df_today = search_posts()
        # join_data(df_today)
    except KeyboardInterrupt:
        print("Exiting gracefully...")


if __name__ == "__main__":
    main()
