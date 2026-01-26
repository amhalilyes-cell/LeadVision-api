import os
import json
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .opportunity_mapper import get_fear_radar, get_opportunity_map
from .env import load_env
load_env(".env")
from .db import init_db, insert_plan, list_plans, get_plan
from .auth import require_api_key

# On réutilise ton V5 pour générer + exporter
from .opportunity_v5 import slug, render_markdown, compact_for_ui, write_json, ensure_output_dir
from .opportunity_v4 import load_videos, load_snapshots, get_winners, summarize_market, call_openai_v4


app = FastAPI(title="YouTube Intelligence API", version="0.1")

# ✅ AJOUT: CORS (corrige OPTIONS 405 + permet au site sur 5500 d'appeler l'API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GeneratePlanRequest(BaseModel):
    niche: str = "saas"
    objective: str = "leads"         # leads/sales/launch/visibility/authority
    threshold_vpd: int = 20000
    top_k: int = 25
    ideas: int = 6
    days: int = 30
    force: bool = False              # si True, regénère même si cache existe (v2 plus tard)


@app.on_event("startup")
def startup():
    load_env(".env")
    init_db()
    ensure_output_dir()


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/fear-radar")
def fear_radar(x_api_key: Optional[str] = Header(default=None, alias="X-API-KEY")):
    require_api_key(x_api_key)
    return get_fear_radar()


@app.get("/opportunity-map")
def opportunity_map(
    niche: str = "saas",
    x_api_key: Optional[str] = Header(default=None, alias="X-API-KEY"),
):
    require_api_key(x_api_key)
    return get_opportunity_map(niche=niche)


@app.get("/plans")
def plans(limit: int = 20):
    return {"plans": list_plans(limit=limit)}


@app.get("/plans/{plan_id}")
def plan(plan_id: int):
    row = get_plan(plan_id)
    if not row:
        raise HTTPException(status_code=404, detail="Plan not found")
    return row


@app.get("/plans/{plan_id}/content")
def plan_content(plan_id: int, format: str = "ui"):
    """
    format: ui | json | md
    """
    row = get_plan(plan_id)
    if not row:
        raise HTTPException(status_code=404, detail="Plan not found")

    if format == "ui":
        path = row["plan_ui_json_path"]
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    if format == "json":
        path = row["plan_json_path"]
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    if format == "md":
        path = row["plan_md_path"]
        with open(path, "r", encoding="utf-8") as f:
            return {"markdown": f.read()}

    raise HTTPException(status_code=400, detail="Invalid format")


@app.post("/generate-plan")
def generate_plan(req: GeneratePlanRequest):
    # 1) Charger data
    videos = load_videos()
    snaps = load_snapshots()

    winners = get_winners(videos, snaps, req.threshold_vpd, req.top_k)
    if not winners:
        raise HTTPException(
            status_code=400,
            detail="No winners found (need >=2 snapshots per video). Run seed_scan again.",
        )

    intel = summarize_market(videos, winners)

    # 2) Générer via OpenAI (V4)
    plan = call_openai_v4(
        intel=intel,
        niche_fr=req.niche,
        objective=req.objective,
        ideas=req.ideas,
        days=req.days,
    )

    # 3) Export files (V5)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = f"plan_{slug(req.niche)}_{slug(req.objective)}_{stamp}"
    json_path = os.path.join("output", base + ".json")
    md_path = os.path.join("output", base + ".md")
    ui_path = os.path.join("output", base + "_ui.json")

    write_json(json_path, plan)

    md = render_markdown(plan)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)

    ui = compact_for_ui(plan)
    write_json(ui_path, ui)

    # 4) Insert DB
    row = {
        "created_at": datetime.now().isoformat(),
        "niche": req.niche,
        "objective": req.objective,
        "threshold_vpd": req.threshold_vpd,
        "top_k": req.top_k,
        "ideas": req.ideas,
        "days": req.days,
        "plan_json_path": json_path,
        "plan_md_path": md_path,
        "plan_ui_json_path": ui_path,
    }
    plan_id = insert_plan(row)

    # ✅ AJOUT: retourner le markdown directement pour l'afficher sur ton site
    return {
        "id": plan_id,
        "markdown": md,
        "meta": {
            "niche": req.niche,
            "objective": req.objective,
            "ideas": req.ideas,
            "days": req.days,
        },
        "files": {"json": json_path, "md": md_path, "ui": ui_path},
    }