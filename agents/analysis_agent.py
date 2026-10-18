from textblob import TextBlob


def compute_asia_tech_exposure(portfolio: dict) -> float:
    """Return the Asia-tech share of the portfolio as a percentage."""
    total = sum(portfolio.values())
    if total == 0:
        return 0.0
    asia_tech = sum(v for k, v in portfolio.items() if "AsiaTech" in k)
    return round((asia_tech / total) * 100, 2)


def get_sentiment(text: str) -> dict:
    """Analyze sentiment of the text and return a label and a reason."""
    polarity = TextBlob(text or "").sentiment.polarity

    if polarity > 0.1:
        return {"label": "positive", "reason": "positive news sentiment"}
    elif polarity < -0.1:
        return {"label": "negative", "reason": "negative news sentiment"}
    return {"label": "neutral", "reason": "mixed or minimal news sentiment"}
