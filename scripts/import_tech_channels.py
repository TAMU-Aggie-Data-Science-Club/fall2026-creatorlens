"""Import the fixed YouTube Tech Channels Kaggle cohort into Supabase once.

Safe to rerun: each INSERT has a conflict rule, and the whole import commits
only when every channel, video, cohort membership, and snapshot succeeds.
"""

import csv
import os
from datetime import datetime, timezone
from pathlib import Path


DATASET = "kenzabz8/youtube-tech-channels"
COHORT = "youtube_tech_channels"
CHANNEL_FILE = "youtube_tech_channels_20251120_133753.csv"
VIDEO_FILE = "youtube_tech_videos_20251120_133004.csv"
SOURCE = f"kaggle:{DATASET}"

CHANNEL_COLUMNS = {
    "channel_id", "channel_name", "description", "subscribers", "total_views",
    "total_videos", "created_date", "country", "uploads_playlist", "scraped_at",
}
VIDEO_COLUMNS = {
    "video_id", "title", "published_at", "views", "likes", "comments",
    "duration", "thumbnail", "video_url", "channel_id", "channel_name",
    "scraped_at", "duration_readable",
}


def read_source(path: Path, expected: set[str]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        found = set(reader.fieldnames or ())
        if found != expected:
            raise ValueError(
                f"{path.name} column mismatch; missing={sorted(expected - found)}, "
                f"unexpected={sorted(found - expected)}"
            )
        rows = list(reader)
    if not rows or any(None in row for row in rows):
        raise ValueError(f"{path.name} has no rows or contains malformed CSV rows")
    return rows


def nullable(value: str) -> str | None:
    return value if value else None


def integer(value: str) -> int | None:
    return int(value) if value else None


def timestamp(value: str) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    # The source's scraped_at values have no timezone. Interpret them as UTC;
    # also retain their exact original strings in scraped_at_raw.
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def import_to_supabase(conn, channels: list[dict[str, str]],
                       videos: list[dict[str, str]]) -> tuple[int, int]:
    channel_ids = [row["channel_id"] for row in channels]
    video_ids = [row["video_id"] for row in videos]
    if any(not value for value in channel_ids + video_ids):
        raise ValueError("A source row has an empty channel_id or video_id")
    if len(set(channel_ids)) != len(channel_ids) or len(set(video_ids)) != len(video_ids):
        raise ValueError("Source has repeated channel_id or video_id values")
    unknown_channels = {row["channel_id"] for row in videos} - set(channel_ids)
    if unknown_channels:
        raise ValueError(f"Video CSV refers to absent channels: {sorted(unknown_channels)}")

    # psycopg commits when this connection context exits successfully;
    # any exception rolls back every insert made by this import.
    with conn.cursor() as cur:
        cur.execute(
            """insert into public.cohorts (cohort_name) values (%s)
               on conflict (cohort_name) do nothing""", (COHORT,),
        )
        cur.execute("select cohort_id from public.cohorts where cohort_name = %s", (COHORT,))
        cohort_id = cur.fetchone()[0]

        for row in channels:
            channel_id = row["channel_id"]
            scraped = timestamp(row["scraped_at"])
            if scraped is None:
                raise ValueError(f"Missing scraped_at for channel {channel_id}")
            cur.execute(
                """insert into public.channels
                   (channel_id, channel_name, description, created_at, country, uploads_playlist)
                   values (%s, %s, %s, %s, %s, %s)
                   on conflict (channel_id) do nothing""",
                (channel_id, nullable(row["channel_name"]), nullable(row["description"]),
                 timestamp(row["created_date"]), nullable(row["country"]),
                 nullable(row["uploads_playlist"])),
            )
            cur.execute(
                """insert into public.cohort_channels (cohort_id, channel_id)
                   values (%s, %s) on conflict (cohort_id, channel_id) do nothing""",
                (cohort_id, channel_id),
            )
            cur.execute(
                """insert into public.channel_snapshots
                   (channel_id, collection_date, collected_at, subscriber_count,
                    view_count, video_count, source, scraped_at_raw)
                   values (%s, %s, %s, %s, %s, %s, %s, %s)
                   on conflict (channel_id, collection_date) do nothing""",
                (channel_id, scraped.date(), scraped, integer(row["subscribers"]),
                 integer(row["total_views"]), integer(row["total_videos"]),
                 SOURCE, row["scraped_at"]),
            )

        for row in videos:
            video_id = row["video_id"]
            scraped = timestamp(row["scraped_at"])
            if scraped is None:
                raise ValueError(f"Missing scraped_at for video {video_id}")
            cur.execute(
                """insert into public.videos
                   (video_id, channel_id, title, published_at, duration, thumbnail,
                    video_url, source_channel_name, duration_readable)
                   values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                   on conflict (video_id) do nothing""",
                (video_id, row["channel_id"], nullable(row["title"]),
                 timestamp(row["published_at"]), nullable(row["duration"]),
                 nullable(row["thumbnail"]), nullable(row["video_url"]),
                 nullable(row["channel_name"]), nullable(row["duration_readable"])),
            )
            cur.execute(
                """insert into public.video_snapshots
                   (video_id, collection_date, collected_at, view_count,
                    like_count, comment_count, source, scraped_at_raw)
                   values (%s, %s, %s, %s, %s, %s, %s, %s)
                   on conflict (video_id, collection_date) do nothing""",
                (video_id, scraped.date(), scraped, integer(row["views"]),
                 integer(row["likes"]), integer(row["comments"]),
                 SOURCE, row["scraped_at"]),
            )

    return len(channel_ids), len(video_ids)


def main() -> None:
    from dotenv import load_dotenv

    load_dotenv()
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("Set DATABASE_URL to your private Supabase Postgres connection string")

    import kagglehub
    import psycopg

    channel_path = Path(kagglehub.dataset_download(DATASET, path=CHANNEL_FILE))
    video_path = Path(kagglehub.dataset_download(DATASET, path=VIDEO_FILE))
    channels = read_source(channel_path, CHANNEL_COLUMNS)
    videos = read_source(video_path, VIDEO_COLUMNS)

    with psycopg.connect(database_url) as conn:
        channel_count, video_count = import_to_supabase(conn, channels, videos)

    print(f"Imported {channel_count} channels and {video_count} videos into {COHORT}.")
    print("Rerunning is safe; existing rows are not duplicated.")


if __name__ == "__main__":
    main()
