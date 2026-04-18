"""Pipeline Runner - Orchestrates the full automation pipeline"""
import asyncio
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Callable

from .script_generator import generate_script
from .tts_generator import generate_tts
from .video_compiler import compile_video
from .thumbnail_generator import generate_thumbnail
from .content_sourcer import download_video, get_video_info
from .youtube_uploader import upload_video

logger = logging.getLogger(__name__)

OUTPUT_BASE_DIR = os.environ.get('PIPELINE_OUTPUT_DIR', '/tmp/yt_automation')


STEP_NAMES = [
    'script',
    'tts',
    'video_source',
    'video_compile',
    'thumbnail',
    'upload'
]


async def run_pipeline(
    job: dict,
    settings: dict,
    update_callback: Optional[Callable] = None,
    log_callback: Optional[Callable] = None
) -> dict:
    """
    Run the full automation pipeline for a job.
    
    job: dict with job data
    settings: dict with YouTube credentials and configuration
    update_callback: async function to call with step updates
    log_callback: async function to call with log messages
    """
    job_id = job.get('id', str(uuid.uuid4()))
    run_id = str(uuid.uuid4())
    output_dir = os.path.join(OUTPUT_BASE_DIR, run_id)
    os.makedirs(output_dir, exist_ok=True)
    
    artifacts = {}
    logs = []
    
    async def log(message: str, level: str = 'info'):
        entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': level,
            'message': message
        }
        logs.append(entry)
        if log_callback:
            await log_callback(entry)
        getattr(logger, level, logger.info)(f"[{job_id}] {message}")
    
    async def update_step(step_name: str, status: str, error: str = None):
        if update_callback:
            await update_callback({
                'step': step_name,
                'status': status,
                'error': error,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
    
    try:
        await log(f"Starting pipeline for job: {job.get('title', job_id)}")
        
        # ============================================================
        # STEP 1: Script Generation
        # ============================================================
        await update_step('script', 'running')
        await log("Generating bilingual script...")
        
        try:
            script_data = await generate_script(
                topic=job.get('topic', 'Roblox adventure'),
                content_type=job.get('content_type', 'roblox'),
                language=job.get('language', 'bilingual'),
                format_type=job.get('format', 'short'),
                custom_prompt=job.get('custom_prompt')
            )
            artifacts['script'] = script_data
            await log(f"Script generated: '{script_data.get('title_es', '')}'")
            await update_step('script', 'completed')
        except Exception as e:
            await log(f"Script generation failed: {e}", 'error')
            await update_step('script', 'failed', str(e))
            raise
        
        # ============================================================
        # STEP 2: TTS Narration
        # ============================================================
        await update_step('tts', 'running')
        await log("Generating TTS narration...")
        
        try:
            primary_lang = job.get('language', 'bilingual')
            tts_result = await generate_tts(
                text_es=script_data.get('script_es', ''),
                text_en=script_data.get('script_en', ''),
                output_dir=output_dir,
                job_id=job_id,
                lang_mode=primary_lang
            )
            artifacts.update(tts_result)
            
            # Use ES audio as primary (or EN if ES not available)
            primary_audio = tts_result.get('audio_es') or tts_result.get('audio_en')
            if not primary_audio:
                raise ValueError("No audio generated")
            
            await log(f"TTS generated: {len(tts_result)} audio files")
            await update_step('tts', 'completed')
        except Exception as e:
            await log(f"TTS generation failed: {e}", 'error')
            await update_step('tts', 'failed', str(e))
            raise
        
        # ============================================================
        # STEP 3: Source Video (Download if URL provided)
        # ============================================================
        source_video_path = None
        source_url = job.get('source_url', '')
        
        await update_step('video_source', 'running')
        
        if source_url:
            await log(f"Downloading source video: {source_url}")
            try:
                download_result = await download_video(
                    url=source_url,
                    output_dir=output_dir,
                    job_id=job_id,
                    max_duration=120,
                    format_type=job.get('format', 'short')
                )
                source_video_path = download_result.get('source_path')
                artifacts['source_video'] = download_result
                await log(f"Source video downloaded: {download_result.get('title', '')}")
            except Exception as e:
                await log(f"Source video download failed (will use color background): {e}", 'warning')
            await update_step('video_source', 'completed')
        else:
            await log("No source video URL - using animated background")
            await update_step('video_source', 'completed')
        
        # ============================================================
        # STEP 4: Video Compilation
        # ============================================================
        await update_step('video_compile', 'running')
        await log("Compiling final video...")
        
        try:
            video_path = await compile_video(
                audio_path=primary_audio,
                output_dir=output_dir,
                job_id=job_id,
                source_video_path=source_video_path,
                format_type=job.get('format', 'short'),
                title=script_data.get('title_es', ''),
                hook_text=script_data.get('hook_es', ''),
                content_type=job.get('content_type', 'roblox')
            )
            artifacts['video_path'] = video_path
            video_size = os.path.getsize(video_path)
            await log(f"Video compiled: {Path(video_path).name} ({video_size:,} bytes)")
            await update_step('video_compile', 'completed')
        except Exception as e:
            await log(f"Video compilation failed: {e}", 'error')
            await update_step('video_compile', 'failed', str(e))
            raise
        
        # ============================================================
        # STEP 5: Thumbnail Generation
        # ============================================================
        await update_step('thumbnail', 'running')
        await log("Generating thumbnail...")
        
        try:
            # Pick language based on setting
            title_for_thumb = script_data.get('title_es', job.get('topic', 'Video'))
            if job.get('language') == 'en':
                title_for_thumb = script_data.get('title_en', title_for_thumb)
            
            thumb_path = await generate_thumbnail(
                title=title_for_thumb,
                output_dir=output_dir,
                job_id=job_id,
                content_type=job.get('content_type', 'roblox')
            )
            artifacts['thumbnail_path'] = thumb_path
            await log(f"Thumbnail generated: {Path(thumb_path).name}")
            await update_step('thumbnail', 'completed')
        except Exception as e:
            await log(f"Thumbnail generation failed: {e}", 'error')
            await update_step('thumbnail', 'failed', str(e))
            raise
        
        # ============================================================
        # STEP 6: YouTube Upload
        # ============================================================
        await update_step('upload', 'running')
        
        yt_client_id = settings.get('youtube_client_id', '')
        yt_client_secret = settings.get('youtube_client_secret', '')
        yt_refresh_token = settings.get('youtube_refresh_token', '')
        
        if yt_client_id and yt_client_secret and yt_refresh_token:
            await log("Uploading to YouTube...")
            try:
                # Choose title, description, tags based on language
                lang = job.get('language', 'bilingual')
                if lang == 'en':
                    title = script_data.get('title_en', '')
                    description = script_data.get('description_en', '')
                else:
                    title = script_data.get('title_es', '')
                    description = script_data.get('description_es', '')
                    if lang == 'bilingual':
                        description += '\n\n' + script_data.get('description_en', '')
                
                # Map content type to YouTube category
                category_map = {
                    'roblox': '20',   # Gaming
                    'curiosity': '27', # Education
                    'story': '1',     # Film & Animation
                    'animated': '1'   # Film & Animation
                }
                category_id = category_map.get(job.get('content_type', 'roblox'), '20')
                
                upload_result = await upload_video(
                    video_path=video_path,
                    thumbnail_path=thumb_path,
                    title=title,
                    description=description,
                    tags=script_data.get('tags', []),
                    category_id=category_id,
                    made_for_kids=job.get('made_for_kids', True),
                    client_id=yt_client_id,
                    client_secret=yt_client_secret,
                    refresh_token=yt_refresh_token,
                    privacy=settings.get('upload_privacy', 'public')
                )
                
                artifacts['youtube_url'] = upload_result['video_url']
                artifacts['youtube_video_id'] = upload_result['video_id']
                await log(f"Video uploaded: {upload_result['video_url']}")
                await update_step('upload', 'completed')
                
            except Exception as e:
                await log(f"YouTube upload failed: {e}", 'error')
                await update_step('upload', 'failed', str(e))
                raise
        else:
            await log("YouTube credentials not configured - skipping upload", 'warning')
            await update_step('upload', 'skipped')
        
        await log("Pipeline completed successfully!")
        
        return {
            'run_id': run_id,
            'job_id': job_id,
            'status': 'completed',
            'artifacts': artifacts,
            'logs': logs,
            'output_dir': output_dir
        }
        
    except Exception as e:
        await log(f"Pipeline failed: {e}", 'error')
        return {
            'run_id': run_id,
            'job_id': job_id,
            'status': 'failed',
            'artifacts': artifacts,
            'logs': logs,
            'output_dir': output_dir,
            'error': str(e)
        }
