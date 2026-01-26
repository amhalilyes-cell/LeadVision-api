import json
import os
from datetime import datetime, timezone

DATA_DIR = "data"
VIDEOS_FILE = os.path.join(DATA_DIR, "videos.jsonl")
SNAPSHOT_FILE = os.path.join(DATA_DIR, "snapshots.jsonl")

os.makedirs(DATA_DIR, exist_ok=True)

def save_video(video: dict) -> None:
    with open(VIDEOS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(video, ensure_ascii=False) + "\n")

def save_snapshot(video_id: str, views: int, likes: int, comments: int) -> None:
    snap = {
        "video_id": video_id,
        "views": int(views),
        "likes": int(likes),
        "comments": int(comments),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    with open(SNAPSHOT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(snap, ensure_ascii=False) + "\n")