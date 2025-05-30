from config.spot import *
from config.config import *
import pprint
import praw
import prawcore
from praw.exceptions import RedditAPIException
from datetime import datetime, timezone, timedelta
import pandas as pd
import re
import os
import time


reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    user_agent="python:ticker_skimmer:v1.0",
    read_only=True,
    ratelimit_seconds=300,
)
pp = pprint.PrettyPrinter(indent=1, sort_dicts=False)


def is_company_name_in_title(val, title):
    if val in title:
        return True


# Searches top posts from each subreddit, posts are filtered out by matching ticker symbols or company names to tokenized post titles
def search_top_posts_by_subreddit(
    timeframe,
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
            post_body = post.selftext
            post_id = post.id
            num_comments = post.num_comments
            upvotes = post.score
            post_date = datetime.fromtimestamp(
                post.created_utc, tz=timezone.utc
            ).strftime("%Y-%m-%d")
            split_title = post_title.split()

            for t, val in watchlist.items():
                if val in post_title:
                    unique_post_id = f"{post_id}_{val}"
                    post_data[unique_post_id] = {
                        "Post_ID": unique_post_id,
                        "Ticker": t,
                        "Title": post_title,
                        "Body": post_body,
                        "Post_Date": post_date,
                        "Upvotes": upvotes,
                        "Num_Comments": num_comments,
                    }

            for token in split_title:
                clean_token = re.sub(r"[^\w]", "", token).upper()
                if clean_token in watchlist or (
                    token.upper() in ambiguous_watchlist and token.startswith("$")
                ):
                    print(f"Found {clean_token} in {post_title} on {post_date}")
                    unique_post_id = f"{post_id}_{clean_token}"

                    post_data[unique_post_id] = {
                        "Post_ID": unique_post_id,
                        "Ticker": clean_token,
                        "Title": post_title,
                        "Body": post_body,
                        "Post_Date": post_date,
                        "Upvotes": upvotes,
                        "Num_Comments": num_comments,
                    }
    df = pd.DataFrame.from_dict(
        post_data,
        orient="index",
        columns=[
            "Post_ID",
            "Ticker",
            "Title",
            "Body",
            "Post_Date",
            "Upvotes",
            "Num_Comments",
        ],
    )
    df.to_csv("data/stock_info.csv", index=False)

    return df


def search_ticker(
    ticker,
):  # Builds csv for a specific ticker by searching multiple subreddits using keyword ticker
    for sub in subreddits:
        subreddit = reddit.subreddit(sub)
        for tf in timeframes:
            print(f"Searching {sub} for {ticker} in timeframe {tf}")
            for post in subreddit.search(
                query=ticker, time_filter=tf, sort="relevance"
            ):
                unique_id = f"{post.id}_{ticker}"
                title = post.title
                post_body = post.selftext
                post_date = datetime.fromtimestamp(
                    post.created_utc, tz=timezone.utc
                ).strftime("%Y-%m-%d")
                upvotes = post.score
                num_comments = post.num_comments
                post_data[unique_id] = {
                    "Post_ID": unique_id,
                    "Ticker": ticker,
                    "Title": title,
                    "Body": post_body,
                    "Post_Date": post_date,
                    "Upvotes": upvotes,
                    "Num_Comments": num_comments,
                }
                print(f"Found {ticker} in {title}")
    df = pd.DataFrame.from_dict(
        post_data,
        orient="index",
        columns=[
            "Post_ID",
            "Ticker",
            "Title",
            "Body",
            "Post_Date",
            "Upvotes",
            "Num_Comments",
        ],
    )
    pattern = rf"(?<![A-Za-z0-9])\$?{ticker}(?![A-Za-z0-9])"
    company_name = get_company_name(ticker)
    rows_to_drop = []
    for idx, row in df.iterrows():
        if not (
            re.search(pattern, row["Title"], re.IGNORECASE)
            or company_name.lower() in row["Title"].lower()
        ):
            rows_to_drop.append(idx)
    df.drop(rows_to_drop, inplace=True)
    tickers_with_csv = get_data_list()
    if ticker in tickers_with_csv:
        join_data(
            df,
            master_path=f"data/{ticker}_reddit_data.csv",
            ticker=ticker,
        )
    else:
        df.to_csv(f"data/{ticker}_reddit_data.csv", index=False)
    return df


def get_company_name(ticker):
    return watchlist.get(ticker)


def get_top_sentiment():
    today = datetime.now().strftime("%Y-%m-%d")
    df = pd.read_csv("data/stock_info.csv")
    today_df = df[df["Post_Date"] == today]
    today_df.sort_values("Title_Sentiment", ascending=False, inplace=True)
    return today_df[["Ticker", "Title_Sentiment"]][:5]


def get_master_df(master_path="data/stock_info.csv"):
    if os.path.exists(master_path):
        print("found master_path")
        return pd.read_csv(master_path)
    else:
        return pd.DataFrame()


def join_data(
    various, master_path="data/reddit_data.csv", ticker=None
):  # Used to join two csv files on post_id
    master_df = get_master_df(master_path)
    df_combined = pd.concat(
        [various, master_df], ignore_index=True
    )  # combine yfinance df with reddit df
    df_combined["Post_Date"] = pd.to_datetime(df_combined["Post_Date"], errors="coerce")
    df_combined = df_combined.sort_values(
        "Post_Date", ascending=False
    )  # sort by post_date
    df_combined = df_combined.drop_duplicates(
        subset="Post_ID", keep="last"
    )  # drop duplicate post_id rows
    if not ticker:
        df_combined.to_csv(f"data/reddit_data.csv")
        return
    df_combined.to_csv(f"data/{ticker}_reddit_data.csv", index=False)


def create_historical_df():  # only use if reddit_data.csv gets deleted - builds a baseline of top posts (cheaper than searching by ticker, but limited results)
    for tf in timeframes:
        various = search_top_posts_by_subreddit(tf)
        join_data(various)


def create_df_by_ticker():  # loops over reddit_data.csv (created from create_historical_df) and separates it into ticker specific files
    df = pd.read_csv("data/reddit_data.csv")
    for t in watchlist.keys():
        tick_dict = {}
        for _, row in df.iterrows():
            if row["Ticker"] == t:
                tick_dict[row["Post_ID"]] = {
                    "Post_ID": row["Post_ID"],
                    "Ticker": row["Ticker"],
                    "Title": row["Title"],
                    "Body": row["Body"],
                    "Post_Date": row["Post_Date"],
                    "Upvotes": row["Upvotes"],
                    "Num_Comments": row["Num_Comments"],
                }
        tick_df = pd.DataFrame.from_dict(
            tick_dict,
            orient="index",
            columns=[
                "Post_ID",
                "Ticker",
                "Title",
                "Body",
                "Post_Date",
                "Upvotes",
                "Num_Comments",
            ],
        )
        if not tick_df.empty:
            tick_df.to_csv(f"data/{t}_reddit_data.csv", index=False)


def get_data_list():  # Returns a list of all tickers that have a reddit_data.csv file in data directory
    list_dir = os.listdir("data/")
    lst = []

    for dir in list_dir:
        lst.append(dir.split("_")[0])

    return lst


def search_all_tickers():  # Uses PRAW's search function to search for every ticker in watchlist
    tickers = list(watchlist)
    failed_tickers = []

    for i, ticker in enumerate(tickers):
        try:
            search_ticker(ticker)
            time.sleep(10)
        except RedditAPIException as e:
            print(f"[{ticker}] Reddit API exception at index {i}: {e}")
            failed_tickers.append(ticker)
            time.sleep(600)  # back off for 10 minutes
        except prawcore.exceptions.RequestException as e:
            print(f"[{ticker}] Request failed at index {i}: {e}")
            failed_tickers.append(ticker)
            time.sleep(60)  # fallback pause for unknown failures
        except Exception as e:
            print(f"[{ticker}] Unexpected error at index {i}: {e}")
            failed_tickers.append(ticker)
            time.sleep(30)

        if failed_tickers:
            print(f"Tickers that still need to be executed: {failed_tickers}")


def main():
    try:
        search_all_tickers()
    except KeyboardInterrupt:
        print("Exiting gracefully...")


if __name__ == "__main__":
    main()
