from agents.analysis_agent import compute_asia_tech_exposure, get_sentiment
from agents.retriever_agent import embed_and_store, retrieve_top_k
from data_ingestion.document_loader import chunk_text


def test_exposure():
    assert compute_asia_tech_exposure({"AsiaTech_TSM": 2, "US_Tech_MSFT": 5}) == 28.57
    assert compute_asia_tech_exposure({}) == 0.0


def test_sentiment_labels():
    assert get_sentiment("great strong beat record profit")["label"] == "positive"
    assert get_sentiment("terrible awful bad loss")["label"] == "negative"


def test_chunking():
    chunks = chunk_text("One. Two. Three. " * 50)
    assert chunks and all(c.strip() for c in chunks)


def test_retrieval_returns_results():
    index, texts = embed_and_store(["TSMC earnings beat", "Samsung memory prices", "Yen weakens"])
    assert len(retrieve_top_k("TSMC earnings", index, texts, k=2)) == 2
