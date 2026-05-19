from __future__ import annotations

import asyncio
import json
from typing import Literal, cast

import typer
from loguru import logger

from alvaro.db.client import build_db_client
from alvaro.db.queries import niches as niches_q
from alvaro.db.queries import videos as videos_q
from alvaro.publishing._types import QuotaExceededError
from alvaro.publishing.publisher import publish_video
from alvaro.publishing.quota import get_daily_quota_used
from alvaro.scripting.models import Script
from alvaro.storage.r2 import build_r2_client

_UNITS_PER_UPLOAD = 1600
_QUOTA_DAILY_CAP = 9000
_VALID_PRIVACY = ("public", "unlisted", "private")

__all__ = ["upload_cmd"]


def upload_cmd(
    max_videos: int = typer.Option(5, help="Maximum number of videos to upload"),
    privacy: str = typer.Option("public", help="Privacy status: public, unlisted, private"),
) -> None:
    if privacy not in _VALID_PRIVACY:
        raise typer.BadParameter(f"privacy must be one of {_VALID_PRIVACY}, got '{privacy}'")
    try:
        asyncio.run(_run(max_videos, cast(Literal["public", "unlisted", "private"], privacy)))
    except SystemExit:
        raise
    except Exception as exc:
        logger.error("unhandled error: {}", exc)
        raise typer.Exit(code=1) from exc


async def _run(max_videos: int, privacy: Literal["public", "unlisted", "private"]) -> None:
    db = build_db_client()
    await db.connect()

    try:
        r2 = build_r2_client()
        videos = await videos_q.get_uploadable(db, max_videos)
        ok, failed, skipped = 0, 0, 0

        for vid in videos:
            if vid.script_json is None:
                logger.warning("video {} has no script_json, skipping", vid.id)
                skipped += 1
                continue
            if vid.r2_key is None:
                logger.warning("video {} has no r2_key, skipping", vid.id)
                skipped += 1
                continue

            used = await get_daily_quota_used(db)
            if used + _UNITS_PER_UPLOAD > _QUOTA_DAILY_CAP:
                logger.warning(
                    "quota cap reached ({}/{}) stopping upload loop", used, _QUOTA_DAILY_CAP
                )
                break

            try:
                script = Script(**json.loads(vid.script_json))
                result = await publish_video(
                    job_id=vid.job_id,
                    r2_key=vid.r2_key,
                    script=script,
                    r2_client=r2,
                    db=db,
                    video_db_id=vid.id,
                    privacy_status=privacy,
                )
                await niches_q.increment_uploads(db, vid.niche_id)
                logger.info("uploaded video_id={} yt_id={}", vid.id, result.video_id)
                ok += 1
            except QuotaExceededError:
                logger.warning("quota exceeded mid-loop, stopping")
                break
            except Exception as exc:
                logger.error("upload failed video_id={} err={}", vid.id, exc)
                failed += 1

        logger.info("upload done ok={} failed={} skipped={}", ok, failed, skipped)

    finally:
        await db.close()
