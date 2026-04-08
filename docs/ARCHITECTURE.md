# Architecture & System Design

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        USER LAYER                           │
│                                                             │
│         Browser → Streamlit UI (localhost:8501)             │
└─────────────────────────┬───────────────────────────────────┘
                          │  Natural Language Query
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                        │
│                                                             │
│   ┌─────────────┐   ┌──────────────┐   ┌───────────────┐   │
│   │query_parser │ → │graph_retriever│ → │  llm_ranker   │   │
│   │  (LLM)      │   │  (Cypher)    │   │   (LLM)       │   │
│   └─────────────┘   └──────────────┘   └───────────────┘   │
│          ↑                  ↑                  ↑            │
│          └──────────────────┴──────────────────┘           │
│                    engine.py (Orchestrator)                 │
└──────────┬──────────────────────────────────┬──────────────┘
           │                                  │
           ▼                                  ▼
┌─────────────────────┐            ┌─────────────────────┐
│    GROQ API         │            │   NEO4J DATABASE     │
│  llama-3.1-8b       │            │  Knowledge Graph     │
│  (Cloud LLM)        │            │  14,026 products     │
└─────────────────────┘            └─────────────────────┘
                                            ↑
                                   ┌────────┴────────┐
                                   │   DATA LAYER    │
                                   │  preprocess.py  │
                                   │  ingest.py      │
                                   │  Amazon CSV     │
                                   │  Flipkart CSV   │
                                   └─────────────────┘
```

---

## 2. Knowledge Graph Schema

```
        ┌──────────────┐
        │   Category   │
        │  (e.g Mobile)│
        └──────┬───────┘
               │ BELONGS_TO
               │
        ┌──────▼───────┐      MADE_BY      ┌─────────┐
        │   Product    │──────────────────▶│  Brand  │
        │  OnePlus 10T │                   │ OnePlus │
        │  ₹49,999     │                   └─────────┘
        │  Rating: 4.2 │
        └──────┬───────┘
               │
       ┌───────┴────────┐
       │                │
  HAS_FEATURE      SUITABLE_FOR
       │                │
       ▼                ▼
┌────────────┐   ┌─────────────┐
│  Feature   │   │   UseCase   │
│ 50MP Camera│   │ Photography │
└────────────┘   └─────────────┘
```

Relationships:
- `(Product)-[:BELONGS_TO]->(Category)`
- `(Product)-[:HAS_FEATURE]->(Feature)`
- `(Product)-[:SUITABLE_FOR]->(UseCase)`
- `(Product)-[:MADE_BY]->(Brand)`

---

## 3. GraphRAG Pipeline

```
Step 1: PARSE
─────────────
User: "Best mobiles for photography under ₹30000"
         │
         ▼
    Groq LLM (llama-3.1-8b)
         │
         ▼
    {
      category:  "mobile",
      use_case:  "photography",
      max_price: 30000,
      intent:    "recommend"
    }

Step 2: RETRIEVE
────────────────
Parsed params → graph_retriever.py → Cypher on Neo4j
         │
         ▼
    MATCH (p:Product)-[:BELONGS_TO]->(c:Category),
          (p)-[:SUITABLE_FOR]->(u:UseCase)
    WHERE c.name CONTAINS 'mobile'
      AND u.name CONTAINS 'photography'
      AND p.price <= 30000
    RETURN p ORDER BY p.rating DESC
         │
         ▼
    20 candidate products

Step 3: RANK & GENERATE
────────────────────────
20 candidates + original query → Groq LLM → Top 5 with explanations
```

---

## 4. Technology Stack

```
┌─────────────────────────────────────────────┐
│              PRESENTATION LAYER             │
│         Streamlit (Python web UI)           │
│         localhost:8501                      │
└─────────────────────────────────────────────┘
┌─────────────────────────────────────────────┐
│               BUSINESS LAYER               │
│  query_parser → retriever → ranker          │
│  engine.py (orchestrator)                   │
└─────────────────────────────────────────────┘
┌──────────────────┬──────────────────────────┐
│   AI LAYER       │      DATA LAYER          │
│  Groq API        │   Neo4j Graph DB         │
│  llama-3.1-8b    │   bolt://localhost:7687  │
│  - Parse query   │   14,026 product nodes   │
│  - Rank results  │   Cypher queries         │
└──────────────────┴──────────────────────────┘
┌─────────────────────────────────────────────┐
│               DATA SOURCE LAYER             │
│   Amazon CSV (1,337) + Flipkart CSV (12,689)│
│   Kaggle Open Datasets                      │
└─────────────────────────────────────────────┘
```

---

## 5. Request-Response Flow

```
1.  User types query in browser
2.  Streamlit calls engine.recommend(query)
3.  engine calls query_parser.parse_query(query)
4.  query_parser sends query to Groq API
5.  Groq returns structured JSON {category, use_case, price}
6.  engine calls graph_retriever.retrieve(driver, parsed)
7.  graph_retriever picks best Cypher query strategy
8.  Cypher query runs on Neo4j, returns 20 products
9.  engine calls llm_ranker.rank_and_explain(query, candidates)
10. Groq LLM picks top 5, writes explanation for each
11. Results returned to Streamlit UI
12. User sees product cards with price, rating, reason
```

---

## 6. Fallback Design

```
LLM Available?
      │
   YES│              NO
      ▼               ▼
 Groq API        Rule-based parser
 parses query    (regex + keywords)
      │               │
      └───────┬────────┘
              ▼
         Graph retrieval
              │
         LLM Available?
              │
           YES│              NO
              ▼               ▼
         Groq ranks       Sort by rating
         top 5            + price (fallback)
```

System never crashes — works even without internet or API access.
