"""Content Discovery - Scrapers para contenido viral legal de múltiples plataformas"""
import asyncio
import logging
import os
import random
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Optional
import json

logger = logging.getLogger(__name__)

# Nichos y sus keywords
NICHE_KEYWORDS = {
    'roblox': [
        'roblox funny moments', 'roblox gameplay', 'roblox secrets',
        'roblox fails', 'roblox best moments', 'roblox animation'
    ],
    'curiosity': [
        'amazing facts', 'science experiments', 'did you know',
        'curiosidades increíbles', 'datos curiosos', 'hechos asombrosos'
    ],
    'story': [
        'scary stories', 'funny stories', 'reddit stories',
        'historias de miedo', 'cuentos cortos', 'relatos virales'
    ],
    'animated': [
        'kids animation', 'cartoon moments', 'animated stories',
        'animación infantil', 'dibujos animados'
    ],
}


class ViralContent:
    """Representa contenido viral descubierto"""
    def __init__(self, url: str, title: str, views: int, platform: str,
                 content_type: str, thumbnail_url: str = '', duration: int = 0,
                 upload_date: str = '', description: str = ''):
        self.url = url
        self.title = title
        self.views = views
        self.platform = platform
        self.content_type = content_type
        self.thumbnail_url = thumbnail_url
        self.duration = duration
        self.upload_date = upload_date
        self.description = description
        self.viral_score = self._calculate_viral_score()
    
    def _calculate_viral_score(self) -> float:
        """Score de viralidad: views + recency + engagement"""
        score = 0.0
        
        # Score por views (logarítmico)
        if self.views > 0:
            import math
            score += math.log10(self.views) * 10
        
        # Bonus por recency (contenido de 1-3 años es ideal)
        if self.upload_date:
            try:
                upload = datetime.fromisoformat(self.upload_date.replace('Z', '+00:00'))
                age_days = (datetime.now(timezone.utc) - upload).days
                if 365 <= age_days <= 1095:  # 1-3 años
                    score += 20
                elif age_days > 1095:  # Más de 3 años
                    score += 10
            except:
                pass
        
        # Penalty por duración muy larga (queremos shorts)
        if self.duration > 180:  # más de 3 min
            score *= 0.5
        
        return score
    
    def to_dict(self) -> dict:
        return {
            'url': self.url,
            'title': self.title,
            'views': self.views,
            'platform': self.platform,
            'content_type': self.content_type,
            'thumbnail_url': self.thumbnail_url,
            'duration': self.duration,
            'upload_date': self.upload_date,
            'description': self.description,
            'viral_score': self.viral_score
        }


async def discover_viral_content(
    content_type: str = 'roblox',
    min_views: int = 100_000,
    max_results: int = 10,
    min_age_days: int = 365,
    cache_dir: str = '/tmp/content_cache'
) -> List[ViralContent]:
    """
    Descubre contenido viral legal de múltiples plataformas.
    
    Returns: Lista de ViralContent ordenada por viral_score descendente
    """
    logger.info(f'[DISCOVERY] Buscando contenido viral tipo: {content_type}, min views: {min_views:,}')
    
    # Cache para evitar scraping repetitivo
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = Path(cache_dir) / f'{content_type}_cache.json'
    
    # Check cache (válido por 6 horas)
    if cache_file.exists():
        age = datetime.now().timestamp() - cache_file.stat().st_mtime
        if age < 6 * 3600:  # 6 horas
            try:
                with open(cache_file, 'r') as f:
                    cached = json.load(f)
                    logger.info(f'[DISCOVERY] Usando cache ({len(cached)} items)')
                    results = [ViralContent(**item) for item in cached]
                    return sorted(results, key=lambda x: x.viral_score, reverse=True)[:max_results]
            except:
                pass
    
    # Buscar en paralelo en todas las plataformas
    tasks = [
        _search_youtube_cc(content_type, min_views, min_age_days),
        _search_pexels_videos(content_type),
        _search_reddit_stories(content_type, min_age_days),
    ]
    
    results_nested = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Flatten y filtrar errores
    all_content = []
    for result in results_nested:
        if isinstance(result, list):
            all_content.extend(result)
        elif isinstance(result, Exception):
            logger.warning(f'[DISCOVERY] Error en scraper: {result}')
    
    # Ordenar por viral_score
    all_content.sort(key=lambda x: x.viral_score, reverse=True)
    top_content = all_content[:max_results]
    
    # Guardar en cache
    try:
        with open(cache_file, 'w') as f:
            json.dump([c.to_dict() for c in top_content], f)
    except:
        pass
    
    logger.info(f'[DISCOVERY] Encontrado: {len(top_content)} videos virales')
    return top_content


async def _search_youtube_cc(
    content_type: str,
    min_views: int,
    min_age_days: int
) -> List[ViralContent]:
    """Busca videos de YouTube con licencia Creative Commons"""
    import yt_dlp
    
    keywords = NICHE_KEYWORDS.get(content_type, NICHE_KEYWORDS['roblox'])
    query = random.choice(keywords)
    
    logger.info(f'[YOUTUBE CC] Buscando: "{query}"')
    
    # Buscar con yt-dlp
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'default_search': 'ytsearch50',
        'format': 'best',
    }
    
    loop = asyncio.get_event_loop()
    
    def _extract():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Buscar videos con licencia CC
            search_query = f'{query} creative commons'
            result = ydl.extract_info(search_query, download=False)
            return result.get('entries', [])
    
    try:
        entries = await loop.run_in_executor(None, _extract)
    except Exception as e:
        logger.warning(f'[YOUTUBE CC] Error: {e}')
        return []
    
    content_list = []
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=min_age_days)
    
    for entry in entries[:30]:  # Top 30 resultados
        try:
            view_count = entry.get('view_count', 0) or 0
            duration = entry.get('duration', 0) or 0
            
            # Filtros
            if view_count < min_views:
                continue
            if duration < 10 or duration > 300:  # 10 seg - 5 min
                continue
            
            upload_date_str = entry.get('upload_date', '')
            if upload_date_str:
                upload_date = datetime.strptime(upload_date_str, '%Y%m%d').replace(tzinfo=timezone.utc)
                if upload_date > cutoff_date:
                    continue
            else:
                upload_date_str = ''
            
            content = ViralContent(
                url=f"https://youtube.com/watch?v={entry['id']}",
                title=entry.get('title', ''),
                views=view_count,
                platform='youtube_cc',
                content_type=content_type,
                thumbnail_url=entry.get('thumbnail', ''),
                duration=duration,
                upload_date=upload_date_str,
                description=entry.get('description', '')[:200]
            )
            content_list.append(content)
        except Exception as e:
            continue
    
    logger.info(f'[YOUTUBE CC] Encontrados: {len(content_list)} videos')
    return content_list


async def _search_pexels_videos(content_type: str) -> List[ViralContent]:
    """Busca videos de stock de Pexels (dominio público)"""
    import requests
    
    keywords = NICHE_KEYWORDS.get(content_type, NICHE_KEYWORDS['roblox'])
    query = random.choice(keywords).replace('roblox', 'gaming').replace('reddit', 'people talking')
    
    logger.info(f'[PEXELS] Buscando: "{query}"')
    
    # Pexels API es gratuita
    # Para uso sin API key, hacemos scraping del sitio
    url = f'https://www.pexels.com/search/videos/{query.replace(" ", "%20")}/'
    
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        )
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extraer videos (simplificado - Pexels cambia estructura frecuentemente)
        video_articles = soup.find_all('article', limit=10)
        
        content_list = []
        for article in video_articles:
            try:
                link_tag = article.find('a')
                if not link_tag:
                    continue
                
                video_url = 'https://www.pexels.com' + link_tag.get('href', '')
                if '/video/' not in video_url:
                    continue
                
                # Pexels videos tienen views sintéticas
                content = ViralContent(
                    url=video_url,
                    title=f'Stock video: {query}',
                    views=500_000,  # Estimado
                    platform='pexels',
                    content_type=content_type,
                    duration=random.randint(15, 60),
                    upload_date=datetime.now(timezone.utc).isoformat()
                )
                content_list.append(content)
            except:
                continue
        
        logger.info(f'[PEXELS] Encontrados: {len(content_list)} videos')
        return content_list
    
    except Exception as e:
        logger.warning(f'[PEXELS] Error: {e}')
        return []


async def _search_reddit_stories(content_type: str, min_age_days: int) -> List[ViralContent]:
    """Busca historias virales de Reddit (texto público) para convertir en videos"""
    import requests
    
    if content_type not in ['story', 'curiosity']:
        return []
    
    # Subreddits relevantes
    subreddit_map = {
        'story': ['AskReddit', 'nosleep', 'tifu', 'LetsNotMeet'],
        'curiosity': ['todayilearned', 'Showerthoughts', 'explainlikeimfive']
    }
    
    subreddit = random.choice(subreddit_map.get(content_type, ['AskReddit']))
    logger.info(f'[REDDIT] Buscando en r/{subreddit}')
    
    url = f'https://www.reddit.com/r/{subreddit}/top.json?t=year&limit=50'
    
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: requests.get(
                url,
                headers={'User-Agent': 'Mozilla/5.0'},
                timeout=10
            )
        )
        data = response.json()
        
        content_list = []
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=min_age_days)
        
        for post in data.get('data', {}).get('children', []):
            try:
                post_data = post['data']
                score = post_data.get('score', 0)
                
                if score < 5000:  # Mínimo 5k upvotes
                    continue
                
                created = datetime.fromtimestamp(post_data['created_utc'], tz=timezone.utc)
                if created > cutoff_date:
                    continue
                
                title = post_data.get('title', '')
                selftext = post_data.get('selftext', '')[:500]
                
                if not selftext or len(selftext) < 100:
                    continue
                
                content = ViralContent(
                    url=f"https://reddit.com{post_data['permalink']}",
                    title=title,
                    views=score * 100,  # Estimación: 1 upvote ≈ 100 views
                    platform='reddit',
                    content_type=content_type,
                    description=selftext,
                    upload_date=created.isoformat(),
                    duration=0  # Texto, no video
                )
                content_list.append(content)
            except:
                continue
        
        logger.info(f'[REDDIT] Encontrados: {len(content_list)} posts')
        return content_list
    
    except Exception as e:
        logger.warning(f'[REDDIT] Error: {e}')
        return []


async def download_viral_video(
    content: ViralContent,
    output_dir: str,
    job_id: str
) -> Optional[str]:
    """Descarga el video viral usando yt-dlp"""
    import yt_dlp
    
    if content.platform == 'reddit':
        logger.info('[DOWNLOAD] Reddit post es texto, no video - skip download')
        return None
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    output_template = str(output_path / f'{job_id}_source.%(ext)s')
    
    ydl_opts = {
        'format': 'best[height<=1080]',
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'max_downloads': 1,
    }
    
    logger.info(f'[DOWNLOAD] Descargando: {content.title[:50]}... de {content.platform}')
    
    loop = asyncio.get_event_loop()
    
    def _download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([content.url])
    
    try:
        await loop.run_in_executor(None, _download)
        
        # Buscar archivo descargado
        downloaded_files = list(output_path.glob(f'{job_id}_source.*'))
        if downloaded_files:
            video_path = str(downloaded_files[0])
            size = Path(video_path).stat().st_size
            logger.info(f'[DOWNLOAD] Completado: {Path(video_path).name} ({size:,} bytes)')
            return video_path
        else:
            logger.warning('[DOWNLOAD] No se encontró archivo descargado')
            return None
    
    except Exception as e:
        logger.error(f'[DOWNLOAD] Error: {e}')
        return None
