from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/generate-plan")
def generate_plan(data: dict):
    return {
        "markdown": f"Plan généré avec succès ✅\n\nDonnées reçues : {data}"
    }
