import os
import traceback

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from backend.youtube import search_youtube
from backend.market import analyze_market

app = FastAPI(title="LeadVision API")

# CORS simple (pour éviter les bugs)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/run-agent")
def run_agent(query: str = "alex hormozi"):
    videos = search_youtube(query, max_results=25)
    results = analyze_market(videos)
    return {
        "query": query,
        "videos_found": len(videos),
        "top_opportunities": results[:10],
    }

@app.post("/generate")
def generate(payload: dict):
    query = (payload.get("query") or "").strip()
    max_results = int(payload.get("max_results") or 10)

    if not query:
        raise HTTPException(status_code=400, detail="Missing query")

    try:
        videos = search_youtube(query, max_results=max_results)
        results = analyze_market(videos)
        return {
            "query": query,
            "videos_count": len(videos),
            "results": results,
        }
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Generation failed")

# Alias pour le frontend
@app.post("/api/generate")
def api_generate(payload: dict):
    return generate(payload)
