"""TTS Generator - Uses gTTS for free text-to-speech narration"""
import asyncio
import logging
import os
from pathlib import Path
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


async def generate_tts(
    text_es: str,
    text_en: str,
    output_dir: str,
    job_id: str,
    lang_mode: str = 'bilingual'  # 'es', 'en', 'bilingual'
) -> dict:
    """Generate TTS audio files for Spanish and/or English narration."""
    from gtts import gTTS
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    result = {}
    
    try:
        if lang_mode in ('es', 'bilingual') and text_es:
            logger.info(f"Generating Spanish TTS for job {job_id}")
            tts_es = gTTS(text=text_es, lang='es', slow=False)
            audio_es_path = output_path / f"{job_id}_narration_es.mp3"
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, tts_es.save, str(audio_es_path))
            result['audio_es'] = str(audio_es_path)
            result['audio_es_size'] = audio_es_path.stat().st_size
            logger.info(f"Spanish TTS saved: {audio_es_path} ({result['audio_es_size']:,} bytes)")
        
        if lang_mode in ('en', 'bilingual') and text_en:
            logger.info(f"Generating English TTS for job {job_id}")
            tts_en = gTTS(text=text_en, lang='en', slow=False)
            audio_en_path = output_path / f"{job_id}_narration_en.mp3"
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, tts_en.save, str(audio_en_path))
            result['audio_en'] = str(audio_en_path)
            result['audio_en_size'] = audio_en_path.stat().st_size
            logger.info(f"English TTS saved: {audio_en_path} ({result['audio_en_size']:,} bytes)")
        
        return result
        
    except Exception as e:
        logger.error(f"TTS generation error for job {job_id}: {e}")
        raise


def get_audio_duration(audio_path: str) -> float:
    """Get audio file duration in seconds."""
    try:
        from moviepy import AudioFileClip
        clip = AudioFileClip(audio_path)
        duration = clip.duration
        clip.close()
        return duration
    except Exception as e:
        logger.warning(f"Could not get audio duration: {e}")
        return 60.0  # Default 60 seconds
