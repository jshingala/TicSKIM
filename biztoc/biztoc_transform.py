import os
import uuid
from datetime import datetime
from config.spot import watchlist
import pandas as pd


def join_data(df, parent_df):
    combined_df = pd.concat([df, parent_df], ignore_index=True)
    combined_df.drop_duplicates(subset="Post_ID", keep="first", inplace=True)
    return combined_df


def convert_to_csv(data, ticker):
    info = {}
    for post in data:
        post_id = str(uuid.uuid4())
        info[post_id] = {
            "Post_ID": post_id,
            "Ticker": ticker,
            "Title": post.get("title", ""),
            "Body": post.get("body", ""),
            "Post_Date": calculate_post_date(post["published"]),
            "Upvotes": None,
            "Num_Comments": None,
        }
    df = pd.DataFrame.from_dict(
        info,
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
    path = f"data/{ticker}_biztoc.csv"
    if os.path.exists(path):
        parent_df = pd.read_csv(path)
        print(f"Updating existing biztoc csv for {ticker}")
        new_df = join_data(df, parent_df)
        new_df.to_csv(path, index=False)
        return
    print(f"Creating new biztoc csv for {ticker}")
    df.to_csv(path, index=False)


def calculate_post_date(date):
    dt = datetime.strptime(date, "%a, %d %b %Y %H:%M:%S %Z")
    formatted = dt.strftime("%Y-%m-%d")
    return formatted
