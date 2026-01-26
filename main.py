from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# ✅ CORS pour GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://amhalilyes-cell.github.io",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/generate-plan")
def generate_plan(data: dict):
    return {
        "markdown": f"Plan généré avec succès ✅\n\nDonnées reçues : {data}"
    }
