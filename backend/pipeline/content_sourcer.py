"""Content Sourcer - Uses yt-dlp to download and process Roblox clips and other videos"""
import asyncio
import logging
import os
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


async def download_video(
    url: str,
    output_dir: str,
    job_id: str,
    max_duration: int = 120,  # max 2 minutes
    format_type: str = 'short'  # 'short' (9:16) or 'long' (16:9)
) -> dict:
    """Download a video using yt-dlp with anti-detection options."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    output_file = output_path / f"{job_id}_source.%(ext)s"
    
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': str(output_file),
        'quiet': True,
        'no_warnings': True,
        'match_filter': _duration_filter(max_duration),
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
        # Anti-detection: random user agent
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        },
    }
    
    try:
        import yt_dlp
        
        loop = asyncio.get_event_loop()
        
        def _download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return info
        
        info = await loop.run_in_executor(None, _download)
        
        # Find the downloaded file
        downloaded_file = output_path / f"{job_id}_source.mp4"
        if not downloaded_file.exists():
            # Try to find any downloaded file
            for f in output_path.glob(f"{job_id}_source.*"):
                if f.suffix in ('.mp4', '.webm', '.mkv'):
                    downloaded_file = f
                    break
        
        result = {
            'source_path': str(downloaded_file) if downloaded_file.exists() else None,
            'title': info.get('title', ''),
            'duration': info.get('duration', 0),
            'uploader': info.get('uploader', ''),
            'view_count': info.get('view_count', 0),
        }
        
        logger.info(f"Downloaded: {result['title']} ({result['duration']}s)")
        return result
        
    except Exception as e:
        logger.error(f"Download error for {url}: {e}")
        raise


def _duration_filter(max_duration: int):
    """Create a duration filter for yt-dlp."""
    def filter_func(info, *, incomplete):
        duration = info.get('duration', 0)
        if duration and duration > max_duration:
            return f"Video too long: {duration}s > {max_duration}s"
        return None
    return filter_func


async def get_video_info(url: str) -> dict:
    """Get video info without downloading."""
    try:
        import yt_dlp
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
        }
        
        loop = asyncio.get_event_loop()
        
        def _get_info():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)
        
        info = await loop.run_in_executor(None, _get_info)
        
        return {
            'title': info.get('title', ''),
            'duration': info.get('duration', 0),
            'uploader': info.get('uploader', ''),
            'thumbnail': info.get('thumbnail', ''),
            'description': info.get('description', '')[:200],
            'view_count': info.get('view_count', 0),
            'upload_date': info.get('upload_date', ''),
        }
    except Exception as e:
        logger.error(f"Error getting video info: {e}")
        raise


async def normalize_video(
    input_path: str,
    output_dir: str,
    job_id: str,
    format_type: str = 'short'
) -> str:
    """Normalize video to YouTube Shorts (9:16) or standard (16:9) format."""
    output_path = Path(output_dir)
    output_file = output_path / f"{job_id}_normalized.mp4"
    
    if format_type == 'short':
        # 9:16 for Shorts: 1080x1920
        vf_filter = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
    else:
        # 16:9 for standard: 1920x1080
        vf_filter = "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080"
    
    cmd = [
        'ffmpeg', '-i', input_path,
        '-vf', vf_filter,
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '23',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-r', '30',
        '-y',
        str(output_file)
    ]
    
    loop = asyncio.get_event_loop()
    
    def _run_ffmpeg():
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg error: {result.stderr}")
        return result
    
    await loop.run_in_executor(None, _run_ffmpeg)
    logger.info(f"Video normalized: {output_file}")
    return str(output_file)
