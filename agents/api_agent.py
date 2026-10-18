from data_ingestion.market_data import fetch_historical_prices, fetch_stock_summary


def get_stock_data(ticker: str):
    return fetch_historical_prices(ticker)


def get_stock_summary(ticker: str):
    return fetch_stock_summary(ticker)
