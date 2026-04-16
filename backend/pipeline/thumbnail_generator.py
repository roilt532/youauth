"""Thumbnail Generator - Uses Pillow to create eye-catching YouTube thumbnails"""
import asyncio
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Color themes for different content types
CONTENT_THEMES = {
    'roblox': {
        'bg': (10, 15, 40),
        'accent': (255, 50, 50),
        'text_color': (255, 255, 255),
        'highlight': (255, 215, 0)
    },
    'curiosity': {
        'bg': (15, 25, 50),
        'accent': (0, 180, 255),
        'text_color': (255, 255, 255),
        'highlight': (255, 200, 0)
    },
    'story': {
        'bg': (30, 10, 50),
        'accent': (180, 50, 255),
        'text_color': (255, 255, 255),
        'highlight': (255, 180, 50)
    },
    'animated': {
        'bg': (5, 30, 60),
        'accent': (0, 200, 100),
        'text_color': (255, 255, 255),
        'highlight': (255, 255, 50)
    }
}


async def generate_thumbnail(
    title: str,
    output_dir: str,
    job_id: str,
    content_type: str = 'roblox',
    subtitle: Optional[str] = None
) -> str:
    """Generate a YouTube thumbnail with bold text and kid-friendly design."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        _generate_thumbnail_sync,
        title, output_dir, job_id, content_type, subtitle
    )


def _generate_thumbnail_sync(
    title: str,
    output_dir: str,
    job_id: str,
    content_type: str = 'roblox',
    subtitle: Optional[str] = None
) -> str:
    """Synchronous thumbnail generation."""
    from PIL import Image, ImageDraw, ImageFont
    
    theme = CONTENT_THEMES.get(content_type, CONTENT_THEMES['roblox'])
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # YouTube standard thumbnail size
    width, height = 1280, 720
    
    # Create base image
    img = Image.new('RGB', (width, height), color=theme['bg'])
    draw = ImageDraw.Draw(img)
    
    # Gradient background effect
    for y in range(height):
        progress = y / height
        r = int(theme['bg'][0] + progress * 30)
        g = int(theme['bg'][1] + progress * 20)
        b = int(theme['bg'][2] + progress * 40)
        draw.line([(0, y), (width, y)], fill=(min(r, 255), min(g, 255), min(b, 255)))
    
    # Top accent bar (brand)
    draw.rectangle([0, 0, width, 10], fill=theme['accent'])
    draw.rectangle([0, height - 10, width, height], fill=theme['accent'])
    
    # Corner decorations
    accent_r, accent_g, accent_b = theme['accent']
    for i in range(80):
        alpha = int(120 * (1 - i / 80))
        draw.rectangle([0, 0, 80 - i, 80 - i], fill=(accent_r, accent_g, accent_b))
    
    # Fonts
    try:
        font_paths = [
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
        font_large = None
        font_medium = None
        font_small = None
        
        for fp in font_paths:
            if os.path.exists(fp):
                font_large = ImageFont.truetype(fp, 90)
                font_medium = ImageFont.truetype(fp, 55)
                font_small = ImageFont.truetype(fp, 38)
                break
        
        if not font_large:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
    except Exception:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    def draw_text_with_outline(draw_obj, pos, text, font, text_color, outline_color, outline_w=4):
        x, y = pos
        for dx in range(-outline_w, outline_w + 1):
            for dy in range(-outline_w, outline_w + 1):
                if dx != 0 or dy != 0:
                    draw_obj.text((x + dx, y + dy), text, font=font, fill=outline_color)
        draw_obj.text(pos, text, font=font, fill=text_color)
    
    # Title text (split into 2 lines max)
    clean_title = title.replace('\n', ' ')
    words = clean_title.split()
    lines = []
    current_line = ''
    
    for word in words:
        test_line = (current_line + ' ' + word).strip()
        bbox = draw.textbbox((0, 0), test_line, font=font_large)
        if bbox[2] - bbox[0] < width - 100:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
        if len(lines) >= 2:
            break
    if current_line and len(lines) < 2:
        lines.append(current_line)
    
    # Draw title
    y_offset = 180
    for line in lines[:2]:
        bbox = draw.textbbox((0, 0), line, font=font_large)
        text_w = bbox[2] - bbox[0]
        x = (width - text_w) // 2
        draw_text_with_outline(draw, (x, y_offset), line, font_large, theme['text_color'], (0, 0, 0), 5)
        y_offset += 100
    
    # Content type badge
    badge_map = {
        'roblox': '🎮 ROBLOX',
        'curiosity': '🔬 CURIOSIDADES',
        'story': '📖 HISTORIA',
        'animated': '🎨 ANIMADO'
    }
    badge_text = badge_map.get(content_type, '▶ VIDEO')
    draw_text_with_outline(draw, (50, 570), badge_text, font_medium, theme['highlight'], (0, 0, 0), 3)
    
    # KIDS SAFE green badge
    badge_x = width - 220
    badge_y = height - 75
    draw.rounded_rectangle([badge_x, badge_y, badge_x + 200, badge_y + 55], radius=8, fill=(0, 160, 80))
    draw.text((badge_x + 15, badge_y + 12), '✅ KIDS SAFE', font=font_small, fill=(255, 255, 255))
    
    # Save thumbnail
    thumb_path = output_path / f"{job_id}_thumbnail.jpg"
    img.save(str(thumb_path), 'JPEG', quality=95)
    
    logger.info(f"Thumbnail generated: {thumb_path} ({thumb_path.stat().st_size:,} bytes)")
    return str(thumb_path)
