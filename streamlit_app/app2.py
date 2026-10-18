"""Alternative UI that records with the server's microphone via sounddevice.

Requires the optional packages: sounddevice, scipy (and PortAudio on Linux).
Run with: streamlit run streamlit_app/app2.py
"""
import os
import tempfile

import requests
import speech_recognition as sr
import streamlit as st

from audio_controller import audio
from config import BACKEND_URL

st.set_page_config(page_title="🎙️ Morning Market Brief Assistant")
st.title("🎙️ Morning Market Brief Assistant")

st.session_state.setdefault("brief", "")
st.session_state.setdefault("query", "")
st.session_state.setdefault("audio_path", "")


def get_voice_input():
    try:
        import sounddevice as sd
        from scipy.io.wavfile import write
    except ImportError:
        st.error("Install optional packages first: pip install sounddevice scipy")
        return None

    recognizer = sr.Recognizer()
    fs = 16000
    seconds = 15
    st.info("🎤 Listening... Please speak your query (15 seconds).")
    wav_path = None
    try:
        recording = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype="int16")
        sd.wait()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            wav_path = tmp.name
        write(wav_path, fs, recording)

        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
        st.success("✅ Voice captured. Transcribing...")
        return recognizer.recognize_google(audio_data)
    except sr.UnknownValueError:
        st.error("⚠️ Could not understand audio.")
    except sr.RequestError:
        st.error("⚠️ API unavailable or quota exceeded.")
    except Exception as e:
        st.error(f"❌ Transcription error: {e}")
    finally:
        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)
    return None


def fetch_brief(query):
    try:
        response = requests.get(f"{BACKEND_URL}/brief", params={"query": query}, timeout=120)
        response.raise_for_status()
        st.session_state.brief = response.json().get("brief", "")
        st.session_state.audio_path = audio.generate_audio(st.session_state.brief) or ""
    except Exception as e:
        st.error(f"❌ Error: {e}")


input_method = st.radio("Choose input method:", ["⌨️ Text", "🎙️ Record Voice"])

if input_method == "⌨️ Text":
    st.session_state.query = st.text_input("Enter your market question", value=st.session_state.query)
    if st.button("Get Market Brief (Text)") and st.session_state.query:
        with st.spinner("🔄 Fetching brief..."):
            fetch_brief(st.session_state.query)
else:
    if st.button("🎤 Record and Transcribe"):
        query = get_voice_input()
        if query:
            st.success(f"📝 Transcribed: {query}")
            st.session_state.query = query
            with st.spinner("🔄 Fetching market brief..."):
                fetch_brief(query)

if st.session_state.brief:
    st.subheader("📄 Market Brief")
    st.write(st.session_state.brief)

    if st.session_state.audio_path and os.path.exists(st.session_state.audio_path):
        with open(st.session_state.audio_path, "rb") as f:
            st.audio(f.read(), format="audio/mp3", start_time=0)
