"""Snapshot the Supabase tech cohort from YouTube once per UTC day in Nov 2026.

Rerunning on the same day refreshes that day's API observations. The original
Kaggle observations from 2025 remain separate, with their original dates.
"""

import os
from datetime import date, datetime, timezone


COHORT = "youtube_tech_channels"
STUDY_START = date(2026, 11, 1)
STUDY_END = date(2026, 12, 1)  # exclusive; no API requests after November
BATCH_SIZE = 50
SOURCE = "youtube_api"


def batches(values, size=BATCH_SIZE):
    for offset in range(0, len(values), size):
        yield values[offset:offset + size]


def utc_datetime(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def optional_int(data, key):
    return int(data[key]) if key in data else None


def cohort_ids(conn):
    with conn.cursor() as cur:
        cur.execute(
            """select cc.channel_id from public.cohort_channels cc
               join public.cohorts c on c.cohort_id = cc.cohort_id
               where c.cohort_name = %s order by cc.channel_id""", (COHORT,),
        )
        channels = [row[0] for row in cur.fetchall()]
        cur.execute(
            """select v.video_id from public.videos v
               join public.cohort_channels cc on cc.channel_id = v.channel_id
               join public.cohorts c on c.cohort_id = cc.cohort_id
               where c.cohort_name = %s order by v.video_id""", (COHORT,),
        )
        videos = [row[0] for row in cur.fetchall()]
    return channels, videos


def fetch_channels(youtube, channel_ids, observed_at):
    found = []
    for group in batches(channel_ids):
        response = youtube.channels().list(
            part="snippet,statistics,contentDetails", id=",".join(group),
        ).execute()
        for item in response.get("items", []):
            found.append((item, observed_at()))
    return found


def discover_uploads(youtube, channel_items):
    """Get all playlist IDs published during the study period, across pages."""
    ids = set()
    for channel, _ in channel_items:
        playlist = channel.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
        if not playlist:
            print(f"No uploads playlist for {channel['id']}; skipping discovery", flush=True)
            continue
        token = None
        while True:
            kwargs = {"part": "contentDetails", "playlistId": playlist, "maxResults": 50}
            if token:
                kwargs["pageToken"] = token
            try:
                response = youtube.playlistItems().list(**kwargs).execute()
            except Exception as exc:
                # Some public channels return an uploads playlist ID that the
                # playlistItems endpoint cannot resolve. Do not print the
                # exception: googleapiclient includes the API key in its URL.
                if getattr(getattr(exc, "resp", None), "status", None) == 404:
                    print(f"Uploads playlist unavailable for channel {channel['id']}; "
                          "skipping discovery", flush=True)
                    break
                raise
            reached_old_upload = False
            for item in response.get("items", []):
                details = item.get("contentDetails", {})
                video_id = details.get("videoId")
                published = details.get("videoPublishedAt")
                if not published:
                    continue  # cannot establish this upload belongs to the study window
                if published and utc_datetime(published).date() < STUDY_START:
                    reached_old_upload = True
                    break  # uploads playlists list newest items first
                if video_id:
                    ids.add(video_id)
            token = response.get("nextPageToken")
            if reached_old_upload or not token:
                break
    return ids


def fetch_videos(youtube, video_ids, observed_at):
    found = []
    for group in batches(sorted(video_ids)):
        response = youtube.videos().list(
            part="snippet,statistics,contentDetails", id=",".join(group),
        ).execute()
        for item in response.get("items", []):
            found.append((item, observed_at()))
    return found


def save_snapshots(conn, channel_items, video_items, collection_date):
    """Commit all metadata and dated counts together; later same-day fetch wins."""
    with conn.transaction():
        with conn.cursor() as cur:
            for item, observed_at in channel_items:
                snippet = item.get("snippet", {})
                stats = item.get("statistics", {})
                playlist = item.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
                cur.execute(
                    """insert into public.channels
                       (channel_id, channel_name, description, created_at, country, uploads_playlist)
                       values (%s, %s, %s, %s, %s, %s)
                       on conflict (channel_id) do update set
                         channel_name = excluded.channel_name,
                         description = excluded.description,
                         created_at = coalesce(public.channels.created_at, excluded.created_at),
                         country = coalesce(excluded.country, public.channels.country),
                         uploads_playlist = coalesce(excluded.uploads_playlist, public.channels.uploads_playlist)""",
                    (item["id"], snippet.get("title"), snippet.get("description"),
                     utc_datetime(snippet["publishedAt"]) if snippet.get("publishedAt") else None,
                     snippet.get("country"), playlist),
                )
                cur.execute(
                    """insert into public.channel_snapshots
                       (channel_id, collection_date, collected_at,
                        subscriber_count, view_count, video_count, source)
                       values (%s, %s, %s, %s, %s, %s, %s)
                       on conflict (channel_id, collection_date) do update set
                         collected_at = excluded.collected_at,
                         subscriber_count = excluded.subscriber_count,
                         view_count = excluded.view_count,
                         video_count = excluded.video_count,
                         source = excluded.source
                       where public.channel_snapshots.collected_at <= excluded.collected_at""",
                    (item["id"], collection_date, observed_at,
                     optional_int(stats, "subscriberCount"), optional_int(stats, "viewCount"),
                     optional_int(stats, "videoCount"), SOURCE),
                )

            for item, observed_at in video_items:
                snippet = item.get("snippet", {})
                stats = item.get("statistics", {})
                video_id = item["id"]
                thumbnail = snippet.get("thumbnails", {}).get("high", {}).get("url")
                if not thumbnail:
                    thumbnail = snippet.get("thumbnails", {}).get("default", {}).get("url")
                cur.execute(
                    """insert into public.videos
                       (video_id, channel_id, title, published_at, duration,
                        thumbnail, video_url, source_channel_name)
                       values (%s, %s, %s, %s, %s, %s, %s, %s)
                       on conflict (video_id) do update set
                         title = excluded.title,
                         published_at = excluded.published_at,
                         duration = coalesce(excluded.duration, public.videos.duration),
                         thumbnail = coalesce(excluded.thumbnail, public.videos.thumbnail),
                         video_url = excluded.video_url,
                         source_channel_name = excluded.source_channel_name""",
                    (video_id, snippet["channelId"], snippet.get("title"),
                     utc_datetime(snippet["publishedAt"]) if snippet.get("publishedAt") else None,
                     item.get("contentDetails", {}).get("duration"), thumbnail,
                     f"https://www.youtube.com/watch?v={video_id}", snippet.get("channelTitle")),
                )
                cur.execute(
                    """insert into public.video_snapshots
                       (video_id, collection_date, collected_at,
                        view_count, like_count, comment_count, source)
                       values (%s, %s, %s, %s, %s, %s, %s)
                       on conflict (video_id, collection_date) do update set
                         collected_at = excluded.collected_at,
                         view_count = excluded.view_count,
                         like_count = excluded.like_count,
                         comment_count = excluded.comment_count,
                         source = excluded.source
                       where public.video_snapshots.collected_at <= excluded.collected_at""",
                    (video_id, collection_date, observed_at, optional_int(stats, "viewCount"),
                     optional_int(stats, "likeCount"), optional_int(stats, "commentCount"), SOURCE),
                )


def run(conn, youtube, now=None):
    observed_at = now or (lambda: datetime.now(timezone.utc))
    today = observed_at().date()
    if not STUDY_START <= today < STUDY_END:
        print(f"Outside November 2026 UTC: {today}; no API requests made.", flush=True)
        return 0, 0

    channel_ids, existing_video_ids = cohort_ids(conn)
    if not channel_ids:
        raise ValueError(f"No channel IDs in cohort {COHORT}; run the Kaggle import first")
    print(f"Collecting {len(channel_ids)} channels for {today} UTC...", flush=True)
    channel_items = fetch_channels(youtube, channel_ids, observed_at)
    missing_channels = set(channel_ids) - {item["id"] for item, _ in channel_items}
    if missing_channels:
        print(f"Unavailable channels: {len(missing_channels)}", flush=True)
    print(f"Retrieved {len(channel_items)} channels; checking uploads...", flush=True)
    new_ids = discover_uploads(youtube, channel_items)
    all_video_ids = set(existing_video_ids) | new_ids
    print(f"Fetching {len(all_video_ids)} tracked videos ({len(new_ids - set(existing_video_ids))} newly discovered)...", flush=True)
    video_items = fetch_videos(youtube, all_video_ids, observed_at)
    missing_videos = all_video_ids - {item["id"] for item, _ in video_items}
    if missing_videos:
        print(f"Unavailable/private videos: {len(missing_videos)}", flush=True)
    save_snapshots(conn, channel_items, video_items, today)
    print(f"Saved {len(channel_items)} channel and {len(video_items)} video snapshots for {today} UTC.", flush=True)
    return len(channel_items), len(video_items)


def main():
    from dotenv import load_dotenv
    from googleapiclient.discovery import build
    import psycopg

    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not database_url or not api_key:
        raise SystemExit("Set DATABASE_URL and YOUTUBE_API_KEY before running the collector")

    # Autocommit keeps the initial read queries from holding a transaction open
    # during API calls. The writes use an explicit transaction in save_snapshots.
    with psycopg.connect(database_url, autocommit=True) as conn:
        youtube = build("youtube", "v3", developerKey=api_key, cache_discovery=False)
        run(conn, youtube)


if __name__ == "__main__":
    main()
