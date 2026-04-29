"""Thumbnail Generator - AI images via Pollinations.ai (free, no API key) + Pillow overlay"""
import asyncio
import logging
import os
import random
import urllib.parse
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

CONTENT_THEMES = {
    'roblox':    {'accent1': (255, 40,  40),  'accent2': (255, 215, 0),   'bg': (15, 10, 45)},
    'curiosity': {'accent1': (0,  170, 255),  'accent2': (0,  230, 130),  'bg': (10, 20, 60)},
    'story':     {'accent1': (200, 60, 255),  'accent2': (255, 180, 50),  'bg': (35, 10, 55)},
    'animated':  {'accent1': (0,  210, 100),  'accent2': (255, 240, 50),  'bg': (10, 40, 20)},
}


async def generate_thumbnail(
    title: str,
    output_dir: str,
    job_id: str,
    content_type: str = 'roblox',
    subtitle: Optional[str] = None,
    ai_prompt: Optional[str] = None,
) -> str:
    """Generate thumbnail: try AI (Pollinations.ai free) then fall back to Pillow."""
    loop = asyncio.get_event_loop()

    # Try AI-generated background first
    ai_bg_path = None
    if ai_prompt:
        try:
            ai_bg_path = await _generate_ai_background(ai_prompt, output_dir, job_id)
        except Exception as e:
            logger.warning(f'AI thumbnail failed ({e}), using Pillow fallback')

    return await loop.run_in_executor(
        None,
        _compose_thumbnail,
        title, output_dir, job_id, content_type, subtitle, ai_bg_path
    )


async def _generate_ai_background(
    prompt: str, output_dir: str, job_id: str
) -> Optional[str]:
    """Download AI-generated image from Pollinations.ai (completely free, no API key)."""
    import requests

    # Build optimized prompt for viral kids YouTube thumbnail
    full_prompt = (
        f'{prompt}, kids youtube thumbnail style, no text, no watermark, '
        'bright vivid colors, dramatic lighting, hyper realistic, 4K, '
        'cinematic composition, high contrast'
    )
    encoded = urllib.parse.quote(full_prompt)
    seed = random.randint(1, 999_999_999)

    url = (
        f'https://image.pollinations.ai/prompt/{encoded}'
        f'?width=1280&height=720&nologo=true&model=flux&seed={seed}&enhance=true'
    )

    logger.info(f'[THUMB] Requesting AI image from Pollinations.ai...')
    resp = requests.get(url, timeout=90)
    resp.raise_for_status()

    ai_path = Path(output_dir) / f'{job_id}_ai_bg.jpg'
    ai_path.write_bytes(resp.content)

    if ai_path.stat().st_size < 10_000:
        raise ValueError('AI image too small, likely failed')

    logger.info(f'[THUMB] AI background saved: {ai_path.name} ({ai_path.stat().st_size:,} bytes)')
    return str(ai_path)


def _compose_thumbnail(
    title: str,
    output_dir: str,
    job_id: str,
    content_type: str,
    subtitle: Optional[str],
    ai_bg_path: Optional[str]
) -> str:
    """Compose final thumbnail: AI background (if available) + text overlay."""
    from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

    W, H = 1280, 720
    theme = CONTENT_THEMES.get(content_type, CONTENT_THEMES['roblox'])
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # ---- Background ----
    if ai_bg_path and os.path.exists(ai_bg_path):
        try:
            bg = Image.open(ai_bg_path).convert('RGB').resize((W, H))
            # Slightly darken for text readability
            bg = ImageEnhance.Brightness(bg).enhance(0.75)
        except Exception:
            bg = _make_gradient_bg(W, H, theme)
    else:
        bg = _make_gradient_bg(W, H, theme)

    img = bg.copy()
    draw = ImageDraw.Draw(img)

    a1 = theme['accent1']
    a2 = theme['accent2']

    # ---- Overlay elements ----
    # Top and bottom accent bars
    draw.rectangle([0, 0, W, 12], fill=a1)
    draw.rectangle([0, H-12, W, H], fill=a1)

    # Left edge highlight
    draw.rectangle([0, 0, 10, H], fill=a2)

    # Semi-transparent title area
    title_overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(title_overlay)
    td.rectangle([0, H//3, W, H*3//4 + 20], fill=(0, 0, 0, 140))
    img = Image.alpha_composite(img.convert('RGBA'), title_overlay).convert('RGB')
    draw = ImageDraw.Draw(img)

    # ---- Fonts ----
    def _font(size: int):
        for fp in [
            '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        ]:
            if os.path.exists(fp):
                try:
                    return ImageFont.truetype(fp, size)
                except Exception:
                    pass
        return ImageFont.load_default()

    def _outline_text(d, xy, text, font, fill=(255,255,255), outline=(0,0,0), ow=5):
        x, y = xy
        for dx in range(-ow, ow+1):
            for dy in range(-ow, ow+1):
                if dx or dy:
                    d.text((x+dx, y+dy), text, font=font, fill=outline)
        d.text(xy, text, font=font, fill=fill)

    # ---- Title text ----
    clean = title.replace('\n', ' ')
    font_lg = _font(82)
    words = clean.split()
    lines, cur = [], ''
    for w in words:
        test = (cur + ' ' + w).strip()
        bbox = draw.textbbox((0, 0), test, font=font_lg)
        if bbox[2] - bbox[0] < W - 80:
            cur = test
        else:
            if cur: lines.append(cur)
            cur = w
        if len(lines) >= 2: break
    if cur and len(lines) < 2: lines.append(cur)

    y_off = H // 3 + 10
    for line in lines[:2]:
        bbox = draw.textbbox((0, 0), line, font=font_lg)
        x = (W - (bbox[2]-bbox[0])) // 2
        _outline_text(draw, (x, y_off), line, font_lg, (255,255,255), (0,0,0), 5)
        y_off += 95

    # ---- Content type badge (bottom-left) ----
    badge_map = {
        'roblox':    '🎮 ROBLOX',
        'curiosity': '🔬 CURIOSIDADES',
        'story':     '📖 HISTORIA',
        'animated':  '🎨 ANIMADO',
    }
    badge = badge_map.get(content_type, '▶ VIDEO')
    font_md = _font(48)
    bbox = draw.textbbox((0, 0), badge, font=font_md)
    bw = bbox[2]-bbox[0] + 36
    draw.rounded_rectangle([30, H-80, 30+bw, H-16], radius=10, fill=a1)
    draw.text((48, H-76), badge, font=font_md, fill=(255,255,255))

    # ---- KIDS SAFE badge (bottom-right) ----
    ks = '✅ KIDS SAFE'
    font_sm = _font(36)
    bbox2 = draw.textbbox((0, 0), ks, font=font_sm)
    ksx = W - (bbox2[2]-bbox2[0]) - 42
    draw.rounded_rectangle([ksx-10, H-76, ksx+(bbox2[2]-bbox2[0])+22, H-18], radius=8, fill=(0,160,80))
    draw.text((ksx+6, H-70), ks, font=font_sm, fill=(255,255,255))

    # ---- Save ----
    thumb_path = output_path / f'{job_id}_thumbnail.jpg'
    img.save(str(thumb_path), 'JPEG', quality=96)
    logger.info(f'[THUMB] Final: {thumb_path.name} ({thumb_path.stat().st_size:,} bytes)')
    return str(thumb_path)


def _make_gradient_bg(W: int, H: int, theme: dict):
    from PIL import Image, ImageDraw
    bg_color = theme.get('bg', (15, 10, 45))
    img = Image.new('RGB', (W, H))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        p = y / H
        r = min(255, int(bg_color[0] + p * 50))
        g = min(255, int(bg_color[1] + p * 30))
        b = min(255, int(bg_color[2] + p * 60))
        draw.line([(0, y), (W, y)], fill=(r, g, b))
    return img
