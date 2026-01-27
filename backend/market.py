from googleapiclient.discovery import build
import os

def analyze_market(videos):
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing YOUTUBE_API_KEY")

    youtube = build("youtube", "v3", developerKey=api_key)

    # ✅ FIX ICI
    ids = ",".join(
        v["id"]
        for v in videos
        if isinstance(v, dict) and "id" in v
    )

    if not ids:
        return []

    stats = youtube.videos().list(
        part="statistics,contentDetails",
        id=ids
    ).execute()

    results = []

    for v, s in zip(videos, stats.get("items", [])):
        views = int(s["statistics"].get("viewCount", 0))
        likes = int(s["statistics"].get("likeCount", 0))

        like_rate = likes / views if views > 0 else 0
        score = views * like_rate

        results.append({
            "title": v["snippet"]["title"],  # ✅ titre correct
            "views": views,
            "likes": likes,
            "like_rate": like_rate,
            "views_per_day": views / 30,
            "score": score
        })

    return sorted(results, key=lambda x: x["score"], reverse=True)
