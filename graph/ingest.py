"""
graph/ingest.py
Loads processed products CSV into Neo4j as a knowledge graph.
Uses batched MERGE for idempotent ingestion (safe to re-run).
"""

import os, sys, json, uuid
import pandas as pd
from neo4j import GraphDatabase

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, PROCESSED_DIR
from graph.schema import apply_schema

BATCH_SIZE = 500

# Merge products, categories, brands
MERGE_PRODUCT = """
UNWIND $rows AS row
MERGE (p:Product {id: row.id})
SET   p.name     = row.name,
      p.price    = row.price,
      p.rating   = row.rating,
      p.brand    = row.brand,
      p.category = row.category
MERGE (c:Category {name: row.category})
MERGE (p)-[:BELONGS_TO]->(c)
MERGE (b:Brand {name: row.brand})
MERGE (p)-[:MADE_BY]->(b)
"""

# Merge features
MERGE_FEATURES = """
UNWIND $rows AS row
MATCH (p:Product {id: row.id})
UNWIND row.features AS feat
MERGE (f:Feature {name: feat})
MERGE (p)-[:HAS_FEATURE]->(f)
"""

# Merge use cases
MERGE_USECASES = """
UNWIND $rows AS row
MATCH (p:Product {id: row.id})
UNWIND row.use_cases AS uc
MERGE (u:UseCase {name: uc})
MERGE (p)-[:SUITABLE_FOR]->(u)
"""


def _batches(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i: i + size]


def ingest(driver, df: pd.DataFrame):
    rows = []
    for _, r in df.iterrows():
        features  = json.loads(r["features"])  if isinstance(r["features"],  str) else r["features"]
        use_cases = json.loads(r["use_cases"]) if isinstance(r["use_cases"], str) else r["use_cases"]
        rows.append({
            "id":        str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{r['name']}_{r['category']}")),
            "name":      str(r["name"]),
            "price":     float(r["price"])  if pd.notna(r["price"])  else 0.0,
            "rating":    float(r["rating"]) if pd.notna(r["rating"]) else None,
            "brand":     str(r["brand"])    if pd.notna(r["brand"])  else "Unknown",
            "category":  str(r["category"]),
            "features":  [f[:100] for f in features[:10]],
            "use_cases": use_cases,
        })

    with driver.session() as session:
        for batch in _batches(rows, BATCH_SIZE):
            session.run(MERGE_PRODUCT,  rows=batch)
        print("  Products & categories merged.")
        for batch in _batches(rows, BATCH_SIZE):
            session.run(MERGE_FEATURES, rows=batch)
        print("  Features merged.")
        for batch in _batches(rows, BATCH_SIZE):
            session.run(MERGE_USECASES, rows=batch)
        print("  Use cases merged.")


def run():
    csv_path = os.path.join(PROCESSED_DIR, "products.csv")
    if not os.path.exists(csv_path):
        print(f"Run scripts/preprocess.py first. File not found: {csv_path}")
        return

    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} products.")

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        apply_schema(driver)
        ingest(driver, df)
        print("Ingestion complete.")
    finally:
        driver.close()


if __name__ == "__main__":
    run()
