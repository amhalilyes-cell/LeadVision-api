from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# ✅ CORS (garde ça)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://amhalilyes-cell.github.io", "http://localhost:5500", "http://127.0.0.1:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/generate-plan")
def generate_plan(data: dict):
    niche = data.get("niche", "")
    objective = data.get("objective", "")
    ideas = data.get("ideas", 6)
    days = data.get("days", 30)

    md = f"""# Plan YouTube (MVP)

## Infos
- **Niche**: {niche}
- **Objectif**: {objective}
- **Idées**: {ideas}
- **Durée**: {days} jours

## 6 idées de vidéos
1. Vidéo 1: ...
2. Vidéo 2: ...
3. Vidéo 3: ...
4. Vidéo 4: ...
5. Vidéo 5: ...
6. Vidéo 6: ...

## CTA
- Lien en bio
- Commentaire épinglé
- Offre gratuite
"""
    return {"markdown": md}
