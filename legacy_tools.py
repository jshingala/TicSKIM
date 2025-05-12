def get_posts(ticker):
    ticker_count = {}
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
        for post in subreddit.search(ticker, sort="top", limit=10000):
            # for post in subreddit.top(time_filter='all', limit=None):
            post_date = datetime.fromtimestamp(
                post.created_utc, tz=timezone.utc
            ).strftime("%Y-%m-%d")
            post_id = post.id
            title = post.title
            title_split = title.split()
            num_comments = post.num_comments
            upvotes = post.score
            for token in title_split:
                if token.startswith("$"):
                    token = token[1:]
                if re.sub(r"[^\w]", "", token) == ticker:
                    if token not in ticker_count:
                        ticker_count[token] = {
                            "Ticker": token,
                            "Post_ID": post_id,
                            "Title": [title],
                            "Post_Date": [post_date],
                            "Upvotes": [upvotes],
                            "Num_Comments": [num_comments],
                            "Num_Mentions": 1,
                        }
                    else:
                        ticker_count[token]["Post_ID"] = post_id
                        ticker_count[token]["Title"].append(title)
                        ticker_count[token]["Post_Date"].append(post_date)
                        ticker_count[token]["Upvotes"].append(upvotes)
                        ticker_count[token]["Num_Comments"].append(num_comments)
                        ticker_count[token]["Num_Mentions"] += 1

    formatted_data = []
    for symbol, data in ticker_count.items():
        for i in range(len(data["Title"])):  # Iterate over all values in lists
            if data["Upvotes"][i] > 0 and data["Post_Date"][i] == datetime.now(
                timezone.utc
            ).strftime("%Y-%m-%d"):
                formatted_data.append(
                    {
                        "Ticker": symbol,
                        "Post_ID": data["Post_ID"],
                        "Title_Sentiment": vs.polarity_scores(data["Title"][i])[
                            "compound"
                        ],
                        "Title": data["Title"][i],
                        "Post_Date": data["Post_Date"][i],
                        "Upvotes": data["Upvotes"][i],
                        "Num_Comments": data["Num_Comments"][i],
                        "Num_Mentions": data["Num_Mentions"],
                    }
                )

    df = pd.DataFrame(formatted_data)
    df.to_csv(f"{ticker}_reddit_data.csv", index=False)

    print(f"Historical data saved to{ticker}_reddit_data.csv!")
