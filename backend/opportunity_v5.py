import os
import json
import argparse
from datetime import datetime
import re

from .opportunity_v4 import (
    load_videos, load_snapshots, get_winners, summarize_market,
    call_openai_v4, OBJECTIVES
)
from .env import load_env

def ensure_output_dir():
    os.makedirs("output", exist_ok=True)

def slug(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")

def write_json(path: str, obj: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def render_markdown(plan: dict) -> str:
    # Notion-ready Markdown
    niche = plan.get("niche")
    objective = plan.get("objective")
    out = []
    out.append(f"# Plan YouTube — {niche} — Objectif: {objective}\n")

    tp = plan.get("test_protocol", {})
    out.append("## Protocole de test\n")
    out.append(f"- Fenêtre: **{tp.get('test_window_hours', '—')}h**\n")
    out.append(f"- Impressions min: **{tp.get('minimum_impressions', '—')}**\n")
    out.append(f"- Kill: {tp.get('when_to_kill', '—')}\n")
    out.append(f"- Double-down: {tp.get('when_to_double_down', '—')}\n")
    notes = tp.get("notes", [])
    if notes:
        out.append("- Notes:\n")
        for n in notes:
            out.append(f"  - {n}\n")

    out.append("\n## Opportunités\n")
    for opp in plan.get("opportunities", []):
        out.append(f"\n### Opportunité #{opp.get('id')}\n")
        out.append(f"- **Levers**: {opp.get('lever_combo')}\n")
        out.append(f"- **Angle**: {opp.get('angle')}\n")
        out.append(f"- **Hook (0–10s)**: {opp.get('hook_0_10s')}\n")
        out.append(f"- **Promesse**: {opp.get('promise')}\n")

        ab = opp.get("ab_test", {})
        out.append("\n**A/B Test**\n")
        out.append(f"- Title A: {ab.get('title_A')}\n")
        out.append(f"- Title B: {ab.get('title_B')}\n")
        thA = ab.get("thumbnail_A", {})
        thB = ab.get("thumbnail_B", {})
        out.append(f"- Thumb A: **{thA.get('text','—')}** | {thA.get('layout','—')} | {thA.get('visual_elements',[])}\n")
        out.append(f"- Thumb B: **{thB.get('text','—')}** | {thB.get('layout','—')} | {thB.get('visual_elements',[])}\n")
        out.append(f"- Hypothèse: {ab.get('hypothesis')}\n")

        out.append("\n**Script long**\n")
        ls = opp.get("long_script", {})
        out.append(f"- Durée cible: {ls.get('duration_target_min','—')} min\n")
        for beat in ls.get("structure", []):
            out.append(f"  - {beat.get('t')} — **{beat.get('beat')}**\n")
            for line in beat.get("lines", []):
                out.append(f"    - {line}\n")

        out.append("\n**Shorts**\n")
        for i, sh in enumerate(opp.get("short_scripts", []), start=1):
            out.append(f"- Short #{i} ({sh.get('duration_target_sec','—')}s)\n")
            out.append(f"  - Hook: {sh.get('hook')}\n")
            core = sh.get("core", [])
            if core:
                out.append("  - Core:\n")
                for c in core:
                    out.append(f"    - {c}\n")
            out.append(f"  - CTA: {sh.get('cta')}\n")

        cta = opp.get("cta_stack", {})
        out.append("\n**CTA Stack**\n")
        out.append(f"- CTA principal: {cta.get('primary_cta')}\n")
        out.append(f"- Lead magnet / Offer: {cta.get('lead_magnet_or_offer')}\n")
        dm = cta.get("dm_script", [])
        if dm:
            out.append("- DM script:\n")
            for msg in dm:
                out.append(f"  - {msg}\n")

        metrics = opp.get("success_metrics", {})
        out.append("\n**Metrics**\n")
        out.append(f"- Primary: {metrics.get('primary')}\n")
        out.append(f"- Secondary: {metrics.get('secondary')}\n")
        out.append(f"- Rule: {metrics.get('decision_rule')}\n")

    out.append("\n## Calendrier 30 jours\n")
    for item in plan.get("calendar", []):
        out.append(
            f"- Jour {item.get('day')}: **{item.get('objective_stage')}** "
            f"| Op#{item.get('opportunity_id')} | {item.get('deliverable')} — {item.get('note')}\n"
        )

    return "".join(out)

def compact_for_ui(plan: dict) -> dict:
    # Format léger pour front (liste + champs essentiels)
    ui = {
        "niche": plan.get("niche"),
        "objective": plan.get("objective"),
        "opportunities": [],
        "calendar": plan.get("calendar", []),
        "test_protocol": plan.get("test_protocol", {}),
    }
    for opp in plan.get("opportunities", []):
        ab = opp.get("ab_test", {})
        ui["opportunities"].append({
            "id": opp.get("id"),
            "lever_combo": opp.get("lever_combo"),
            "angle": opp.get("angle"),
            "hook": opp.get("hook_0_10s"),
            "promise": opp.get("promise"),
            "title_A": ab.get("title_A"),
            "title_B": ab.get("title_B"),
            "thumb_A_text": (ab.get("thumbnail_A", {}) or {}).get("text"),
            "thumb_B_text": (ab.get("thumbnail_B", {}) or {}).get("text"),
            "hypothesis": ab.get("hypothesis"),
            "cta": (opp.get("cta_stack", {}) or {}).get("primary_cta"),
        })
    return ui

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--niche", default="saas")
    parser.add_argument("--objective", default="leads", choices=OBJECTIVES)
    parser.add_argument("--threshold_vpd", type=int, default=20000)
    parser.add_argument("--top_k", type=int, default=25)
    parser.add_argument("--ideas", type=int, default=6)
    parser.add_argument("--days", type=int, default=30)
    args = parser.parse_args()

    load_env(".env")

    videos = load_videos()
    snaps = load_snapshots()

    winners = get_winners(videos, snaps, args.threshold_vpd, args.top_k)
    if not winners:
        print("No winners found. Run snapshots again (seed_scan) to get >=2 snapshots per video.")
        return

    intel = summarize_market(videos, winners)

    print("\n=== MARKET INTEL (US) ===")
    print("Dominant levers:", intel["dominant_levers"][:8])
    print("Top words:", intel["top_words"][:12])

    plan = call_openai_v4(
        intel=intel,
        niche_fr=args.niche,
        objective=args.objective,
        ideas=args.ideas,
        days=args.days
    )

    ensure_output_dir()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = f"plan_{slug(args.niche)}_{slug(args.objective)}_{stamp}"

    json_path = os.path.join("output", base + ".json")
    md_path = os.path.join("output", base + ".md")
    ui_path = os.path.join("output", base + "_ui.json")

    write_json(json_path, plan)

    md = render_markdown(plan)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)

    ui = compact_for_ui(plan)
    write_json(ui_path, ui)

    print("\n=== SAVED ===")
    print("JSON:", json_path)
    print("MD  :", md_path)
    print("UI  :", ui_path)

if __name__ == "__main__":
    main()