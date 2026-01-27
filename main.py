from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from backend.youtube import search_youtube
from backend.market import analyze_market

app = FastAPI()

# 🔐 CORS : autorise ton site public
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "https://amhalilyes-cell.github.io",
        "https://amhalilyes-cell.github.io/LeadVision",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

def run_agent(query: str):
    videos = search_youtube(query)
    results = analyze_market(videos)

    lines = []
    lines.append(f"# Résultats pour : {query}\n")
    lines.append(f"**Vidéos analysées :** {len(videos)}\n")
    lines.append("## TOP OPPORTUNITIES\n")

    for r in results[:10]:
        lines.append(
            f"- **{int(r['score'])}** | "
            f"**{int(r['views_per_day'])} v/j** | "
            f"**{round(r['like_rate']*100,2)}%** | "
            f"{r['title']}"
        )

    return "\n".join(lines)

@app.post("/generate-plan")
def generate_plan(data: dict):
    query = data.get("niche") or "alex hormozi"
    markdown = run_agent(query)
    return {"markdown": markdown}
