"""
EV AI Diagnostic Chatbot
Streamlit interface for EV knowledge base diagnostics
"""

import streamlit as st
import chromadb
from sentence_transformers import SentenceTransformer


# ── Page config ─────────────────────────────────────────
st.set_page_config(
    page_title="EV AI Diagnostics",
    page_icon="⚡",
    layout="wide",
)


# ── Styling ─────────────────────────────────────────────
st.markdown("""
<style>
.main-title {font-size:2rem;font-weight:800;color:#0D1117;}
.subtitle {font-size:1rem;color:#586069;margin-bottom:1rem;}
.badge {background:#1F6FEB;color:white;border-radius:4px;
padding:2px 8px;font-size:0.75rem;margin:2px;display:inline-block;}
</style>
""", unsafe_allow_html=True)


# ── Sidebar ─────────────────────────────────────────────
with st.sidebar:

    st.markdown("## EV Diagnostic Assistant")

    st.markdown("### Vehicle Information")

    brand = st.selectbox(
        "Brand",
        ["Tesla", "Nissan", "Hyundai", "BMW", "Kia", "Volkswagen", "Ather", "Tata"],
    )

    model_v = st.text_input("Model", "Model 3")

    year = st.number_input("Year", 2015, 2025, 2023)

    st.markdown("---")

    st.markdown("### Live Sensor Data")

    soc = st.slider("Battery SOC %", 0, 100, 72)

    btemp = st.slider("Battery Temp °C", -10, 80, 34)

    mtemp = st.slider("Motor Temp °C", 10, 150, 42)

    st.markdown("---")

    st.markdown("### Active DTC Codes")

    dtcs = st.text_area(
        "Enter codes (one per line)",
        placeholder="P0A0F\nP0C6B",
        height=80,
    )

    st.markdown("---")

    k_results = st.slider("Context chunks", 2, 8, 4)

    if st.button("Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.caption(
        "EV AI Diagnostic Platform\n"
        "Google Colab + ChromaDB + Streamlit"
    )


# ── Load Knowledge Base ─────────────────────────────────
@st.cache_resource(show_spinner="Loading EV knowledge base...")
def load_kb():

    try:

        persist_dir = "data/vector_store"

        client = chromadb.PersistentClient(path=persist_dir)

        col = client.get_or_create_collection(
            name="ev_manuals",
            metadata={"hnsw:space": "cosine"},
        )

        model = SentenceTransformer("all-MiniLM-L6-v2")

        return col, model, col.count()

    except Exception as e:

        print("KB load error:", e)

        return None, None, 0


# ── Search Knowledge Base ───────────────────────────────
def search_kb(question, col, model, k=4):

    if col is None:
        return []

    try:

        q_vec = model.encode(question, normalize_embeddings=True).tolist()

        results = col.query(
            query_embeddings=[q_vec],
            n_results=k,
        )

        return list(zip(results["documents"][0], results["distances"][0]))

    except Exception:

        return []


# ── Build Chatbot Response ──────────────────────────────
def build_answer(question, docs_dists):

    lines = []

    if docs_dists:

        lines.append("### 🔎 Relevant Information From EV Manuals\n")

        for i, (doc, dist) in enumerate(docs_dists, 1):

            similarity = round((1 - dist) * 100, 1)

            lines.append(f"**Result {i} — relevance {similarity}%**")

            lines.append(f"> {doc[:300]}...\n")

    else:

        lines.append(
            "*Knowledge base not loaded — ensure vector database exists.*"
        )

    return "\n".join(lines)


# ── Main UI ─────────────────────────────────────────────
col_kb, model_kb, doc_count = load_kb()


st.markdown(
    '<p class="main-title">EV AI Diagnostic Assistant</p>',
    unsafe_allow_html=True,
)

st.markdown(
    f'<p class="subtitle">'
    f'<span class="badge">Knowledge Base: {doc_count} chunks</span> '
    f'<span class="badge">{brand} {model_v} {year}</span> '
    f'<span class="badge">SOC {soc}%</span>'
    f'</p>',
    unsafe_allow_html=True,
)


# ── Chat History ───────────────────────────────────────
if "messages" not in st.session_state:

    st.session_state.messages = [
        {
            "role": "assistant",
            "content": f"Hello! I am your EV AI Diagnostic Assistant. "
            f"How can I help with your {brand} {model_v}?",
        }
    ]


for msg in st.session_state.messages:

    with st.chat_message(msg["role"]):

        st.markdown(msg["content"])


# ── Chat Input ─────────────────────────────────────────
if prompt := st.chat_input("Describe your EV issue..."):

    with st.chat_message("user"):

        st.markdown(prompt)

    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    with st.chat_message("assistant"):

        with st.spinner("Searching EV manuals..."):

            docs = search_kb(prompt, col_kb, model_kb, k_results)

            answer = build_answer(prompt, docs)

        st.markdown(answer)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer}
    )
