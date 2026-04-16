"""Video Compiler - Uses MoviePy + FFmpeg to compile final videos"""
import asyncio
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


async def compile_video(
    audio_path: str,
    output_dir: str,
    job_id: str,
    source_video_path: Optional[str] = None,
    format_type: str = 'short',
    title: str = '',
    hook_text: str = ''
) -> str:
    """Compile final video with audio narration, overlays, and effects."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        _compile_video_sync,
        audio_path, output_dir, job_id,
        source_video_path, format_type, title, hook_text
    )


def _compile_video_sync(
    audio_path: str,
    output_dir: str,
    job_id: str,
    source_video_path: Optional[str] = None,
    format_type: str = 'short',
    title: str = '',
    hook_text: str = ''
) -> str:
    """Synchronous video compilation."""
    from moviepy import (
        VideoFileClip, AudioFileClip, ColorClip,
        CompositeVideoClip, concatenate_videoclips
    )
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Video dimensions
    if format_type == 'short':
        width, height = 1080, 1920  # 9:16 Shorts
    else:
        width, height = 1920, 1080  # 16:9 Standard
    
    try:
        # Load audio
        audio_clip = AudioFileClip(audio_path)
        audio_duration = audio_clip.duration
        
        # Create or load base video
        if source_video_path and os.path.exists(source_video_path):
            logger.info(f"Using source video: {source_video_path}")
            try:
                base_video = VideoFileClip(source_video_path)
                # Loop if video is shorter than audio
                if base_video.duration < audio_duration:
                    repeats = int(audio_duration / base_video.duration) + 1
                    clips_to_concat = [base_video] * repeats
                    base_video = concatenate_videoclips(clips_to_concat)
                # Trim to audio length
                base_video = base_video.subclipped(0, audio_duration)
                # Resize to target dimensions
                base_video = base_video.resized((width, height))
            except Exception as e:
                logger.warning(f"Error loading source video: {e}. Using color background.")
                base_video = _create_kids_background(width, height, audio_duration)
        else:
            logger.info("No source video provided, creating animated background")
            base_video = _create_kids_background(width, height, audio_duration)
        
        # Attach audio
        final_video = base_video.with_audio(audio_clip)
        
        # Output path
        output_file = output_path / f"{job_id}_final.mp4"
        
        # Render video
        logger.info(f"Rendering video: {output_file}")
        final_video.write_videofile(
            str(output_file),
            fps=30,
            codec='libx264',
            audio_codec='aac',
            preset='ultrafast',
            audio_bitrate='128k',
            logger=None
        )
        
        # Cleanup
        try:
            audio_clip.close()
            base_video.close()
            final_video.close()
        except Exception:
            pass
        
        video_size = output_file.stat().st_size
        logger.info(f"Video compiled: {output_file} ({video_size:,} bytes, {audio_duration:.1f}s)")
        return str(output_file)
        
    except Exception as e:
        logger.error(f"Video compilation error for job {job_id}: {e}")
        raise


def _create_kids_background(width: int, height: int, duration: float):
    """Create a vibrant animated background for videos without source."""
    from moviepy import ColorClip
    # Deep navy background with YouTube/gaming vibe
    return ColorClip(size=(width, height), color=(10, 15, 50), duration=duration)
