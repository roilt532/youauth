#!/usr/bin/env python3
"""
Daily YouTube Automation Script - VIRAL CONTENT CURATION
Run by GitHub Actions or manually for standalone automation.

Environment Variables Required:
  GEMINI_API_KEY   - Google Gemini API key (free tier)
  YT_CLIENT_ID     - YouTube OAuth Client ID
  YT_CLIENT_SECRET - YouTube OAuth Client Secret
  YT_REFRESH_TOKEN - YouTube OAuth Refresh Token
  VIDEO_TOPIC      - (Optional) Specific topic to use
  CONTENT_TYPE     - (Optional) roblox/curiosity/story/animated (default: roblox)
  LANGUAGE         - (Optional) es/en (default: es)
  FORMAT           - (Optional) short/long (default: short)
"""

import asyncio
import json
import logging
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Auto-topics for when no specific topic is provided
AUTO_TOPICS = {
    'roblox': [
        'El secreto más increíble de Roblox que nadie conoce',
        'El momento más emocionante en Roblox de la semana',
        'El truco de Roblox que te volverá viral instantáneamente',
        '¿Qué pasaría si combinas todos los poderes de Roblox?',
        'Los 5 errores de Roblox que nadie ha visto antes',
        'El modo oculto de Roblox que cambia todo el juego',
        'Cuando hice trampa en Roblox y pasó algo increíble',
        'La estrategia definitiva para ganar siempre en Roblox',
    ],
    'curiosity': [
        '¿Por qué los pulpos son más inteligentes que los humanos?',
        'El lugar más extraño del mundo que existe de verdad',
        '5 cosas increíbles que pasan mientras duermes',
        '¿Qué hay realmente dentro de un agujero negro?',
        'Los animales más rápidos del mundo que te sorprenderán',
        'Por qué el cielo cambia de color en el atardecer',
    ],
    'story': [
        'La historia del niño que descubrió un mundo mágico',
        'El día que un robot quiso ser humano',
        'La aventura del pequeño dragón que no podía escupir fuego',
        'El niño que podía hablar con los animales',
    ],
    'animated': [
        'Las aventuras de los superhéroes de Roblox',
        'El mundo mágico de los colores que cobran vida',
        'Cuando los juguetes se despiertan por la noche',
    ]
}


async def run_daily_automation():
    """Main automation function with viral content curation."""
    logger.info("=" * 70)
    logger.info("🚀 YOUTUBE SHORTS AUTOMATION - VIRAL CONTENT CURATION")
    logger.info(f"⏰ Time: {datetime.now(timezone.utc).isoformat()}")
    logger.info("=" * 70)
    
    # Get environment variables
    gemini_key = os.environ.get('GEMINI_API_KEY', '')
    yt_client_id = os.environ.get('YT_CLIENT_ID', '')
    yt_client_secret = os.environ.get('YT_CLIENT_SECRET', '')
    yt_refresh_token = os.environ.get('YT_REFRESH_TOKEN', '')
    
    if not gemini_key:
        logger.error("❌ GEMINI_API_KEY not set!")
        sys.exit(1)
    
    if not yt_refresh_token:
        logger.warning("⚠️ YT_REFRESH_TOKEN not set - will skip upload")
    
    # Build job from env or defaults
    content_type = os.environ.get('CONTENT_TYPE', 'curiosity')  # Default: curiosity (más versátil)
    language = os.environ.get('LANGUAGE', 'es')  # Default: español
    format_type = os.environ.get('FORMAT', 'short')
    
    topic = os.environ.get('VIDEO_TOPIC', '')
    if not topic:
        topics_for_type = AUTO_TOPICS.get(content_type, AUTO_TOPICS['curiosity'])
        topic = random.choice(topics_for_type)
        logger.info(f"🎲 Auto-selected topic: {topic}")
    
    # Anti-detection: random delay (1-5 minutes for faster testing, can increase for production)
    delay_seconds = random.randint(60, 300)
    logger.info(f"⏳ Anti-detection delay: {delay_seconds}s")
    await asyncio.sleep(delay_seconds)
    
    job = {
        'id': f'auto_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
        'title': f'Auto Viral: {topic[:50]}',
        'topic': topic,
        'source_url': '',  # Will be discovered automatically
        'content_type': content_type,
        'language': language,
        'format': format_type,
        'made_for_kids': True,
        'use_viral_curation': True,  # 🆕 Activar curación viral
        'optimize_shorts': True,     # 🆕 Optimizar para Shorts
        'add_subtitles': True,       # 🆕 Agregar subtítulos
        'min_views': 100_000,        # Mínimo 100k views
        'min_age_days': 365,         # Al menos 1 año de antigüedad
    }
    
    settings = {
        'youtube_client_id': yt_client_id,
        'youtube_client_secret': yt_client_secret,
        'youtube_refresh_token': yt_refresh_token,
        'upload_privacy': 'public',
    }
    
    # Set API key in environment
    os.environ['GEMINI_API_KEY'] = gemini_key
    
    logger.info(f"📝 Job: {job['title']}")
    logger.info(f"🎯 Content type: {content_type} | Language: {language} | Format: {format_type}")
    logger.info(f"🔍 Viral curation: Enabled (min {job['min_views']:,} views)")
    
    from pipeline.pipeline_runner import run_pipeline
    
    async def log_callback(entry):
        level = entry.get('level', 'info')
        msg = entry.get('message', '')
        getattr(logger, level if level in ('info', 'warning', 'error') else 'info', logger.info)(msg)
    
    result = await run_pipeline(
        job=job,
        settings=settings,
        log_callback=log_callback
    )
    
    logger.info("=" * 70)
    logger.info(f"📊 PIPELINE RESULT: {result.get('status', 'unknown').upper()}")
    
    if result.get('status') == 'completed':
        artifacts = result.get('artifacts', {})
        
        # Log viral content used
        if artifacts.get('viral_content'):
            vc = artifacts['viral_content']
            logger.info(f"✨ Viral source: {vc.get('title', '')[:60]}...")
            logger.info(f"   Platform: {vc.get('platform')} | Views: {vc.get('views', 0):,}")
        
        if artifacts.get('youtube_url'):
            logger.info(f"🎬 Video uploaded: {artifacts['youtube_url']}")
        if artifacts.get('script', {}).get('title_es'):
            logger.info(f"📌 Title: {artifacts['script']['title_es']}")
        logger.info("🎉 AUTOMATION COMPLETE!")
    else:
        error = result.get('error', 'Unknown error')
        logger.error(f"❌ PIPELINE FAILED: {error}")
        sys.exit(1)
    
    logger.info("=" * 70)
    
    # Save results to file
    results_path = Path(os.environ.get('PIPELINE_OUTPUT_DIR', '/tmp/yt_automation')) / 'last_run.json'
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, 'w') as f:
        json.dump({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': result.get('status'),
            'job_title': job['title'],
            'youtube_url': result.get('artifacts', {}).get('youtube_url'),
            'viral_source': result.get('artifacts', {}).get('viral_content', {}).get('title', 'None'),
        }, f, indent=2)
    
    logger.info(f"💾 Results saved to: {results_path}")


if __name__ == '__main__':
    asyncio.run(run_daily_automation())
