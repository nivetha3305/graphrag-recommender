"""
rag/query_parser.py
Parses natural language queries into structured parameters using LLM.
Falls back to rule-based parsing if LLM is unavailable.

Recommended model: llama3.2 via Ollama (local, free)
  Install: https://ollama.com
  Pull:    ollama pull llama3.2
  Serve:   ollama serve
"""

import json, re, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from openai import OpenAI
from config import LLM_API_KEY, LLM_MODEL, LLM_BASE_URL


SYSTEM_PROMPT = """You are a query parser for a product recommendation system.
Extract structured information from the user query.

Return ONLY valid JSON with these fields:
{
  "category":  "product category (laptop, shoes, mobile, headphone, etc.) or null",
  "use_case":  "intended use (video editing, running, photography, gaming, etc.) or null",
  "max_price": numeric value in rupees or null,
  "features":  ["list of specific features"] or [],
  "intent":    "search" or "recommend"
}

Examples:
"Show laptops under ₹1000 suitable for video editing"
-> {"category":"laptop","use_case":"video editing","max_price":1000,"features":[],"intent":"search"}

"Recommend shoes for running under ₹200"
-> {"category":"shoes","use_case":"running","max_price":200,"features":[],"intent":"recommend"}

"Best mobiles for photography"
-> {"category":"mobile","use_case":"photography","max_price":null,"features":[],"intent":"recommend"}
"""


def parse_query(query: str) -> dict:
    """Parse natural language query. Uses LLM if available, else rule-based fallback."""
    try:
        client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": query}
            ],
            temperature=0.1,
            max_tokens=300,
        )
        content = response.choices[0].message.content.strip()
        # Strip markdown code fences if present
        if "```" in content:
            content = content.split("```")[1].split("```")[0]
            if content.startswith("json"):
                content = content[4:]
        return json.loads(content.strip())
    except Exception as e:
        print(f"[LLM parse failed: {e}] Using rule-based fallback.")
        return _fallback_parse(query)


def _fallback_parse(query: str) -> dict:
    q = query.lower()

    # Price extraction
    max_price = None
    for pattern in [r'under\s*[₹$]?\s*(\d+)', r'below\s*[₹$]?\s*(\d+)', r'[₹$]\s*(\d+)']:
        m = re.search(pattern, q)
        if m:
            max_price = float(m.group(1))
            break

    # Category
    category_map = {
        "laptop":    ["laptop", "notebook", "computer"],
        "mobile":    ["mobile", "phone", "smartphone"],
        "shoes":     ["shoes", "sneakers", "footwear", "boots", "running shoes", "sandal"],
        "headphone": ["headphone", "earphone", "earbuds"],
        "camera":    ["camera", "dslr"],
        "tablet":    ["tablet", "ipad"],
        "watch":     ["watch", "smartwatch"],
        "tv":        ["tv", "television"],
        "clothing":  ["shirt", "dress", "jeans", "clothing", "apparel"],
    }
    category = None
    for cat, keywords in category_map.items():
        if any(k in q for k in keywords):
            category = cat
            break

    # Use case
    use_case_map = {
        "video editing":  ["video editing", "editing", "creator"],
        "gaming":         ["gaming", "game"],
        "photography":    ["photography", "photo", "camera"],
        "running":        ["running", "jogging"],
        "office work":    ["office", "work", "productivity"],
        "music":          ["music", "audio"],
        "fitness":        ["fitness", "gym", "workout"],
        "travel":         ["travel", "portable"],
    }
    use_case = None
    for uc, keywords in use_case_map.items():
        if any(k in q for k in keywords):
            use_case = uc
            break

    intent = "recommend" if any(w in q for w in ["recommend", "suggest", "best", "top"]) else "search"

    return {"category": category, "use_case": use_case, "max_price": max_price, "features": [], "intent": intent}
