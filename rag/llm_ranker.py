"""
rag/llm_ranker.py
Re-ranks graph-retrieved candidates using LLM and generates explanations.
This is the "Generation" step of GraphRAG.

Model: llama3.2 (Ollama) — local, free, no API key needed.
"""

import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from openai import OpenAI
from config import LLM_API_KEY, LLM_MODEL, LLM_BASE_URL


RANKER_PROMPT = """You are a helpful product recommendation assistant.
Given a user query and candidate products retrieved from a knowledge graph,
select the TOP 5 most relevant products and explain why each fits the query.

IMPORTANT RULES:
- Always return the top 5 products from the list, even if they are not a perfect match
- Never say "none of the products match" — always pick the best available options
- If exact matches are unavailable, recommend the closest alternatives and explain why
- Be helpful and positive in your explanations

Return ONLY valid JSON:
{
  "recommendations": [
    {
      "name":   "product name",
      "price":  price as number,
      "rating": rating as number or null,
      "reason": "concise explanation of why this fits the query"
    }
  ]
}
"""


def rank_and_explain(query: str, candidates: list) -> dict:
    """LLM re-ranking with graph context. Falls back to rating sort."""
    if not candidates:
        return {"recommendations": []}

    if not LLM_API_KEY or LLM_API_KEY == "":
        return _fallback_rank(candidates)

    # Build candidate summary for LLM context
    candidate_text = "\n".join([
        f"{i+1}. {c['name']} | ₹{c['price']} | Rating: {c.get('rating','N/A')} | "
        f"Category: {c.get('category','N/A')} | "
        f"Use Cases: {', '.join(c.get('use_cases', []))} | "
        f"Features: {', '.join(c.get('features', [])[:5])}"
        for i, c in enumerate(candidates[:20])
    ])

    try:
        client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": RANKER_PROMPT},
                {"role": "user",   "content": f"Query: {query}\n\nCandidates:\n{candidate_text}"}
            ],
            temperature=0.3,
            max_tokens=800,
        )
        content = response.choices[0].message.content.strip()
        if "```" in content:
            content = content.split("```")[1].split("```")[0]
            if content.startswith("json"):
                content = content[4:]
        return json.loads(content.strip())
    except Exception as e:
        print(f"[LLM ranking failed: {e}] Using fallback.")
        return _fallback_rank(candidates)


def _fallback_rank(candidates: list) -> dict:
    """Sort by rating desc, price asc."""
    top5 = sorted(candidates, key=lambda x: (-(x.get("rating") or 0), x.get("price", 1e9)))[:5]
    return {
        "recommendations": [
            {
                "name":   c["name"],
                "price":  c["price"],
                "rating": c.get("rating"),
                "reason": f"Rated {c.get('rating','N/A')}/5 — good value at ₹{c['price']}."
            }
            for c in top5
        ]
    }
