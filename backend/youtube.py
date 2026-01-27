import os
from dotenv import load_dotenv
from googleapiclient.discovery import build

load_dotenv()

def _get_youtube():
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing YOUTUBE_API_KEY")
    return build("youtube", "v3", developerKey=api_key)


def search_youtube(query: str, max_results: int = 25):
    """
    Retourne une liste de vidéos (items) avec snippet + stats + contentDetails
    """
    youtube = _get_youtube()

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


def list_channel_videos(channel_id: str, max_results: int = 25):
    youtube = _get_youtube()

    res = youtube.search().list(
        part="id,snippet",
        channelId=channel_id,
        order="date",
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


def search_business_us(max_results: int = 50):
    youtube = _get_youtube()
    request = youtube.search().list(
        q="business",
        part="id,snippet",
        type="video",
        relevanceLanguage="en",
        regionCode="US",
        maxResults=max_results,
        order="date"
    )
    return request.execute().get("items", [])


def get_video_stats(video_ids):
    youtube = _get_youtube()
    request = youtube.videos().list(
        part="statistics,contentDetails",
        id=",".join(video_ids)
    )
    return request.execute().get("items", [])
