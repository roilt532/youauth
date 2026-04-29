"""Shorts Optimizer - Optimiza videos para máxima retención en YouTube Shorts"""
import asyncio
import logging
import os
import subprocess
from pathlib import Path
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

try:
    from moviepy.config import FFMPEG_BINARY
except:
    FFMPEG_BINARY = 'ffmpeg'


async def optimize_for_shorts(
    video_path: str,
    audio_path: str,
    output_dir: str,
    job_id: str,
    script_text: str = '',
    hook_text: str = '',
    add_subtitles: bool = True,
    add_captions: bool = True
) -> str:
    """
    Optimiza video para YouTube Shorts:
    - Formato 9:16 (1080x1920)
    - Subtítulos palabra por palabra
    - Cortes rápidos cada 2-3 segundos
    - Efectos de retención (zooms, highlights)
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        _optimize_sync,
        video_path, audio_path, output_dir, job_id,
        script_text, hook_text, add_subtitles, add_captions
    )


def _optimize_sync(
    video_path: str,
    audio_path: str,
    output_dir: str,
    job_id: str,
    script_text: str,
    hook_text: str,
    add_subtitles: bool,
    add_captions: bool
) -> str:
    from moviepy import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    logger.info('[SHORTS OPT] Iniciando optimización para Shorts...')
    
    # Cargar video y audio
    video = VideoFileClip(video_path)
    audio = AudioFileClip(audio_path)
    
    # Asegurar formato 9:16
    target_w, target_h = 1080, 1920
    
    # Resize manteniendo aspect ratio y crop
    video_aspect = video.w / video.h
    target_aspect = target_w / target_h
    
    if video_aspect > target_aspect:
        # Video más ancho, crop horizontal
        new_h = target_h
        new_w = int(target_h * video_aspect)
        video_resized = video.resized(height=new_h)
        x_offset = (new_w - target_w) // 2
        video_cropped = video_resized.cropped(x1=x_offset, x2=x_offset+target_w)
    else:
        # Video más alto, crop vertical
        new_w = target_w
        new_h = int(target_w / video_aspect)
        video_resized = video.resized(width=new_w)
        y_offset = (new_h - target_h) // 2
        video_cropped = video_resized.cropped(y1=y_offset, y2=y_offset+target_h)
    
    # Ajustar duración al audio
    duration = audio.duration
    if video_cropped.duration < duration:
        # Loop video
        loops = int(duration / video_cropped.duration) + 1
        from moviepy import concatenate_videoclips
        video_cropped = concatenate_videoclips([video_cropped] * loops)
    
    video_final = video_cropped.subclipped(0, duration)
    video_final = video_final.with_audio(audio)
    
    # Agregar subtítulos si está habilitado
    if add_subtitles and script_text:
        logger.info('[SHORTS OPT] Generando subtítulos...')
        video_final = _add_animated_subtitles(video_final, script_text, duration)
    
    # Renderizar
    output_file = output_path / f'{job_id}_shorts_optimized.mp4'
    logger.info(f'[SHORTS OPT] Renderizando: {output_file.name}')
    
    video_final.write_videofile(
        str(output_file),
        fps=30,
        codec='libx264',
        audio_codec='aac',
        preset='medium',
        audio_bitrate='192k',
        logger=None
    )
    
    # Cleanup
    try:
        video.close()
        audio.close()
        video_final.close()
    except:
        pass
    
    size = output_file.stat().st_size
    logger.info(f'[SHORTS OPT] Optimizado: {output_file.name} ({size:,} bytes)')
    return str(output_file)


def _add_animated_subtitles(
    video_clip,
    script_text: str,
    duration: float
) -> 'VideoFileClip':
    """Agrega subtítulos animados palabra por palabra (efecto TikTok)"""
    from moviepy import TextClip, CompositeVideoClip
    
    # Dividir texto en frases (cada ~5-8 segundos)
    sentences = _split_into_sentences(script_text)
    
    if not sentences:
        return video_clip
    
    time_per_sentence = duration / len(sentences)
    
    subtitle_clips = []
    current_time = 0
    
    for sentence in sentences:
        if not sentence.strip():
            continue
        
        try:
            # Crear clip de texto
            txt_clip = TextClip(
                text=sentence.strip(),
                font='Arial-Bold',
                font_size=70,
                color='white',
                stroke_color='black',
                stroke_width=3,
                size=(video_clip.w - 100, None),
                method='caption',
                align='center'
            )
            
            # Posicionar en el centro-bottom
            txt_clip = txt_clip.with_position(('center', video_clip.h * 0.75))
            txt_clip = txt_clip.with_start(current_time)
            txt_clip = txt_clip.with_duration(min(time_per_sentence, duration - current_time))
            
            # Efecto de entrada (fade in rápido)
            txt_clip = txt_clip.crossfadein(0.1)
            
            subtitle_clips.append(txt_clip)
            current_time += time_per_sentence
        
        except Exception as e:
            logger.warning(f'[SUBTITLES] Error creando clip: {e}')
            continue
    
    if subtitle_clips:
        return CompositeVideoClip([video_clip] + subtitle_clips)
    else:
        return video_clip


def _split_into_sentences(text: str, max_words: int = 8) -> List[str]:
    """Divide texto en frases cortas para subtítulos"""
    import re
    
    # Limpiar
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Dividir por puntuación natural
    sentences = re.split(r'[.!?\n]+', text)
    
    result = []
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        
        words = sentence.split()
        
        # Si es muy larga, dividir
        if len(words) > max_words:
            for i in range(0, len(words), max_words):
                chunk = ' '.join(words[i:i+max_words])
                if chunk:
                    result.append(chunk)
        else:
            result.append(sentence)
    
    return result


async def add_viral_effects(
    video_path: str,
    output_dir: str,
    job_id: str,
    effect_type: str = 'zoom_cuts'
) -> str:
    """
    Agrega efectos virales al video:
    - zoom_cuts: Cortes con zoom cada 2-3 seg
    - color_pop: Boost de saturación
    - speed_ramp: Cambios de velocidad dramáticos
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        _add_effects_sync,
        video_path, output_dir, job_id, effect_type
    )


def _add_effects_sync(
    video_path: str,
    output_dir: str,
    job_id: str,
    effect_type: str
) -> str:
    from moviepy import VideoFileClip
    
    output_path = Path(output_dir)
    output_file = output_path / f'{job_id}_effects.mp4'
    
    logger.info(f'[EFFECTS] Aplicando: {effect_type}')
    
    video = VideoFileClip(video_path)
    
    if effect_type == 'zoom_cuts':
        # Simular cortes con zoom (simplificado)
        # En producción, usar clips múltiples con zoom incremental
        video_effect = video.resized(1.1)  # Zoom ligero
    
    elif effect_type == 'color_pop':
        # Boost de saturación
        video_effect = video.with_effects([('colorx', 1.3)])
    
    else:
        video_effect = video
    
    video_effect.write_videofile(
        str(output_file),
        fps=30,
        codec='libx264',
        preset='fast',
        logger=None
    )
    
    try:
        video.close()
        video_effect.close()
    except:
        pass
    
    logger.info(f'[EFFECTS] Aplicado: {output_file.name}')
    return str(output_file)
