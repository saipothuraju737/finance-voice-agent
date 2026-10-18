import json
from pathlib import Path
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from agents import analysis_agent, api_agent, language_agent, retriever_agent
from data_ingestion.document_loader import chunk_text, load_txt_documents

BASE_DIR = Path(__file__).resolve().parent.parent
NEWS_DIR = BASE_DIR / "data" / "news"
app = FastAPI(title="FinSight AI Finance Voice Agent", version="2.0")

_texts = load_txt_documents(str(NEWS_DIR))
_chunks = [c for t in _texts for c in chunk_text(t)]
index, source_texts = retriever_agent.embed_and_store(_chunks)

# These are lookup defaults, not a claim that all listed stocks have live data.
COMPANIES = ["TSM", "005930.KS", "AAPL", "GOOGL"]


def _format_stock(ticker, data):
    if not data:
        return f"{ticker}: market data unavailable from the configured provider."
    fields = []
    labels = [("price", "latest available price"), ("sector", "sector"), ("marketCap", "market capitalization"), ("peRatio", "trailing P/E"), ("eps", "trailing EPS")]
    for key, label in labels:
        value = data.get(key)
        if value is not None:
            fields.append(f"{label}: {value}")
    return f"{ticker}: " + ("; ".join(fields) if fields else "no usable quote fields returned") + "."


@app.get("/")
def root():
    return {"status": "ok", "service": "FinSight AI", "endpoints": ["/brief?query=...", "/health"]}


@app.get("/health")
def health():
    return {"status": "ok", "news_documents_loaded": len(source_texts), "timestamp_utc": datetime.now(timezone.utc).isoformat()}



@app.get("/stock-history")
def stock_history(ticker: str = "AAPL", period: str = "6mo", interval: str = "1d"):
    """Return historical OHLCV rows for frontend charts; data can be delayed."""
    allowed_periods = {"1mo", "3mo", "6mo", "1y", "2y", "5y"}
    allowed_intervals = {"1d", "1wk", "1mo"}
    ticker = ticker.strip().upper()
    if period not in allowed_periods or interval not in allowed_intervals:
        return JSONResponse(status_code=400, content={"error": "Unsupported period or interval."})
    try:
        import yfinance as yf
        frame = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=False)
        if frame is None or frame.empty:
            return {"ticker": ticker, "history": [], "source": "Yahoo Finance via yfinance", "note": "No history returned."}
        frame = frame.reset_index()
        date_col = "Date" if "Date" in frame.columns else "Datetime"
        rows = []
        for _, row in frame.iterrows():
            stamp = row.get(date_col)
            rows.append({
                "date": stamp.isoformat() if hasattr(stamp, "isoformat") else str(stamp),
                "open": _safe_number(row.get("Open")),
                "high": _safe_number(row.get("High")),
                "low": _safe_number(row.get("Low")),
                "close": _safe_number(row.get("Close")),
                "volume": _safe_number(row.get("Volume")) or 0,
            })
        return {"ticker": ticker, "history": rows, "source": "Yahoo Finance via yfinance", "note": "Historical data may be delayed or revised."}
    except Exception as exc:
        print(f"[HISTORY ERROR] {ticker}: {exc}")
        return JSONResponse(status_code=502, content={"error": f"Historical market data unavailable for {ticker}: {type(exc).__name__}"})


def _safe_number(value):
    try:
        number = float(value)
        if number != number or number in (float("inf"), float("-inf")):
            return None
        return number
    except (TypeError, ValueError):
        return None

@app.get("/brief")
def morning_brief(query: str = "Asia tech earnings"):
    try:
        query = query.strip() or "Asia tech earnings"
        lower_query = query.lower()
        stock_details = []
        # A single-stock query receives focused information; broad market queries include a compact watchlist.
        ticker_map = {
            "apple": "AAPL", "aapl": "AAPL", "google": "GOOGL", "alphabet": "GOOGL", "googl": "GOOGL",
            "tsmc": "TSM", "tsm": "TSM", "samsung": "005930.KS", "005930": "005930.KS",
            "microsoft": "MSFT", "msft": "MSFT", "tcs": "TCS.NS", "infosys": "INFY.NS", "infy": "INFY.NS"
        }
        selected = list(dict.fromkeys(t for word, t in ticker_map.items() if word in lower_query))
        if not selected:
            selected = COMPANIES
        for ticker in selected[:5]:
            try:
                data = api_agent.get_stock_summary(ticker)
                stock_details.append(_format_stock(ticker, data))
            except Exception as exc:
                stock_details.append(f"{ticker}: data lookup failed ({type(exc).__name__}).")

        retrieved_docs = retriever_agent.retrieve_top_k(query, index, source_texts)
        news_summary = "\n".join(retrieved_docs) if retrieved_docs else "No relevant local news documents were retrieved."
        sentiment = analysis_agent.get_sentiment(news_summary)
        facts = (
            f"User question: {query}\n"
            f"Data retrieval timestamp (UTC): {datetime.now(timezone.utc).isoformat()}\n"
            f"Latest available stock fields from Yahoo Finance/yfinance (may be delayed; unavailable fields omitted):\n"
            + "\n".join(stock_details)
            + f"\nSentiment of retrieved text: {sentiment.get('label', 'neutral')} ({sentiment.get('reason', 'not enough text')}).\n"
            f"News retrieval note: these are documents bundled locally with this project, not guaranteed live news:\n{news_summary}\n\n"
            "Important: No analyst-consensus estimates or verified actual EPS values were provided. Do not invent earnings surprises, daily percentage changes, portfolio AUM/allocation, or current-market claims. Explicitly say when a requested value is unavailable. Distinguish last available quote from today's live price. Give a clear, detailed answer in headings/bullets when useful, explain financial terms simply, identify the data timestamp and source limitations, and do not give personalized investment advice."
        )
        brief = language_agent.generate_brief(facts)
        if not brief:
            brief = facts
        return {"brief": brief, "timestamp_utc": datetime.now(timezone.utc).isoformat(), "source_note": "Yahoo Finance via yfinance for available quote fields; news retrieval uses bundled local documents."}
    except Exception as exc:
        print(f"[SERVER ERROR] {exc}")
        return JSONResponse(status_code=500, content={"error": str(exc)})
