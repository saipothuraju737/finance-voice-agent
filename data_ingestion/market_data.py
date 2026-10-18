import yfinance as yf


def fetch_historical_prices(ticker: str, period: str = "5d", interval: str = "1d"):
    return yf.Ticker(ticker).history(period=period, interval=interval)


def fetch_stock_summary(ticker: str):
    stock = yf.Ticker(ticker)
    try:
        info = stock.info or {}
    except Exception:
        info = {}

    price = info.get("regularMarketPrice") or info.get("currentPrice")
    if price is None:
        try:
            price = stock.fast_info["last_price"]
        except Exception:
            price = None

    return {
        "symbol": info.get("symbol", ticker),
        "sector": info.get("sector"),
        "price": price,
        "marketCap": info.get("marketCap"),
        "peRatio": info.get("trailingPE"),
        "eps": info.get("trailingEps"),
    }
