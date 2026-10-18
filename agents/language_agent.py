import os

from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = (
    "You are FinSight AI, a careful financial information assistant. Use ONLY the facts provided; never fabricate prices, returns, earnings, analyst estimates, dates, portfolio values, or sources. "
    "Keep the main answer concise and skimmable: start with a 1-2 sentence takeaway, then use short sections and bullets rather than a long wall of text. "
    "For stock questions, use this structure when the relevant data exists: Quick view; Price/performance; Fundamentals; News and drivers; Risks; Outlook scenarios (bull/base/bear, with explicit assumptions and no unsupported numeric targets); Research stance (positive/mixed/negative/insufficient evidence, with reasons); Data sources and timestamp. "
    "Explain metrics in beginner-friendly language. Distinguish latest available close from a live intraday price, cite only supplied sources, and clearly label missing fields and data limitations. "
    "Do not present forecasts as facts, do not guarantee returns, and do not give personalized investment advice. If evidence is insufficient, say so rather than inventing a recommendation."
)

_model = None
_model_failed = False


def _get_model():
    """Create the Gemini model lazily. Returns None if it is not configured."""
    global _model, _model_failed
    if _model is not None or _model_failed:
        return _model

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[WARN] GEMINI_API_KEY not set - returning the raw prompt instead of an LLM brief.")
        _model_failed = True
        return None

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        _model = genai.GenerativeModel(model_name=name, system_instruction=SYSTEM_PROMPT)
        print(f"[INFO] Gemini model loaded: {name}")
    except Exception as e:
        print(f"[ERROR] Could not initialise Gemini: {e}")
        _model_failed = True
        _model = None
    return _model


def generate_brief(prompt: str):
    model = _get_model()
    if model is None:
        return None
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"[ERROR] Failed to generate content: {e}")
        return None
