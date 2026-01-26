from .youtube import search_business_us, get_video_stats
from .storage import save_video, save_snapshot

def run_snapshot():
    results = search_business_us()

    video_ids = [v["id"]["videoId"] for v in results]

    stats = get_video_stats(video_ids)

    for meta, stat in zip(results, stats):
        vid = meta["id"]["videoId"]
        title = meta["snippet"]["title"]

        views = int(stat["statistics"].get("viewCount", 0))
        likes = int(stat["statistics"].get("likeCount", 0))
        comments = int(stat["statistics"].get("commentCount", 0))

        save_video({
            "id": vid,
            "title": title
        })

        save_snapshot(vid, views, likes, comments)

        print(f"{views} views | {title}")

if __name__ == "__main__":
    run_snapshot()