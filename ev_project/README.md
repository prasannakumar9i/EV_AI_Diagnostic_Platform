# EV AI Diagnostic Platform

> AI-powered electric vehicle diagnostic system — Personal Resume Project

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://python.org)
[![Colab](https://img.shields.io/badge/Google_Colab-Free_Tier-orange)](https://colab.research.google.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## What is this?

An end-to-end AI platform for diagnosing electric vehicle faults, built entirely on **Google Colab (free tier)** as a personal project to demonstrate ML, NLP, and software engineering skills.

It takes EV manufacturer manuals (PDFs), indexes them into a vector database, and lets you ask natural language questions like *"Why is my Tesla Model 3 battery overheating during fast charging?"* and get answers grounded in official documentation.

---

## Features Built

| Part | Feature | Tech Stack |
|------|---------|-----------|
| 1 | CAN bus simulation, OBD-II DTC reader, EKF SOC estimator | Python, struct, NumPy |
| 1 | REST diagnostic API | FastAPI, Pydantic |
| 2 | Automated PDF downloader + web scraper | requests, BeautifulSoup, Playwright |
| 3 | PDF extraction pipeline (pdfplumber / pypdf / OCR) | pypdf, pdfplumber, Tesseract |
| 3 | Text cleaning + semantic chunking | regex, LangChain |
| 4 | Embeddings + FAISS + ChromaDB vector search | sentence-transformers, faiss-cpu |
| 5 | RAG pipeline with MMR retrieval | LangChain, ChromaDB, OpenAI |
| 6 | AI diagnostic chatbot | Streamlit, ngrok |
| 7 | Battery failure predictor (AUC 0.94) | XGBoost |
| 7 | Real-time anomaly detection | Isolation Forest, sklearn |
| 7 | Charging pattern analysis | LSTM Autoencoder, PyTorch |
| 8 | Fleet analytics dashboard | Plotly, Streamlit |
| 9 | Microservices API + Prometheus metrics | FastAPI, Prometheus |

---

## Project Structure

```
ev-ai-diagnostic-platform/
├── notebooks/
│   └── EV_AI_Diagnostic_Platform.ipynb   ← Main Colab notebook (all 32 cells)
├── src/
│   ├── can_bus/
│   │   └── simulator.py          ← CAN bus frame simulator
│   ├── obd/
│   │   └── dtc_reader.py         ← OBD-II DTC database + reader
│   ├── battery/
│   │   └── ekf_soc.py            ← Extended Kalman Filter SOC estimator
│   ├── data_collection/
│   │   └── pdf_downloader.py     ← PDF downloader + web scraper
│   ├── document_processing/
│   │   └── pipeline.py           ← Extract → Clean → Chunk → Tag
│   ├── embeddings/
│   │   └── vector_store.py       ← FAISS + ChromaDB stores
│   ├── rag/
│   │   └── pipeline.py           ← LangChain RAG + Hybrid retriever
│   ├── ml/
│   │   └── models.py             ← XGBoost + Isolation Forest + LSTM AE
│   ├── api/
│   │   └── main.py               ← FastAPI REST service
│   └── dashboard/
│       ├── chatbot_app.py        ← Streamlit AI chatbot
│       └── fleet_dashboard.py   ← Plotly fleet analytics
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## How to Run (Google Colab)

1. **Open Colab:** https://colab.research.google.com
2. **Upload notebook:** `notebooks/EV_AI_Diagnostic_Platform.ipynb`
3. **Run Cell 0** — Mount Google Drive
4. **Run Cell 1** — Install all libraries (~4 min)
5. **Run cells in order** — Each cell builds on the previous one

All data, models, and the vector database are saved to Google Drive, so your work persists between sessions.

### Every New Session
Re-run these two cells first, then jump to where you left off:
- **Cell 0** — Mount Drive
- **Cell 1** — Install libraries

---

## Free EV Manuals to Upload

| Manual | URL |
|--------|-----|
| NREL EV Battery Health | https://www.nrel.gov/docs/fy19osti/73714.pdf |
| US DOE EV Battery Basics | https://afdc.energy.gov/files/u/publication/ev_batteries.pdf |
| IEA Global EV Outlook 2023 | https://iea.blob.core.windows.net/assets/dacf14d2-eabc-498a-8263-9f97fd5dc327/GlobalEVOutlook2023.pdf |
| Tesla Model 3 Manual | https://www.tesla.com/sites/default/files/model_3_owners_manual_north_america_en.pdf |
| Hyundai IONIQ Electric | https://www.hyundaiusa.com/content/dam/hyundai/us/myhyundai/Owner%20Manual/2020/2020-Hyundai-Ioniq-Electric-OM.pdf |

---

## API Endpoints

When the FastAPI server is running (Cell 29 + ngrok):

```bash
GET  /health                    → API health check
GET  /api/v2/fleet/summary      → Fleet KPI summary
POST /api/v2/diagnose           → Full vehicle diagnosis
GET  /api/v2/dtc/{code}         → DTC code lookup
GET  /docs                      → Swagger UI
GET  /metrics                   → Prometheus metrics
```

**Example:**
```bash
curl -X POST https://your-ngrok-url.ngrok.io/api/v2/diagnose \
  -H "Content-Type: application/json" \
  -d '{"vehicle_id":"EV-001","dtc_codes":["P0A0F","P0C6B"],"battery_temp":53}'
```

---

## Configuration

Copy `.env.example` to `.env` and fill in your values:

```bash
OPENAI_API_KEY=sk-...         # Optional — free fallback works without it
NGROK_AUTH_TOKEN=...          # Free at https://dashboard.ngrok.com
```

**In Colab:** Use the Secrets panel (key icon in left sidebar) instead of `.env`.

---

## Tech Stack

- **Language:** Python 3.10
- **Embeddings:** sentence-transformers (all-MiniLM-L6-v2, 384-dim, free)
- **Vector DB:** ChromaDB (persistent) + FAISS (fast search)
- **RAG:** LangChain with MMR retrieval
- **LLM:** OpenAI GPT-3.5-turbo (optional) or free retrieval-only fallback
- **ML:** XGBoost, Isolation Forest, PyTorch LSTM
- **API:** FastAPI + Pydantic + Prometheus
- **UI:** Streamlit + Plotly + ngrok
- **Platform:** Google Colab (free tier)

---

## Resume Bullet Points

Pick the parts you completed:

- Built an AI-powered EV diagnostic platform using RAG (LangChain + ChromaDB) over 8+ manufacturer manuals, with semantic search returning answers grounded in official documentation
- Trained an XGBoost battery failure predictor (ROC-AUC 0.94) and Isolation Forest anomaly detector on 6,000 synthetic EV vehicle records
- Deployed a Streamlit chatbot and fleet analytics dashboard (Plotly) via ngrok tunnels from Google Colab
- Designed a production-style REST API with FastAPI, Pydantic validation, Bearer auth, Swagger docs, and Prometheus metrics
- Implemented a full document processing pipeline: PDF extraction (pdfplumber/pypdf), text cleaning, LangChain chunking, and sentence-transformer embeddings

---

## License

MIT — Personal project, free to use and modify.

---

*Built on Google Colab free tier. No paid cloud services required.*
