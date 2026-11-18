# Data

This file describes CreatorLens's data sources and the daily Supabase snapshots for its Tech Channels and Science & Mathematics cohorts.

> **`DATA.md` is tracked in git. The `data/` folder is not.** Clone the repo, then populate `data/` locally.

## Suggested sources (starting point)
Articles on Models:

https://www.geeksforgeeks.org/machine-learning/arima-vs-sarima-model/ 

| Source | Origin / URL | Access method | License | Sensitivity | Notes |
|--------|--------------|---------------|---------|-------------|-------|
| YouTube Data API v3 | https://developers.google.com/youtube/v3 | REST via `google-api-python-client`, Google Cloud key | Google API ToS | None (public channels) | 10,000-unit daily quota — plan queries carefully |
| Kaggle Trending YouTube Video Dataset | https://www.kaggle.com/datasets/rsrishav/youtube-trending-video-dataset | Public download via `kagglehub` | CC0 | None (public video metadata) | All daily trending observations; `trending-dataset-20-24` is only the local folder name. Useful for prototyping without using YouTube API quota. |
| YouTube Tech Channels | https://www.kaggle.com/datasets/kenzabz8/youtube-tech-channels | Public download via `kagglehub` | TBD: verify on Kaggle | Public channel and video metadata | Initial tech cohort of 130 channels and 1,300 video rows; the supplied source snapshots were scraped November 20, 2025. |
| Social Blade (optional) | https://socialblade.com | HTML — **verify ToS before scraping** | Proprietary | None | Historical subscriber trajectories back in time. Check licensing terms first. |
| Kaggle YouTube 8M subset | https://research.google.com/youtube8m/ | Research download | Custom (research use) | None | Only if going toward visual features later |
| Kaggle YouTube Dataset of all Data Science Channels | [https://research.google.com/youtube8m/](https://www.kaggle.com/datasets/abhishek0032/youtube-dataset-all-data-scienceanalyst-channels) | Research download | Custom (research use) | None | Only if going toward visual features later |
| Social Media Engagement Dataset | https://www.kaggle.com/datasets/aviral342/social-media-engagement-dataset | Kaggle download | Comprehensive engagement metrics across major platforms | 
| Social Media Sponsorship & Engagement Dataset | https://www.kaggle.com/datasets/aviral342/social-media-engagement-dataset | Custom (research use) | None | Multi-platform dataset featuring sponsorship disclosures, creator metrics, demographics, and engagement performance |
| Instagram Data | https://www.kaggle.com/datasets/propriyam/instagram-data | Kaggle | Custom (research use) | None | Instagram post metrics including owner IDs, captions, likes, comments, and post upload Unix timestamps |
| YouTube Video Analytics Dataset | https://www.kaggle.com/datasets/kundanbedmutha/youtube-video-analytics-dataset | Kaggle | Custom (research use) | None | Large scale dataset containing video level metrics and performance statistics for analyzing YouTube content engagement |

## How to think about using each source

- **Quota.** The YouTube API quota is small. Cache every response to `data/raw/` and design fetchers to be resumable — never re-hit the API for something you already have.
- **Fitness.** The API returns *current* channel stats, not historical time series. To get trajectories you either scrape a third-party (with ToS in mind) or snapshot the API over the course of the project.
- **License / ToS.** Public channel metadata is fine to work with. Republishing raw video content, thumbnails, or user comments has ToS and copyright implications — stick to metrics and metadata in v1.
- **PII.** Public creator handles aren't PII, but if you branch into comment analysis later, treat commenters as sensitive.

Choosing and vetting a source is a **judgment call** — surface it to a PM rather than deciding a major data direction alone.

## Local layout convention

```
data/
├── raw/          # API responses as fetched, one file per (channel, endpoint, date)
├── interim/      # normalized channel + video tables
└── processed/    # feature tables and cohort splits
```

Because `data/` isn't in git, the **pipeline that fetches and builds these folders** is what must be committed and reproducible — not the data itself.


## Data Ingestion

### Supabase table reference

Both daily collectors use the same six Supabase PostgreSQL tables. Each collector
looks up its cohort by name and reads its channel IDs from `cohort_channels`.
Teammates can browse the rows in Supabase's **Table Editor**.

**`channels`** — one row per creator channel.

| Column | Type | Description |
|---|---|---|
| `channel_id` | `text` | Primary key; YouTube channel ID |
| `channel_name` | `text` | Channel name |
| `description` | `text` | Channel description |
| `created_at` | `timestamptz` | Channel creation time |
| `country` | `text` | Channel country, when available |
| `uploads_playlist` | `text` | ID of the channel's uploads playlist |

**`cohorts`** — named groups of channels.

| Column | Type | Description |
|---|---|---|
| `cohort_id` | `bigint` | Generated primary key |
| `cohort_name` | `text` | The two study cohorts are `youtube_tech_channels` and `youtube_science_math_channels` |

**`cohort_channels`** — links channels to cohorts.

| Column | Type | Description |
|---|---|---|
| `cohort_id` | `bigint` | References `cohorts.cohort_id`; part of composite primary key |
| `channel_id` | `text` | References `channels.channel_id`; part of composite primary key |

**`channel_snapshots`** — channel metrics observed on a collection date.

| Column | Type | Description |
|---|---|---|
| `channel_id` | `text` | References `channels.channel_id`; part of composite primary key |
| `collection_date` | `date` | UTC date; part of composite primary key |
| `collected_at` | `timestamptz` | Time the measurement was collected |
| `subscriber_count` | `bigint` | Subscriber count, when public |
| `view_count` | `bigint` | Total channel views |
| `video_count` | `bigint` | Public video count |
| `source` | `text` | Observation source. Daily values are `youtube_api` (tech) and `youtube_api:science_math` (science/math). |
| `scraped_at_raw` | `text` | Original source timestamp or date, when available |

**`videos`** — one row per tracked video.

| Column | Type | Description |
|---|---|---|
| `video_id` | `text` | Primary key; YouTube video ID |
| `channel_id` | `text` | References `channels.channel_id` |
| `title` | `text` | Video title |
| `published_at` | `timestamptz` | Video publication time |
| `duration` | `text` | ISO 8601 video duration |
| `thumbnail` | `text` | Thumbnail URL |
| `video_url` | `text` | YouTube video URL |
| `source_channel_name` | `text` | Channel name reported with the video |
| `duration_readable` | `text` | Readable duration from the Kaggle source, if provided |

**`video_snapshots`** — video metrics observed on a collection date.

| Column | Type | Description |
|---|---|---|
| `video_id` | `text` | References `videos.video_id`; part of composite primary key |
| `collection_date` | `date` | UTC date; part of composite primary key |
| `collected_at` | `timestamptz` | Time the measurement was collected |
| `view_count` | `bigint` | Video views |
| `like_count` | `bigint` | Likes, when available |
| `comment_count` | `bigint` | Comments, when available |
| `source` | `text` | Observation source. Daily values are `youtube_api` (tech) and `youtube_api:science_math` (science/math). |
| `scraped_at_raw` | `text` | Original source timestamp or date, when available |

Both cohorts share one snapshot per channel or video ID per UTC date. If a
channel belongs to both cohorts, the collectors share its daily row. To identify
a channel's cohorts, join through `cohort_channels` and `cohorts`. The snapshot's
`source` identifies the observation used for that row.

### Local credentials for Supabase imports and daily collection

Both daily collectors read the same credentials. Create a `.env` file in the repository root:

```dotenv
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/postgres
YOUTUBE_API_KEY=YOUR_YOUTUBE_DATA_API_KEY
```

Replace the placeholders with your Supabase PostgreSQL connection URI and
YouTube Data API key. Both collectors require both values. Variables already
set in the shell take precedence. Keep the git-ignored `.env` file local.

### Import the YouTube Tech Channels cohort into Supabase

This is a one-time import of the two CSVs in
`kenzabz8/youtube-tech-channels`. The importer expects the six tables listed
above. For a project with the older six-table schema, run
`sql/002_tech_channels.sql` in Supabase's SQL Editor to add the CSV-specific
columns. From the repository root:

```bash
python -m pip install kagglehub "psycopg[binary]" python-dotenv
python scripts/import_tech_channels.py
```

The script downloads its source files into Kaggle's cache and writes the
channels, cohort membership, video metadata (including duration), and original
2025-11-20 channel/video measurements directly to Supabase. The original
`scraped_at` text is retained alongside the database observation timestamp.
Because the source's naive scrape timestamps have no timezone, the script
assumes UTC for `collected_at`; verify that assumption with the dataset owner.
All other source columns map to the channel, video, or snapshot tables.
The import uses a single transaction and conflict handling on primary keys,
so repeating it does not duplicate data. It creates no project CSV and is not
part of `ingest_all_data.py`. A separate daily API collector will create
current 2026 snapshots for the imported cohort.

### Run both daily collectors

From the repository root, install the shared dependencies once:

```bash
python -m pip install "psycopg[binary]" google-api-python-client python-dotenv
```

Run this command manually once per UTC day during **November 1–30, 2026**:

```bash
python scripts/run_daily_collectors.py
```

The runner starts the tech collector first, then the science/math collector,
using the same Python interpreter and the repository root as the working
directory. Both cohorts must already have channel memberships in Supabase.

| Cohort | Collector in `scripts/` | Videos tracked each day |
|---|---|---|
| Tech Channels (`youtube_tech_channels`) | `collect_tech_cohort_daily.py` | Existing videos for member channels, plus public uploads discovered in their uploads playlists since November 1. All upload formats are eligible. |
| Science & Mathematics (`youtube_science_math_channels`) | `collect_science_math_daily.py` | Previously tracked science/math videos, plus public long-form uploads discovered during November. The collector uses each channel's regular-video playlist and excludes Shorts and livestreams. |

Each cohort started with 130 channels and 1,300 videos. The tracked video count
can grow as either collector discovers uploads. Both collectors batch requests
for channel and video statistics, add newly discovered videos to `videos`, and
write current measurements directly to Supabase:

- `channel_snapshots` records subscriber count, total channel views, and public video count.
- `video_snapshots` records views, likes, and comments for each available tracked video.

**Reruns and missed days.** A later run on the same UTC date can refresh that
day's API counts under the same key. The science/math collector preserves an
existing source CSV observation on a date collision. A missed day leaves a gap
because the API returns current counts. Finish the final run before December 1
at 00:00 UTC (November 30 at 6:00 p.m. Central). The team's planned December 1
database deletion is a separate task.

**Failures and retries.** Each collector commits its own transaction. If one
exits with an error, the runner still attempts the other, lists the failed
scripts, and exits with status 1. A successful collector's writes stay
committed. Unavailable videos are skipped. If a channel's discovery playlist
returns 404, the collector reports it and continues checking previously
tracked videos. To retry one collector, run its command from the repository root:

```bash
python scripts/collect_tech_cohort_daily.py
python scripts/collect_science_math_daily.py
```

**Adding a cohort.** Place its daily collector in `scripts/` and append the
filename to the `COLLECTORS` list in `scripts/run_daily_collectors.py`. List
order determines execution order. The daily command stays the same.

### Run all dataset importers

From the repository root, install the current dependencies and run the main
import command:

```bash
python -m pip install pandas kagglehub
python scripts/ingest_all_data.py
```

Currently this command runs `scripts/ingest_trending_dataset.py` for all 11
regions and writes the resulting CSVs under `data/interim/`. As the project
adopts more datasets, add each finished importer to `INGEST_SCRIPTS` in
`scripts/ingest_all_data.py`; teammates can continue using the same main
command. The separate YouTube API script below collects a TED test channel and
requires an API key, so it is not part of the main command yet.

### Importing the Kaggle trending dataset

To run only the trending importer, use:

```bash
python scripts/ingest_trending_dataset.py
```

This downloads all 11 regional CSV files and their matching category JSON files
to the Kaggle cache and writes one
file per region under `data/interim/trending-dataset-20-24/`, such as
`US_trending_videos.csv`. The folder name is a reference label; the importer
does not restrict years. Use `--region US` (or another supported region shown
by `--help`) to import only one file. Re-run the command to rebuild the CSVs from the latest available
Kaggle version; `--refresh` forces a fresh download instead of using its cache.
The folder is git-ignored, so collaborators run this command after cloning or
pulling the importer code. No YouTube API key is needed for this public dataset.

Each output row is a **video on a region's trending list on a particular day**.
Every source row and field is retained, including `trending_date` and `tags`.
The importer renames `channelId`, `channelTitle`, `publishedAt`, `categoryId`,
and `likes` to CreatorLens's `channel_id`, `channel_name`, `published_at`,
`category_id`, and `like_count`; it adds `region` and `category_name`. Each
`category_name` is looked up from that region's `<region>_category_id.json`
using the row's original `category_id`. Unmapped IDs have an empty name in the
CSV and are reported by the command; no rows are dropped. The output
therefore has one column per value, not both original and alias columns.
`trending_date` remains the source's original
observation timestamp; do not replace it with the date you run the importer.
Repeated appearances and duplicates are kept exactly as provided. The output
CSV is rebuilt on each run, so rerunning does not append a second copy.
This is a broad trending dataset, not a list of only tech channels: any cohort
filter by selected `channel_id`s should happen in a later analysis step.

#### Columns in each regional trending CSV

The loader keeps the source fields, renames five headers for CreatorLens, and
adds two columns. CSV files store text; the types below describe the intended
values when read into pandas.

| Output column | Source field | Type | Description |
|---|---|---|---|
| `video_id` | `video_id` | String | YouTube video identifier. Repeats when a video trends on multiple days. |
| `title` | `title` | String | Video title. |
| `published_at` | `publishedAt` | Datetime string | When the video was published. |
| `channel_id` | `channelId` | String | YouTube channel identifier. |
| `channel_name` | `channelTitle` | String | Channel title in the source data. |
| `category_id` | `categoryId` | String | Original video category ID; interpret it using this region's category JSON. |
| `trending_date` | `trending_date` | Datetime string | Day the video appeared in this region's trending observations. |
| `tags` | `tags` | String | Video tags as supplied by Kaggle, usually separated by `|`. |
| `view_count` | `view_count` | Integer | Video views in this trending observation. |
| `like_count` | `likes` | Integer | Video likes in this trending observation. |
| `dislikes` | `dislikes` | Integer | Dislikes as supplied by the source. |
| `comment_count` | `comment_count` | Integer | Comment count in this trending observation. |
| `thumbnail_link` | `thumbnail_link` | String | URL of the video thumbnail. |
| `comments_disabled` | `comments_disabled` | Boolean | Whether comments were disabled. |
| `ratings_disabled` | `ratings_disabled` | Boolean | Whether ratings were disabled. |
| `description` | `description` | String | Video description, not the channel description. |
| `category_name` | Regional category JSON | String (nullable) | Title matched from this region's JSON by `category_id`; blank if the ID has no match. |
| `region` | Added by loader | String | Two-letter region code for the CSV, such as `US`. |

The Kaggle CSV has no `duration`, so this output has a source-specific schema
and **does not** pass the existing `load_data(..., "videos")` validator, which
requires duration. Read it with `pd.read_csv(...)`, or join with API-collected
video metadata on `video_id` to add verified durations. The source also has no
historical channel subscriber counts. The trending loader writes local CSVs. The two daily cohort collectors write to Supabase.

An offline normalization check is available with
`python -m unittest discover -s tests -p 'test_ingest_trending_dataset.py'`.

### TED single-channel CSV example

For CreatorLens, we're using the YouTube Data API v3 to collect publicly available information about different YouTube channels and their videos. The idea is to create a dataset that we can use to compare creators and eventually understand what factors might contribute to their growth.

For our initial test, we're using the TED YouTube channel and collecting information about its 10 most recent public uploads. This is mainly to make sure our data collection process works before expanding it to more channels.

### Setting Up the API

To access the YouTube API, you'll need to create a project through Google Cloud Console, enable YouTube Data API v3, and generate an API key.

The API key should be stored locally in a `.env` file:

    YOUTUBE_API_KEY=your_key_here

You'll also need to install the Python libraries we're using:

    python -m pip install google-api-python-client python-dotenv pandas

Once everything is set up, run:

    python scripts/collect_youtube_api.py

Make sure the API key isn't committed to GitHub.

### What Data Are We Collecting?

Our script currently uses three API endpoints:

- `channels.list`: Gets information about the channel itself, including its name, description, subscriber count, total views, and video count. It also gives us the channel's uploads playlist ID.
- `playlistItems.list`: Uses the uploads playlist to get the IDs of videos uploaded by the channel.
- `videos.list`: Uses those video IDs to retrieve information about each video, including its title, publication date, duration, views, likes, and comments.

We're separating the information into two datasets, one for channels and another for individual videos, since we'll eventually want to compare both overall channel growth and the performance of specific videos.

### Channel Dataset

Saved as `data/interim/channels_YYYY-MM-DD.csv`.

| Column | Data Type | Description |
|---|---|---|
| channel_id | String | Unique identifier for the channel |
| channel_name | String | Name of the YouTube channel |
| description | String | Channel description |
| published_at | Datetime | When the channel was created |
| subscriber_count | Integer (nullable) | Current public subscriber count |
| view_count | Integer | Total channel views |
| video_count | Integer | Number of public videos |
| collection_date | Date | Date we retrieved the data |

### Video Dataset

Saved as `data/interim/videos_YYYY-MM-DD.csv`.

| Column | Data Type | Description |
|---|---|---|
| video_id | String | Unique identifier for the video |
| channel_id | String | Channel the video belongs to |
| title | String | Video title |
| published_at | Datetime | When the video was published |
| duration | String | Video length in ISO 8601 format |
| category_id | String | YouTube's category identifier |
| view_count | Integer (nullable) | Current number of views |
| like_count | Integer (nullable) | Current number of likes |
| comment_count | Integer (nullable) | Current number of comments |
| collection_date | Date | Date we retrieved the data |

These are the data types we're expecting to work with. Some information, like dates and video durations, is originally returned as strings and may need to be converted when we load the datasets.

### Caching and Saving Our Data

Since the YouTube API has usage limits, we don't want to keep requesting information that we've already collected.

To avoid this, our script saves the original API responses as JSON files inside `data/raw/`, organized by collection date.

Whenever the script runs, it first checks whether we've already collected that particular data on the same day. If the file exists, it loads the saved information instead of making another API request. Otherwise, it retrieves the data from YouTube and saves the response.

This also allows us to collect snapshots on different days, which will eventually help us understand how a creator's statistics change over time.

After retrieving the information, we use Pandas to organize it into two CSV datasets, which are saved in `data/interim/`.

### API Quota Limitations

The YouTube Data API has a default daily quota of 10,000 units for standard requests, with separate limits for certain operations such as searching.

Different API operations have different costs. The three endpoints we're currently using each cost 1 unit per request:

- `channels.list`: 1 unit
- `playlistItems.list`: 1 unit
- `videos.list`: 1 unit

The TED test only requires around 3 units when its responses aren't already cached. Both daily collectors request fresh statistics and page through channel playlists, so their usage depends on the number of tracked IDs and playlist pages.

However, as we start collecting information from more channels and videos, we'll need to be more careful with how many requests we're making, especially if we need multiple pages of results.

### Limitations of Our Data

One of the bigger limitations is that the public YouTube API primarily gives us current statistics rather than complete historical records.

For example, we can retrieve a video's current view count, but we generally can't go back and see exactly how many views it had on a particular day in the past unless that information was previously recorded.

Some other limitations include:

- Subscriber counts are rounded, making smaller changes harder to measure.
- Likes and comments may not always be available.
- Information such as watch time, audience retention, impressions, and click-through rate requires access to a creator's private analytics.
- Revenue information isn't publicly accessible through the API.
- Private, deleted, or inaccessible videos may not appear in our dataset.
- Our initial test only collects recent uploads rather than a channel's entire video history.

Because of this, collecting snapshots over time will be especially important if we want to study long-term creator growth rather than just comparing current statistics.

### Data Loading and Validation

After generating the CSV files, use `scripts/load_data.py` to load them into pandas DataFrames and validate their contents. Run the following commands from the repository root (the folder containing `scripts/` and `tests/`). Replace `YYYY-MM-DD` with the collection date in your actual filenames.

```python
from scripts.load_data import load_data

channels = load_data("data/interim/channels_YYYY-MM-DD.csv", "channels")
videos = load_data("data/interim/videos_YYYY-MM-DD.csv", "videos")

print(channels.head())
print(videos.head())
print(channels.dtypes)
```

`load_data(file_path, dataset_type)` accepts a CSV path and either `"channels"` or `"videos"`. It returns a pandas DataFrame when the file passes validation. The loader checks that the file exists, the dataset type is supported, and required columns are present. It also checks numeric counts, required text fields, and date values; video durations are validated for video datasets. Invalid data raises an error rather than being silently accepted. Some YouTube statistics are optional and can be missing.

#### Required CSV columns

The loader requires **all columns listed below to exist** in the CSV, even if some cells are allowed to be empty. A missing column raises a `ValueError`.

**Channel dataset** (`dataset_type="channels"`):

| Required column | Expected value | Missing cell allowed? |
|---|---|---|
| `channel_id` | Nonempty string | No |
| `channel_name` | Nonempty string | No |
| `description` | Channel description (text) | Yes |
| `published_at` | Valid ISO 8601 timestamp | No |
| `subscriber_count` | Nonnegative integer | Yes |
| `view_count` | Nonnegative integer | No |
| `video_count` | Nonnegative integer | No |
| `collection_date` | Date in `YYYY-MM-DD` format | No |

**Video dataset** (`dataset_type="videos"`):

| Required column | Expected value | Missing cell allowed? |
|---|---|---|
| `video_id` | Nonempty string | No |
| `channel_id` | Nonempty string | No |
| `title` | Nonempty string | No |
| `published_at` | Valid ISO 8601 timestamp | No |
| `duration` | ISO 8601 duration, such as `PT5M30S` | No |
| `category_id` | Category identifier (text) | Yes |
| `view_count` | Nonnegative integer | Yes |
| `like_count` | Nonnegative integer | Yes |
| `comment_count` | Nonnegative integer | Yes |
| `collection_date` | Date in `YYYY-MM-DD` format | No |

For numeric columns, whole-number values are expected; optional missing statistics are supported using pandas' nullable `Int64` dtype. The date format applies to the CSV's **stored text**, not the way spreadsheet software may display the date.

#### Running the loader validation example

The standalone validation script is located at `tests/test_load_data.py`. From the repository root, run:

```powershell
python -m tests.test_load_data
```

The script creates temporary sample CSV data, so it does **not** require a YouTube API key or previously downloaded datasets. It demonstrates four cases:

1. A valid channel CSV loads successfully.
2. A nonnumeric view count is rejected.
3. A missing required column is rejected.
4. An invalid collection date is rejected.

Each successful check prints a `PASS` message. If a check fails, the script raises an error. Ensure the `tests/` folder contains `test_load_data.py` so the module command works consistently.

### Reproducing the Dataset

The Python script and documentation will be committed to GitHub, but the actual datasets and API keys will remain stored locally.

This means another team member should be able to clone the repository, set up their own API key, install the required libraries, and run the script to generate the same dataset structure.

The actual statistics may be different depending on when they run the script, since YouTube views, subscribers, and engagement are constantly changing.
