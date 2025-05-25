# before run this, install APIs:
# pip install matplotlib
# pip install yfinance
# pip install seaborn
# pip install scikit-learn
# pip install praw
# pip install pipeline
# pip install transformers
# pip install tensorflow
# pip install torch

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import io
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt
import yfinance as yf
from transformers import pipeline

import os
from datetime import datetime, timedelta

import reddit.historical as historical  # custom file

global_ticker = ""
visualize = True


class StockDF:
    def loadDFbyTicker():
        global global_ticker
        global_ticker = input("Enter the Ticker of the stock: ").strip().upper()

        # Get stock data from Yahoo Finance
        stock_data = yf.Ticker(global_ticker)
        df = stock_data.history(period="max")  # we can adjust the term

        if df.shape[0] < 100:  # we need at least 100 rows
            raise ValueError("DataFrame has less than 100 rows.")

        df.fillna("?", inplace=True)

        return df

    def manageNull(df):  ###need to work on this
        return df


class SentimentLoad:
    def __init__(self):
        if not is_file_recent(global_ticker):
            historical.launch(global_ticker)
        self.sentiment_task = pipeline(
            "text-classification",
            model="cardiffnlp/twitter-roberta-base-sentiment-latest",
        )

    def run(self):
        df = self.getSentiments(self.getPosts())
        return self.simplifyDF(df)

    def getPosts(self):
        posts = pd.read_csv("./" + global_ticker + "_reddit_data.csv", na_values=False)
        posts = posts[["Title", "Post_Date", "Upvotes"]]
        posts = posts.sort_values(by="Post_Date", ascending=True)

        return posts

    def getSentiments(self, posts):
        sentiments = posts["Title"].apply(self.sentiment_task)

        sentiment_df = sentiments.to_frame(name="Sentiments")
        sentiment_df["label"] = sentiment_df["Sentiments"].apply(
            lambda x: x[0]["label"]
        )
        sentiment_df["score"] = sentiment_df["Sentiments"].apply(
            lambda x: x[0]["score"]
        )
        sentiment_df = sentiment_df.drop("Sentiments", axis=1)

        sentiment_df["sentiment_value"] = sentiment_df.apply(
            self.simplify_sentiment, axis=1
        )  # positive == score, negative == -score, neutral -= 0.5
        df = pd.concat([posts, sentiment_df], axis=1)

        if visualize:
            print(df)

        return df

    def simplify_sentiment(self, row):
        sentiment_type = row["label"]
        sentiment_value = row["score"]

        if sentiment_type == "negative":
            sentiment_value = -sentiment_value
        elif sentiment_type == "neutral":
            sentiment_value -= 0.5

        return sentiment_value

    def simplifyDF(self, df):
        df = df.drop("Title", axis=1)
        df = df.dropna()  # remove null values (either no date or title)

        # Compress the duplicates by averaging 'Upvotes' and 'sentiment_value' cloumns
        grouped_df = (
            df.groupby("Post_Date")
            .agg(
                {
                    "Upvotes": "mean",  # Calculate the average of Upvotes
                    "sentiment_value": "mean",  # Calculate the average of sentiment scores
                }
            )
            .reset_index()
        )

        # Weight sentiment_value by Upvotes
        grouped_df["log_weighted_sentiment"] = grouped_df["sentiment_value"] * np.log(
            grouped_df["Upvotes"]
        )
        grouped_df["weighted_sentiment"] = (
            grouped_df["sentiment_value"] * grouped_df["log_weighted_sentiment"]
        )

        new_sentiment_df = grouped_df[["Post_Date", "log_weighted_sentiment"]]
        new_sentiment_df = new_sentiment_df.rename(
            columns={"Post_Date": "date", "log_weighted_sentiment": "sentiment"}
        )

        return new_sentiment_df  # Final form of sentiment dataframe


def visualization(df):
    plt.figure(figsize=(15, 6))  # size of the graph
    plt.plot(df["Close"])
    plt.title(global_ticker + " Company stock price")
    plt.xlabel("Days")
    plt.ylabel("Price")
    plt.show()


def merge_df(stock_df, sentiment_df):
    new_df = stock_df[
        ["Open", "High", "Low", "Close", "Volume"]
    ]  # Drop the unnecessary columns

    sentiment_df["date"] = pd.to_datetime(sentiment_df["date"])
    new_df.index = pd.to_datetime(new_df.index).tz_localize(None)

    new_df = new_df.merge(
        sentiment_df, left_index=True, right_on="date", how="left"
    )  # how='left': keeping all data of new_df, how='right': merge data that only exist in new_sentiment_df
    new_df["sentiment"] = new_df["sentiment"].fillna(
        0
    )  # if there is no sentiment data on the date, fill it with 0

    return new_df


def is_file_recent(global_ticker):
    file_path = f"./{global_ticker}_reddit_data.csv"
    limit_days = 5

    if not os.path.exists(file_path):
        print(f"{file_path} does not exist.")
        return False

    # Get file's last modified time
    last_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
    modify_limit = datetime.now() - timedelta(days=limit_days)

    if last_modified >= modify_limit:
        print(
            f"'{global_ticker}_reddit_data.csv' is created in {limit_days} already."
            + "\nWill create sentiment DataFrame immediately"
        )

    return last_modified >= modify_limit  # if it's modified in {modify_limit} days


def main():
    # this is main method
    stock_df = StockDF.loadDFbyTicker()

    if stock_df.isnull().any(axis=1).any():
        stock_df = StockDF.manageNull(stock_df)

    print(stock_df)

    sentiment_instance = SentimentLoad()
    sentiment_df = sentiment_instance.run()

    df = merge_df(stock_df, sentiment_df)

    if visualize:
        print(df[df["sentiment"] > 0.0])  # print where sentiment is valid
        visualization(stock_df)


if __name__ == "__main__":
    main()
