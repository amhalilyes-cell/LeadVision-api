import os
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

def get_youtube():
    return build("youtube", "v3", developerKey=os.getenv("YOUTUBE_API_KEY"))

def search_business_us(max_results=50):
    yt = get_youtube()

    request = yt.search().list(
        q="business",
        part="id,snippet",
        type="video",
        relevanceLanguage="en",
        regionCode="US",
        maxResults=max_results,
        order="date"
    )
    return request.execute()["items"]

def get_video_stats(video_ids):
    yt = get_youtube()
    request = yt.videos().list(
        part="statistics,contentDetails",
        id=",".join(video_ids)
    )
    return request.execute()["items"]

def list_channel_videos(channel_id: str, max_results: int = 25):
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing YOUTUBE_API_KEY")

    youtube = build("youtube", "v3", developerKey=api_key)

    req = youtube.search().list(
        part="id,snippet",
        channelId=channel_id,
        order="date",
        type="video",
        maxResults=max_results
    )
    res = req.execute()

    video_ids = [it["id"]["videoId"] for it in res.get("items", []) if it.get("id", {}).get("videoId")]
    if not video_ids:
        return []

    details = youtube.videos().list(
        part="snippet,statistics,contentDetails",
        id=",".join(video_ids)
    ).execute()

    return details.get("items", [])
    def search_youtube(query: str, max_results: int = 25):
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing YOUTUBE_API_KEY")

    youtube = build("youtube", "v3", developerKey=api_key)

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
