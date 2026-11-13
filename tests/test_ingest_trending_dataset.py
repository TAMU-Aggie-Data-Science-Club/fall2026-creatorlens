import unittest

import pandas as pd

from scripts.ingest_trending_dataset import category_names, normalize_trending


class TrendingDatasetTest(unittest.TestCase):
    def test_all_observations_and_source_fields_are_retained(self):
        source = pd.DataFrame({
            "video_id": ["vid1", "vid1", "vid1", "vid2"],
            "channelId": ["UC1"] * 4,
            "channelTitle": ["Tech Channel"] * 4,
            "title": ["A review"] * 4,
            "publishedAt": ["2020-01-01T10:00:00Z"] * 4,
            "categoryId": [28] * 4,
            "view_count": [100, 110, 200, 300],
            "likes": [10, 11, 20, 30],
            "comment_count": [1, 2, 3, 4],
            "trending_date": [
                "2020-01-02T00:00:00Z", "2020-01-02T00:00:00Z",
                "2020-01-03T00:00:00Z", "2025-01-01T00:00:00Z",
            ],
            "tags": ["review|phone", "review|phone", None, "new"],
        })
        result = normalize_trending(source, "US", {"28": "Science & Technology"})
        self.assertEqual(len(result), 4)
        self.assertEqual(result["trending_date"].iloc[-1], "2025-01-01T00:00:00Z")
        self.assertEqual(result["view_count"].tolist(), [100, 110, 200, 300])
        self.assertEqual(result["tags"].iloc[0], "review|phone")
        self.assertTrue(pd.isna(result["tags"].iloc[2]))
        self.assertEqual(result["channel_id"].tolist(), ["UC1"] * 4)
        self.assertEqual(result.columns.is_unique, True)
        self.assertEqual(len(result.columns), len(source.columns) + 2)  # category_name and region
        self.assertNotIn("channelId", result.columns)
        self.assertNotIn("likes", result.columns)
        self.assertEqual(result["like_count"].tolist(), source["likes"].tolist())
        self.assertEqual(result["category_id"].tolist(), [28] * 4)
        self.assertEqual(result["category_name"].tolist(), ["Science & Technology"] * 4)

    def test_category_names_use_each_regions_json(self):
        source = pd.DataFrame({
            "video_id": ["vid1"], "channelId": ["UC1"], "title": ["Video"],
            "publishedAt": ["2020-01-01T00:00:00Z"], "categoryId": [28],
            "view_count": [100], "trending_date": ["2020-01-02T00:00:00Z"],
            "tags": ["tech"],
        })
        us = category_names({"items": [{"id": "28", "snippet": {"title": "Science & Technology"}}]})
        fr = category_names({"items": [{"id": "28", "snippet": {"title": "Science et technologie"}}]})
        self.assertEqual(normalize_trending(source, "US", us)["category_name"].iloc[0], "Science & Technology")
        self.assertEqual(normalize_trending(source, "FR", fr)["category_name"].iloc[0], "Science et technologie")
        self.assertEqual(normalize_trending(source, "FR", {})["category_id"].iloc[0], 28)
        self.assertTrue(pd.isna(normalize_trending(source, "FR", {})["category_name"].iloc[0]))

    def test_missing_required_column_fails(self):
        with self.assertRaisesRegex(ValueError, "missing columns"):
            normalize_trending(pd.DataFrame({"video_id": ["vid1"]}), "US", {})


if __name__ == "__main__":
    unittest.main()
