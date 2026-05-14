from __future__ import annotations

import asyncio
import datetime
from pathlib import Path
from typing import Literal

from loguru import logger

from alvaro.db.client import DbClient
from alvaro.db.queries import uploads as uploads_q
from alvaro.publishing._types import PublishingError, QuotaExceededError, UploadResult
from alvaro.publishing.metadata_builder import build_video_metadata
from alvaro.publishing.quota import record_quota_usage, reserve_quota
from alvaro.publishing.youtube_client import YouTubeClient
from alvaro.scripting.models import Script
from alvaro.storage.r2 import R2Client

_UNITS_UPLOAD = 1600


def _reconstruct_result(
    upload: uploads_q.Upload,
    script: Script,
    niche_id: str,
    privacy_status: str,
) -> UploadResult:
    meta = build_video_metadata(script, niche_id, privacy_status)
    yt_id = upload.youtube_video_id or ""
    return UploadResult(
        video_id=yt_id,
        video_url=f"https://youtube.com/shorts/{yt_id}",
        title=str(meta["snippet"]["title"]),
        description=str(meta["snippet"]["description"]),
        privacy_status=upload.privacy,
        upload_timestamp=datetime.datetime.fromtimestamp(
            upload.uploaded_at or 0, tz=datetime.UTC
        ),
        quota_units_consumed=0,
    )


async def publish_video(
    job_id: str,
    r2_key: str,
    script: Script,
    r2_client: R2Client,
    db: DbClient,
    video_db_id: str,
    privacy_status: Literal["private", "public", "unlisted"] = "private",
) -> UploadResult:
    existing = await uploads_q.get_by_video_id(db, video_db_id)

    if existing is not None:
        if existing.status == "done":
            logger.info("upload already exists for job_id={}, skipping", job_id)
            return _reconstruct_result(existing, script, script.niche_id, privacy_status)
        if existing.status == "uploading":
            raise PublishingError(
                "upload in inconsistent state, "
                "manual review in YouTube Studio required"
            )

    tmp = Path(f"/tmp/{job_id}_upload.mp4")  # noqa: S108
    upload_id: str | None = None

    try:
        logger.info("youtube upload start job_id={}", job_id)

        data = await asyncio.to_thread(r2_client.download_asset, r2_key)
        tmp.write_bytes(data)

        await reserve_quota(db, _UNITS_UPLOAD)

        meta = build_video_metadata(script, script.niche_id, privacy_status)

        if existing is None:
            new_upload = await uploads_q.insert_upload(
                db, video_id=video_db_id, privacy=privacy_status
            )
            upload_id = new_upload.id
        else:
            upload_id = existing.id
        await uploads_q.mark_uploading(db, upload_id)

        yt_client = YouTubeClient()
        try:
            yt_video_id = await yt_client.upload(meta, tmp)
        except Exception as exc:
            await uploads_q.mark_failed(db, upload_id, str(exc))
            raise

        await uploads_q.mark_done(db, upload_id, yt_video_id, _UNITS_UPLOAD)
        await record_quota_usage(db, _UNITS_UPLOAD, yt_video_id)

        now = datetime.datetime.now(tz=datetime.UTC)
        result = UploadResult(
            video_id=yt_video_id,
            video_url=f"https://youtube.com/shorts/{yt_video_id}",
            title=str(meta["snippet"]["title"]),
            description=str(meta["snippet"]["description"]),
            privacy_status=privacy_status,
            upload_timestamp=now,
            quota_units_consumed=_UNITS_UPLOAD,
        )
        logger.info("youtube upload done video_id={} job_id={}", yt_video_id, job_id)
        return result

    except QuotaExceededError:
        logger.error("youtube upload quota exceeded job_id={}", job_id)
        raise
    except Exception as exc:
        logger.error("youtube upload failed job_id={} err={}", job_id, exc)
        raise
    finally:
        tmp.unlink(missing_ok=True)
