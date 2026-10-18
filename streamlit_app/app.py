import os, tempfile
from datetime import datetime

import requests
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import speech_recognition as sr
from gtts import gTTS
from config import BACKEND_URL

try:
    from st_audiorec import st_audiorec
except Exception:
    st_audiorec = None

st.set_page_config(page_title="FinSight AI | Market Intelligence", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

st.markdown(r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root{--ink:#edf3ff;--muted:#9eacc8;--panel:#111d34;--line:rgba(148,170,210,.18);--blue:#5b8cff;--cyan:#3de0cf}
.stApp{background:radial-gradient(ellipse at 12% 0%,#193761 0%,#091224 38%,#070d19 80%);color:var(--ink);font-family:'DM Sans',sans-serif}
[data-testid="stHeader"]{background:rgba(7,13,25,.72)}.block-container{padding-top:1.25rem;max-width:1550px}
h1,h2,h3{font-family:'Space Grotesk',sans-serif!important;letter-spacing:-.03em}
.hero{padding:1.8rem 2rem;border:1px solid var(--line);border-radius:25px;background:linear-gradient(115deg,rgba(25,48,85,.98),rgba(15,27,49,.95) 55%,rgba(20,47,69,.96));position:relative;overflow:hidden}
.hero:after{content:'✦';position:absolute;right:7%;top:-18%;font-size:11rem;color:rgba(61,224,207,.12);animation:floaty 5s ease-in-out infinite}
.hero-kicker{color:#75e8dd;font-size:.76rem;letter-spacing:.18em;font-weight:700;text-transform:uppercase}.hero h1{font-size:clamp(2rem,4vw,3.25rem);line-height:1.08;margin:.5rem 0;color:white}.hero p{color:#c0cce2;max-width:760px;font-size:1.02rem}
@keyframes floaty{0%,100%{transform:translateY(0) rotate(0)}50%{transform:translateY(-12px) rotate(8deg)}}
.panel,.metric-card{background:linear-gradient(145deg,rgba(23,36,64,.97),rgba(13,23,42,.97));border:1px solid var(--line);border-radius:18px;padding:1rem 1.1rem;box-shadow:0 10px 35px rgba(0,0,0,.12)}
.metric-card{min-height:116px}.metric-label{color:var(--muted);font-size:.78rem;font-weight:700;letter-spacing:.04em}.metric-value{font-family:'Space Grotesk',sans-serif;color:#fff;font-size:1.7rem;font-weight:700;margin:.3rem 0}.metric-note{color:#8ca0c3;font-size:.78rem}
.section-title{font-family:'Space Grotesk',sans-serif;font-size:1.35rem;font-weight:700;color:#f2f6ff;margin:.4rem 0 .8rem}.pill{display:inline-block;border:1px solid rgba(91,140,255,.35);background:rgba(91,140,255,.12);color:#bcd0ff;border-radius:100px;padding:.25rem .65rem;font-size:.75rem;margin-right:.3rem;margin-bottom:.25rem}
.news-card{border:1px solid var(--line);background:rgba(17,27,49,.85);border-radius:14px;padding:.9rem 1rem;margin:.45rem 0;color:#dce6fa}
.stButton>button{border-radius:12px;border:1px solid rgba(91,140,255,.55);background:linear-gradient(100deg,#3978f6,#5b8cff);color:white;font-weight:700;padding:.62rem 1rem}.stButton>button:hover{border-color:#3de0cf;color:white;filter:brightness(1.08)}
.stTextInput input,.stTextArea textarea{background:#101c32!important;color:#eef3ff!important;border:1px solid var(--line)!important;border-radius:12px!important}[data-testid="stSidebar"]{background:#0b1425;border-right:1px solid var(--line)}[data-testid="stSidebar"] *{color:#dce6fa}footer{visibility:hidden}
[data-testid="stMetric
[data-testid="stMetric"]{background:rgba(17,29,52,.7);border:1px solid var(--line);padding:12px;border-radius:14px}
</style>
""", unsafe_allow_html=True)

st.session_state.setdefault("last_query", "")
st.session_state.setdefault("last_brief", "")
st.session_state.setdefault("last_data", {})
st.session_state.setdefault("mute", False)

with st.sidebar:
    st.markdown("## ✦ FinSight **AI**")
    st.caption("Your personal market intelligence desk")
    st.markdown("---")
    page = st.radio("Workspace", ["Market dashboard", "Ask Finance AI", "Stock research"], label_visibility="collapsed")
    st.markdown("---")
    st.toggle("Mute spoken response", key="mute")
    st.caption("Quotes may be delayed. Verify figures with the cited provider before acting.")

st.markdown("""
<div class="hero">
  <div class="hero-kicker">✦ AI-powered market intelligence</div>
  <h1>See the signals.<br>Understand the story.</h1>
  <p>Explore stock trends with interactive charts, ask finance questions in plain language, and get data-aware summaries, risks, and scenarios—not unexplained numbers.</p>
  <span class="pill">Live-provider lookup</span><span class="pill">Interactive charts</span><span class="pill">Text + voice</span><span class="pill">AI insights</span>
</div>
""", unsafe_allow_html=True)
st.write("")

SUGGESTIONS = [
    "Analyze NVIDIA stock with recent price trend, risks, and outlook",
    "Give me today's Indian market update for Nifty 50 and Sensex",
    "Compare TCS and Infosys using price trend and fundamentals",
    "Summarize the latest financial news affecting Apple",
    "Explain Microsoft's recent stock movement in simple terms",
]

def speak(text):
    if st.session_state.get("mute", False) or not text:
        return
    path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            path = tmp.name
        gTTS(text=text[:4500], lang="en").save(path)
        with open(path, "rb") as f:
            st.audio(f.read(), format="audio/mp3")
    except Exception as exc:
        st.info(f"Voice output is unavailable right now: {exc}")
    finally:
        if path and os.path.exists(path):
            os.remove(path)

def fetch_answer(query):
    if not query.strip():
        st.warning("Enter a question first.")
        return
    try:
        with st.spinner("Checking available market data and preparing your analysis…"):
            res = requests.get(f"{BACKEND_URL}/brief", params={"query": query.strip()}, timeout=150)
        try:
            data = res.json()
        except Exception:
            data = {}
        if res.status_code != 200 or data.get("error"):
            st.error("The finance API could not complete the request: " + str(data.get("error", res.text[:400])))
            return
        answer = data.get("brief", "")
        if not answer:
            st.warning("No answer was returned. Check the backend logs and data providers.")
            return
        st.session_state.last_query = query.strip()
        st.session_state.last_brief = answer
        st.session_state.last_data = data
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot connect to {BACKEND_URL}. Start FastAPI in a separate terminal first.")
    except Exception as exc:
        st.error(f"Request failed: {exc}")

def fetch_history(ticker, period="6mo", interval="1d"):
    try:
        response = requests.get(f"{BACKEND_URL}/stock-history", params={"ticker": ticker, "period": period, "interval": interval}, timeout=25)
        if response.ok:
            payload = response.json()
            rows = payload.get("history", [])
            if rows:
                df = pd.DataFrame(rows)
                df["date"] = pd.to_datetime(df["date"])
                return df, payload.get("source", "Yahoo Finance via yfinance")
    except Exception:
        pass
    return pd.DataFrame(), "History unavailable"

def show_answer():
    answer = st.session_state.get("last_brief", "")
    if not answer:
        return
    st.markdown('<div class="section-title">✦ Your finance briefing</div>', unsafe_allow_html=True)
    st.caption(f"Question: {st.session_state.last_query} · Generated {datetime.now().strftime('%d %b %Y, %I:%M %p')}")
    st.markdown(answer)
    st.download_button("⬇ Download briefing", answer, file_name="finsight_finance_briefing.txt", mime="text/plain")
    if st.button("🔊 Read briefing aloud", key="read_brief"):
        speak(answer)
    meta = st.session_state.get("last_data", {})
    if meta.get("source_note"):
        st.caption("Data notes: " + meta["source_note"])

if page == "Market dashboard":
    try:
        health = requests.get(f"{BACKEND_URL}/health", timeout=3).json()
        online = health.get("status") == "ok"
    except Exception:
        online = False
    st.markdown('<div class="section-title">Your market command centre</div>', unsafe_allow_html=True)
    st.image("https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1800&q=85", caption="Market intelligence · Charts and analysis", use_container_width=True)
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.markdown('<div class="metric-card"><div class="metric-label">AI WORKSPACE</div><div class="metric-value">FinSight AI</div><div class="metric-note">Financial research assistant</div></div>', unsafe_allow_html=True)
    with m2: st.markdown(f'<div class="metric-card"><div class="metric-label">BACKEND STATUS</div><div class="metric-value">{"Online" if online else "Offline"}</div><div class="metric-note">FastAPI connection</div></div>', unsafe_allow_html=True)
    with m3: st.markdown('<div class="metric-card"><div class="metric-label">CHARTS</div><div class="metric-value">Interactive</div><div class="metric-note">Price history and volume</div></div>', unsafe_allow_html=True)
    with m4: st.markdown(f'<div class="metric-card"><div class="metric-label">LOCAL TIME</div><div class="metric-value">{datetime.now().strftime("%I:%M %p")}</div><div class="metric-note">{datetime.now().strftime("%d %b %Y")}</div></div>', unsafe_allow_html=True)
    st.write("")
    left, right = st.columns([1.5, 1])
    with left:
        st.markdown('<div class="section-title">📉 Explore a stock trend</div>', unsafe_allow_html=True)
        stock_options = {"NVIDIA": "NVDA", "Apple": "AAPL", "Alphabet / Google": "GOOGL", "Microsoft": "MSFT", "TSMC": "TSM", "Samsung Electronics": "005930.KS", "TCS": "TCS.NS", "Infosys": "INFY.NS", "Reliance Industries": "RELIANCE.NS", "Nifty 50 ETF proxy": "^NSEI", "S&P 500": "^GSPC"}
        chosen_name = st.selectbox("Choose a stock or index", list(stock_options.keys()), key="dash_stock")
        period = st.select_slider("Chart period", options=["1mo", "3mo", "6mo", "1y", "2y", "5y"], value="6mo", key="dash_period")
        ticker = stock_options[chosen_name]
        df, source = fetch_history(ticker, period=period)
        if not df.empty:
            latest = df.iloc[-1]
            previous = df.iloc[-2] if len(df) > 1 else latest
            change = ((latest["close"] / previous["close"]) - 1) * 100 if previous["close"] else 0
            a, b, c = st.columns(3)
            a.metric("Latest available close", f"{latest['close']:,.2f}", f"{change:+.2f}% vs prior close")
            b.metric("Period high", f"{df['high'].max():,.2f}")
            c.metric("Period low", f"{df['low'].min():,.2f}")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df["date"], y=df["close"], name="Close", mode="lines", line=dict(width=3, color="#5b8cff"), fill="tozeroy", fillcolor="rgba(91,140,255,.10)"))
            fig.update_layout(template="plotly_dark", height=360, margin=dict(l=10,r=10,t=25,b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(10,20,38,.4)", xaxis_title="Date", yaxis_title="Price", legend=dict(orientation="h"))
            st.plotly_chart(fig, use_container_width=True)
            vol = go.Figure(go.Bar(x=df["date"], y=df["volume"], name="Volume", marker_color="#3de0cf"))
            vol.update_layout(template="plotly_dark", height=210, margin=dict(l=10,r=10,t=25,b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(10,20,38,.4)", xaxis_title="Date", yaxis_title="Volume")
            st.plotly_chart(vol, use_container_width=True)
            st.caption(f"Source: {source}. Latest available daily close, not necessarily a live intraday quote. Values may be delayed.")
        else:
            st.info("Price history is unavailable right now. Check that the backend is running and that the market-data provider is reachable.")
    with right:
        st.markdown('<div class="section-title">✨ Ask the AI analyst</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel"><p>Get a structured report with available facts, recent context, risks, possible scenarios, and a clearly qualified outlook.</p><span class="pill">Price action</span><span class="pill">Fundamentals</span><span class="pill">Risks</span><span class="pill">Scenarios</span></div>', unsafe_allow_html=True)
        q = st.text_area("Your question", placeholder="e.g. Analyze NVIDIA's stock performance, recent news, risks and possible scenarios", height=125, key="dash_query", label_visibility="collapsed")
        if st.button("✦ Generate analysis", key="dash_ask", use_container_width=True): fetch_answer(q)
        st.markdown('<div class="news-card">🧭 <b>How to read predictions</b><br>Scenarios are uncertain, not guarantees. A recommendation should explain its evidence, time horizon, and risks—not just say buy or sell.</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Try a question</div>', unsafe_allow_html=True)
    cards = st.columns(3)
    for i, suggestion in enumerate(SUGGESTIONS[:3]):
        with cards[i]:
            if st.button(suggestion, key=f"dashboard_suggest_{i}", use_container_width=True): fetch_answer(suggestion)
    show_answer()

elif page == "Ask Finance AI":
    st.markdown('<div class="section-title">Ask anything about finance</div>', unsafe_allow_html=True)
    st.write("Ask about a company, stock movement, market index, financial news, business results, or investing terminology.")
    query = st.text_area("Financial question", placeholder="Example: Compare TCS and Infosys using recent price trends, fundamentals, news, risks and possible scenarios.", height=130, key="finance_query")
    b1, b2 = st.columns([1, 1])
    with b1:
        if st.button("✦ Research question", use_container_width=True, key="finance_submit"): fetch_answer(query)
    with b2:
        if st.button("Clear answer", use_container_width=True):
            st.session_state.last_query = ""
            st.session_state.last_brief = ""
            st.session_state.last_data = {}
            st.rerun()
    st.markdown('<div class="section-title">Suggested prompts</div>', unsafe_allow_html=True)
    for i, suggestion in enumerate(SUGGESTIONS):
        if st.button("💡 " + suggestion, key=f"finance_suggest_{i}", use_container_width=True): fetch_answer(suggestion)
    show_answer()

elif page == "Stock research":
    st.markdown('<div class="section-title">Stock research studio</div>', unsafe_allow_html=True)
    st.image("https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=1800&q=80", caption="Research workspace · Historical data and indicators", use_container_width=True)
    stock_options = {"Apple": "AAPL", "Alphabet / Google": "GOOGL", "Microsoft": "MSFT", "NVIDIA": "NVDA", "TSMC": "TSM", "Samsung Electronics": "005930.KS", "TCS": "TCS.NS", "Infosys": "INFY.NS", "Reliance Industries": "RELIANCE.NS"}
    c1, c2, c3 = st.columns([1.3, 1, 1])
    with c1: company = st.selectbox("Company", list(stock_options.keys()), key="research_company")
    with c2: period = st.selectbox("Historical window", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=2, key="research_period")
    with c3: chart_type = st.selectbox("Chart type", ["Line", "Candlestick"], key="research_chart")
    ticker = stock_options[company]
    df, source = fetch_history(ticker, period=period)
    if not df.empty:
        last = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else last
        change = ((last["close"] / prev["close"]) - 1) * 100 if prev["close"] else 0
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Latest close", f"{last['close']:,.2f}", f"{change:+.2f}%")
        k2.metric("High in selected period", f"{df['high'].max():,.2f}")
        k3.metric("Low in selected period", f"{df['low'].min():,.2f}")
        k4.metric("Observations", f"{len(df):,}")
        if chart_type == "Candlestick":
            fig = go.Figure(go.Candlestick(x=df["date"], open=df["open"], high=df["high"], low=df["low"], close=df["close"], name=ticker))
        else:
            fig = go.Figure(go.Scatter(x=df["date"], y=df["close"], name="Closing price", mode="lines", line=dict(width=3, color="#5b8cff")))
        fig.update_layout(template="plotly_dark", height=430, margin=dict(l=10,r=10,t=30,b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(10,20,38,.4)", xaxis_title="Date", yaxis_title="Price")
        st.plotly_chart(fig, use_container_width=True)
        # Moving averages are derived from the downloaded closing-price series.
        ma = df[["date", "close"]].copy()
        ma["MA20"] = ma["close"].rolling(20).mean()
        ma["MA50"] = ma["close"].rolling(50).mean()
        mfig = go.Figure()
        mfig.add_trace(go.Scatter(x=ma["date"], y=ma["close"], name="Close", line=dict(width=2, color="#5b8cff")))
        mfig.add_trace(go.Scatter(x=ma["date"], y=ma["MA20"], name="20-day average", line=dict(width=2, color="#3de0cf")))
        mfig.add_trace(go.Scatter(x=ma["date"], y=ma["MA50"], name="50-day average", line=dict(width=2, color="#f6b85e")))
        mfig.update_layout(template="plotly_dark", height=300, margin=dict(l=10,r=10,t=25,b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(10,20,38,.4)", xaxis_title="Date", yaxis_title="Price")
        st.markdown('<div class="section-title">Trend and moving averages</div>', unsafe_allow_html=True)
        st.plotly_chart(mfig, use_container_width=True)
        st.caption(f"Source: {source}. Moving averages are technical indicators, not standalone buy/sell signals.")
    else:
        st.warning("Could not load historical prices. Start the backend and check the market-data connection.")
    st.markdown('<div class="section-title">Ask for an evidence-based stock view</div>', unsafe_allow_html=True)
    stock_q = st.text_area("Analysis request", value=f"Analyze {company} ({ticker}) using the latest available stock data and news. Explain performance, fundamentals, risks, bullish and bearish scenarios, and what data is still missing.", height=110, key="research_query")
    if st.button("Analyze this stock", key="research_analyze", use_container_width=True): fetch_answer(stock_q)
    show_answer()

st.markdown("<div style='text-align:center;color:#8192b2;font-size:.78rem;padding:1.5rem 0'>FinSight AI · Data may be delayed or incomplete · For research and education, not personalized investment advice</div>", unsafe_allow_html=True)
