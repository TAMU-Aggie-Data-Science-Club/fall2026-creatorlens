# Deliverables & Timeline

> **How to read this file.** This is the PMs' best current estimate of what CreatorLens needs to ship and roughly when. It is a **living plan, not a contract**. The authoritative picture lives in **GitHub Issues and the Project board**.

## Milestones (suggested)

| # | Deliverable | Description | Owner (role) | Target |
|---|-------------|-------------|--------------|--------|
| 1 | Project scoping | Pick niches + cohort size. Define what "success" means (subscriber growth rate? view velocity? something else). | PM | Week 1 |
| 2 | Data access | YouTube API key setup, quota strategy, cache layout. Documented in [`DATA.md`](DATA.md). | PM + members | Week 1 |
| 3 | Cohort ingestion | Reproducible fetch of channel + top-N videos per channel with resumable caching. | Members | Weeks 2–3 |
| 4 | EDA | Distributions of engagement metrics, upload cadence patterns, correlations with growth. | Members | Week 3 |
| 5 | Feature engineering | Upload cadence, title/thumbnail length, view/like ratios, first-week view velocity. | Members | Week 4 |
| 6 | Clustering + PCA | KMeans / KNN on channels, PCA 2D projection for visualization. | Members | Weeks 4–5 |
| 7 | Trajectory analysis | Time-series charts, simple change-point detection, "what changed for this creator?" narrative view. | Members | Weeks 5–6 |
| 8 | Streamlit dashboard | Channel picker, cohort compare, growth explorer, cluster archetype browser. | Members + PM | Weeks 6–7 |
| 9 | Handoff & retro | Reproducibility check, short writeup, lessons learned. | PM | Week 8 |

## Timeline (rough)

```
Week:   1     2     3     4     5     6     7     8
        |-----|-----|-----|-----|-----|-----|-----|
Scope   ██
Ingest        ████
EDA                 ██
Features                  ██
Cluster                       ████
Trajectory                          ████
Dashboard                                  ████
Retro                                              ██
```

## Working agreements

- **Each deliverable maps to one or more GitHub Issues.** The board is the source of truth; this file is the summary.
- **Dates are estimates.** When reality diverges, update the issue and this file if the shift is material.
- **"Done" is defined per issue** via acceptance criteria — not by a date passing.
- **Reprioritize openly.** If a deliverable changes, a PM notes why in the issue so the decision is auditable.
