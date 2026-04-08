"""
graph/queries.py
Cypher query templates for structured graph retrieval.
"""

from neo4j import Driver


def _run(driver: Driver, cypher: str, params: dict) -> list:
    with driver.session() as session:
        return [dict(r) for r in session.run(cypher, **params)]


# Category keyword aliases for broader matching
CATEGORY_ALIASES = {
    "shoes":     ["shoe", "footwear", "sandal", "boot", "sneaker"],
    "laptop":    ["laptop", "notebook", "computer"],
    "mobile":    ["mobile", "phone", "smartphone"],
    "headphone": ["headphone", "earphone", "earbud"],
    "clothing":  ["clothing", "shirt", "dress", "apparel", "fashion"],
    "watch":     ["watch"],
    "camera":    ["camera", "dslr"],
    "tablet":    ["tablet"],
    "tv":        ["tv", "television"],
}


def _category_filter(category: str) -> str:
    """Build a Cypher WHERE clause that matches category aliases."""
    aliases = CATEGORY_ALIASES.get(category.lower(), [category.lower()])
    conditions = " OR ".join([f"toLower(c.name) CONTAINS '{a}'" for a in aliases])
    return f"({conditions})"


def search_by_category_and_price(driver, category: str, max_price: float) -> list:
    cat_filter = _category_filter(category)
    return _run(driver, f"""
        MATCH (p:Product)-[:BELONGS_TO]->(c:Category)
        WHERE {cat_filter}
          AND p.price <= $max_price
        RETURN p.id AS id, p.name AS name, p.price AS price,
               p.rating AS rating, p.brand AS brand, c.name AS category
        ORDER BY p.rating DESC, p.price ASC LIMIT 20
    """, {"max_price": max_price})


def search_by_use_case_and_price(driver, use_case: str, max_price: float) -> list:
    return _run(driver, """
        MATCH (p:Product)-[:SUITABLE_FOR]->(u:UseCase)
        WHERE toLower(u.name) CONTAINS toLower($use_case)
          AND p.price <= $max_price
        RETURN p.id AS id, p.name AS name, p.price AS price,
               p.rating AS rating, p.brand AS brand, p.category AS category
        ORDER BY p.rating DESC, p.price ASC LIMIT 20
    """, {"use_case": use_case, "max_price": max_price})


def search_by_category_and_use_case(driver, category: str, use_case: str, max_price: float = 1e9) -> list:
    cat_filter = _category_filter(category)
    return _run(driver, f"""
        MATCH (p:Product)-[:BELONGS_TO]->(c:Category),
              (p)-[:SUITABLE_FOR]->(u:UseCase)
        WHERE {cat_filter}
          AND toLower(u.name) CONTAINS toLower($use_case)
          AND p.price <= $max_price
        RETURN p.id AS id, p.name AS name, p.price AS price,
               p.rating AS rating, p.brand AS brand, c.name AS category
        ORDER BY p.rating DESC, p.price ASC LIMIT 20
    """, {"use_case": use_case, "max_price": max_price})


def search_by_feature(driver, feature_keyword: str, max_price: float = 1e9) -> list:
    return _run(driver, """
        MATCH (p:Product)-[:HAS_FEATURE]->(f:Feature)
        WHERE toLower(f.name) CONTAINS toLower($feature)
          AND p.price <= $max_price
        RETURN p.id AS id, p.name AS name, p.price AS price,
               p.rating AS rating, p.brand AS brand, p.category AS category
        ORDER BY p.rating DESC LIMIT 20
    """, {"feature": feature_keyword, "max_price": max_price})


def get_product_context(driver, product_id: str) -> dict:
    """Fetch full graph context for a product."""
    rows = _run(driver, """
        MATCH (p:Product {id: $id})
        OPTIONAL MATCH (p)-[:BELONGS_TO]->(c:Category)
        OPTIONAL MATCH (p)-[:HAS_FEATURE]->(f:Feature)
        OPTIONAL MATCH (p)-[:SUITABLE_FOR]->(u:UseCase)
        OPTIONAL MATCH (p)-[:MADE_BY]->(b:Brand)
        RETURN p.name AS name, p.price AS price, p.rating AS rating,
               c.name AS category, b.name AS brand,
               collect(DISTINCT f.name) AS features,
               collect(DISTINCT u.name) AS use_cases
    """, {"id": product_id})
    return rows[0] if rows else {}


def free_text_search(driver, keyword: str, max_price: float = 1e9) -> list:
    return _run(driver, """
        MATCH (p:Product)
        WHERE (toLower(p.name) CONTAINS toLower($kw)
            OR toLower(p.category) CONTAINS toLower($kw))
          AND p.price <= $max_price
        RETURN p.id AS id, p.name AS name, p.price AS price,
               p.rating AS rating, p.brand AS brand, p.category AS category
        ORDER BY p.rating DESC LIMIT 20
    """, {"kw": keyword, "max_price": max_price})
