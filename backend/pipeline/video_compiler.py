"""Video Compiler - Creates visually rich animated videos using Pillow + MoviePy"""
import asyncio
import logging
import os
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Get the FFmpeg binary from moviepy's imageio-ffmpeg
try:
    from moviepy.config import FFMPEG_BINARY
except Exception:
    FFMPEG_BINARY = 'ffmpeg'

CONTENT_THEMES = {
    'roblox':    {'bg': (15, 10, 45),   'accent1': (255, 50,  50),  'accent2': (255, 210, 0)},
    'curiosity': {'bg': (10, 20, 60),   'accent1': (0,  170, 255),  'accent2': (0,  230, 130)},
    'story':     {'bg': (35, 10, 55),   'accent1': (200, 60, 255),  'accent2': (255, 180, 50)},
    'animated':  {'bg': (10, 40, 20),   'accent1': (0,  210, 100),  'accent2': (255, 240, 50)},
}


async def compile_video(
    audio_path: str,
    output_dir: str,
    job_id: str,
    source_video_path: Optional[str] = None,
    format_type: str = 'short',
    title: str = '',
    hook_text: str = '',
    content_type: str = 'roblox'
) -> str:
    """Compile a visually rich video with text overlays and animated background."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, _compile_video_sync,
        audio_path, output_dir, job_id,
        source_video_path, format_type, title, hook_text, content_type
    )


def _compile_video_sync(
    audio_path: str,
    output_dir: str,
    job_id: str,
    source_video_path: Optional[str] = None,
    format_type: str = 'short',
    title: str = '',
    hook_text: str = '',
    content_type: str = 'roblox'
) -> str:
    from moviepy import AudioFileClip, ImageClip, VideoFileClip, concatenate_videoclips, CompositeVideoClip
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Dimensions
    if format_type == 'short':
        W, H = 1080, 1920
    else:
        W, H = 1920, 1080

    theme = CONTENT_THEMES.get(content_type, CONTENT_THEMES['roblox'])

    # ---- Load fonts ----
    font_paths = [
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    ]
    def _font(size):
        for fp in font_paths:
            if os.path.exists(fp):
                try:
                    return ImageFont.truetype(fp, size)
                except Exception:
                    pass
        return ImageFont.load_default()

    def _outline_text(draw, xy, text, font, fill, outline, ow=4):
        x, y = xy
        for dx in range(-ow, ow+1):
            for dy in range(-ow, ow+1):
                if dx or dy:
                    draw.text((x+dx, y+dy), text, font=font, fill=outline)
        draw.text(xy, text, font=font, fill=fill)

    def _wrap_text(text, font, draw, max_width):
        words = text.split()
        lines = []
        line = ''
        for w in words:
            test = (line + ' ' + w).strip()
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] <= max_width:
                line = test
            else:
                if line:
                    lines.append(line)
                line = w
        if line:
            lines.append(line)
        return lines

    # ---- Generate background frame ----
    def _make_frame(phase: str = 'main') -> np.ndarray:
        img = Image.new('RGB', (W, H))
        draw = ImageDraw.Draw(img)

        # Gradient background
        bg = theme['bg']
        for y in range(H):
            p = y / H
            r = min(255, int(bg[0] + p * 40))
            g = min(255, int(bg[1] + p * 25))
            b = min(255, int(bg[2] + p * 50))
            draw.line([(0, y), (W, y)], fill=(r, g, b))

        a1 = theme['accent1']
        a2 = theme['accent2']

        # Top banner
        draw.rectangle([0, 0, W, 14], fill=a1)

        # Bottom banner
        draw.rectangle([0, H-14, W, H], fill=a1)

        # Corner glow (top-left)
        for i in range(100):
            alpha = max(0, 100 - i)
            draw.ellipse([-i, -i, 200-i, 200-i], fill=a1)

        # Decorative circles
        draw.ellipse([W-180, H-180, W+60, H+60], outline=a2, width=6)
        draw.ellipse([W-140, H-140, W+20, H+20], outline=a1, width=3)

        # Side vertical bars
        bar_w = 8
        for i, color in enumerate([a1, a2, a1]):
            x = W - 30 - i * 18
            draw.rectangle([x, 60, x+bar_w, H-60], fill=color)

        if phase == 'hook' and hook_text:
            # ---- HOOK FRAME: giant hook text ----
            font_hook = _font(min(90, W // 12))
            lines = _wrap_text('\u00a1' + hook_text + '!', font_hook, draw, W - 120)
            y_start = H // 2 - (len(lines) * 100) // 2
            for line in lines[:4]:
                bbox = draw.textbbox((0, 0), line, font=font_hook)
                x = (W - (bbox[2]-bbox[0])) // 2
                _outline_text(draw, (x, y_start), line, font_hook, (255,255,255), (0,0,0), 5)
                y_start += 110
            # "No te pierdas" label
            lbl = '\u25b6 NO TE LO PIERDAS \u25c4'
            font_lbl = _font(45)
            bbox = draw.textbbox((0, 0), lbl, font=font_lbl)
            x = (W - (bbox[2]-bbox[0])) // 2
            draw.rectangle([x-20, H*3//4-10, x+(bbox[2]-bbox[0])+20, H*3//4+65], fill=a1)
            draw.text((x, H*3//4), lbl, font=font_lbl, fill=(255,255,255))

        else:
            # ---- MAIN FRAME: title + content badge ----
            if title:
                font_title = _font(min(88, W // 11))
                lines = _wrap_text(title, font_title, draw, W - 100)
                y_start = H // 3
                for line in lines[:3]:
                    bbox = draw.textbbox((0, 0), line, font=font_title)
                    x = (W - (bbox[2]-bbox[0])) // 2
                    _outline_text(draw, (x, y_start), line, font_title, (255,255,255), (0,0,0), 6)
                    y_start += 105

            # Content badge
            badge_map = {
                'roblox': '\U0001f3ae ROBLOX',
                'curiosity': '\U0001f52c CURIOSIDADES',
                'story': '\U0001f4d6 HISTORIA',
                'animated': '\U0001f3a8 ANIMADO',
            }
            badge = badge_map.get(content_type, '\u25b6 VIDEO')
            font_badge = _font(50)
            bbox = draw.textbbox((0, 0), badge, font=font_badge)
            bw = bbox[2]-bbox[0] + 40
            bx = (W - bw) // 2
            by = H * 2 // 3
            draw.rounded_rectangle([bx, by, bx+bw, by+70], radius=12, fill=a1)
            draw.text((bx+20, by+10), badge, font=font_badge, fill=(255,255,255))

            # KIDS SAFE badge bottom-right
            font_ks = _font(36)
            ks_text = '\u2705 KIDS SAFE'
            bbox2 = draw.textbbox((0,0), ks_text, font=font_ks)
            ksx = W - (bbox2[2]-bbox2[0]) - 30
            ksy = H - 90
            draw.rounded_rectangle([ksx-12, ksy-8, ksx+(bbox2[2]-bbox2[0])+12, ksy+50], radius=8, fill=(0,160,80))
            draw.text((ksx, ksy), ks_text, font=font_ks, fill=(255,255,255))

        return np.array(img)

    # ---- Load audio ----
    audio = AudioFileClip(audio_path)
    duration = audio.duration
    hook_duration = min(4.0, duration * 0.15)   # first 15% = hook
    main_duration = duration - hook_duration

    logger.info(f'Video: {W}x{H}, {duration:.1f}s total ({hook_duration:.1f}s hook + {main_duration:.1f}s main)')

    if source_video_path and os.path.exists(source_video_path):
        # Use real source video with audio overlay
        logger.info(f'Using source video: {source_video_path}')
        try:
            base = VideoFileClip(source_video_path)
            # Loop to fill audio length
            if base.duration < duration:
                loops = int(duration / base.duration) + 1
                base = concatenate_videoclips([base] * loops)
            base = base.subclipped(0, duration).resized((W, H))
            final = base.with_audio(audio)
        except Exception as e:
            logger.warning(f'Source video load error ({e}), using generated background')
            source_video_path = None

    if not source_video_path or not os.path.exists(source_video_path or ''):
        # Build animated background from Pillow frames
        hook_frame = _make_frame('hook')
        main_frame = _make_frame('main')

        hook_clip = ImageClip(hook_frame).with_duration(hook_duration)
        main_clip = ImageClip(main_frame).with_duration(main_duration)

        base = concatenate_videoclips([hook_clip, main_clip])
        final = base.with_audio(audio)

    # ---- Render ----
    output_file = output_path / f'{job_id}_final.mp4'
    logger.info(f'Rendering to {output_file}...')
    final.write_videofile(
        str(output_file),
        fps=24,
        codec='libx264',
        audio_codec='aac',
        preset='ultrafast',
        audio_bitrate='128k',
        logger=None
    )

    try:
        audio.close(); final.close()
    except Exception:
        pass

    sz = output_file.stat().st_size
    logger.info(f'Video compiled: {output_file.name} ({sz:,} bytes)')
    return str(output_file)
