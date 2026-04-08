"""
app.py - CLI entrypoint for the GraphRAG Product Recommendation System

Usage:
  python app.py                          # interactive mode
  python app.py "Best mobiles for photography"
  python app.py --ingest                 # ingest data into Neo4j
  python app.py --preprocess             # preprocess raw CSVs
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

EXAMPLE_QUERIES = [
    "Show laptops under ₹1000 suitable for video editing",
    "Recommend shoes for running under ₹200",
    "Best mobiles for photography",
    "Gaming headphones under ₹500",
    "Lightweight laptop for travel under ₹800",
]


def print_recommendations(result: dict):
    recs = result.get("recommendations", [])
    query = result.get("query", "")

    console.print(Panel(f"[bold cyan]Query:[/] {query}", box=box.ROUNDED))

    parsed = result.get("parsed", {})
    console.print(f"[dim]Parsed → category:[/] {parsed.get('category')} | "
                  f"[dim]use_case:[/] {parsed.get('use_case')} | "
                  f"[dim]max_price:[/] ₹{parsed.get('max_price')}")

    if not recs:
        console.print("[yellow]No recommendations found. Try a different query or check your data.[/]")
        return

    table = Table(title="Top Recommendations", box=box.SIMPLE_HEAVY, show_lines=True)
    table.add_column("#",       style="dim",    width=3)
    table.add_column("Product", style="bold",   min_width=30)
    table.add_column("Price",   style="green",  width=10)
    table.add_column("Rating",  style="yellow", width=8)
    table.add_column("Why",     style="white",  min_width=40)

    for i, r in enumerate(recs, 1):
        table.add_row(
            str(i),
            r.get("name", "N/A"),
            f"₹{r.get('price', 'N/A')}",
            str(r.get("rating", "N/A")),
            r.get("reason", ""),
        )

    console.print(table)


def run_interactive():
    from recommender.engine import RecommendationEngine

    console.print(Panel(
        "[bold green]GraphRAG Product Recommendation System[/]\n"
        "[dim]Powered by Neo4j + LLM (llama3.2 via Ollama)[/]",
        box=box.DOUBLE
    ))

    console.print("\n[bold]Example queries:[/]")
    for q in EXAMPLE_QUERIES:
        console.print(f"  [cyan]•[/] {q}")

    engine = RecommendationEngine()
    try:
        while True:
            console.print()
            query = console.input("[bold yellow]Enter query (or 'quit'):[/] ").strip()
            if query.lower() in ("quit", "exit", "q"):
                break
            if not query:
                continue
            result = engine.recommend(query)
            print_recommendations(result)
    except KeyboardInterrupt:
        pass
    finally:
        engine.close()
        console.print("\n[dim]Goodbye.[/]")


def run_single(query: str):
    from recommender.engine import RecommendationEngine
    engine = RecommendationEngine()
    try:
        result = engine.recommend(query)
        print_recommendations(result)
    finally:
        engine.close()


def run_ingest():
    from graph.ingest import run
    run()


def run_preprocess():
    from scripts.preprocess import run
    run()


if __name__ == "__main__":
    args = sys.argv[1:]

    if "--preprocess" in args:
        run_preprocess()
    elif "--ingest" in args:
        run_ingest()
    elif args:
        run_single(" ".join(args))
    else:
        run_interactive()
