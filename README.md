# GraphRAG Product Recommendation System

Intelligent product recommendations using **Neo4j Knowledge Graph** + **GraphRAG** + **LLM**.

## Architecture

```
User Query (NL)
      │
      ▼
 query_parser.py  ──── LLM (llama3.2) ────► structured params
      │                                     {category, use_case, max_price}
      ▼
 graph_retriever.py ── Cypher queries ────► candidate products
      │                  (Neo4j)
      ▼
 llm_ranker.py ──────── LLM (llama3.2) ──► top-5 + explanations
      │
      ▼
 Recommendations
```

## Knowledge Graph Schema

```
(Product)-[:BELONGS_TO]->(Category)
(Product)-[:HAS_FEATURE]->(Feature)
(Product)-[:SUITABLE_FOR]->(UseCase)
(Product)-[:MADE_BY]->(Brand)
```

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Start Neo4j
Download from https://neo4j.com/download/ or use Docker:
```bash
docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:latest
```

### 3. Setup LLM (Ollama — local & free)
```bash
# Install Ollama from https://ollama.com
ollama pull llama3.2
ollama serve
```

### 4. Configure environment
```bash
cp .env.example .env
# Edit .env with your Neo4j password
```

### 5. Add data
Download any product dataset from Kaggle (e.g. "Amazon Sales Dataset")
and place the CSV files in `data/raw/`.

### 6. Preprocess & ingest
```bash
python app.py --preprocess   # clean CSVs -> data/processed/products.csv
python app.py --ingest       # load into Neo4j
```

### 7. Run
```bash
python app.py                                          # interactive mode
python app.py "Best mobiles for photography"           # single query
python app.py "Laptops under 1000 for video editing"
```

## Example Queries
- `Show laptops under ₹1000 suitable for video editing`
- `Recommend shoes for running under ₹200`
- `Best mobiles for photography`
- `Gaming headphones under ₹500`

## LLM Options

| Provider | Cost | Speed | Setup |
|----------|------|-------|-------|
| **Ollama (llama3.2)** | Free | Medium | Local install |
| **Groq (llama-3.1-8b)** | Free API | Very fast | API key at console.groq.com |
| OpenAI (gpt-4o-mini) | Paid | Fast | API key |
