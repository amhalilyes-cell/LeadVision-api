import json
import re
import html
from collections import defaultdict, Counter
from datetime import datetime

VIDEOS_FILE = "data/videos.jsonl"
SNAPSHOT_FILE = "data/snapshots.jsonl"

# ============ MODE ============
BUSINESS_ONLY = True  # True = analyse "business only" (recommandé)

# ============ FILTERS ============
# On blacklist agressive pour éviter que "Diary of a CEO health" écrase ton business scan
BLOCK_WORDS = {
    # health / medical / fitness / nutrition
    "insulin","ozempic","keto","cancer","dementia","gut","fat","doctor","poo","health",
    "diet","protein","workout","gym","calories","supplement","testosterone","hormone",
    "sleep","adhd","anxiety","depression","autism","disease","symptom","blood","cholesterol",
    "diabetes","weight","skin","hair","fasting","longevity","brain","neuroscience","dopamine",
    "psychology","therapy",

    # motivation fluff
    "motivation","motivational","discipline","mindset","manifest","affirmation","affirmations",
}

# On whitelist business/monétisation/AI/finance
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

# ============ LEVERS (Business-focused) ============
LEX = {
    "money": {"money","wealth","rich","poor","income","cash","salary","profit","million","billion"},
    "business": {"business","entrepreneur","entrepreneurship","startup","company","ceo","founder","operator"},
    "sales": {"sales","sell","selling","closing","closer","deal","pipeline"},
    "marketing": {"marketing","ads","advertising","copywriting","funnel","funnels","leads","clients","acquisition"},
    "investing": {"investing","investor","stocks","stock","crypto","bitcoin","real","estate","valuation"},
    "ai": {"ai","artificial","intelligence","automation","agents","jobs","future"},
    "authority": {"expert","ceo","founder","investor","billionaire","professor","author"},
    "contrarian": {"truth","myth","lie","wrong","stop","dont","don’t","shouldnt","shouldn’t","poorer"},
    "urgency": {"now","before","warning","crash","collapse","in","months","years"},
}

# ============ IO ============
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

# ============ METRICS ============
def views_per_day(snaps):
    snaps.sort(key=lambda x: x["timestamp"])
    t1 = datetime.fromisoformat(snaps[0]["timestamp"])
    t2 = datetime.fromisoformat(snaps[-1]["timestamp"])
    days = (t2 - t1).total_seconds() / 86400.0
    days = max(1e-6, days)  # évite division par 0
    dv = (snaps[-1]["views"] - snaps[0]["views"])
    return dv / days

# ============ TEXT ============
def normalize_title(title: str) -> str:
    # corrige les "&#39;" etc.
    t = html.unescape(title or "")
    t = t.lower().strip()
    return t

def is_blocked(title: str) -> bool:
    t = normalize_title(title)
    return any(w in t for w in BLOCK_WORDS)

def is_business(title: str) -> bool:
    t = normalize_title(title)
    return any(w in t for w in BUSINESS_WHITELIST)

def tokenize(title: str):
    t = normalize_title(title)
    t = re.sub(r"[^a-z0-9\s']", " ", t)
    toks = [x for x in t.split() if x and x not in STOPWORDS and len(x) > 2]
    return toks

def multi_labels(title: str):
    toks = set(tokenize(title))
    labels = set()
    for label, words in LEX.items():
        if toks.intersection(words):
            labels.add(label)
    if not labels:
        labels.add("other")
    return labels

# ============ MAIN ============
def main():
    videos = load_videos()
    snaps = load_snapshots()

    THRESHOLD_VPD = 20000

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

    print("\n=== VIRAL WINNERS (by views/day) ===\n")
    for vid, vpd in winners[:20]:
        title = videos[vid].get("title", "")
        channel = videos[vid].get("channel", "?")
        print(f"{int(vpd)} v/day | {channel} | {html.unescape(title)}")

    label_counts = Counter()
    word_counts = Counter()
    clusters = defaultdict(list)

    for vid, vpd in winners:
        title = videos[vid].get("title", "")
        labels = multi_labels(title)
        toks = tokenize(title)

        for lb in labels:
            label_counts[lb] += 1
            clusters[lb].append((vpd, html.unescape(title)))

        for w in toks:
            word_counts[w] += 1

    print("\n=== DOMINANT LEVERS (multi-label) ===\n")
    for lb, c in label_counts.most_common():
        print(f"{lb} → {c} winners")

    print("\n=== TOP WORDS (winners only) ===\n")
    for w, c in word_counts.most_common(25):
        print(f"{w} → {c}")

    print("\n=== TOP TITLES BY LEVER ===\n")
    for lb, items in sorted(clusters.items(), key=lambda kv: -len(kv[1])):
        items.sort(key=lambda x: -x[0])
        print(f"\n[{lb}] ({len(items)} winners)")
        for vpd, title in items[:7]:
            print(f"- {int(vpd)} v/day | {title}")

if __name__ == "__main__":
    main()