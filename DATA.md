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
