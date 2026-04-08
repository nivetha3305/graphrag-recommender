"""
scripts/preprocess.py
Cleans and standardizes raw Kaggle product CSVs into a unified format.

Place your Kaggle CSV files in:  graphrag_recommender/data/raw/
Output goes to:                  graphrag_recommender/data/processed/products.csv

Supported Kaggle datasets (examples):
  - Amazon Sales Dataset
  - Flipkart Products Dataset
  - Any multi-category product CSV
"""

import os, sys, json, re
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import RAW_DIR, PROCESSED_DIR

# Normalize varied column names from different Kaggle datasets
COLUMN_MAP = {
    "title":                  "name",
    "product_name":           "name",
    "product":                "name",
    "main_category":          "category",
    "sub_category":           "category",
    "product_category_tree":  "category",
    "selling_price":          "price",
    "retail_price":           "price",
    "about_item":             "features",
    "about_product":          "features",
    "description":            "features",
    "product_specifications": "features",
    "ratings":                "rating",
    "product_rating":         "rating",
    "overall_rating":         "rating",
    "no_of_ratings":          "num_ratings",
    "rating_count":           "num_ratings",
}

# Price column priority: discounted_price > actual_price > price
PRICE_COLS = ["discounted_price", "actual_price", "price"]

REQUIRED_COLS = ["name", "category", "price"]


def clean_price(val) -> float:
    if val is None:
        return None
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    val = str(val).replace("₹", "").replace("$", "").replace(",", "").strip()
    try:
        return float(val)
    except ValueError:
        return None


def split_features(val) -> list:
    if pd.isna(val) or str(val).strip() == "":
        return []
    for sep in ["|", ";", ","]:
        if sep in str(val):
            return [f.strip() for f in str(val).split(sep) if f.strip()]
    return [str(val).strip()]


def infer_use_cases(row: pd.Series) -> list:
    """Rule-based use-case tagging from category + features text."""
    text = f"{row.get('category', '')} {row.get('features_raw', '')}".lower()
    rules = {
        "video editing":  ["video editing", "4k", "render", "creator", "content creation"],
        "gaming":         ["gaming", "game", "fps", "gpu", "esports"],
        "photography":    ["camera", "photo", "lens", "megapixel", "photography", "dslr"],
        "running":        ["running", "jogging", "marathon", "trail", "sport"],
        "office work":    ["office", "productivity", "spreadsheet", "word", "business"],
        "travel":         ["travel", "lightweight", "portable", "compact", "backpack"],
        "music":          ["music", "audio", "headphone", "speaker", "bass", "earphone"],
        "fitness":        ["fitness", "gym", "workout", "health", "tracker"],
    }
    cases = [case for case, kws in rules.items() if any(k in text for k in kws)]
    return cases if cases else ["general use"]


def _resolve_col(df: pd.DataFrame, col_name: str) -> pd.Series:
    """If a column is duplicated (DataFrame), merge into single Series."""
    col = df.get(col_name)
    if col is None:
        return pd.Series(dtype=str)
    if isinstance(col, pd.DataFrame):
        # Combine all duplicate columns into one string
        return col.fillna("").astype(str).apply(lambda r: " ".join(r[r != ""]), axis=1)
    return col


def process_file(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath, on_bad_lines="skip", encoding="utf-8", low_memory=False)
    df.columns = [c.lower().strip() for c in df.columns]

    # Rename one-to-one mappings only (avoid duplicate column conflicts)
    # Apply column map carefully: rename only if target doesn't already exist
    for src, tgt in COLUMN_MAP.items():
        if src in df.columns and tgt not in df.columns:
            df.rename(columns={src: tgt}, inplace=True)

    # Handle price: pick first available price column
    if "price" not in df.columns:
        for col in PRICE_COLS:
            if col in df.columns:
                df["price"] = df[col]
                break

    # Resolve any duplicate columns into single Series
    for col in ["name", "category", "price", "features", "rating"]:
        if isinstance(df.get(col), pd.DataFrame):
            df[col] = _resolve_col(df, col)

    for col in REQUIRED_COLS:
        if col not in df.columns:
            print(f"  [skip] Missing '{col}' in {os.path.basename(filepath)}")
            return pd.DataFrame()

    df = df.dropna(subset=["name"])

    # Clean category: Flipkart uses tree format like "Clothing >> Shoes >> Running"
    if "category" in df.columns:
        df["category"] = df["category"].apply(
            lambda x: str(x).split(">>")[1].strip() if ">>" in str(x) else str(x).split("|")[0].strip()
        )

    df["price"] = df["price"].apply(clean_price)
    df = df[df["price"].notna() & (df["price"] > 0)]

    # Build features_raw from whichever feature columns exist
    feat_cols = [c for c in ["features", "description", "product_specifications", "about_product", "about_item"] if c in df.columns]
    if feat_cols:
        df["features_raw"] = df[feat_cols[0]].fillna("").astype(str)
    else:
        df["features_raw"] = ""

    df["features"]  = df["features_raw"].apply(split_features)
    df["use_cases"] = df.apply(infer_use_cases, axis=1)

    if "rating" not in df.columns:
        df["rating"] = None
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")

    if "brand" not in df.columns:
        df["brand"] = df["name"].apply(lambda x: str(x).split()[0] if pd.notna(x) else "Unknown")

    df = df.drop_duplicates(subset=["name", "category"])
    return df[["name", "category", "price", "rating", "brand", "features", "use_cases"]]


def run():
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    csv_files = [f for f in os.listdir(RAW_DIR) if f.endswith(".csv")]

    if not csv_files:
        print(f"No CSV files in {RAW_DIR}")
        print("Download a dataset from Kaggle (e.g. Amazon Sales Dataset) and place it there.")
        return

    frames = []
    for fname in csv_files:
        print(f"Processing {fname}...")
        df = process_file(os.path.join(RAW_DIR, fname))
        if not df.empty:
            frames.append(df)
            print(f"  -> {len(df)} products")

    if not frames:
        print("No data processed.")
        return

    combined = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["name", "category"])
    combined["features"]  = combined["features"].apply(json.dumps)
    combined["use_cases"] = combined["use_cases"].apply(json.dumps)

    out = os.path.join(PROCESSED_DIR, "products.csv")
    combined.to_csv(out, index=False)
    print(f"\nSaved {len(combined)} products -> {out}")


if __name__ == "__main__":
    run()
