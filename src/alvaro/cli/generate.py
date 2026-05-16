from __future__ import annotations

import asyncio
import dataclasses
import datetime
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

import typer
from loguru import logger

from alvaro.config.loader import load_voices
from alvaro.db.client import build_db_client
from alvaro.db.migrations import run_migrations
from alvaro.db.queries import jobs as jobs_q
from alvaro.db.queries import niches as niches_q
from alvaro.db.queries import videos as videos_q
from alvaro.ideation.generator import generate_ideas
from alvaro.ideation.selector import select_best
from alvaro.llm.gemini_client import GeminiClient
from alvaro.llm.groq_client import GroqClient
from alvaro.llm.router import RouterClient
from alvaro.scripting.generator import generate_script
from alvaro.storage.r2 import build_r2_client
from alvaro.subtitles.builder import build_subtitles
from alvaro.tts.synthesizer import synthesize_script
from alvaro.video.background import select_background
from alvaro.video.compositor import compose_video

app = typer.Typer(name="generate", help="Run full video generation pipeline for a niche+slot")


@app.command()
def generate(
    niche: str = typer.Option(..., help="Niche ID (e.g. science, history)"),
    slot: str = typer.Option(..., help="Time slot: morning | noon | evening"),
) -> None:
    try:
        asyncio.run(_run(niche, slot))
    except SystemExit:
        raise
    except Exception as exc:
        logger.error("unhandled error: {}", exc)
        raise typer.Exit(code=1) from exc


async def _run(niche_id: str, slot: str) -> None:
    date_utc = datetime.datetime.now(tz=datetime.UTC).strftime("%Y-%m-%d")
    idempotency_key = f"{niche_id}_{date_utc}_{slot}"

    db = build_db_client()
    await db.connect()
    job = None
    tmp_dir: Path | None = None

    try:
        await run_migrations(db)

        job = await jobs_q.upsert_job(db, idempotency_key=idempotency_key, niche_id=niche_id)
        if job.status == "done":
            logger.info("job already done, skipping key={}", idempotency_key)
            return

        niche_state = await niches_q.get_or_create(db, niche_id)
        if niche_state.paused:
            logger.warning("niche {} is paused, skipping", niche_id)
            return

        await jobs_q.mark_running(db, job.id)
        await niches_q.mark_run_started(db, niche_id)

        llm = RouterClient(GroqClient(), GeminiClient())
        voices = load_voices()
        r2 = build_r2_client()

        ideas = await generate_ideas(niche_id, llm, db)
        best = select_best(ideas)
        script = await generate_script(best, niche_id, llm, voices)

        tmp_dir = Path(tempfile.mkdtemp(prefix=f"{job.id}_"))
        audio_path = tmp_dir / "audio.mp3"
        subs_path = tmp_dir / "subs.ass"
        output_path = tmp_dir / "final.mp4"

        await synthesize_script(script, script.suggested_voice_id, voices, audio_path)
        await build_subtitles(audio_path, script, subs_path)
        bg_path = await select_background(
            script.suggested_background_niche, r2, job_id=job.id
        )
        video_meta = await compose_video(
            audio_path, bg_path, subs_path, output_path, job.id, r2
        )

        sha256 = hashlib.sha256(output_path.read_bytes()).hexdigest()

        video = await videos_q.insert_video(
            db,
            job_id=job.id,
            niche_id=niche_id,
            title=script.hook_text,
            script_hash=sha256[:16],
            duration_s=int(video_meta.duration_s),
        )
        await videos_q.set_file_sha256(db, video.id, sha256)
        await videos_q.set_r2_location(db, video.id, video_meta.r2_key, r2._bucket)
        await videos_q.set_script_json(db, video.id, json.dumps(dataclasses.asdict(script)))

        await jobs_q.mark_done(db, job.id)
        await niches_q.mark_success(db, niche_id)
        logger.info("generate done niche={} slot={} video_id={}", niche_id, slot, video.id)

    except Exception as exc:
        if job is not None:
            await jobs_q.mark_failed(db, job.id, str(exc))
            await niches_q.increment_failures(db, niche_id)
        logger.error("generate failed niche={} slot={} err={}", niche_id, slot, exc)
        raise SystemExit(1) from exc

    finally:
        await db.close()
        if tmp_dir is not None and tmp_dir.exists():
            try:
                shutil.rmtree(tmp_dir)
            except Exception as exc:
                logger.warning("cleanup failed tmp_dir={} err={}", tmp_dir, exc)
