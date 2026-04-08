"""
config.py - Neo4j and LLM configuration
Supports: Ollama (local/free), Groq (free API), OpenAI
"""
import os

# Neo4j connection
NEO4J_URI      = os.getenv("NEO4J_URI",      "bolt://localhost:7687")
NEO4J_USER     = os.getenv("NEO4J_USER",     "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# Data paths
DATA_DIR      = os.path.join(os.path.dirname(__file__), "data")
RAW_DIR       = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")

# ─── LLM Provider ────────────────────────────────────────────────────────────
# Options: "ollama" (local, free) | "groq" (free API) | "openai"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")

if LLM_PROVIDER == "ollama":
    # Run locally: `ollama pull llama3.2` then `ollama serve`
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
    LLM_API_KEY  = "ollama"
    LLM_MODEL    = os.getenv("LLM_MODEL", "llama3.2")   # or mistral, qwen2.5

elif LLM_PROVIDER == "groq":
    # Free at console.groq.com — very fast inference
    LLM_BASE_URL = "https://api.groq.com/openai/v1"
    LLM_API_KEY  = os.getenv("GROQ_API_KEY", "")
    LLM_MODEL    = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")

elif LLM_PROVIDER == "openai":
    LLM_BASE_URL = "https://api.openai.com/v1"
    LLM_API_KEY  = os.getenv("OPENAI_API_KEY", "")
    LLM_MODEL    = os.getenv("LLM_MODEL", "gpt-4o-mini")

else:
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
    LLM_API_KEY  = os.getenv("LLM_API_KEY",  "ollama")
    LLM_MODEL    = os.getenv("LLM_MODEL",    "llama3.2")
