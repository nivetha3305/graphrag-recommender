"""
ui.py - Streamlit web interface for GraphRAG Product Recommendation System
Run: streamlit run graphrag_recommender/ui.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass

import streamlit as st
from recommender.engine import RecommendationEngine

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GraphRAG Recommender",
    page_icon="🛍️",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0f1117; }
    .stTextInput > div > div > input {
        background-color: #1e1e2e;
        color: white;
        border: 1px solid #7c3aed;
        border-radius: 8px;
        font-size: 16px;
    }
    .product-card {
        background: linear-gradient(135deg, #1e1e2e, #2a2a3e);
        border: 1px solid #7c3aed44;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
        transition: border 0.2s;
    }
    .product-card:hover { border-color: #7c3aed; }
    .rank-badge {
        background: #7c3aed;
        color: white;
        border-radius: 50%;
        width: 28px; height: 28px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 13px;
        margin-right: 10px;
    }
    .product-name { font-size: 16px; font-weight: 600; color: #e2e8f0; }
    .product-price { font-size: 20px; font-weight: 700; color: #10b981; }
    .product-rating { color: #f59e0b; font-size: 14px; }
    .product-reason { color: #94a3b8; font-size: 13px; margin-top: 6px; }
    .tag {
        display: inline-block;
        background: #7c3aed22;
        color: #a78bfa;
        border: 1px solid #7c3aed44;
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 12px;
        margin: 2px;
    }
    .example-btn {
        background: #1e1e2e;
        border: 1px solid #7c3aed44;
        border-radius: 8px;
        padding: 8px 14px;
        color: #a78bfa;
        cursor: pointer;
        font-size: 13px;
        margin: 4px;
    }
</style>
""", unsafe_allow_html=True)


# ── Engine (cached) ───────────────────────────────────────────────────────────
@st.cache_resource
def get_engine():
    return RecommendationEngine()


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## 🛍️ GraphRAG Product Recommendation System")
st.markdown("<p style='color:#94a3b8'>Powered by Neo4j Knowledge Graph + LLM (Groq / llama-3.1-8b)</p>",
            unsafe_allow_html=True)
st.divider()

# ── Example queries ───────────────────────────────────────────────────────────
EXAMPLES = [
    "Best mobiles for photography",
    "Shoes for running under ₹200",
    "Gaming headphones under ₹500",
    "Laptops for video editing",
    "Lightweight laptop for travel under ₹800",
]

st.markdown("**Try an example:**")
cols = st.columns(len(EXAMPLES))
for i, ex in enumerate(EXAMPLES):
    if cols[i].button(ex, key=f"ex_{i}"):
        st.session_state["query_input"] = ex

# ── Search bar ────────────────────────────────────────────────────────────────
query = st.text_input(
    "🔍 Ask anything about products",
    placeholder='e.g. "Best mobiles for photography under ₹15000"',
    key="query_input",
    label_visibility="collapsed",
)

search_clicked = st.button("Search", type="primary", use_container_width=False)

# ── Results ───────────────────────────────────────────────────────────────────
if query and search_clicked or (query and st.session_state.get("query_input") == query and search_clicked):
    try:
        engine = get_engine()

        with st.spinner("Searching knowledge graph..."):
            result = engine.recommend(query)

        recs   = result.get("recommendations", [])
        parsed = result.get("parsed", {})

        # Parsed params display
        with st.expander("🔎 Query Analysis", expanded=False):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Category",  parsed.get("category")  or "—")
            c2.metric("Use Case",  parsed.get("use_case")  or "—")
            c3.metric("Max Price", f"₹{parsed.get('max_price')}" if parsed.get("max_price") else "Any")
            c4.metric("Intent",    parsed.get("intent")    or "—")

        st.markdown(f"### Results for: *{query}*")

        if not recs:
            st.warning("No recommendations found. Try a different query or add more datasets.")
        else:
            for i, r in enumerate(recs, 1):
                rating_stars = "⭐" * int(float(r.get("rating") or 0))
                rating_val   = r.get("rating") or "N/A"
                price        = r.get("price", "N/A")

                st.markdown(f"""
                <div class="product-card">
                    <span class="rank-badge">{i}</span>
                    <span class="product-name">{r.get('name', 'N/A')}</span><br><br>
                    <span class="product-price">₹{price}</span>
                    &nbsp;&nbsp;
                    <span class="product-rating">{rating_stars} {rating_val}/5</span>
                    <p class="product-reason">💡 {r.get('reason', '')}</p>
                </div>
                """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error: {e}")
        st.info("Make sure Neo4j is running and data is ingested.")

elif query and not search_clicked:
    st.info("Press **Search** to get recommendations.")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ System Info")
    st.markdown(f"**LLM:** `{os.getenv('LLM_MODEL', 'llama-3.1-8b-instant')}`")
    st.markdown(f"**Provider:** `{os.getenv('LLM_PROVIDER', 'groq')}`")
    st.markdown(f"**Graph DB:** Neo4j")
    st.divider()
    st.markdown("### 📊 How it works")
    st.markdown("""
    1. **Parse** — LLM extracts category, use case & price from your query
    2. **Retrieve** — Cypher queries fetch matching products from Neo4j graph
    3. **Rank** — LLM re-ranks and explains the top 5 results
    """)
    st.divider()
    st.markdown("### 🗂️ Graph Schema")
    st.code("""
(Product)-[:BELONGS_TO]->(Category)
(Product)-[:HAS_FEATURE]->(Feature)
(Product)-[:SUITABLE_FOR]->(UseCase)
(Product)-[:MADE_BY]->(Brand)
    """)
