"""TTS Generator - edge-tts (Microsoft Neural voices, completely free, no API key)"""
import asyncio
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Microsoft Neural voices - very realistic, completely free
VOICES = {
    # Spanish
    'es_male':    'es-ES-AlvaroNeural',      # Spanish Spain male - very natural
    'es_female':  'es-ES-ElviraNeural',      # Spanish Spain female - very natural
    'es_mx_male': 'es-MX-JorgeNeural',       # Mexican Spanish male
    'es_mx_fem':  'es-MX-DaliaNeural',       # Mexican Spanish female
    # English
    'en_female':  'en-US-AriaNeural',        # US English female - very natural
    'en_male':    'en-US-GuyNeural',         # US English male - very natural
    'en_female2': 'en-US-JennyNeural',       # US English female (warm)
    # Multilingual
    'multi':      'en-US-AndrewMultilingualNeural',
}

# Default voices per language
DEFAULT_VOICE = {
    'es': VOICES['es_male'],
    'en': VOICES['en_female'],
    'bilingual': VOICES['es_male'],
}


async def generate_tts(
    text_es: str,
    text_en: str,
    output_dir: str,
    job_id: str,
    lang_mode: str = 'bilingual',
    voice_es: Optional[str] = None,
    voice_en: Optional[str] = None,
    rate: str = '+10%',          # Slightly faster = more energetic for kids
    pitch: str = '+5Hz',         # Slightly higher pitch = younger voice energy
) -> dict:
    """Generate TTS audio using edge-tts (Microsoft Neural voices - free)."""
    import edge_tts

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    result = {}

    _voice_es = voice_es or DEFAULT_VOICE.get('es')
    _voice_en = voice_en or DEFAULT_VOICE.get('en')

    if lang_mode in ('es', 'bilingual') and text_es.strip():
        logger.info(f'[TTS] Generating Spanish narration (voice: {_voice_es})')
        audio_path = output_path / f'{job_id}_narration_es.mp3'
        await _generate_audio(text_es, _voice_es, str(audio_path), rate, pitch)
        result['audio_es'] = str(audio_path)
        result['audio_es_size'] = audio_path.stat().st_size
        logger.info(f'[TTS] ES audio: {audio_path.name} ({result["audio_es_size"]:,} bytes)')

    if lang_mode in ('en', 'bilingual') and text_en.strip():
        logger.info(f'[TTS] Generating English narration (voice: {_voice_en})')
        audio_path = output_path / f'{job_id}_narration_en.mp3'
        await _generate_audio(text_en, _voice_en, str(audio_path), rate, pitch)
        result['audio_en'] = str(audio_path)
        result['audio_en_size'] = audio_path.stat().st_size
        logger.info(f'[TTS] EN audio: {audio_path.name} ({result["audio_en_size"]:,} bytes)')

    if not result:
        raise ValueError('No audio generated - check text and lang_mode')

    return result


async def _generate_audio(
    text: str,
    voice: str,
    output_path: str,
    rate: str = '+10%',
    pitch: str = '+5Hz'
) -> None:
    """Generate audio file using edge-tts."""
    import edge_tts
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await communicate.save(output_path)


async def list_available_voices(language_prefix: str = 'es') -> list:
    """List available edge-tts voices for a language (for UI selection)."""
    import edge_tts
    voices = await edge_tts.list_voices()
    return [
        {'name': v['Name'], 'gender': v['Gender'], 'locale': v['Locale']}
        for v in voices
        if v['Locale'].lower().startswith(language_prefix.lower())
    ]
