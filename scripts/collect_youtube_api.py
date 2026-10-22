import os
import json
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd
from dotenv import load_dotenv
from googleapiclient.discovery import build


# 1. Connect to the YouTube API

load_dotenv()

api_key = os.getenv("YOUTUBE_API_KEY")

if not api_key:
    raise ValueError("YouTube API key not found!")

youtube = build("youtube", "v3", developerKey=api_key)


# 2. Set up channels and storage folders

# Start with TED; add more channels after cohort approval
channel_ids = [
    "UCAuUUnT6oDeKwE6v1NGQxug"
]

videos_per_channel = 10

# Use UTC dates so everyone follows the same convention
collection_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

raw_folder = Path("data/raw") / collection_date
interim_folder = Path("data/interim")

raw_folder.mkdir(parents=True, exist_ok=True)
interim_folder.mkdir(parents=True, exist_ok=True)


# 3. Function to fetch data or use saved data

def get_data(request, filename):
    cache_file = raw_folder / filename

    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as file:
            response = json.load(file)

        print("Loaded from cache:", filename)

    else:
        response = request.execute()

        with open(cache_file, "w", encoding="utf-8") as file:
            json.dump(response, file, indent=4)

        print("Retrieved from YouTube:", filename)

    return response


# 4. Collect channel and video information

channel_data = []
video_data = []

for channel_id in channel_ids:

    print("\nCollecting channel:", channel_id)

    # Request channel information
    channel_request = youtube.channels().list(
        part="snippet,statistics,contentDetails",
        id=channel_id
    )

    channel_response = get_data(
        channel_request,
        f"{channel_id}_channel.json"
    )

    if not channel_response.get("items"):
        print("Channel not found:", channel_id)
        continue

    channel = channel_response["items"][0]

    snippet = channel["snippet"]
    stats = channel["statistics"]
    details = channel["contentDetails"]

    # Save channel information in a dictionary
    channel_data.append({
        "channel_id": channel["id"],
        "channel_name": snippet["title"],
        "description": snippet.get("description"),
        "published_at": snippet.get("publishedAt"),
        "subscriber_count": (
            int(stats["subscriberCount"])
            if "subscriberCount" in stats else None
        ),
        "view_count": int(stats["viewCount"]),
        "video_count": int(stats["videoCount"]),
        "collection_date": collection_date
    })

    # Get the playlist containing the channel's uploads
    uploads_playlist = details["relatedPlaylists"]["uploads"]

    playlist_request = youtube.playlistItems().list(
        part="contentDetails",
        playlistId=uploads_playlist,
        maxResults=videos_per_channel
    )

    playlist_response = get_data(
        playlist_request,
        f"{channel_id}_playlist.json"
    )

    # Extract video IDs
    video_ids = []

    for item in playlist_response.get("items", []):
        video_id = item["contentDetails"]["videoId"]
        video_ids.append(video_id)

    if not video_ids:
        print("No videos found for:", channel_id)
        continue

    # Request statistics for the retrieved videos
    video_request = youtube.videos().list(
        part="snippet,statistics,contentDetails",
        id=",".join(video_ids)
    )

    video_response = get_data(
        video_request,
        f"{channel_id}_videos.json"
    )

    # Extract the useful information from each video
    for video in video_response.get("items", []):

        video_snippet = video["snippet"]
        video_stats = video.get("statistics", {})
        video_details = video["contentDetails"]

        video_data.append({
            "video_id": video["id"],
            "channel_id": channel_id,
            "title": video_snippet["title"],
            "published_at": video_snippet["publishedAt"],
            "duration": video_details["duration"],
            "category_id": video_snippet.get("categoryId"),
            "view_count": (
                int(video_stats["viewCount"])
                if "viewCount" in video_stats else None
            ),
            "like_count": (
                int(video_stats["likeCount"])
                if "likeCount" in video_stats else None
            ),
            "comment_count": (
                int(video_stats["commentCount"])
                if "commentCount" in video_stats else None
            ),
            "collection_date": collection_date
        })


# 5. Convert information into Pandas DataFrames

channels_df = pd.DataFrame(channel_data)
videos_df = pd.DataFrame(video_data)


# 6. Save the organized datasets

channels_file = interim_folder / f"channels_{collection_date}.csv"
videos_file = interim_folder / f"videos_{collection_date}.csv"

channels_df.to_csv(channels_file, index=False)
videos_df.to_csv(videos_file, index=False)


# 7. Display results

print("\nData collection completed!")

print("\nChannels collected:", len(channels_df))
print("Videos collected:", len(videos_df))

print("\nChannel Data:")
print(channels_df.head())

print("\nVideo Data:")
print(videos_df.head())

print("\nFiles saved to:")
print(channels_file)
print(videos_file)