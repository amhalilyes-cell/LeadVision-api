import json
import re
import html
from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Any

VIDEOS_FILE = "data/videos.jsonl"
SNAPSHOT_FILE = "data/snapshots.jsonl"

# ===== Filters (reprend ton stack) =====
BUSINESS_ONLY = True
THRESHOLD_VPD = 20000
TOP_K_WINNERS = 50

BLOCK_WORDS = {
    "insulin","ozempic","keto","cancer","dementia","gut","fat","doctor","poo","health",
    "diet","protein","workout","gym","calories","supplement","testosterone","hormone",
    "sleep","adhd","anxiety","depression","autism","disease","symptom","blood","cholesterol",
    "diabetes","weight","skin","hair","fasting","longevity","brain","neuroscience","dopamine",
    "psychology","therapy",
    "motivation","motivational","discipline","mindset","manifest","affirmation","affirmations",
}

BUSINESS_WHITELIST = {
    "business","money","wealth","rich","profit","revenue","sales","marketing","startup",
    "entrepreneur","entrepreneurship","agency","saas","copywriting","closing",
    "real estate","investing","investor","stock","stocks","crypto","bitcoin","finance",
    "valuation","deal","ecommerce","shopify","amazon","ads","advertising",
    "ai","artificial intelligence","automation","agents","b2b","pricing","offer",
    "funnel","funnels","lead","leads","clients","customer","customers"
}

STOPWORDS = {
    "the","a","an","and","or","to","of","in","on","for","with","is","are","you","your","i","we","they","my",
    "this","that","it","how","what","why","when","who","will","new","from","vs","as","at","by","be","do","does",
    "these","those","should","only","before","after","into","out","than","about","over","under","up","down",
}

# ===== Fear taxonomy (same as fear_map) =====
FEARS = {
    "financial_decline": {
        "label_fr": "Déclin financier (devenir pauvre / mauvaises décisions)",
        "keywords": {"poor","poorer","broke","money","income","wealth","renting","house","invest","investing","crypto","smart investment","salary","profit","crash"}
    },
    "ai_obsolescence": {
        "label_fr": "Obsolescence IA (perdre son job / devenir inutile)",
        "keywords": {"ai","jobs","exist","automation","future","years","changes","won't exist","will not exist","robots"}
    },
    "business_failure": {
        "label_fr": "Échec business (ton système est cassé)",
        "keywords": {"business","startup","fail","failure","mistake","kills","dead","dying","bankrupt","lose","losing","revenue"}
    },
    "status_loss": {
        "label_fr": "Perte de statut (être derrière / humilié)",
        "keywords": {"top","best","secret","nobody","truth","wrong","stop","only","should"}
    },
    "relationship_break": {
        "label_fr": "Rupture / divorce (perte relationnelle)",
        "keywords": {"divorce","marriage","dating","relationship","breakup"}
    },
    "attention_decay": {
        "label_fr": "Cerveau / attention détruite (dopamine, short-form)",
        "keywords": {"dopamine","short","form","frying","addiction","brain","attention"}
    },
}

# ===== Playbooks (monétisation) =====
PLAYBOOKS = {
    "ai_obsolescence": {
        "audiences": [
            "Fondateurs SaaS < 20k€/mois (peur de se faire cloner)",
            "Freelances / agences (peur de commoditisation)",
            "Creators business (peur de perdre l’attention + revenus)"
        ],
        "business_angles": [
            "SaaS 'AI-proof': niche très spécifique + distribution + données propriétaires",
            "Agency d’automatisation (implémentation > outil) : workflows, intégrations, SOP",
            "Produits 'copilots' verticaux (un job / une tâche / une niche)",
            "Monétisation via templates + audits + implémentation"
        ],
        "lead_magnets": [
            "AI Survival Map 2026 (jobs qui meurent / jobs qui gagnent)",
            "Checklist 'AI-proof SaaS' (7 critères non-copiables)",
            "Scorecard: Ton business est-il clonable par l’IA ?"
        ],
        "video_hooks": [
            "Dans 24 mois, ton business peut devenir GRATUIT. Voilà pourquoi.",
            "L’IA ne vole pas ton job. Elle vole ton *pricing power*.",
            "Si ton SaaS n’a pas ça, il va se faire écraser."
        ],
        "cta": "Commente 'AI' et je t’envoie la Scorecard + le plan d’action."
    },
    "financial_decline": {
        "audiences": [
            "Entrepreneurs (cash management)",
            "Jeunes actifs (mauvais choix financiers)",
            "Créateurs qui veulent investir intelligemment"
        ],
        "business_angles": [
            "SaaS finance perso pour entrepreneurs (cashflow, runway, allocation)",
            "Contenu + produit: 'decision frameworks' (où mettre l’argent / où couper)",
            "Offre 'audit runway' + plan d’optimisation"
        ],
        "lead_magnets": [
            "Framework: 7 décisions financières qui te rendent pauvre",
            "Runway Calculator + Plan anti-crash",
            "Checklist: 'Investir en 2026 sans te faire laver'"
        ],
        "video_hooks": [
            "Le piège financier que 90% des entrepreneurs font en 2026.",
            "Tu penses investir. En réalité tu perds du temps et du cash.",
            "Ce move te rend pauvre même si tu gagnes plus."
        ],
        "cta": "Tape 'RUNWAY' et je t’envoie le calculator + template."
    },
    "business_failure": {
        "audiences": [
            "SaaS early stage (0–10k€/mois)",
            "Agences qui stagnent",
            "Creators qui n’ont pas de système"
        ],
        "business_angles": [
            "Système d’acquisition (pipeline) > features",
            "Pricing + offre (packaging) comme levier #1",
            "Rétention: onboarding + activation"
        ],
        "lead_magnets": [
            "SaaS Growth Autopsy (diagnostic)",
            "Template: Offer + Pricing Matrix",
            "Pipeline Sheet (leads → close)"
        ],
        "video_hooks": [
            "La vraie raison pour laquelle ton SaaS est bloqué.",
            "Si tu fais ça, tu tues ton SaaS sans le savoir.",
            "Ton problème n’est pas le produit. C’est l’acquisition."
        ],
        "cta": "Commente 'DIAG' pour recevoir la Growth Autopsy."
    },
    "status_loss": {
        "audiences": [
            "Creators business (course / consulting)",
            "Fondateurs qui veulent 'authority'"
        ],
        "business_angles": [
            "Positionnement contrarian (myth-busting)",
            "Proof stacking (études de cas + résultats)",
            "Content 'insider' (what no one says)"
        ],
        "lead_magnets": [
            "Authority Blueprint (30 jours)",
            "Framework: Proof Stack",
            "Checklist: '3 messages qui dominent une niche'"
        ],
        "video_hooks": [
            "La vérité que personne ne dit sur [niche].",
            "Tu fais [X] ? Arrête. C’est pour ça que tu restes invisible.",
            "Les meilleurs font l’inverse. Voilà pourquoi."
        ],
        "cta": "Commente 'AUTH' et je t’envoie le blueprint."
    },
    "attention_decay": {
        "audiences": [
            "Entrepreneurs (productivité)",
            "Creators (focus / output)",
        ],
        "business_angles": [
            "Systèmes de production (SOP + batching + IA en support)",
            "Programme de focus: 2h deep work/jour",
            "Tooling: dashboards + routines"
        ],
        "lead_magnets": [
            "Focus OS (routine + template)",
            "7-day attention reset",
        ],
        "video_hooks": [
            "Ton attention est ton vrai salaire. Et elle se fait voler.",
            "Si tu consommes du short form, tu détruis ton business.",
        ],
        "cta": "Tape 'FOCUS' et je t’envoie le Focus OS."
    },
    "other": {
        "audiences": ["Business creators"],
        "business_angles": ["Angles contrarian + authority"],
        "lead_magnets": ["Checklist simple"],
        "video_hooks": ["Voici ce que l’algo pousse vraiment."],
        "cta": "Commente 'PLAN'."
    }
}

def normalize_title(title: str) -> str:
    t = html.unescape(title or "").lower().strip()
    t = t.replace("’", "'")
    return t

def tokenize(title: str):
    t = normalize_title(title)
    t = re.sub(r"[^a-z0-9\s']", " ", t)
    toks = [x for x in t.split() if x and x not in STOPWORDS and len(x) > 2]
    return toks

def is_blocked(title: str) -> bool:
    t = normalize_title(title)
    return any(w in t for w in BLOCK_WORDS)

def is_business(title: str) -> bool:
    t = normalize_title(title)
    return any(w in t for w in BUSINESS_WHITELIST)

def load_videos():
    vids = {}
    with open(VIDEOS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            v = json.loads(line)
            vids[v["id"]] = v
    return vids

def load_snapshots():
    snaps = defaultdict(list)
    with open(SNAPSHOT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            s = json.loads(line)
            snaps[s["video_id"]].append(s)
    return snaps

def views_per_day(snaps):
    snaps.sort(key=lambda x: x["timestamp"])
    t1 = datetime.fromisoformat(snaps[0]["timestamp"])
    t2 = datetime.fromisoformat(snaps[-1]["timestamp"])
    days = max(1e-6, (t2 - t1).total_seconds() / 86400.0)
    dv = (snaps[-1]["views"] - snaps[0]["views"])
    return dv / days

def fear_primary(title: str) -> str:
    t = normalize_title(title)
    toks = set(tokenize(title))
    best = ("other", 0)

    for fk, meta in FEARS.items():
        sc = 0
        for kw in meta["keywords"]:
            if " " in kw:
                if kw in t:
                    sc += 2
            else:
                if kw in toks or kw in t:
                    sc += 1
        if sc > best[1]:
            best = (fk, sc)

    return best[0] if best[1] > 0 else "other"

def build_fear_radar(videos, snaps):
    winners = []
    for vid, s in snaps.items():
        if len(s) < 2 or vid not in videos:
            continue
        title = videos[vid].get("title", "")
        if is_blocked(title):
            continue
        if BUSINESS_ONLY and not is_business(title):
            continue
        vpd = views_per_day(s)
        if vpd >= THRESHOLD_VPD:
            winners.append((vid, vpd))

    winners.sort(key=lambda x: -x[1])
    winners = winners[:TOP_K_WINNERS]

    agg = defaultdict(lambda: {"count": 0, "sum_vpd": 0.0, "examples": []})
    for vid, vpd in winners:
        v = videos[vid]
        title = v.get("title", "")
        channel = v.get("channel", "?")
        fk = fear_primary(title)

        agg[fk]["count"] += 1
        agg[fk]["sum_vpd"] += vpd
        agg[fk]["examples"].append({
            "video_id": vid,
            "views_per_day": int(vpd),
            "channel": channel,
            "title": html.unescape(title)
        })

    # sort examples
    for fk in agg:
        agg[fk]["examples"].sort(key=lambda x: -x["views_per_day"])
        agg[fk]["examples"] = agg[fk]["examples"][:5]

    ranked = sorted(agg.items(), key=lambda kv: -kv[1]["sum_vpd"])
    return ranked

def map_to_opportunities(fear_key: str, niche: str):
    pb = PLAYBOOKS.get(fear_key, PLAYBOOKS["other"])
    # petite personnalisation niche
    niche = (niche or "business").lower().strip()

    # hooks adaptés au niche
    hooks = []
    for h in pb["video_hooks"]:
        hooks.append(h.replace("[niche]", niche))

    return {
        "fear_key": fear_key,
        "fear_label_fr": FEARS.get(fear_key, {}).get("label_fr", "Autre / non classé"),
        "audiences": pb["audiences"],
        "business_angles": pb["business_angles"],
        "lead_magnets": pb["lead_magnets"],
        "video_hooks": hooks,
        "cta": pb["cta"],
    }
def get_fear_radar(niche: str = "saas") -> Dict[str, Any]:
    videos = load_videos()
    snaps = load_snapshots()
    ranked = build_fear_radar(videos, snaps)
    if not ranked:
        return {"niche": niche, "error": "No winners found", "fear_radar": []}

    result = {
        "niche": niche,
        "threshold_vpd": THRESHOLD_VPD,
        "generated_at": datetime.now().isoformat(),
        "fear_radar": []
    }

    for fk, data in ranked:
        label = FEARS.get(fk, {}).get("label_fr", "Autre / non classé") if fk != "other" else "Autre / non classé"
        result["fear_radar"].append({
            "fear_key": fk,
            "fear_label_fr": label,
            "videos_count": data["count"],
            "sum_views_per_day": int(data["sum_vpd"]),
            "examples": data["examples"]
        })

    return result


def get_opportunity_map(niche: str = "saas") -> Dict[str, Any]:
    videos = load_videos()
    snaps = load_snapshots()
    ranked = build_fear_radar(videos, snaps)
    if not ranked:
        return {"niche": niche, "error": "No winners found", "fear_radar": []}

    out = {
        "niche": niche,
        "threshold_vpd": THRESHOLD_VPD,
        "generated_at": datetime.now().isoformat(),
        "fear_radar": []
    }

    for fk, data in ranked:
        mapped = map_to_opportunities(fk, niche)
        out["fear_radar"].append({
            "fear": mapped,
            "signal": {
                "videos_count": data["count"],
                "sum_views_per_day": int(data["sum_vpd"]),
                "examples": data["examples"]
            }
        })

    return out
    
def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--niche", default="saas")
    parser.add_argument("--out", default="output/opportunity_map.json")
    args = parser.parse_args()

    videos = load_videos()
    snaps = load_snapshots()

    ranked = build_fear_radar(videos, snaps)
    if not ranked:
        print("No winners found. Run seed_scan/snapshots again.")
        return

    out = {
        "niche": args.niche,
        "threshold_vpd": THRESHOLD_VPD,
        "generated_at": datetime.now().isoformat(),
        "fear_radar": []
    }

    for fk, data in ranked:
        mapped = map_to_opportunities(fk, args.niche)
        out["fear_radar"].append({
            "fear": mapped,
            "signal": {
                "videos_count": data["count"],
                "sum_views_per_day": int(data["sum_vpd"]),
                "examples": data["examples"]
            }
        })

    # save
    import os
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Saved: {args.out}\n")
    print("=== TOP FEARS (mapped) ===")
    for item in out["fear_radar"][:3]:
        label = item["fear"]["fear_label_fr"]
        vpd = item["signal"]["sum_views_per_day"]
        print(f"- {label} → {vpd} vues/jour")

if __name__ == "__main__":
    main()