import json
from collections import defaultdict
from datetime import datetime

SNAPSHOT_FILE = "data/snapshots.jsonl"

def main():
    videos = defaultdict(list)

    with open(SNAPSHOT_FILE) as f:
        for line in f:
            s = json.loads(line)
            videos[s["video_id"]].append(s)

    print("\n=== VIRALITY ANALYSIS ===\n")

    for vid, snaps in videos.items():
        if len(snaps) < 2:
            continue

        snaps.sort(key=lambda x: x["timestamp"])
        first = snaps[0]
        last = snaps[-1]

        t1 = datetime.fromisoformat(first["timestamp"])
        t2 = datetime.fromisoformat(last["timestamp"])
        days = (t2 - t1).total_seconds() / 86400
        if days <= 0:
            continue

        vpd = (last["views"] - first["views"]) / days

        print(f"{vid} | {int(vpd)} views/day")

if __name__ == "__main__":
    main()