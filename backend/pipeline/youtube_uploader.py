"""YouTube Uploader - OAuth 2.0 upload with made-for-kids compliance"""
import asyncio
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

YOUTUBE_SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/youtube'
]


def build_youtube_service(client_id: str, client_secret: str, refresh_token: str):
    """Build YouTube API service with OAuth credentials."""
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    import google.auth.transport.requests
    
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=client_id,
        client_secret=client_secret,
        scopes=YOUTUBE_SCOPES
    )
    
    # Refresh to get valid access token
    request = google.auth.transport.requests.Request()
    creds.refresh(request)
    
    return build('youtube', 'v3', credentials=creds, cache_discovery=False)


async def upload_video(
    video_path: str,
    thumbnail_path: str,
    title: str,
    description: str,
    tags: list,
    category_id: str = '20',  # 20 = Gaming
    made_for_kids: bool = True,
    client_id: str = '',
    client_secret: str = '',
    refresh_token: str = '',
    privacy: str = 'public'
) -> dict:
    """Upload video to YouTube with all metadata."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        _upload_video_sync,
        video_path, thumbnail_path, title, description,
        tags, category_id, made_for_kids,
        client_id, client_secret, refresh_token, privacy
    )


def _upload_video_sync(
    video_path: str,
    thumbnail_path: str,
    title: str,
    description: str,
    tags: list,
    category_id: str,
    made_for_kids: bool,
    client_id: str,
    client_secret: str,
    refresh_token: str,
    privacy: str
) -> dict:
    """Synchronous YouTube upload."""
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError
    
    youtube = build_youtube_service(client_id, client_secret, refresh_token)
    
    # Prepare video metadata
    body = {
        'snippet': {
            'title': title[:100],  # YouTube max title length
            'description': description[:5000],
            'tags': tags[:500],  # YouTube max tags
            'categoryId': category_id,
            'defaultLanguage': 'es',
            'defaultAudioLanguage': 'es'
        },
        'status': {
            'privacyStatus': privacy,
            'selfDeclaredMadeForKids': made_for_kids,
        }
    }
    
    # Upload video
    media = MediaFileUpload(
        video_path,
        mimetype='video/mp4',
        resumable=True,
        chunksize=1024*1024*5  # 5MB chunks
    )
    
    logger.info(f"Uploading video: {video_path}")
    
    request = youtube.videos().insert(
        part='snippet,status',
        body=body,
        media_body=media
    )
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            progress = int(status.progress() * 100)
            logger.info(f"Upload progress: {progress}%")
    
    video_id = response['id']
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    logger.info(f"Video uploaded: {video_url}")
    
    # Upload thumbnail
    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path, mimetype='image/jpeg')
            ).execute()
            logger.info(f"Thumbnail uploaded for video {video_id}")
        except Exception as e:
            logger.warning(f"Thumbnail upload failed: {e}")
    
    return {
        'video_id': video_id,
        'video_url': video_url,
        'title': response['snippet']['title'],
        'made_for_kids': made_for_kids
    }


def get_auth_url(client_id: str, client_secret: str, redirect_uri: str) -> str:
    """Generate YouTube OAuth authorization URL (no PKCE - simple flow)."""
    from urllib.parse import urlencode
    
    scope = ' '.join(YOUTUBE_SCOPES)
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': scope,
        'access_type': 'offline',
        'prompt': 'consent',
        'include_granted_scopes': 'true'
    }
    return 'https://accounts.google.com/o/oauth2/auth?' + urlencode(params)


def exchange_code_for_tokens(
    code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str
) -> dict:
    """Exchange authorization code for refresh token using direct HTTP POST."""
    import requests as req
    
    response = req.post(
        'https://oauth2.googleapis.com/token',
        data={
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
    )
    tokens = response.json()
    if 'error' in tokens:
        raise ValueError(f"Token exchange error: {tokens['error']} - {tokens.get('error_description', '')}")
    return {
        'access_token': tokens.get('access_token', ''),
        'refresh_token': tokens.get('refresh_token', ''),
    }


async def get_channel_info(client_id: str, client_secret: str, refresh_token: str) -> dict:
    """Get channel information from YouTube API."""
    loop = asyncio.get_event_loop()
    
    def _get_info():
        youtube = build_youtube_service(client_id, client_secret, refresh_token)
        response = youtube.channels().list(
            part='snippet,statistics,brandingSettings',
            mine=True
        ).execute()
        
        if not response.get('items'):
            return None
        
        item = response['items'][0]
        return {
            'id': item['id'],
            'title': item['snippet']['title'],
            'description': item['snippet'].get('description', ''),
            'thumbnail': item['snippet']['thumbnails'].get('default', {}).get('url', ''),
            'subscriber_count': int(item['statistics'].get('subscriberCount', 0)),
            'view_count': int(item['statistics'].get('viewCount', 0)),
            'video_count': int(item['statistics'].get('videoCount', 0)),
        }
    
    return await loop.run_in_executor(None, _get_info)


async def get_channel_videos(
    client_id: str,
    client_secret: str,
    refresh_token: str,
    max_results: int = 20
) -> list:
    """Get list of channel videos with statistics."""
    loop = asyncio.get_event_loop()
    
    def _get_videos():
        youtube = build_youtube_service(client_id, client_secret, refresh_token)
        
        # Get uploads playlist
        channels = youtube.channels().list(part='contentDetails', mine=True).execute()
        if not channels.get('items'):
            return []
        
        uploads_playlist_id = channels['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        
        # Get videos from playlist
        playlist_items = youtube.playlistItems().list(
            part='snippet',
            playlistId=uploads_playlist_id,
            maxResults=max_results
        ).execute()
        
        video_ids = [
            item['snippet']['resourceId']['videoId']
            for item in playlist_items.get('items', [])
        ]
        
        if not video_ids:
            return []
        
        # Get video statistics
        videos_response = youtube.videos().list(
            part='snippet,statistics',
            id=','.join(video_ids)
        ).execute()
        
        videos = []
        for item in videos_response.get('items', []):
            videos.append({
                'id': item['id'],
                'title': item['snippet']['title'],
                'published_at': item['snippet']['publishedAt'],
                'thumbnail': item['snippet']['thumbnails'].get('high', {}).get('url', ''),
                'view_count': int(item['statistics'].get('viewCount', 0)),
                'like_count': int(item['statistics'].get('likeCount', 0)),
                'comment_count': int(item['statistics'].get('commentCount', 0)),
                'url': f"https://www.youtube.com/watch?v={item['id']}"
            })
        
        return videos
    
    return await loop.run_in_executor(None, _get_videos)
