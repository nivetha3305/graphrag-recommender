# Tools & Libraries Used

## 1. Python 3.13
- Core programming language for the entire project
- Used across all files for data processing, API calls, graph operations, and web UI

---

## 2. Pandas
- Python library for data manipulation and analysis
- Used in: `scripts/preprocess.py`

```python
import pandas as pd

df = pd.read_csv("amazon.csv")
df.rename(columns={"product_name": "name"}, inplace=True)
df["price"] = df["price"].apply(clean_price)
df = df.drop_duplicates(subset=["name", "category"])
```

---

## 3. Neo4j
- Native graph database — stores data as nodes and relationships
- Used in: `graph/ingest.py`, `graph/queries.py`, `graph/schema.py`

```python
from neo4j import GraphDatabase
driver = GraphDatabase.driver("neo4j://127.0.0.1:7687", auth=("neo4j", "password"))
```

Why not MySQL?
- MySQL needs complex JOINs for relationship queries
- Neo4j handles relationships natively and efficiently

---

## 4. Cypher Query Language
- Neo4j's query language (like SQL but for graphs)
- Used in: `graph/queries.py`, `graph/ingest.py`

```cypher
MATCH (p:Product)-[:BELONGS_TO]->(c:Category),
      (p)-[:SUITABLE_FOR]->(u:UseCase)
WHERE toLower(c.name) CONTAINS 'mobile'
  AND toLower(u.name) CONTAINS 'photography'
  AND p.price <= 30000
RETURN p.name, p.price, p.rating
ORDER BY p.rating DESC
LIMIT 20
```

---

## 5. Groq API + llama-3.1-8b-instant
- Groq: cloud platform for fast LLM inference (free)
- llama-3.1-8b: open-source AI model by Meta
- Used in: `rag/query_parser.py`, `rag/llm_ranker.py`

Two uses:
1. Parse natural language query → structured JSON
2. Rank candidates → top 5 with explanations

Why Groq over OpenAI?
- OpenAI costs money per request
- Groq is free and gives sub-second responses

---

## 6. OpenAI Python Library
- Used as the API client to call Groq (Groq is OpenAI-compatible)
- Used in: `rag/query_parser.py`, `rag/llm_ranker.py`

```python
from openai import OpenAI
client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
response = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[...])
```

---

## 7. Streamlit
- Python library to build web apps — no HTML/CSS/JS needed
- Used in: `ui.py`

```python
import streamlit as st
st.title("GraphRAG Recommender")
query = st.text_input("Search products...")
if st.button("Search"):
    result = engine.recommend(query)
```

Run with: `streamlit run ui.py` → opens at `localhost:8501`

---

## 8. python-dotenv
- Loads environment variables from `.env` file
- Keeps API keys and passwords out of source code
- Used in: `app.py`, `ui.py`

```python
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
```

---

## 9. Rich
- Python library for beautiful terminal output
- Used in: `app.py` (CLI version)

```python
from rich.console import Console
from rich.table import Table
console = Console()
console.print("[bold green]Results found![/]")
```

---

## 10. Kaggle Datasets
- Free open datasets used as data source

| Dataset | Products | Categories |
|---|---|---|
| Amazon Sales Dataset | 1,337 | Electronics, Accessories |
| Flipkart E-commerce Sample | 12,689 | Footwear, Clothing, Electronics |
| Total | 14,026 | Multiple |

---

## Summary Table

| Tool / Library | Category | Used In | Purpose |
|---|---|---|---|
| Python 3.13 | Language | All files | Core programming |
| Pandas | Data library | preprocess.py | Clean & transform CSV data |
| Neo4j | Database | ingest.py, queries.py | Store knowledge graph |
| Cypher | Query language | queries.py | Search the graph |
| Groq API | AI service | query_parser, llm_ranker | LLM inference |
| llama-3.1-8b | AI model | via Groq | Parse queries, rank results |
| OpenAI library | Python library | query_parser, llm_ranker | API client for Groq |
| Streamlit | Web framework | ui.py | Web interface |
| python-dotenv | Utility | app.py, ui.py | Load .env secrets |
| Rich | Terminal UI | app.py | Colored CLI output |
| Kaggle | Data source | data/raw/ | Product datasets |
