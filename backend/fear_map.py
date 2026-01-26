import json
import re
import html
from collections import defaultdict, Counter
from datetime import datetime

VIDEOS_FILE = "data/videos.jsonl"
SNAPSHOT_FILE = "data/snapshots.jsonl"

# Reprend tes filtres "business-only" (tu peux ajuster)
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

# Fear taxonomy (business-oriented)
# Une vidéo peut matcher plusieurs peurs, mais on sort 1 "primary" (la plus forte)
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

def normalize_title(title: str) -> str:
    t = html.unescape(title or "").lower().strip()
    # normalise apostrophes
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

def fear_scores(title: str):
    """
    Retourne (primary_fear_key, scores_dict)
    score = nb matches keywords (title contains keyword OR token contains keyword)
    """
    t = normalize_title(title)
    toks = set(tokenize(title))

    scores = {}
    for fk, meta in FEARS.items():
        sc = 0
        for kw in meta["keywords"]:
            if " " in kw:
                if kw in t:
                    sc += 2  # phrase match plus fort
            else:
                if kw in toks or kw in t:
                    sc += 1
        scores[fk] = sc

    # primary = max score; si tous 0 => "other"
    primary = max(scores.items(), key=lambda x: x[1])[0] if scores else "other"
    if scores.get(primary, 0) == 0:
        primary = "other"
    return primary, scores

def main():
    videos = load_videos()
    snaps = load_snapshots()

    THRESHOLD_VPD = 20000
    TOP_K = 50

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
    winners = winners[:TOP_K]

    if not winners:
        print("No winners found. (Need >=2 snapshots per video + matching filters.)")
        return

    # Aggregate by primary fear
    agg = defaultdict(lambda: {"count": 0, "sum_vpd": 0, "items": []})
    secondary_counts = Counter()

    for vid, vpd in winners:
        title = videos[vid].get("title", "")
        channel = videos[vid].get("channel", "?")
        primary, scores = fear_scores(title)

        agg[primary]["count"] += 1
        agg[primary]["sum_vpd"] += vpd
        agg[primary]["items"].append((vpd, channel, html.unescape(title), scores))

        # count secondary signals (for "also present")
        for fk, sc in scores.items():
            if sc > 0:
                secondary_counts[fk] += 1

    # Sort fears by sum_vpd
    ranked = sorted(agg.items(), key=lambda kv: -kv[1]["sum_vpd"])

    print("\n=== FEAR RADAR (winners) ===\n")
    for fk, data in ranked:
        if fk == "other":
            label = "Autre / non classé"
        else:
            label = FEARS[fk]["label_fr"]

        print(f"{label}  |  {data['count']} vidéos  |  {int(data['sum_vpd'])} vues/jour cumulées")

        data["items"].sort(key=lambda x: -x[0])
        for vpd, channel, title, scores in data["items"][:5]:
            # show top 2 scored fears for transparency
            top2 = sorted(scores.items(), key=lambda x: -x[1])[:2]
            top2 = [(k, v) for k, v in top2 if v > 0]
            top2_str = ", ".join([f"{k}:{v}" for k, v in top2]) if top2 else "-"
            print(f"  - {int(vpd)} v/j | {channel} | {title}  ({top2_str})")
        print("")

    print("=== SECONDARY SIGNALS (how often fears appear in winners) ===")
    for fk, c in secondary_counts.most_common():
        label = FEARS[fk]["label_fr"] if fk in FEARS else fk
        print(f"{label} → {c}")

if __name__ == "__main__":
    main()