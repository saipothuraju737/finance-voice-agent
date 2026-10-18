# 🎙️ Multi-Agent Financial Assistant

A production-ready, voice-powered financial assistant that delivers spoken market briefs using multi-agent orchestration, Retrieval-Augmented Generation (RAG), and real-time data analysis.

**Video Demo Link** : https://drive.google.com/file/d/1sPu0vMsnTmpZkiMrVLUnbKBz7p2qjj9c/view?usp=sharing

---

## 🚀 Features

- **🎤 Voice I/O**: Ask financial questions via browser microphone.
- **📊 Real-Time Analysis**: Summarizes risk exposure, earnings surprises, and market events.
- **🧠 Multi-Agent Architecture**: Decoupled agents for scraping, retrieval, reasoning, and voice synthesis.
- **🧾 RAG Pipeline**: Retrieves real-time earnings/risk data from multiple APIs and web sources.
- **📈 Quantitative Reasoning**: Supports exposure % breakdowns and sentiment-based interpretations.
- **📺 Streamlit UI**: Low-latency interface for spoken and typed interaction.

---

## 🧠 Architecture Overview

```
                ┌────────────────────┐
                │ Streamlit Frontend │
                └────────┬───────────┘
                         │
            ┌────────────▼────────────┐
            │   FastAPI Orchestrator  │
            └────────────┬────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
 ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
 │  RAG Agent  │  │ Voice Agent │  │ NLP Agent   │
 │ (LLM + DB)  │  │ TTS + STT   │  │ Fin. Parsing│
 └─────────────┘  └─────────────┘  └─────────────┘
        │                │                │
 ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
 │  Web Agent  │  │ API Agent   │  │ Analysis    │
 │  (Scraping) │  │ (News/Stock)│  │ Engine      │
 └─────────────┘  └─────────────┘  └─────────────┘
```

---

## 🧰 Tech Stack & Toolkits

| Agent Type        | Toolkits Used                                                                 |
|-------------------|-------------------------------------------------------------------------------|
| **Web Agent**     | `Selenium`, `BeautifulSoup`, `Playwright`                                     |
| **Retrieval Agent**| `FAISS`, `Chroma`, `LangChain`, `OpenAI Embeddings`                          |
| **Language Agent**| `Gemini`, `transformers`, `LangChain`, `Prompt Templates`                      |
| **Voice Agent**   | `SpeechRecognition`, `pyttsx3`, `st_audiorec`, `gTTS`                         |
| **Frontend**      | `Streamlit`, `st_audiorec`, `Matplotlib`, `Plotly`, `Altair`                  |
| **Backend/API**   | `FastAPI`, `Uvicorn`, `pydantic`                                               |
| **CI/CD**         | `GitHub Actions`, `Black`, `flake8`, `pytest`                                 |

---


## 🛠️ Setup Instructions (VS Code)

### 1. Create a virtual environment and install
```bash
cd finance-voice-agent-master
python -m venv .venv
# Windows: .venv\Scripts\activate     macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Add your Gemini API key
```bash
cp .env.example .env      # Windows: copy .env.example .env
```
Edit `.env` and set `GEMINI_API_KEY` (free key: https://aistudio.google.com/app/apikey).
Without a key the app still works and returns a plain-text brief.

### 3. Launch the backend (FastAPI) — from the project root
```bash
uvicorn orchestrator.main:app --host 127.0.0.1 --port 8000
```

### 4. Launch the frontend (Streamlit) — in a second terminal, from the project root
```bash
streamlit run streamlit_app/app.py
```

Or in VS Code: **Run and Debug → "Run Backend + Frontend"** (config in `.vscode/launch.json`).

> The first start downloads the `all-MiniLM-L6-v2` embedding model (~90 MB). If it
> can't be downloaded, retrieval falls back to keyword search automatically.
> Voice input/output (Google speech recognition + gTTS) needs an internet connection.

### 5. Deploy on Render
Start command:
```bash
uvicorn orchestrator.main:app --host 0.0.0.0 --port $PORT
```
Then set `BACKEND_URL` for the Streamlit app to the deployed URL.

---

## 🧪 Testing

```bash
pytest tests/
```

---

## 🧠 Prompt Engineering & RAG

- **System prompt**: Guides the LLM to structure briefs concisely (e.g., “Summarize risk exposure, then earnings surprises...”)
- **Chunking strategy**: 500-token overlapping windows
- **Similarity Search**: FAISS with cosine distance
- **Sources**: Alpha Vantage, Yahoo Finance, Reuters

---

## 🧑‍🔬 Evaluation Criteria Mapping

| Criteria             | Evidence                                                                      |
|----------------------|--------------------------------------------------------------------------------|
| Technical Depth       | Multi-agent orchestration, RAG pipeline, sentiment & risk analysis            |
| Framework Breadth     | ≥2 toolkits per agent type: `LangChain`, `Selenium`, `TTS`, `Chroma`, etc.    |
| Code Quality          | Modular design, test suite, CI-ready                                          |
| Documentation         | Clear setup, agent explanation, AI-tool use transparency                      |
| UX & Performance      | Fast Streamlit UI, live transcription, voice synthesis, error handling        |

---



## 📢 Demo Query Examples

- “What’s our risk exposure in Asia tech stocks today?”
- “Summarize any earnings surprises from last night.”
- “Which sectors are driving today's US market performance?”

---



## FinSight AI redesign and data-quality notes

The Streamlit interface has been redesigned with a responsive dark financial dashboard, a three-column overview, question suggestions, stock-research workspace, voice input/output, and downloadable briefings.

**Important data limitation:** the project bundle includes static sample news documents. Yahoo Finance data retrieved through `yfinance` may be delayed or incomplete. Earnings surprises are intentionally not fabricated; analyst consensus data must be integrated from a licensed/reliable provider before reporting an actual-versus-estimate percentage. Portfolio allocation should be connected to real portfolio holdings before displaying allocation claims.

Run backend and frontend from the project root in separate VS Code terminals:

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn orchestrator.main:app --host 127.0.0.1 --port 8000
```

```powershell
.\.venv\Scripts\Activate.ps1
python -m streamlit run streamlit_app/app.py
```


## Updated dashboard features

- Market dashboard with a historical price line chart and trading-volume bar chart.
- Stock research workspace with line/candlestick views and 20-/50-day moving averages.
- New FastAPI endpoint `GET /stock-history?ticker=AAPL&period=6mo&interval=1d` for historical chart data.
- Compact navigation focused on dashboard, AI questions, and stock research; the old About section is removed.
- Scenario-oriented AI prompts encourage explicit assumptions, risks, source notes, and missing-data disclosures. Forecasts are not guaranteed and should not be treated as personalized investment advice.

Historical chart data comes from Yahoo Finance through `yfinance`, may be delayed or unavailable, and is not guaranteed to be a live quote. Install the updated dependencies with `python -m pip install -r requirements.txt`.
