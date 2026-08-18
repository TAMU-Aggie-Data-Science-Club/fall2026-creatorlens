# CreatorLens — Beginner

*ADSC Catalyst Project · Fall 2026*

## Overview

CreatorLens analyzes YouTube channel growth by combining video metadata, audience engagement, and channel statistics to uncover the factors that drive long-term creator success. The final artifact is a dashboard that visualizes growth trajectories and compares creators side by side.

## Objective

Build a comparative-analytics tool for YouTube creators that surfaces which content, timing, and channel-level patterns correlate with sustained growth — and lets a viewer explore trajectories interactively.

## Suggested tech stack

- **Data processing:** Python, Pandas, NumPy
- **Modeling / ML:** KMeans, KNN, PCA, simple time-series decomposition
- **Visualization / dashboard:** Streamlit, Plotly
- **Data sources:** YouTube Data API v3, Kaggle YouTube datasets

See [`DATA.md`](DATA.md) for concrete data sources and how to access them.

## What team members will gain

- Real YouTube engagement analysis with hands-on API work
- A defensible take on what actually makes big-creator videos pop
- Insights an actual small creator could apply

## Suggested scope (v1)

Pick a **cohort of 100–500 channels in 2–3 niches** (e.g., science communication + tech reviews) rather than "all of YouTube." A small, comparable cohort produces much better analysis than a broad thin one.

Build:

1. Ingestion for channel + video metadata via YouTube Data API v3 (respect quota),
2. Feature engineering (upload cadence, title/thumbnail length, view/like ratios, view velocity in first N days),
3. Clustering (KMeans / KNN) + PCA visualization of channel archetypes,
4. Trajectory time-series charts (subscribers, cumulative views) with change-point highlighting,
5. Streamlit dashboard: channel picker, cohort comparison, growth explorer.

**Out of scope for v1:** comment-sentiment NLP, thumbnail computer vision, real-time ingest, monetization/revenue estimation.

See [`DELIVERABLES.md`](DELIVERABLES.md) for the suggested deliverable breakdown and rough timeline.

## Repository map

| File / folder | Purpose |
|---|---|
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | **Start here.** How the team runs the project on GitHub — PM vs. member roles, the issue → PR → `main` flow, branching, worktrees, reviews. |
| [`DELIVERABLES.md`](DELIVERABLES.md) | Suggested deliverables and rough timeline. A living plan, not a contract. |
| [`DATA.md`](DATA.md) | Suggested data sources, how to access them, and the source register. |
| [`data/`](data/) | Local working folder for datasets. **Git-ignored** — data is never committed. |
| [`AGENTS.md`](AGENTS.md) | Machine-facing workflow rules for AI coding agents. |
| [`CODEOWNERS`](CODEOWNERS) | **Team roster + review policy.** PMs, members, and the code-owner rule for PRs into `main`. |


## Team

The current PMs and members for this project are listed in [`CODEOWNERS`](CODEOWNERS). PMs listed there are the code owners for PRs into `main`.
## Notes for PMs

This README, [`DELIVERABLES.md`](DELIVERABLES.md), and [`DATA.md`](DATA.md) are **suggestions**, not commitments. Rewrite them as the team scopes the real project.

## Notes for members

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) before touching code. Then pick up an issue from the board.
