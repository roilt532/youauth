"""Pipeline Runner - Orchestrates the full automation pipeline with viral content curation"""
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
from .content_discovery import discover_viral_content, download_viral_video
from .viral_analyzer import analyze_viral_content, generate_renarracion_script
from .shorts_optimizer import optimize_for_shorts

logger = logging.getLogger(__name__)

OUTPUT_BASE_DIR = os.environ.get('PIPELINE_OUTPUT_DIR', '/tmp/yt_automation')


STEP_NAMES = [
    'content_discovery',
    'viral_analysis',
    'script',
    'tts',
    'video_source',
    'video_compile',
    'shorts_optimize',
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
        await log(f"Starting VIRAL CURATION pipeline for job: {job.get('title', job_id)}")
        
        # ============================================================
        # STEP 0: Viral Content Discovery (NEW)
        # ============================================================
        viral_content = None
        use_viral_curation = job.get('use_viral_curation', True)  # Activado por defecto
        
        if use_viral_curation:
            await update_step('content_discovery', 'running')
            await log("🔍 Descubriendo contenido viral legal...")
            
            try:
                from .content_discovery import discover_viral_content
                
                content_type = job.get('content_type', 'roblox')
                viral_results = await discover_viral_content(
                    content_type=content_type,
                    min_views=job.get('min_views', 100_000),
                    max_results=5,
                    min_age_days=job.get('min_age_days', 365)
                )
                
                if viral_results:
                    # Tomar el primero (más viral)
                    viral_content = viral_results[0]
                    artifacts['viral_content'] = viral_content.to_dict()
                    await log(f"✅ Contenido viral encontrado: '{viral_content.title[:50]}...' ({viral_content.views:,} views)")
                else:
                    await log("⚠️ No se encontró contenido viral, usando modo clásico", 'warning')
                
                await update_step('content_discovery', 'completed')
            except Exception as e:
                await log(f"Content discovery failed: {e}", 'warning')
                await update_step('content_discovery', 'failed', str(e))
                # Continuar sin viral content
        
        # ============================================================
        # STEP 1: Viral Analysis (NEW - si tenemos viral content)
        # ============================================================
        viral_analysis = None
        
        if viral_content:
            await update_step('viral_analysis', 'running')
            await log("🧠 Analizando factores de viralidad...")
            
            try:
                from .viral_analyzer import analyze_viral_content
                
                viral_analysis = await analyze_viral_content(viral_content.to_dict())
                artifacts['viral_analysis'] = viral_analysis
                await log(f"✅ Análisis completado. Hook: '{viral_analysis.get('hook_strategy', '')[:50]}...'")
                await update_step('viral_analysis', 'completed')
            except Exception as e:
                await log(f"Viral analysis failed: {e}", 'warning')
                await update_step('viral_analysis', 'failed', str(e))
        
        # ============================================================
        # STEP 2: Script Generation (Adaptado a viral content)
        # ============================================================
        await update_step('script', 'running')
        await log("📝 Generando script...")
        
        try:
            if viral_content and viral_analysis:
                # Generar script de renarracion basado en análisis
                from .viral_analyzer import generate_renarracion_script
                
                script_result = await generate_renarracion_script(
                    content_data=viral_content.to_dict(),
                    analysis=viral_analysis,
                    language=job.get('language', 'es')
                )
                
                # Construir script_data compatible con el resto del pipeline
                script_data = {
                    'title_es': viral_analysis.get('title_optimized_es', viral_content.title),
                    'title_en': viral_content.title,
                    'hook_es': viral_analysis.get('hook_strategy', '¡No te lo pierdas!'),
                    'hook_en': viral_analysis.get('hook_strategy', 'Don\'t miss this!'),
                    'script_es': script_result.get('script_es', ''),
                    'script_en': script_result.get('script_es', ''),  # Mantener español
                    'thumbnail_prompt': f'viral youtube shorts thumbnail {viral_content.content_type} {viral_content.title[:50]} bright colorful dramatic no text 4K',
                    'tags': ['viral', 'shorts', viral_content.content_type, 'español', 'kids'],
                    'category': 'Gaming' if viral_content.content_type == 'roblox' else 'Entertainment',
                    'description_es': f"Contenido viral increíble sobre {viral_content.title[:80]}. ¡Dale like y suscríbete! #viral #shorts #{viral_content.content_type}",
                    'description_en': f"Amazing viral content about {viral_content.title[:80]}. Like and subscribe! #viral #shorts",
                }
                
                await log(f"✅ Script de renarracion generado")
            else:
                # Modo clásico: generar script original
                script_data = await generate_script(
                    topic=job.get('topic', 'Roblox adventure'),
                    content_type=job.get('content_type', 'roblox'),
                    language=job.get('language', 'bilingual'),
                    format_type=job.get('format', 'short'),
                    custom_prompt=job.get('custom_prompt')
                )
                await log(f"✅ Script original generado")
            
            artifacts['script'] = script_data
            await log(f"Script title: '{script_data.get('title_es', '')}'")
            await update_step('script', 'completed')
        except Exception as e:
            await log(f"Script generation failed: {e}", 'error')
            await update_step('script', 'failed', str(e))
            raise
        
        # ============================================================
        # STEP 2: TTS Narration
        # ============================================================
        await update_step('tts', 'running')
        await log("🎤 Generating TTS narration...")
        
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
            
            await log(f"✅ TTS generated: {len(tts_result)} audio files")
            await update_step('tts', 'completed')
        except Exception as e:
            await log(f"TTS generation failed: {e}", 'error')
            await update_step('tts', 'failed', str(e))
            raise
        
        # ============================================================
        # STEP 3: Source Video Download (Viral content o URL manual)
        # ============================================================
        source_video_path = None
        
        await update_step('video_source', 'running')
        
        # Prioridad 1: Viral content descubierto
        if viral_content and viral_content.platform != 'reddit':
            await log(f"📥 Descargando video viral: {viral_content.url}")
            try:
                from .content_discovery import download_viral_video
                
                source_video_path = await download_viral_video(
                    content=viral_content,
                    output_dir=output_dir,
                    job_id=job_id
                )
                
                if source_video_path:
                    artifacts['source_video'] = {
                        'path': source_video_path,
                        'title': viral_content.title,
                        'platform': viral_content.platform,
                        'views': viral_content.views
                    }
                    await log(f"✅ Video viral descargado")
                else:
                    await log("⚠️ Download falló, usando background generado", 'warning')
            except Exception as e:
                await log(f"Viral video download failed ({e}), usando background generado", 'warning')
        
        # Prioridad 2: URL manual del usuario
        elif job.get('source_url'):
            source_url = job['source_url']
            await log(f"📥 Descargando video manual: {source_url}")
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
                await log(f"✅ Video manual descargado: {download_result.get('title', '')}")
            except Exception as e:
                await log(f"Manual video download failed ({e}), usando background generado", 'warning')
        
        # Sin video fuente
        if not source_video_path:
            await log("📺 No video source - usando animated background")
        
        await update_step('video_source', 'completed')
        
        # ============================================================
        # STEP 4: Video Compilation
        # ============================================================
        await update_step('video_compile', 'running')
        await log("🎬 Compiling final video...")
        
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
            await log(f"✅ Video compiled: {Path(video_path).name} ({video_size:,} bytes)")
            await update_step('video_compile', 'completed')
        except Exception as e:
            await log(f"Video compilation failed: {e}", 'error')
            await update_step('video_compile', 'failed', str(e))
            raise
        
        # ============================================================
        # STEP 5: Shorts Optimization (NEW)
        # ============================================================
        optimize_shorts = job.get('optimize_shorts', True)
        
        if optimize_shorts and source_video_path:
            await update_step('shorts_optimize', 'running')
            await log("⚡ Optimizing for Shorts (subtitles, effects)...")
            
            try:
                from .shorts_optimizer import optimize_for_shorts
                
                optimized_path = await optimize_for_shorts(
                    video_path=video_path,
                    audio_path=primary_audio,
                    output_dir=output_dir,
                    job_id=job_id,
                    script_text=script_data.get('script_es', ''),
                    hook_text=script_data.get('hook_es', ''),
                    add_subtitles=job.get('add_subtitles', True)
                )
                
                # Reemplazar video_path con optimizado
                video_path = optimized_path
                artifacts['video_path'] = video_path
                await log(f"✅ Shorts optimized: {Path(video_path).name}")
                await update_step('shorts_optimize', 'completed')
            except Exception as e:
                await log(f"Shorts optimization failed ({e}), usando video sin optimizar", 'warning')
                await update_step('shorts_optimize', 'failed', str(e))
        else:
            await log("⏭️ Skipping Shorts optimization (no source video or disabled)")
            await update_step('shorts_optimize', 'skipped')
        
        # ============================================================
        # STEP 5: Thumbnail Generation
        # ============================================================
        await update_step('thumbnail', 'running')
        await log("🖼️ Generating thumbnail...")
        
        try:
            # Pick language based on setting
            title_for_thumb = script_data.get('title_es', job.get('topic', 'Video'))
            if job.get('language') == 'en':
                title_for_thumb = script_data.get('title_en', title_for_thumb)
            
            # Use AI prompt from analysis if available
            ai_prompt = None
            if viral_analysis and 'thumbnail_prompt' in script_data:
                ai_prompt = script_data['thumbnail_prompt']
            
            thumb_path = await generate_thumbnail(
                title=title_for_thumb,
                output_dir=output_dir,
                job_id=job_id,
                content_type=job.get('content_type', 'roblox'),
                ai_prompt=ai_prompt
            )
            artifacts['thumbnail_path'] = thumb_path
            await log(f"✅ Thumbnail generated: {Path(thumb_path).name}")
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
            await log("📤 Uploading to YouTube...")
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
                
                # Add viral source credit if using curated content
                if viral_content and viral_content.platform != 'reddit':
                    description += f'\n\n🎥 Inspired by viral content from {viral_content.platform}'
                
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
                await log(f"✅ Video uploaded: {upload_result['video_url']}")
                await update_step('upload', 'completed')
                
            except Exception as e:
                await log(f"YouTube upload failed: {e}", 'error')
                await update_step('upload', 'failed', str(e))
                raise
        else:
            await log("⚠️ YouTube credentials not configured - skipping upload", 'warning')
            await update_step('upload', 'skipped')
        
        await log("🎉 Pipeline completed successfully!")
        
        return {
            'run_id': run_id,
            'job_id': job_id,
            'status': 'completed',
            'artifacts': artifacts,
            'logs': logs,
            'output_dir': output_dir
        }
        
    except Exception as e:
        await log(f"❌ Pipeline failed: {e}", 'error')
        return {
            'run_id': run_id,
            'job_id': job_id,
            'status': 'failed',
            'artifacts': artifacts,
            'logs': logs,
            'output_dir': output_dir,
            'error': str(e)
        }
