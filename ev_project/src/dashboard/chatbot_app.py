"""
dashboard/chatbot_app.py
Streamlit AI chatbot for EV diagnostics.
Run: streamlit run chatbot_app.py
"""
import sys
import os

# ── Adjust path for Colab ─────────────────────────────────────────────────────
BASE = os.environ.get("EV_BASE", "/content/drive/MyDrive/EV_AI_Platform")
sys.path.insert(0, os.path.join(BASE, "code"))

import streamlit as st
import chromadb
from sentence_transformers import SentenceTransformer

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title = "EV AI Diagnostics",
    page_icon  = "EV",
    layout     = "wide",
)

st.markdown("""
<style>
    .main-title  { font-size:2rem; font-weight:800; color:#0D1117; }
    .subtitle    { font-size:1rem; color:#586069; margin-bottom:1rem; }
    .badge       { background:#1F6FEB; color:white; border-radius:4px;
                   padding:2px 8px; font-size:0.75rem; margin:2px; display:inline-block; }
    .warn-badge  { background:#E84855; color:white; border-radius:4px;
                   padding:2px 8px; font-size:0.75rem; margin:2px; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## EV Diagnostic Assistant")
    st.markdown("---")

    st.markdown("### Vehicle Information")
    brand    = st.selectbox("Brand", ["Tesla", "Nissan", "Hyundai", "BMW",
                                       "Kia", "Volkswagen", "Ather", "Tata"])
    model_v  = st.text_input("Model", "Model 3")
    year     = st.number_input("Year", 2015, 2025, 2023)
    st.markdown("---")

    st.markdown("### Live Sensor Data")
    soc      = st.slider("Battery SOC %", 0, 100, 72)
    btemp    = st.slider("Battery Temp °C", -10, 80, 34)
    mtemp    = st.slider("Motor Temp °C", 10, 150, 42)
    st.markdown("---")

    st.markdown("### Active DTC Codes")
    dtcs     = st.text_area("Enter codes (one per line)",
                             placeholder="P0A0F\nP0C6B", height=80)
    st.markdown("---")

    search_mode = st.radio("Search Mode",
                           ["Knowledge Base", "Quick Answer"],
                           index=0)
    k_results   = st.slider("Context chunks", 2, 8, 4)

    if st.button("Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.markdown("**About**")
    st.caption("EV AI Diagnostic Platform — Personal Resume Project\n"
               "Google Colab + LangChain + ChromaDB + Streamlit")


# ── Knowledge base loader ─────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Loading AI model...")
def load_kb():
    try:
        client = chromadb.PersistentClient(path=f"{BASE}/vector_db")
        col    = client.get_collection("ev_manuals")
        model  = SentenceTransformer("all-MiniLM-L6-v2")
        return col, model, col.count()
    except Exception as e:
        return None, None, 0


def search_kb(question: str, col, model, k: int = 4) -> list:
    if col is None:
        return []
    try:
        q_vec   = model.encode(question, normalize_embeddings=True).tolist()
        results = col.query(query_embeddings=[q_vec], n_results=k)
        return list(zip(results["documents"][0], results["distances"][0]))
    except Exception:
        return []


def build_answer(question: str, docs_dists: list,
                 brand: str, model_v: str, soc: int,
                 btemp: int, dtcs: str) -> str:
    dtc_list = [d.strip() for d in dtcs.strip().split("\n") if d.strip()]

    # Vehicle context header
    lines = [
        f"**Vehicle:** {brand} {model_v} {year}",
        f"**SOC:** {soc}%  |  **Battery:** {btemp}°C  |  **Motor:** {mtemp}°C",
    ]
    if dtc_list:
        lines.append(f"**Active DTCs:** {', '.join(dtc_list)}")

    lines.append("")

    if docs_dists:
        lines.append("**From EV Knowledge Base:**")
        for i, (doc, dist) in enumerate(docs_dists, 1):
            sim = round((1 - dist) * 100, 1)
            lines.append(f"\n**[{i}] Relevance: {sim}%**")
            lines.append(f"> {doc[:300]}...")
        lines.append("")
        lines.append("*Add your OpenAI API key for full AI-generated diagnosis.*")
    else:
        lines.append("*Knowledge base not loaded — upload EV manuals and run the embedding pipeline.*")

    return "\n".join(lines)


# ── Main UI ───────────────────────────────────────────────────────────────────
col_kb, model_kb, doc_count = load_kb()

st.markdown('<p class="main-title">EV AI Diagnostic Assistant</p>', unsafe_allow_html=True)
st.markdown(
    f'<p class="subtitle">'
    f'<span class="badge">Knowledge Base: {doc_count} chunks</span> '
    f'<span class="badge">{brand} {model_v} {year}</span> '
    f'<span class="badge">SOC {soc}%</span>'
    f'</p>',
    unsafe_allow_html=True
)

# Initialise chat
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content":
         f"Hello! I am your EV AI Diagnostic Assistant. "
         f"I am ready to help diagnose your {brand} {model_v}. "
         f"What issue are you experiencing?"}
    ]

# Render history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Describe your EV problem or ask a question..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Searching EV manuals..."):
            docs = search_kb(prompt, col_kb, model_kb, k_results)
            answer = build_answer(prompt, docs, brand, model_v, soc, btemp, dtcs)
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
