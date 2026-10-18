# AI Tool Usage Log and Documentation

## 🔍 Project Overview
This project is a multi-agent, voice-enabled **Finance Assistant** that provides stock updates, company summaries, and financial news using voice and text inputs. The assistant is built using:
- **Google Generative AI (Gemini)**
- **Whisper (OpenAI)** for speech-to-text
- **FAISS + Sentence Transformers** for document retrieval
- **FastAPI** backend and **Streamlit** frontend

---

## 🔧 AI Tools and Prompts

### 🧠 1. Google Generative AI (Gemini)
- **Usage**: Financial query generation and summarization
- **Prompt Template**:
  ```plaintext
  You are a finance assistant. Provide a brief and up-to-date summary of the company: {company_name}.
