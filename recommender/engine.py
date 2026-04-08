"""
recommender/engine.py
Main GraphRAG pipeline:
  1. Parse natural language query  (LLM / fallback)
  2. Retrieve candidates from Neo4j graph  (Cypher)
  3. Re-rank and explain with LLM
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
from rag.query_parser import parse_query
from rag.graph_retriever import retrieve
from rag.llm_ranker import rank_and_explain


class RecommendationEngine:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def close(self):
        self.driver.close()

    def recommend(self, query: str) -> dict:
        """
        Full GraphRAG pipeline.
        Returns:
          {
            "query":           original query string,
            "parsed":          structured parameters extracted by LLM,
            "recommendations": top-5 ranked products with explanations
          }
        """
        parsed     = parse_query(query)
        print(f"[Parsed]    {parsed}")

        candidates = retrieve(self.driver, parsed)
        print(f"[Retrieved] {len(candidates)} candidates from graph")

        result     = rank_and_explain(query, candidates)

        return {
            "query":           query,
            "parsed":          parsed,
            "recommendations": result.get("recommendations", [])
        }
