from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from backend.youtube import search_youtube
from backend.market import analyze_market

app = FastAPI()

# CORS (pour GitHub Pages)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "https://amhalilyes-cell.github.io",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/run-agent")
def run_agent(query: str = "alex hormozi"):
    videos = search_youtube(query)
    results = analyze_market(videos)

    # on renvoie un JSON propre au frontend
    return {
        "query": query,
        "videos_found": len(videos),
        "top_opportunities": results[:10],
    }
