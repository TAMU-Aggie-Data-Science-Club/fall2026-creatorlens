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


**What are we trying to understand?**

Discovering quantifiable metrics that contribute to channel growth and popularity. Understanding what leads to long-term creator success, especially in the context of current trends and entertainment standards

**Define "Creator Growth"**

- Engagement (views, comments, likes, reposts) 
- Revenue per video/piece of content
- Finding your audience / gaining subscribers
- Increase in views, likes, comments, and shares across videos
- Popular in their niche
- Viewer retention rate

Growth capital - funding and resources that provide the means to further one’s business, the channel, to continue providing the product, the channel’s content, towards the customer base, the online audience. In a content creation environment, this can refer to salaries given to editors, maintaining a studio to increase production quality, and marketing investments that push one’s channel to a wider audience. Source - GigaStar

**Define the unit of analysis**
- Subscriber count
- Average video view count
- Average view duration per viewer
- Frequency of posts
- Number of brand collaborations
- Should be segmented by niche/demographic

**Six Metrics that contribute to channel performance (Source - uptube):**

Click-through rate - the percentage of people that clicked after viewing the thumbnail
Average view and duration and audience retention - how long people stay on a video and where in the video do they drop off
Average percentage viewed - the percentage of the video watched on average, independent of length
Impressions and traffic sources - how many times YouTube showed the thumbnail, and where views are being generated/promoted (search, suggested, browse, internal)
Returning vs new viewers - the division between new viewers and returning ones
Subscribers gained per video - how many subscribers each video earned
Understand the YouTube API

**Based on the Youtube API:**
**What channel information can we retrieve?**
                  
- Statistics: subscriber count, video count, likes, comments, and view count or what percentage of a channel’s total views come from views 6 months ago versus recent uploads
Source: https://www.searchapi.io/docs/youtube-channel

**What video information can we retrieve?**

List of videos uploaded by the channel
Channel metadata: title, description, keywords, and custom branding assets
Channel’s shorts and owned channels
Source: https://www.searchapi.io/docs/youtube-channel
What statistics are available?
For other channels, YouTube shows sub count, video count, view count, total public views, likes, and comments. Metadata such as upload frequency, times, and dates, etc.
https://www.searchapi.io/docs/youtube-channel 

**What information can be retrieved historically?**

Past public videos and their metadata (view count, publication date, etc.)
Specific video data (likes, comments, etc.)
There are some online tools that allow people to see other channels YouTube analytics. Stats like subscriber charts and sponsored video statistics are available to view.
https://clipchamp.com/en/blog/how-to-see-youtube-analytics-other-channels/ 

**What information cannot be retrieved historically?**

Historical timelines and graphs of metrics like sub count, total viewership, and specific video views require a third-party analysis tool like Social Blade
Also gives insight to keyword tags and content strategy/optimization
Dislikes on a video. Dislikes can indicate if a video was well received or not, but the ability to view the number of dislikes was removed (YouTube Blog). It seems it may still be possible to view using third party tools like this YouTube dislike viewer.  
*Are subscriber counts available?* Yes
*Are view counts available?* Yes
*Are likes/comments available?* Yes, unless hidden/restricted by creator
*What are the API quota limitations?*
Default limit of 10,000 units per day
Searching for Videos (100 units)
Information (1 unit)
Making Videos (1500 units)
What data will require us to collect snapshots over time?
Subscriber count
Video View count
Like count
Comment Count
Track the trends of these statistics individually, as well as in comparison to each other over time

**Which growth metrics can we actually pull for channels we don’t own?**

Only the public stuff: subscriber count, total views, and video count, plus views, likes, and comments on each video.
Click-through rate, impressions, watch time, and retention need the channel owner’s permission, so most of the six metrics above won’t be usable unless a creator shares their own data. Public sub counts are also rounded, so small changes on big channels are hard to see.
Source: Channels | YouTube Data API

**Does upload frequency relate to creator growth?**
In general, the more videos are uploaded the higher the total amount of views someone is going to get, or have a higher chance at having a video go viral, but there is no confirmation of what specific amount of videos uploaded in any respective time frame is most optimal for engagement.
Typically, it’s thought that more frequent uploads increase engagement as they allow for increased opportunity to be recommended. Total views tend to rise with output, but posting more only helps if quality can also be sustained. Videos must have strong retention so that the algorithm continues to recommend them.
Source - ScienceDirect

**Does engagement relate to creator growth?**

Yes, strong engagement shows viewer satisfaction, the strength of the community built around a channel, and boosts the growth of a channel long term through high activity. Engagement rate is defined as the ability to generate interaction, which is separate from CTR, retention, and watch time.
Source - mediaCube

**Do different types of creators experience different growth rates?**

Yes, depending on the growing popularity of content or niche, different creators can see vast growth. This is dependent on time of entering the niche, how stable the popularization is, and type of content produced. For example, an easy comparison would be short versus long-form content creators. Short form content became increasingly popular around 2020, and YouTube responded to this by adding YouTube shorts. However now long-form content is receiving “better completion and action rates” and boosts from algorithms than its counterpart short-form content. It all really just depends on the time and era of content, and creators and platforms need to adapt accordingly so that they can retain as many viewers as possible and keep them engaged and interested in the content being shared
Sources: Fastest Growing YouTube Niches in 2026: Growth Data & Velocity Rankings | OutlierKit Resources 
The Revival of Long-Form: Why Micro-Content Is Losing to Depth in 2025 
Important limitation
**Document any API limitation that could affect our definition of growth or our ability to use historical data.**
limitations on what data each app or platform share
having missing or estimated data in comparisons
ex: engagement can be hidden;
engagement totals don’t always accurately reflect history as view counts are typically lifetime totals. might not reflect recent virality or resurgences.
Limited data on popularity in terms of how well the general public recognizes a youtuber
Limited data on how well a youtuber’s content is liked/useful
source: App Limitations - A Complete Guide | Socialinsider Help Center 
