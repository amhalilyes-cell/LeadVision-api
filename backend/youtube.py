import os
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()

def search_youtube(query: str, max_results: int = 10):
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing YOUTUBE_API_KEY")

    try:
        youtube = build("youtube", "v3", developerKey=api_key)

        search_response = youtube.search().list(
            part="id,snippet",
            q=query,
            type="video",
            maxResults=max_results,
            order="relevance"
        ).execute()

        video_ids = [
            item.get("id", {}).get("videoId")
            for item in search_response.get("items", [])
            if item.get("id", {}).get("videoId")
        ]

        if not video_ids:
            return []

        stats_response = youtube.videos().list(
            part="snippet,statistics,contentDetails",
            id=",".join(video_ids)
        ).execute()

        videos = []
        for item in stats_response.get("items", []):
            stats = item.get("statistics", {}) or {}
            snippet = item.get("snippet", {}) or {}

            videos.append({
                "video_id": item.get("id"),
                "title": snippet.get("title"),
                "views": int(stats.get("viewCount", 0) or 0),
                "likes": int(stats.get("likeCount", 0) or 0),
            })

        return videos

    except HttpError as e:
        raise RuntimeError(f"YouTube API error: {e}") from e