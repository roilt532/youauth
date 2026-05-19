from __future__ import annotations

import asyncio
import datetime
import time

import typer
from loguru import logger

from alvaro.db.client import build_db_client
from alvaro.db.queries import metrics as metrics_q
from alvaro.db.queries import uploads as uploads_q
from alvaro.publishing.youtube_client import YouTubeClient

__all__ = ["analytics_cmd"]


def analytics_cmd(
    window_days: int = typer.Option(7, help="Number of days to look back"),
) -> None:
    try:
        asyncio.run(_run(window_days))
    except Exception as exc:
        logger.error("unhandled error: {}", exc)
        raise typer.Exit(code=1) from exc


async def _run(window_days: int) -> None:
    since = int(
        (datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(days=window_days)).timestamp()
    )

    db = build_db_client()
    await db.connect()

    try:
        done_uploads = await uploads_q.get_recent_done(db, since)
        if not done_uploads:
            logger.info("no uploads in window, nothing to fetch")
            return

        yt = YouTubeClient()
        ok, failed = 0, 0

        for up in done_uploads:
            yt_id = up.youtube_video_id
            if yt_id is None:
                continue
            try:
                stats = await _fetch_stats(yt, yt_id)
                await metrics_q.insert_snapshot(
                    db,
                    youtube_video_id=yt_id,
                    snapshot_at=int(time.time()),
                    views=stats["views"],
                    likes=stats["likes"],
                    comments=stats["comments"],
                )
                ok += 1
            except Exception as exc:
                logger.error("metrics failed yt_id={} err={}", yt_id, exc)
                failed += 1

        logger.info("analytics done ok={} failed={}", ok, failed)

    finally:
        await db.close()


async def _fetch_stats(yt: YouTubeClient, yt_id: str) -> dict[str, int]:
    def _call() -> dict[str, int]:
        resp = yt._service.videos().list(part="statistics", id=yt_id).execute()
        items = resp.get("items", [])
        if not items:
            raise ValueError(f"no stats returned for yt_id={yt_id}")
        s = items[0]["statistics"]
        return {
            "views": int(s.get("viewCount", 0)),
            "likes": int(s.get("likeCount", 0)),
            "comments": int(s.get("commentCount", 0)),
        }

    return await asyncio.to_thread(_call)
