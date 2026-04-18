from fastapi import FastAPI, APIRouter, BackgroundTasks, HTTPException, Query
from fastapi.responses import JSONResponse, RedirectResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import uuid
import asyncio
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'yt_automation')]

app = FastAPI(title="YouTube Automation Dashboard")
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# In-memory store for active pipeline runs
active_runs: Dict[str, dict] = {}

# ============================================================
# Helpers
# ============================================================
def serialize_doc(doc) -> dict:
    if doc is None:
        return None
    result = {}
    for k, v in doc.items():
        if k == '_id':
            continue
        if isinstance(v, datetime):
            result[k] = v.isoformat()
        elif isinstance(v, dict):
            result[k] = serialize_doc(v)
        elif isinstance(v, list):
            result[k] = [serialize_doc(i) if isinstance(i, dict) else (i.isoformat() if isinstance(i, datetime) else i) for i in v]
        else:
            result[k] = v
    return result

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

# ============================================================
# Models
# ============================================================
class JobCreate(BaseModel):
    title: str
    topic: str
    source_url: Optional[str] = ''
    content_type: str = 'roblox'  # roblox, curiosity, story, animated
    language: str = 'bilingual'   # es, en, bilingual
    format: str = 'short'          # short (9:16) or long (16:9)
    template_id: Optional[str] = None
    made_for_kids: bool = True
    priority: int = 5
    scheduled_at: Optional[str] = None
    custom_prompt: Optional[str] = None

class JobUpdate(BaseModel):
    title: Optional[str] = None
    topic: Optional[str] = None
    source_url: Optional[str] = None
    content_type: Optional[str] = None
    language: Optional[str] = None
    format: Optional[str] = None
    priority: Optional[int] = None
    scheduled_at: Optional[str] = None
    status: Optional[str] = None

class TemplateCreate(BaseModel):
    name: str
    content_type: str = 'roblox'
    hook_style: str = 'surprise'  # surprise, question, bold, story
    language: str = 'bilingual'
    tts_voice: str = 'standard'
    tags: List[str] = []
    custom_prompt: Optional[str] = None
    description: Optional[str] = ''

class SettingsUpdate(BaseModel):
    youtube_client_id: Optional[str] = None
    youtube_client_secret: Optional[str] = None
    youtube_refresh_token: Optional[str] = None
    posting_window_start: Optional[str] = '15:00'
    posting_window_end: Optional[str] = '20:00'
    max_daily_uploads: Optional[int] = 1
    random_delay_minutes: Optional[int] = 30
    anti_detection_enabled: Optional[bool] = True
    made_for_kids_default: Optional[bool] = True
    upload_privacy: Optional[str] = 'public'
    github_actions_enabled: Optional[bool] = False

# ============================================================
# Dashboard
# ============================================================
@api_router.get("/dashboard/stats")
async def get_dashboard_stats():
    """Get overview statistics for the dashboard."""
    try:
        total_jobs = await db.jobs.count_documents({})
        total_runs = await db.runs.count_documents({})
        completed_runs = await db.runs.count_documents({'status': 'completed'})
        failed_runs = await db.runs.count_documents({'status': 'failed'})
        running_runs = await db.runs.count_documents({'status': 'running'})
        pending_jobs = await db.jobs.count_documents({'status': 'pending'})
        
        success_rate = round((completed_runs / total_runs * 100) if total_runs > 0 else 0, 1)
        
        # Recent runs (last 5)
        recent_runs = await db.runs.find({}, {'_id': 0}).sort('created_at', -1).limit(5).to_list(5)
        
        # Current active run
        active_run = None
        if active_runs:
            active_run = list(active_runs.values())[0]
        else:
            active_run_doc = await db.runs.find_one({'status': 'running'}, {'_id': 0})
            if active_run_doc:
                active_run = serialize_doc(active_run_doc)
        
        # Quota usage (estimate: 1600 units per upload, 10000 daily limit)
        today_uploads = await db.runs.count_documents({
            'status': 'completed',
            'created_at': {'$gte': datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()}
        })
        quota_used = today_uploads * 1600
        quota_total = 10000
        quota_percent = min(round(quota_used / quota_total * 100), 100)
        
        return {
            'total_jobs': total_jobs,
            'total_runs': total_runs,
            'completed_runs': completed_runs,
            'failed_runs': failed_runs,
            'running_runs': running_runs,
            'pending_jobs': pending_jobs,
            'success_rate': success_rate,
            'quota_used': quota_used,
            'quota_total': quota_total,
            'quota_percent': quota_percent,
            'today_uploads': today_uploads,
            'recent_runs': [serialize_doc(r) for r in recent_runs],
            'active_run': active_run
        }
    except Exception as e:
        logger.error(f"Dashboard stats error: {e}")
        return {
            'total_jobs': 0, 'total_runs': 0, 'completed_runs': 0,
            'failed_runs': 0, 'running_runs': 0, 'pending_jobs': 0,
            'success_rate': 0, 'quota_used': 0, 'quota_total': 10000,
            'quota_percent': 0, 'today_uploads': 0, 'recent_runs': [], 'active_run': None
        }

# ============================================================
# Jobs
# ============================================================
@api_router.get("/jobs")
async def list_jobs(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    query = {}
    if status:
        query['status'] = status
    jobs = await db.jobs.find(query, {'_id': 0}).sort('created_at', -1).skip(offset).limit(limit).to_list(limit)
    total = await db.jobs.count_documents(query)
    return {'jobs': [serialize_doc(j) for j in jobs], 'total': total}


@api_router.post("/jobs")
async def create_job(job: JobCreate):
    job_id = str(uuid.uuid4())
    doc = {
        'id': job_id,
        'title': job.title,
        'topic': job.topic,
        'source_url': job.source_url,
        'content_type': job.content_type,
        'language': job.language,
        'format': job.format,
        'template_id': job.template_id,
        'made_for_kids': job.made_for_kids,
        'priority': job.priority,
        'scheduled_at': job.scheduled_at,
        'custom_prompt': job.custom_prompt,
        'status': 'pending',
        'created_at': now_iso(),
        'updated_at': now_iso(),
        'last_run_id': None
    }
    await db.jobs.insert_one(doc)
    logger.info(f"Job created: {job_id} - {job.title}")
    return serialize_doc(doc)


@api_router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    job = await db.jobs.find_one({'id': job_id}, {'_id': 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return serialize_doc(job)


@api_router.put("/jobs/{job_id}")
async def update_job(job_id: str, update: JobUpdate):
    job = await db.jobs.find_one({'id': job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    update_data['updated_at'] = now_iso()
    await db.jobs.update_one({'id': job_id}, {'$set': update_data})
    updated = await db.jobs.find_one({'id': job_id}, {'_id': 0})
    return serialize_doc(updated)


@api_router.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    job = await db.jobs.find_one({'id': job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    await db.jobs.delete_one({'id': job_id})
    return {'message': 'Job deleted', 'id': job_id}


@api_router.post("/jobs/{job_id}/run")
async def run_job(job_id: str, background_tasks: BackgroundTasks):
    """Start pipeline execution for a job."""
    job = await db.jobs.find_one({'id': job_id}, {'_id': 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.get('status') == 'running':
        raise HTTPException(status_code=409, detail="Job is already running")
    
    # Get settings
    settings_doc = await db.settings.find_one({}, {'_id': 0})
    settings = serialize_doc(settings_doc) if settings_doc else {}
    
    # Create run document
    run_id = str(uuid.uuid4())
    steps = [
        {'name': 'script', 'label': 'Script Generation', 'status': 'pending', 'started_at': None, 'completed_at': None, 'duration': None},
        {'name': 'tts', 'label': 'TTS Narration', 'status': 'pending', 'started_at': None, 'completed_at': None, 'duration': None},
        {'name': 'video_source', 'label': 'Source Video', 'status': 'pending', 'started_at': None, 'completed_at': None, 'duration': None},
        {'name': 'video_compile', 'label': 'Video Compile', 'status': 'pending', 'started_at': None, 'completed_at': None, 'duration': None},
        {'name': 'thumbnail', 'label': 'Thumbnail', 'status': 'pending', 'started_at': None, 'completed_at': None, 'duration': None},
        {'name': 'upload', 'label': 'YouTube Upload', 'status': 'pending', 'started_at': None, 'completed_at': None, 'duration': None},
    ]
    
    run_doc = {
        'id': run_id,
        'job_id': job_id,
        'job_title': job.get('title', ''),
        'status': 'running',
        'steps': steps,
        'logs': [],
        'artifacts': {},
        'error': None,
        'created_at': now_iso(),
        'updated_at': now_iso(),
        'completed_at': None
    }
    
    await db.runs.insert_one(run_doc)
    await db.jobs.update_one({'id': job_id}, {'$set': {'status': 'running', 'last_run_id': run_id, 'updated_at': now_iso()}})
    
    # Track in memory for real-time access
    active_runs[run_id] = serialize_doc(run_doc)
    
    # Run pipeline in background
    background_tasks.add_task(_execute_pipeline, job_id, run_id, serialize_doc(job), settings)
    
    return {'run_id': run_id, 'job_id': job_id, 'status': 'started'}


async def _execute_pipeline(job_id: str, run_id: str, job: dict, settings: dict):
    """Execute the automation pipeline as a background task."""
    from pipeline.pipeline_runner import run_pipeline
    
    async def update_step_callback(step_update: dict):
        step_name = step_update['step']
        step_status = step_update['status']
        timestamp = step_update.get('timestamp', now_iso())
        
        # Update in MongoDB
        await db.runs.update_one(
            {'id': run_id, 'steps.name': step_name},
            {'$set': {
                f'steps.$.status': step_status,
                f'steps.$.started_at': timestamp if step_status == 'running' else None,
                f'steps.$.completed_at': timestamp if step_status in ('completed', 'failed', 'skipped') else None,
                'updated_at': now_iso()
            }}
        )
        
        # Update in memory
        if run_id in active_runs:
            for step in active_runs[run_id].get('steps', []):
                if step['name'] == step_name:
                    step['status'] = step_status
                    break
    
    async def log_callback(entry: dict):
        await db.runs.update_one(
            {'id': run_id},
            {'$push': {'logs': entry}, '$set': {'updated_at': now_iso()}}
        )
        if run_id in active_runs:
            active_runs[run_id].setdefault('logs', []).append(entry)
    
    try:
        result = await run_pipeline(
            job=job,
            settings=settings,
            update_callback=update_step_callback,
            log_callback=log_callback
        )
        
        final_status = result.get('status', 'completed')
        
        # Update run with final status and artifacts
        update_data = {
            'status': final_status,
            'artifacts': result.get('artifacts', {}),
            'error': result.get('error'),
            'completed_at': now_iso(),
            'updated_at': now_iso()
        }
        
        await db.runs.update_one({'id': run_id}, {'$set': update_data})
        await db.jobs.update_one(
            {'id': job_id},
            {'$set': {'status': 'completed' if final_status == 'completed' else 'failed', 'updated_at': now_iso()}}
        )
        
        # Update memory
        if run_id in active_runs:
            active_runs[run_id].update(update_data)
        
    except Exception as e:
        logger.error(f"Pipeline execution error: {e}")
        await db.runs.update_one(
            {'id': run_id},
            {'$set': {'status': 'failed', 'error': str(e), 'completed_at': now_iso(), 'updated_at': now_iso()}}
        )
        await db.jobs.update_one({'id': job_id}, {'$set': {'status': 'failed', 'updated_at': now_iso()}})
    finally:
        # Remove from active runs after a delay
        await asyncio.sleep(30)
        active_runs.pop(run_id, None)

# ============================================================
# Runs
# ============================================================
@api_router.get("/runs")
async def list_runs(job_id: Optional[str] = None, limit: int = 20, offset: int = 0):
    query = {}
    if job_id:
        query['job_id'] = job_id
    runs = await db.runs.find(query, {'_id': 0}).sort('created_at', -1).skip(offset).limit(limit).to_list(limit)
    total = await db.runs.count_documents(query)
    return {'runs': [serialize_doc(r) for r in runs], 'total': total}


@api_router.get("/runs/{run_id}")
async def get_run(run_id: str):
    # Check in-memory first for real-time data
    if run_id in active_runs:
        return active_runs[run_id]
    run = await db.runs.find_one({'id': run_id}, {'_id': 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return serialize_doc(run)


@api_router.get("/runs/{run_id}/logs")
async def get_run_logs(run_id: str):
    run = await db.runs.find_one({'id': run_id}, {'_id': 0, 'logs': 1})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return {'logs': run.get('logs', [])}


@api_router.post("/jobs/{job_id}/retry")
async def retry_job(job_id: str, background_tasks: BackgroundTasks):
    """Retry a failed job."""
    job = await db.jobs.find_one({'id': job_id}, {'_id': 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    await db.jobs.update_one({'id': job_id}, {'$set': {'status': 'pending', 'updated_at': now_iso()}})
    return await run_job(job_id, background_tasks)

# ============================================================
# Templates
# ============================================================
@api_router.get("/templates")
async def list_templates():
    templates = await db.templates.find({}, {'_id': 0}).sort('created_at', -1).to_list(100)
    return {'templates': [serialize_doc(t) for t in templates]}


@api_router.post("/templates")
async def create_template(template: TemplateCreate):
    template_id = str(uuid.uuid4())
    doc = {
        'id': template_id,
        'name': template.name,
        'content_type': template.content_type,
        'hook_style': template.hook_style,
        'language': template.language,
        'tts_voice': template.tts_voice,
        'tags': template.tags,
        'custom_prompt': template.custom_prompt,
        'description': template.description,
        'created_at': now_iso(),
        'updated_at': now_iso()
    }
    await db.templates.insert_one(doc)
    return serialize_doc(doc)


@api_router.put("/templates/{template_id}")
async def update_template(template_id: str, template: TemplateCreate):
    existing = await db.templates.find_one({'id': template_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Template not found")
    update_data = template.model_dump()
    update_data['updated_at'] = now_iso()
    await db.templates.update_one({'id': template_id}, {'$set': update_data})
    updated = await db.templates.find_one({'id': template_id}, {'_id': 0})
    return serialize_doc(updated)


@api_router.delete("/templates/{template_id}")
async def delete_template(template_id: str):
    existing = await db.templates.find_one({'id': template_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Template not found")
    await db.templates.delete_one({'id': template_id})
    return {'message': 'Template deleted', 'id': template_id}

# ============================================================
# Settings
# ============================================================
@api_router.get("/settings")
async def get_settings():
    settings = await db.settings.find_one({}, {'_id': 0})
    if not settings:
        # Return defaults
        return {
            'youtube_client_id': '',
            'youtube_client_secret': '',
            'youtube_refresh_token': '',
            'posting_window_start': '15:00',
            'posting_window_end': '20:00',
            'max_daily_uploads': 1,
            'random_delay_minutes': 30,
            'anti_detection_enabled': True,
            'made_for_kids_default': True,
            'upload_privacy': 'public',
            'github_actions_enabled': False,
            'youtube_connected': False
        }
    result = serialize_doc(settings)
    # Mask sensitive data in response
    if result.get('youtube_client_id'):
        result['youtube_connected'] = bool(result.get('youtube_refresh_token'))
        result['youtube_client_id_masked'] = result['youtube_client_id'][:8] + '...' if len(result.get('youtube_client_id', '')) > 8 else ''
    else:
        result['youtube_connected'] = False
    return result


@api_router.put("/settings")
async def update_settings(settings: SettingsUpdate):
    existing = await db.settings.find_one({})
    update_data = {k: v for k, v in settings.model_dump().items() if v is not None}
    update_data['updated_at'] = now_iso()
    
    if existing:
        await db.settings.update_one({}, {'$set': update_data})
    else:
        update_data['created_at'] = now_iso()
        await db.settings.insert_one(update_data)
    
    updated = await db.settings.find_one({}, {'_id': 0})
    return serialize_doc(updated)


@api_router.get("/settings/youtube/auth-url")
async def get_youtube_auth_url():
    """Generate YouTube OAuth URL for user to authorize."""
    settings = await db.settings.find_one({}, {'_id': 0})
    if not settings or not settings.get('youtube_client_id') or not settings.get('youtube_client_secret'):
        raise HTTPException(status_code=400, detail="YouTube client_id and client_secret must be configured first")
    
    from pipeline.youtube_uploader import get_auth_url
    
    redirect_uri = os.environ.get(
        'YOUTUBE_REDIRECT_URI',
        'https://tube-optimizer-ai.preview.emergentagent.com/api/youtube/oauth/callback'
    )
    
    auth_url = get_auth_url(
        client_id=settings['youtube_client_id'],
        client_secret=settings['youtube_client_secret'],
        redirect_uri=redirect_uri
    )
    
    # Store redirect_uri for callback
    await db.settings.update_one({}, {'$set': {'oauth_redirect_uri': redirect_uri}})
    
    return {'auth_url': auth_url, 'redirect_uri': redirect_uri}


@api_router.get("/youtube/oauth/callback")
async def youtube_oauth_callback(code: str = Query(None), error: str = Query(None), state: str = Query(None)):
    """Handle YouTube OAuth callback."""
    if error:
        return RedirectResponse(url=f"/?oauth_error={error}")
    
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code received")
    
    settings = await db.settings.find_one({}, {'_id': 0})
    if not settings:
        raise HTTPException(status_code=400, detail="Settings not configured")
    
    from pipeline.youtube_uploader import exchange_code_for_tokens
    
    redirect_uri = settings.get('oauth_redirect_uri', 
        'https://tube-optimizer-ai.preview.emergentagent.com/api/youtube/oauth/callback')
    
    try:
        tokens = exchange_code_for_tokens(
            code=code,
            client_id=settings['youtube_client_id'],
            client_secret=settings['youtube_client_secret'],
            redirect_uri=redirect_uri
        )
        
        await db.settings.update_one({}, {'$set': {
            'youtube_refresh_token': tokens.get('refresh_token', ''),
            'youtube_access_token': tokens.get('access_token', ''),
            'updated_at': now_iso()
        }})
        
        logger.info("YouTube OAuth completed successfully - refresh token saved")
        return RedirectResponse(url="/settings?oauth_success=true")
        
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return RedirectResponse(url=f"/settings?oauth_error={str(e)}")


@api_router.get("/settings/youtube/status")
async def get_youtube_status():
    """Check YouTube OAuth connection status."""
    settings = await db.settings.find_one({}, {'_id': 0})
    if not settings or not settings.get('youtube_refresh_token'):
        return {'connected': False, 'channel': None}
    
    try:
        from pipeline.youtube_uploader import get_channel_info
        channel = await get_channel_info(
            client_id=settings.get('youtube_client_id', ''),
            client_secret=settings.get('youtube_client_secret', ''),
            refresh_token=settings.get('youtube_refresh_token', '')
        )
        return {'connected': True, 'channel': channel}
    except Exception as e:
        return {'connected': False, 'error': str(e), 'channel': None}


@api_router.post("/settings/youtube/revoke")
async def revoke_youtube_oauth():
    """Revoke YouTube OAuth tokens."""
    await db.settings.update_one({}, {'$set': {
        'youtube_refresh_token': '',
        'youtube_access_token': '',
        'updated_at': now_iso()
    }})
    return {'message': 'YouTube OAuth revoked'}

# ============================================================
# Analytics
# ============================================================
@api_router.get("/analytics/channel")
async def get_channel_analytics():
    """Get YouTube channel analytics."""
    settings = await db.settings.find_one({}, {'_id': 0})
    if not settings or not settings.get('youtube_refresh_token'):
        return {
            'connected': False,
            'channel': None,
            'message': 'Connect YouTube to see analytics'
        }
    
    try:
        from pipeline.youtube_uploader import get_channel_info, get_channel_videos
        
        channel = await get_channel_info(
            client_id=settings.get('youtube_client_id', ''),
            client_secret=settings.get('youtube_client_secret', ''),
            refresh_token=settings.get('youtube_refresh_token', '')
        )
        
        videos = await get_channel_videos(
            client_id=settings.get('youtube_client_id', ''),
            client_secret=settings.get('youtube_client_secret', ''),
            refresh_token=settings.get('youtube_refresh_token', ''),
            max_results=20
        )
        
        # Aggregate stats
        total_views = sum(v.get('view_count', 0) for v in videos)
        total_likes = sum(v.get('like_count', 0) for v in videos)
        
        # Run history stats
        total_automated = await db.runs.count_documents({'status': 'completed'})
        
        return {
            'connected': True,
            'channel': channel,
            'videos': videos,
            'stats': {
                'total_views': total_views,
                'total_likes': total_likes,
                'total_automated': total_automated
            }
        }
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        return {'connected': False, 'error': str(e), 'channel': None}


@api_router.get("/analytics/run-history")
async def get_run_history_analytics():
    """Get automation run history stats."""
    pipeline = [
        {'$group': {
            '_id': {'$substr': ['$created_at', 0, 10]},
            'total': {'$sum': 1},
            'completed': {'$sum': {'$cond': [{'$eq': ['$status', 'completed']}, 1, 0]}},
            'failed': {'$sum': {'$cond': [{'$eq': ['$status', 'failed']}, 1, 0]}}
        }},
        {'$sort': {'_id': -1}},
        {'$limit': 30}
    ]
    
    results = await db.runs.aggregate(pipeline).to_list(30)
    return {'history': [{
        'date': r['_id'],
        'total': r['total'],
        'completed': r['completed'],
        'failed': r['failed']
    } for r in results]}

# ============================================================
# Pipeline Status
# ============================================================
@api_router.get("/pipeline/status")
async def get_pipeline_status():
    """Get current pipeline execution status."""
    if active_runs:
        run_id = list(active_runs.keys())[0]
        return {'active': True, 'run': active_runs[run_id]}
    
    # Check DB for any running run
    running = await db.runs.find_one({'status': 'running'}, {'_id': 0})
    if running:
        return {'active': True, 'run': serialize_doc(running)}
    
    return {'active': False, 'run': None}

# ============================================================
# Health + Root
# ============================================================
@api_router.get("/")
async def root():
    return {"message": "YouTube Automation API", "status": "ok"}

@api_router.get("/health")
async def health():
    return {"status": "healthy", "timestamp": now_iso()}

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event('shutdown')
async def shutdown_db_client():
    client.close()
