"""
rag/graph_retriever.py
Routes parsed query parameters to the best Cypher query strategy.
Returns enriched candidate products with full graph context.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from graph import queries


def retrieve(driver, parsed: dict) -> list:
    """
    Smart routing:
      category + use_case + price  -> most specific
      category + price             -> category filter
      use_case + price             -> use-case filter
      features                     -> feature search
      keyword fallback             -> broad text search
    """
    category  = parsed.get("category")
    use_case  = parsed.get("use_case")
    max_price = parsed.get("max_price") or 1e9
    features  = parsed.get("features", [])

    results = []

    if category and use_case:
        results = queries.search_by_category_and_use_case(driver, category, use_case, max_price)

    if not results and category:
        results = queries.search_by_category_and_price(driver, category, max_price)

    if not results and use_case:
        results = queries.search_by_use_case_and_price(driver, use_case, max_price)

    if not results:
        for feat in features:
            results = queries.search_by_feature(driver, feat, max_price)
            if results:
                break

    if not results:
        keyword = category or use_case or (features[0] if features else "")
        if keyword:
            results = queries.free_text_search(driver, keyword, max_price)

    # Enrich with full graph context (features, use_cases, brand)
    enriched = []
    for r in results:
        ctx = queries.get_product_context(driver, r["id"])
        enriched.append({**r, **ctx})

    return enriched
