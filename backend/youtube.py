import os
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()


def get_youtube():
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing YOUTUBE_API_KEY")

    return build("youtube", "v3", developerKey=api_key)


def search_youtube(query: str, max_results: int = 25):
    youtube = get_youtube()

    res = youtube.search().list(
        part="id,snippet",
        q=query,
        order="relevance",
        type="video",
        maxResults=max_results
    ).execute()

    video_ids = [
        it["id"]["videoId"]
        for it in res.get("items", [])
        if it.get("id", {}).get("videoId")
    ]

    if not video_ids:
        return []

    details = youtube.videos().list(
        part="snippet,statistics,contentDetails",
        id=",".join(video_ids)
    ).execute()

    return details.get("items", [])
