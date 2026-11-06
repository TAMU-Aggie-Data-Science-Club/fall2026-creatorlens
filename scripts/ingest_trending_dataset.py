"""Download the daily YouTube trending dataset into CreatorLens's interim data."""

import argparse
import json
from pathlib import Path

import pandas as pd


DATASET = "rsrishav/youtube-trending-video-dataset"
REGIONS = ("US", "GB", "DE", "CA", "FR", "RU", "BR", "MX", "KR", "JP", "IN")
COLUMN_NAMES = {
    "channelId": "channel_id",
    "channelTitle": "channel_name",
    "publishedAt": "published_at",
    "categoryId": "category_id",
    "likes": "like_count",
}
REQUIRED_COLUMNS = {
    "video_id", "channelId", "title", "publishedAt", "categoryId",
    "view_count", "trending_date", "tags",
}


def category_names(category_data: dict) -> dict[str, str]:
    """Read YouTube category IDs and titles from one region's JSON."""
    items = category_data.get("items")
    if not isinstance(items, list):
        raise ValueError("Category JSON is missing its items list")
    return {str(item["id"]): item["snippet"]["title"] for item in items}


def normalize_trending(
    source: pd.DataFrame, region: str, categories: dict[str, str],
) -> pd.DataFrame:
    """Keep every source row and field, using CreatorLens column names."""
    missing = REQUIRED_COLUMNS - set(source.columns)
    if missing:
        raise ValueError(f"Trending CSV is missing columns: {sorted(missing)}")

    for original, target in COLUMN_NAMES.items():
        if original in source.columns and target in source.columns:
            raise ValueError(f"Trending CSV contains both {original} and {target}")

    df = source.rename(columns=COLUMN_NAMES).copy()
    df["category_name"] = df["category_id"].astype("string").map(categories)
    df["region"] = region
    return df


def ingest(region: str = "US", refresh: bool = False) -> Path:
    """Download a regional CSV and write its normalized interim observations."""
    if region not in REGIONS:
        raise ValueError(f"Unsupported region: {region}")

    # Import lazily so normalization can be checked using a local fixture offline.
    import kagglehub

    filename = f"{region}_youtube_trending_data.csv"
    category_filename = f"{region}_category_id.json"
    source_path = Path(kagglehub.dataset_download(
        DATASET, path=filename, force_download=refresh,
    ))
    category_path = Path(kagglehub.dataset_download(
        DATASET, path=category_filename, force_download=refresh,
    ))
    with category_path.open(encoding="utf-8") as file:
        categories = category_names(json.load(file))
    df = normalize_trending(pd.read_csv(source_path, keep_default_na=False, dtype={
        "video_id": "string", "channelId": "string", "categoryId": "string",
    }), region, categories)

    output_dir = Path(__file__).resolve().parents[1] / "data/interim/trending-dataset-20-24"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{region}_trending_videos.csv"
    df.to_csv(output_path, index=False)
    print(f"Saved {len(df):,} observations to {output_path}")
    missing_categories = df["category_name"].isna().sum()
    if missing_categories:
        print(f"{missing_categories:,} rows have category IDs absent from {category_filename}")
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region", choices=("ALL", *REGIONS), default="ALL")
    parser.add_argument("--refresh", action="store_true", help="Redownload Kaggle data")
    args = parser.parse_args()
    for selected_region in (REGIONS if args.region == "ALL" else (args.region,)):
        ingest(selected_region, args.refresh)
