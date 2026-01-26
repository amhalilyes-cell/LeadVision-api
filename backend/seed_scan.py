from backend.seeds import SEED_CHANNELS
from backend.youtube import list_channel_videos
from backend.storage import save_video, save_snapshot
from datetime import datetime, timezone

def main():
    print("\n=== SEEDED BUSINESS US SCAN ===\n")
    now = datetime.now(timezone.utc)

    for name, cid in SEED_CHANNELS.items():
        print(f"\n--- {name} ---")
        items = list_channel_videos(cid, max_results=25)

        for v in items:
            vid = v["id"]
            title = v["snippet"]["title"]
            stats = v.get("statistics", {})
            views = int(stats.get("viewCount", 0))
            likes = int(stats.get("likeCount", 0))

            save_video({
                "id": vid,
                "title": title,
                "channel": name,
                "publishedAt": v["snippet"].get("publishedAt"),
                "views": views,
                "likes": likes,
            })
            save_snapshot(vid, views=views, likes=likes, comments=int(stats.get("commentCount", 0)))

            print(f"{views} views | {likes} likes | {title}")

if __name__ == "__main__":
    main()
    