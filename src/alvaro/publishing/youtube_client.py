from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

import google.auth.exceptions
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from alvaro.publishing._types import PublishingError, QuotaExceededError

_TOKEN_URI = "https://oauth2.googleapis.com/token"  # noqa: S105


def _is_transient(exc: BaseException) -> bool:
    if isinstance(exc, HttpError):
        return int(exc.resp.status) >= 500
    return isinstance(exc, ConnectionError | TimeoutError)


@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=2, min=2, max=8),
    retry=retry_if_exception(_is_transient),
    reraise=True,
)
def _upload_resumable(
    service: Any,
    body: dict[str, Any],
    mp4_path: Path,
) -> str:
    media = MediaFileUpload(str(mp4_path), mimetype="video/*", chunksize=8_388_608, resumable=True)
    try:
        resp = service.videos().insert(part="snippet,status", body=body, media_body=media).execute()
        return str(resp["id"])
    except HttpError as exc:
        status = int(exc.resp.status)
        details = str(exc.error_details)
        if status == 403 and "quotaExceeded" in details:
            raise QuotaExceededError(f"YouTube quota exceeded: {details}") from exc
        raise PublishingError(f"YouTube upload failed status={status}: {details}") from exc


class YouTubeClient:
    def __init__(self) -> None:
        try:
            creds: Credentials = Credentials(  # type: ignore[no-untyped-call]
                token=None,
                refresh_token=os.environ["YT_REFRESH_TOKEN"],
                client_id=os.environ["YT_CLIENT_ID"],
                client_secret=os.environ["YT_CLIENT_SECRET"],
                token_uri=_TOKEN_URI,
            )
            self._service: Any = build("youtube", "v3", credentials=creds, cache_discovery=False)
        except google.auth.exceptions.RefreshError as exc:
            raise PublishingError("OAuth refresh failed, re-run bootstrap_oauth.py") from exc

    async def upload(self, body: dict[str, Any], mp4_path: Path) -> str:
        try:
            return await asyncio.to_thread(_upload_resumable, self._service, body, mp4_path)
        except google.auth.exceptions.RefreshError as exc:
            raise PublishingError("OAuth refresh failed, re-run bootstrap_oauth.py") from exc
