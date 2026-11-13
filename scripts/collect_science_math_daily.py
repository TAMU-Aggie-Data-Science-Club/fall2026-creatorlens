"""Run manually from the CreatorLens repo: python scripts/collect_science_math_daily.py

Requires the imported science cohort, DATABASE_URL and YOUTUBE_API_KEY.
Reads current counts only. The collection window matches the November 2026 tech study.
"""
import os
from datetime import date, datetime, timezone
from pathlib import Path

COHORT = "youtube_science_math_channels"
SEED_SOURCE = "youtube:science_math_long_form_csv"
SOURCE = "youtube_api:science_math"
START, END = date(2026, 11, 1), date(2026, 12, 1)  # END is exclusive


def now_utc():
    return datetime.now(timezone.utc)


def timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def inputs(conn):
    with conn.cursor() as cur:
        cur.execute("""SELECT cc.channel_id FROM public.cohort_channels cc
                       JOIN public.cohorts c USING (cohort_id)
                       WHERE c.cohort_name = %s ORDER BY cc.channel_id""", (COHORT,))
        channels = [r[0] for r in cur]
        if not channels:
            raise ValueError(f"Empty or missing {COHORT}. Run import_science_math.py first.")
        # A shared channel may also have Shorts tracked by the tech collector.
        cur.execute("""SELECT v.video_id, v.channel_id FROM public.videos v
                       WHERE v.channel_id = ANY(%s)
                         AND EXISTS (SELECT 1 FROM public.video_snapshots s
                                     WHERE s.video_id = v.video_id AND s.source = ANY(%s))""",
                    (channels, [SEED_SOURCE, SOURCE]))
        return channels, dict(cur)


def fetch(endpoint, ids, parts, clock):
    result = []
    ids = sorted(ids)
    for start in range(0, len(ids), 50):
        response = endpoint.list(id=",".join(ids[start:start + 50]), part=parts,
                                 maxResults=50).execute(num_retries=3)
        observed = clock()
        result.extend((item, observed) for item in response.get("items", []))
    return result


def discover(youtube, channel_items):
    from googleapiclient.errors import HttpError

    owners = {}
    unavailable = 0
    for channel, _ in channel_items:
        cid = channel["id"]
        # YouTube's regular-video playlist excludes Shorts and the Live tab.
        # UULF is an undocumented playlist convention; a missing list is reported.
        playlist = "UULF" + cid[2:]
        token = None
        while True:
            try:
                page = youtube.playlistItems().list(
                    playlistId=playlist, part="contentDetails", maxResults=50, pageToken=token
                ).execute(num_retries=3)
            except HttpError as exc:
                if exc.resp.status != 404:
                    raise
                unavailable += 1
                print(f"No regular-video playlist for {cid}. Skipping discovery for this channel.")
                break
            dates = []
            for entry in page.get("items", []):
                item = entry["contentDetails"]
                if item.get("videoPublishedAt"):
                    day = timestamp(item["videoPublishedAt"]).date()
                    dates.append(day)
                    if START <= day < END:
                        owners[item["videoId"]] = cid
            token = page.get("nextPageToken")
            if not token or (dates and max(dates) < START):
                break
    return owners, unavailable


def metric(item, name):
    value = item["statistics"].get(name)
    return int(value) if value is not None else None


def insert_batches(cur, table, columns, rows, conflict):
    # SQL identifiers and conflict clauses are constants; values use bound parameters.
    one = "(" + ",".join(["%s"] * len(columns.split(","))) + ")"
    written = 0
    for offset in range(0, len(rows), 250):
        batch = rows[offset:offset + 250]
        cur.execute(f"INSERT INTO public.{table} ({columns}) VALUES "
                    + ",".join([one] * len(batch)) + " ON CONFLICT " + conflict,
                    [value for row in batch for value in row])
        written += cur.rowcount
    return written


def snapshots(cur, table, key, measures, rows):
    # Preserve initial CSV observations on a date collision. Among API observations,
    # a later collection wins, including if two runs finish out of order.
    columns = [key, "collection_date", "collected_at", *measures, "source"]
    updates = ", ".join(f"{name} = EXCLUDED.{name}" for name in columns[2:])
    conflict = (f"({key}, collection_date) DO UPDATE SET {updates} "
                f"WHERE {table}.source IN ('youtube_api', 'youtube_api:science_math') "
                f"AND {table}.collected_at <= EXCLUDED.collected_at")
    return insert_batches(cur, table, ",".join(columns), rows, conflict)


def save(conn, channels, videos):
    channel_stats, video_stats, metadata = [], [], []
    for item, at in channels:
        subs = None if item["statistics"].get("hiddenSubscriberCount") else metric(item, "subscriberCount")
        channel_stats.append((item["id"], at.date(), at, subs, metric(item, "viewCount"),
                              metric(item, "videoCount"), SOURCE))
    for item, at in videos:
        vid = item["id"]
        snippet = item["snippet"]
        thumbnails = snippet.get("thumbnails", {})
        thumbnail = (thumbnails.get("high") or thumbnails.get("default") or {}).get("url")
        metadata.append((vid, snippet["channelId"], snippet["title"], timestamp(snippet["publishedAt"]),
                         item["contentDetails"].get("duration"), thumbnail,
                         f"https://www.youtube.com/watch?v={vid}", snippet.get("channelTitle")))
        video_stats.append((vid, at.date(), at, metric(item, "viewCount"), metric(item, "likeCount"),
                            metric(item, "commentCount"), SOURCE))
    with conn.transaction(), conn.cursor() as cur:
        new_videos = insert_batches(cur, "videos",
            "video_id,channel_id,title,published_at,duration,thumbnail,video_url,source_channel_name",
            metadata, "(video_id) DO NOTHING")
        cs = snapshots(cur, "channel_snapshots", "channel_id",
                       ("subscriber_count", "view_count", "video_count"), channel_stats)
        vs = snapshots(cur, "video_snapshots", "video_id",
                       ("view_count", "like_count", "comment_count"), video_stats)
    return new_videos, cs, vs


def run(conn, youtube, clock=now_utc):
    day = clock().date()
    if not START <= day < END:
        print(f"Outside the November 2026 UTC study window ({day}).")
        return
    ids, tracked = inputs(conn)
    print(f"{day} UTC: {len(ids)} science channels, {len(tracked)} previously tracked videos.", flush=True)
    channels = fetch(youtube.channels(), ids, "statistics", clock)
    discovered, missing_playlists = discover(youtube, channels)
    expected = {**discovered, **tracked}
    candidates = fetch(youtube.videos(), expected,
                       "snippet,statistics,contentDetails,status,liveStreamingDetails", clock)
    videos = []
    for item, at in candidates:
        snippet = item["snippet"]
        if (snippet["channelId"] == expected[item["id"]]
                and item["status"].get("privacyStatus") == "public"
                and snippet.get("liveBroadcastContent", "none") == "none"
                and "liveStreamingDetails" not in item
                and timestamp(snippet["publishedAt"]) <= at):
            videos.append((item, at))
    if clock().date() != day:
        raise RuntimeError("Collection crossed UTC midnight. Run again to collect one consistent day.")
    added, cs, vs = save(conn, channels, videos)
    print(f"Committed {cs} channel and {vs} video snapshots (inserted or refreshed); "
          f"{added} new video records.")
    print(f"Unavailable channels: {len(ids)-len(channels)}. Unavailable discovery playlists: "
          f"{missing_playlists}. Unavailable or ineligible videos: {len(expected)-len(videos)}.")
    print(f"Existing snapshots retained on date conflicts: {len(channels)-cs} channel, {len(videos)-vs} video.")


def main():
    if not START <= now_utc().date() < END:
        print("Outside the November 2026 UTC study window.")
        return
    from dotenv import load_dotenv
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    import psycopg

    load_dotenv(Path.cwd() / ".env")
    uri, key = os.getenv("DATABASE_URL"), os.getenv("YOUTUBE_API_KEY")
    if not uri or not key:
        raise SystemExit("Set DATABASE_URL and YOUTUBE_API_KEY in your repository's .env.")
    try:
        with psycopg.connect(uri, autocommit=True) as conn:
            youtube = build("youtube", "v3", developerKey=key, cache_discovery=False)
            run(conn, youtube)
    except HttpError as exc:
        # The request URL on an HttpError may contain the API key.
        raise SystemExit(f"YouTube API error {exc.resp.status}: {exc.reason}") from None


if __name__ == "__main__":
    main()
