import os
import json
import argparse
from collections import defaultdict, Counter
from datetime import datetime
import re
import html

from .env import load_env

VIDEOS_FILE = "data/videos.jsonl"
SNAPSHOT_FILE = "data/snapshots.jsonl"

BUSINESS_ONLY = True

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

LEX = {
    "money": {"money","wealth","rich","poor","income","cash","salary","profit","million","billion"},
    "business": {"business","entrepreneur","entrepreneurship","startup","company","ceo","founder","operator"},
    "sales": {"sales","sell","selling","closing","closer","deal","pipeline"},
    "marketing": {"marketing","ads","advertising","copywriting","funnel","funnels","leads","clients","acquisition"},
    "investing": {"investing","investor","stocks","stock","crypto","bitcoin","real","estate","valuation"},
    "ai": {"ai","artificial","intelligence","automation","agents","jobs","future"},
    "authority": {"expert","ceo","founder","investor","billionaire","professor","author"},
    "contrarian": {"truth","myth","lie","wrong","stop","dont","don’t","shouldnt","shouldn’t","poorer"},
    "urgency": {"now","before","warning","crash","collapse","months","years"},
}

OBJECTIVES = ["visibility", "leads", "sales", "authority", "launch"]

def normalize_title(title: str) -> str:
    return html.unescape(title or "").lower().strip()

def is_blocked(title: str) -> bool:
    t = normalize_title(title)
    return any(w in t for w in BLOCK_WORDS)

def is_business(title: str) -> bool:
    t = normalize_title(title)
    return any(w in t for w in BUSINESS_WHITELIST)

def tokenize(title: str):
    t = normalize_title(title)
    t = re.sub(r"[^a-z0-9\s']", " ", t)
    return [x for x in t.split() if x and x not in STOPWORDS and len(x) > 2]

def multi_labels(title: str):
    toks = set(tokenize(title))
    labels = set()
    for label, words in LEX.items():
        if toks.intersection(words):
            labels.add(label)
    if not labels:
        labels.add("other")
    return sorted(labels)

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

def get_winners(videos, snaps, threshold_vpd: int, top_k: int):
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
        if vpd >= threshold_vpd:
            winners.append((vid, vpd))

    winners.sort(key=lambda x: -x[1])
    return winners[:top_k]

def summarize_market(videos, winners):
    label_counts = Counter()
    word_counts = Counter()
    top_titles = []

    for vid, vpd in winners:
        title = videos[vid].get("title", "")
        channel = videos[vid].get("channel", "?")

        labels = multi_labels(title)
        toks = tokenize(title)

        for lb in labels:
            label_counts[lb] += 1
        for w in toks:
            word_counts[w] += 1

        top_titles.append({
            "video_id": vid,
            "views_per_day": int(vpd),
            "channel": channel,
            "title": html.unescape(title),
            "labels": labels
        })

    return {
        "dominant_levers": label_counts.most_common(10),
        "top_words": word_counts.most_common(40),
        "top_titles": top_titles
    }

def _openai_response_text(api_key: str, system: str, user_json: dict) -> str:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        resp = client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(user_json, ensure_ascii=False)}
            ],
        )
        return resp.output_text
    except Exception:
        import openai
        openai.api_key = api_key
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(user_json, ensure_ascii=False)}
            ],
            temperature=0.6,
        )
        return resp["choices"][0]["message"]["content"]

def call_openai_v3(intel: dict, niche_fr: str, objective: str, ideas: int, days: int):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY in .env")

    system = (
        "Tu es un stratège YouTube data-driven (business). "
        "Tu n'inventes pas de données. Tu utilises uniquement market_intel fourni. "
        "Tu dois produire un plan ultra actionnable pour une niche FR.\n\n"
        "IMPORTANT:\n"
        "- Output STRICTEMENT JSON valide. Rien d'autre.\n"
        "- Chaque opportunité doit inclure un A/B test: 2 titres + 2 concepts de miniatures + 1 hypothèse testable.\n"
        "- Donne aussi un protocole de test (durée, métriques, seuils de décision) réaliste.\n"
        "- Pas de blabla, pas de généralités.\n"
    )

    schema = {
        "niche": niche_fr,
        "objective": objective,
        "opportunities": [
            {
                "id": 1,
                "lever_combo": "ai+money / sales+authority / etc",
                "angle": "clair",
                "hook_0_10s": "1 phrase",
                "promise": "résultat concret",
                "structure": ["Hook", "Proof", "3 points", "CTA"],
                "cta": "aligné à objective",
                "ab_test": {
                    "title_A": "Titre FR A",
                    "title_B": "Titre FR B",
                    "thumbnail_A": {
                        "layout": "face/no-face + objet + texte (max 3 mots)",
                        "text": "3 mots max",
                        "visual_elements": ["objet", "émotion", "contraste"]
                    },
                    "thumbnail_B": {
                        "layout": "variation claire vs A",
                        "text": "3 mots max",
                        "visual_elements": ["objet", "émotion", "contraste"]
                    },
                    "hypothesis": "Si X alors CTR ↑ car Y"
                },
                "success_metrics": {
                    "primary": "CTR ou vues/heure",
                    "secondary": ["rétention 30s (si dispo)", "comment_rate", "like_rate"],
                    "decision_rule": "règle simple"
                }
            }
        ],
        "calendar": [
            {
                "day": 1,
                "objective_stage": "awareness|consideration|conversion",
                "opportunity_id": 1,
                "deliverable": "long|short|live|post",
                "note": "1 phrase"
            }
        ],
        "test_protocol": {
            "test_window_hours": 24,
            "when_to_kill": "condition",
            "when_to_double_down": "condition",
            "minimum_impressions": 2000,
            "notes": ["règles de cohérence", "ne pas changer 2 variables"]
        }
    }

    user_json = {
        "task": "OpportunityEngineV3_ABTesting",
        "niche_fr": niche_fr,
        "objective": objective,
        "ideas": ideas,
        "days": days,
        "market_intel": intel,
        "output_schema_example": schema,
        "hard_rules": [
            "JSON only",
            "No health/fitness content",
            "Use levers/words/titles from intel as inspiration (transposition), not copy-paste",
            "A/B test must vary ONE main variable (promise vs fear vs authority) between A and B",
        ]
    }

    text = _openai_response_text(api_key, system, user_json)

    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            raise RuntimeError("Model did not return JSON.")
        return json.loads(m.group(0))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--niche", default="saas")
    parser.add_argument("--objective", default="leads", choices=OBJECTIVES)
    parser.add_argument("--threshold_vpd", type=int, default=20000)
    parser.add_argument("--top_k", type=int, default=25)
    parser.add_argument("--ideas", type=int, default=12)
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

    print("\n=== MARKET INTEL (US) ===\n")
    print("Dominant levers:", intel["dominant_levers"][:8])
    print("Top words:", intel["top_words"][:12])
    print("\nTop winners:")
    for t in intel["top_titles"][:10]:
        print(f"- {t['views_per_day']} v/day | {t['channel']} | {t['title']} | {t['labels']}")

    plan = call_openai_v3(
        intel=intel,
        niche_fr=args.niche,
        objective=args.objective,
        ideas=args.ideas,
        days=args.days
    )

    print("\n=== OPPORTUNITY PLAN V3 (FR + AB TEST) ===\n")
    print(json.dumps(plan, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()