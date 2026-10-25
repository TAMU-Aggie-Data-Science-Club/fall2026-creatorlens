# Data

This file explains **CreatorLens's** suggested data sources.

> **`DATA.md` is tracked in git. The `data/` folder is not.** Clone the repo, then populate `data/` locally.

## Suggested sources (starting point)

| Source | Origin / URL | Access method | License | Sensitivity | Notes |
|--------|--------------|---------------|---------|-------------|-------|
| YouTube Data API v3 | https://developers.google.com/youtube/v3 | REST via `google-api-python-client`, Google Cloud key | Google API ToS | None (public channels) | 10,000-unit daily quota — plan queries carefully |
| Kaggle Trending YouTube Video Dataset | https://www.kaggle.com/datasets/rsrishav/youtube-trending-video-dataset | Kaggle download | CC0 | None | Great for prototyping without burning API quota |
| Social Blade (optional) | https://socialblade.com | HTML — **verify ToS before scraping** | Proprietary | None | Historical subscriber trajectories back in time. Check licensing terms first. |
| Kaggle YouTube 8M subset | https://research.google.com/youtube8m/ | Research download | Custom (research use) | None | Only if going toward visual features later |

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

Our initial test only requires around 3 units when the responses aren't already cached.

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
