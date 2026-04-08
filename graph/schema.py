"""
graph/schema.py
Creates Neo4j constraints and indexes.

Knowledge Graph schema:
  Nodes:         Product, Category, Feature, UseCase, Brand
  Relationships:
    (Product)-[:BELONGS_TO]->(Category)
    (Product)-[:HAS_FEATURE]->(Feature)
    (Product)-[:SUITABLE_FOR]->(UseCase)
    (Product)-[:MADE_BY]->(Brand)
"""

CONSTRAINTS = [
    "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Product)  REQUIRE p.id   IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Category) REQUIRE c.name IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (f:Feature)  REQUIRE f.name IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (u:UseCase)  REQUIRE u.name IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (b:Brand)    REQUIRE b.name IS UNIQUE",
]

INDEXES = [
    "CREATE INDEX IF NOT EXISTS FOR (p:Product) ON (p.price)",
    "CREATE INDEX IF NOT EXISTS FOR (p:Product) ON (p.rating)",
    "CREATE INDEX IF NOT EXISTS FOR (p:Product) ON (p.name)",
]


def apply_schema(driver):
    with driver.session() as session:
        for stmt in CONSTRAINTS + INDEXES:
            session.run(stmt)
    print("Schema applied.")
