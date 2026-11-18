"""Offline checks for the November tech cohort collector."""

import sys
import unittest
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import collect_tech_cohort_daily as collector


NOW = datetime(2026, 11, 6, 12, 0, tzinfo=timezone.utc)


class FakeCursor:
    def __init__(self, conn):
        self.conn = conn
        self.rows = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql, args):
        self.conn.statements.append((sql, args))
        if "select cc.channel_id" in sql:
            self.rows = [("channel-1",)]
        elif "select v.video_id" in sql:
            self.rows = [("old-video",)]

    def fetchall(self):
        return self.rows


class FakeConnection:
    def __init__(self):
        self.statements = []
        self.commits = 0

    def cursor(self):
        return FakeCursor(self)

    @contextmanager
    def transaction(self):
        yield
        self.commits += 1


class FakeEndpoint:
    def __init__(self, callback):
        self.callback = callback
        self.calls = []

    def list(self, **kwargs):
        self.calls.append(kwargs)
        self.kwargs = kwargs
        return self

    def execute(self):
        return self.callback(self.kwargs)


class FakeYouTube:
    def __init__(self):
        self.channel_endpoint = FakeEndpoint(lambda _: {"items": [{
            "id": "channel-1",
            "snippet": {"title": "Tech", "publishedAt": "2020-01-01T00:00:00Z"},
            "contentDetails": {"relatedPlaylists": {"uploads": "uploads-1"}},
            "statistics": {"subscriberCount": "100", "viewCount": "1000", "videoCount": "2"},
        }]})
        self.playlist_endpoint = FakeEndpoint(self.playlist_response)
        self.video_endpoint = FakeEndpoint(lambda args: {"items": [{
            "id": video_id,
            "snippet": {"channelId": "channel-1", "title": video_id,
                        "publishedAt": "2026-11-05T00:00:00Z"},
            "contentDetails": {"duration": "PT1M"},
            "statistics": {"viewCount": "42", "likeCount": "3", "commentCount": "1"},
        } for video_id in args["id"].split(",")]})

    def playlist_response(self, args):
        if "pageToken" not in args:
            return {"items": [{"contentDetails": {
                "videoId": "new-video", "videoPublishedAt": "2026-11-05T01:00:00Z",
            }}], "nextPageToken": "next"}
        return {"items": [{"contentDetails": {
            "videoId": "older-video", "videoPublishedAt": "2025-11-01T01:00:00Z",
        }}], "nextPageToken": "unneeded"}

    def channels(self):
        return self.channel_endpoint

    def playlistItems(self):
        return self.playlist_endpoint

    def videos(self):
        return self.video_endpoint


class CollectorTests(unittest.TestCase):
    def test_daily_run_includes_new_uploads_and_upserts_one_day(self):
        conn, youtube = FakeConnection(), FakeYouTube()
        self.assertEqual(collector.run(conn, youtube, lambda: NOW), (1, 2))
        self.assertEqual(len(youtube.playlist_endpoint.calls), 2)
        self.assertEqual(youtube.video_endpoint.calls[0]["id"], "new-video,old-video")
        self.assertEqual(conn.commits, 1)
        snapshots = [(sql, args) for sql, args in conn.statements
                     if "insert into public.channel_snapshots" in sql
                     or "insert into public.video_snapshots" in sql]
        self.assertEqual(len(snapshots), 3)
        self.assertTrue(all(args[1] == NOW.date() for _, args in snapshots))
        self.assertTrue(all("on conflict" in sql and "collected_at <= excluded.collected_at" in sql
                            for sql, _ in snapshots))
        self.assertEqual(collector.run(conn, youtube, lambda: NOW), (1, 2))
        self.assertEqual(conn.commits, 2)
        self.assertEqual(len([sql for sql, _ in conn.statements
                              if "insert into public.video_snapshots" in sql]), 4)

    def test_outside_window_does_not_request_or_write(self):
        conn, youtube = FakeConnection(), FakeYouTube()
        self.assertEqual(collector.run(conn, youtube,
                        lambda: datetime(2026, 12, 1, tzinfo=timezone.utc)), (0, 0))
        self.assertFalse(conn.statements)
        self.assertFalse(youtube.channel_endpoint.calls)

    def test_api_requests_batch_at_fifty(self):
        youtube = FakeYouTube()
        ids = [f"id-{n}" for n in range(51)]
        collector.fetch_channels(youtube, ids, lambda: NOW)
        collector.fetch_videos(youtube, ids, lambda: NOW)
        self.assertEqual([len(call["id"].split(",")) for call in youtube.channel_endpoint.calls], [50, 1])
        self.assertEqual([len(call["id"].split(",")) for call in youtube.video_endpoint.calls], [50, 1])

    def test_missing_uploads_playlist_does_not_stop_other_channels(self):
        class MissingPlaylist(Exception):
            resp = type("Response", (), {"status": 404})()

        youtube = FakeYouTube()
        channels = [
            ({"id": "missing-channel", "contentDetails": {"relatedPlaylists": {
                "uploads": "missing-playlist"}}}, NOW),
            ({"id": "channel-1", "contentDetails": {"relatedPlaylists": {
                "uploads": "uploads-1"}}}, NOW),
        ]
        regular_response = youtube.playlist_response

        def respond(args):
            if args["playlistId"] == "missing-playlist":
                raise MissingPlaylist()
            return regular_response(args)

        youtube.playlist_endpoint.callback = respond
        self.assertEqual(collector.discover_uploads(youtube, channels), {"new-video"})
        self.assertEqual(len(youtube.playlist_endpoint.calls), 3)

    def test_quota_failure_still_stops_collection(self):
        class QuotaError(Exception):
            resp = type("Response", (), {"status": 403})()

        youtube = FakeYouTube()
        youtube.playlist_endpoint.callback = lambda _: (_ for _ in ()).throw(QuotaError())
        with self.assertRaises(QuotaError):
            collector.run(FakeConnection(), youtube, lambda: NOW)


if __name__ == "__main__":
    unittest.main()
