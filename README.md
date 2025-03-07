 # Stock Predictor with Social Media Sentiment Analysis

A machine learning system for predicting stock prices using both historical market data and social media sentiment from Reddit.

## Overview

This project combines traditional stock market data with Reddit sentiment analysis to predict stock price movements. It uses LSTM (Long Short-Term Memory) neural networks to process time-series financial data enhanced with social sentiment features.

## Features

- Historical stock data retrieval from Yahoo Finance and Alpha Vantage
- Reddit post scraping from finance/investing subreddits
- Sentiment analysis using pre-trained NLP models
- Stock price prediction using bidirectional LSTM neural networks
- Interactive visualization and analysis

## Project Structure

```
stock-predictor/
├── config.py                 # API keys and configuration (create this file)
├── historical.py             # Reddit data scraper and historical data functions
├── spot.py                   # Stock watchlist definitions
├── requirements.txt          # Project dependencies
├── .gitignore                # Git ignore file
└── notebooks/
    └── Ticker_Stock_Predictor.ipynb  # Main analysis notebook
```

## Setup Instructions

1. Clone the repository:
```bash
git clone https://github.com/yourusername/stock-predictor.git
cd stock-predictor
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `config.py` file with your API keys:
```python
# Alpha Vantage API
API_KEY = "your_alphavantage_api_key"

# Reddit API
CLIENT_ID = "your_reddit_client_id"
CLIENT_SECRET = "your_reddit_client_secret"
```

4. Run the Jupyter notebook:
```bash
jupyter notebook notebooks/Ticker_Stock_Predictor.ipynb
```

## How It Works

1. **Data Collection**: The system retrieves historical market data and scrapes Reddit posts related to the specified ticker.
2. **Sentiment Analysis**: Reddit post titles are analyzed with a pre-trained NLP model to extract sentiment scores.
3. **Feature Engineering**: Market data is combined with sentiment scores and normalized.
4. **Model Training**: A bidirectional LSTM model is trained on the combined dataset.
5. **Prediction**: The model predicts future stock prices based on recent market data and sentiment.

## Requirements

- Python 3.7+
- TensorFlow 2.x
- pandas
- numpy
- matplotlib
- seaborn
- praw (Python Reddit API Wrapper)
- transformers (Hugging Face)
- yfinance

## License

[MIT License](LICENSE)
