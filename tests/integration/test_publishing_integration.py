from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("RUN_PUBLISHING_INTEGRATION"),
    reason="RUN_PUBLISHING_INTEGRATION not set - skipping publishing integration test",
)


async def test_youtube_client_lists_my_channels() -> None:
    """Smoke-test that OAuth credentials are valid and the YouTube API responds."""
    import asyncio

    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    token_uri = "https://oauth2.googleapis.com/token"  # noqa: S105

    creds: Credentials = Credentials(  # type: ignore[no-untyped-call]
        token=None,
        refresh_token=os.environ["YT_REFRESH_TOKEN"],
        client_id=os.environ["YT_CLIENT_ID"],
        client_secret=os.environ["YT_CLIENT_SECRET"],
        token_uri=token_uri,
    )
    service = build("youtube", "v3", credentials=creds, cache_discovery=False)

    def _list_channels() -> list[str]:
        resp = service.channels().list(part="snippet", mine=True).execute()
        return [item["snippet"]["title"] for item in resp.get("items", [])]

    channels = await asyncio.to_thread(_list_channels)
    assert isinstance(channels, list)
    assert len(channels) >= 1, "Expected at least one channel for the authenticated account"
