import requests
from bs4 import BeautifulSoup


def get_earnings_summary(url: str, timeout: int = 10) -> str:
    res = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")
    paragraphs = soup.find_all("p")
    return " ".join(p.get_text() for p in paragraphs[:5])
