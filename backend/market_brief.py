from datetime import datetime
from typing import Dict, Any

from .opportunity_mapper import get_fear_radar, get_opportunity_map

def build_market_brief(niche: str = "business", objective: str = "leads", period: str = "weekly") -> Dict[str, Any]:
    fear = get_fear_radar(niche=niche)
    opp = get_opportunity_map(niche=niche)

    # Top fears (3 max)
    top_fears = []
    for item in fear.get("fear_radar", [])[:3]:
        top_fears.append({
            "fear_key": item["fear_key"],
            "fear_label_fr": item["fear_label_fr"],
            "signal": {
                "sum_views_per_day": item["sum_views_per_day"],
                "videos_count": item["videos_count"]
            },
            "proof": item.get("examples", [])[:3]
        })

    # Top opportunities (3 max) -> on prend celles liées aux top fears
    top_opps = []
    rid = 1
    for entry in (opp.get("fear_radar", [])[:3]):
        fear_obj = entry.get("fear", {})
        signal = entry.get("signal", {})
        # On prend 1-2 hooks comme opportunité "actionnable"
        hooks = fear_obj.get("video_hooks", [])[:2]
        if not hooks:
            continue
        top_opps.append({
            "id": rid,
            "title": hooks[0],
            "why_now": "Signal US (views/jour) + pattern 'expert + deadline + risque' observé sur winners",
            "angle": (fear_obj.get("business_angles", ["Angle business"])[0]),
            "lever_combo": ["authority", "fear", "future_ai"]  # simplifié V1
        })
        rid += 1

    # What to avoid (V1)
    what_to_avoid = [{"reason": "Hors-niche / bruit", "examples": ["insulin", "ozempic", "keto", "poo", "gut"]}]

    # Action plan (V1)
    focus = [
        "1) Publie 2 contenus basés sur la peur #1 (avec preuve et deadline).",
        "2) Ajoute un CTA unique vers un lead magnet (commentaire/DM).",
        "3) Répète le même angle 2 fois (l’algo récompense la cohérence)."
    ]

    # Content pack (V1)
    hooks = []
    for entry in (opp.get("fear_radar", [])[:3]):
        fear_obj = entry.get("fear", {})
        hooks.extend(fear_obj.get("video_hooks", [])[:3])
    hooks = hooks[:10]

    titles_ab = []
    if hooks:
        titles_ab.append({"a": hooks[0], "b": hooks[1] if len(hooks) > 1 else hooks[0] + " (version B)"})

    formats = [
        {"type": "long", "length_min": 10, "structure": ["Hook 0–10s", "preuve", "framework", "CTA lead magnet"]},
        {"type": "short", "length_sec": 30, "structure": ["Hook", "1 idée", "CTA commentaire"]}
    ]

    cta = {
        "primary": "Commente 'AI' et je t’envoie la scorecard.",
        "lead_magnet": "AI-Proof Scorecard (PDF/Notion)"
    }

    return {
        "niche": niche,
        "objective": objective,
        "period": period,
        "generated_at": datetime.now().isoformat(),
        "market_snapshot": {
            "top_fears": top_fears,
            "top_opportunities": top_opps,
            "what_to_avoid": what_to_avoid
        },
        "action_plan": {
            "this_week_focus": focus,
            "content_pack": {
                "hooks": hooks,
                "titles_ab": titles_ab,
                "formats": formats,
                "cta": cta
            }
        }
    }