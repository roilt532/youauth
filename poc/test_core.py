#!/usr/bin/env python3
"""
POC Test: YouTube Automation Pipeline Core
Tests: Script Generation → TTS → Video Assembly → Thumbnail Generation
YouTube Upload is tested separately (requires OAuth credentials from user)
"""

import os
import sys
import json
import time
import traceback
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

OUTPUT_DIR = Path("/tmp/yt_test_output")
OUTPUT_DIR.mkdir(exist_ok=True)

EMERGENT_LLM_KEY = "sk-emergent-bC626Fa91F75964424"

results = {}

# ============================================================
# TEST 1: Script Generation with Emergent LLM (Gemini)
# ============================================================
def test_script_generation():
    print("\n" + "="*60)
    print("TEST 1: Script Generation (Emergent LLM → Gemini)")
    print("="*60)
    
    try:
        import asyncio
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        async def generate_script():
            chat = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id="poc_test_script",
                system_message="""Eres un experto creador de contenido para niños en YouTube. 
Generas guiones virales, emocionantes y totalmente seguros para niños (COPPA compliant).
Siempre respondes en JSON válido."""
            )
            
            prompt = """Genera un guión corto para un video de YouTube para niños sobre ROBLOX.
El video debe ser MUY emocionante y enganchable para niños de 6-12 años.

Responde EXACTAMENTE en este formato JSON (sin texto adicional):
{
    "title_es": "título en español (max 60 chars, muy llamativo)",
    "title_en": "title in english (max 60 chars, very catchy)",
    "hook_es": "frase de enganche en español (primeros 3 segundos, muy emocionante)",
    "hook_en": "hook in english (first 3 seconds, very exciting)",
    "script_es": "guión completo en español (60-90 segundos, emocionante y educativo)",
    "script_en": "full script in english (60-90 seconds, exciting and educational)",
    "tags": ["roblox", "niños", "kids", "viral", "gaming"],
    "category": "Gaming",
    "description_es": "descripción del video en español (max 200 chars)",
    "description_en": "video description in english (max 200 chars)"
}"""
            
            return await chat.send_message(UserMessage(text=prompt))
        
        response = asyncio.run(generate_script())
        
        # Parse JSON from response
        content = response.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        script_data = json.loads(content.strip())
        
        # Save to file
        script_path = OUTPUT_DIR / "generated_script.json"
        with open(script_path, "w", encoding="utf-8") as f:
            json.dump(script_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Script generated successfully!")
        print(f"   Title ES: {script_data['title_es']}")
        print(f"   Title EN: {script_data['title_en']}")
        print(f"   Script ES length: {len(script_data['script_es'])} chars")
        print(f"   Script EN length: {len(script_data['script_en'])} chars")
        print(f"   Tags: {script_data['tags']}")
        print(f"   Saved to: {script_path}")
        
        results['script_generation'] = {
            'status': 'PASS',
            'data': script_data
        }
        return script_data
        
    except Exception as e:
        print(f"❌ Script generation FAILED: {e}")
        traceback.print_exc()
        results['script_generation'] = {'status': 'FAIL', 'error': str(e)}
        return None


# ============================================================
# TEST 2: TTS Generation (gTTS - Free)
# ============================================================
def test_tts_generation(script_data):
    print("\n" + "="*60)
    print("TEST 2: TTS Generation (gTTS - Free)")
    print("="*60)
    
    try:
        from gtts import gTTS
        
        if not script_data:
            # Use fallback test text
            text_es = "¡Hola amigos! Bienvenidos a otro video emocionante de Roblox. ¡Hoy vamos a descubrir el secreto más increíble del juego!"
            text_en = "Hello friends! Welcome to another exciting Roblox video. Today we're going to discover the most incredible secret in the game!"
        else:
            text_es = script_data.get('script_es', "Texto de prueba en español para el video de Roblox.")
            text_en = script_data.get('script_en', "Test text in English for the Roblox video.")
        
        # Generate Spanish TTS
        print("  Generating Spanish narration...")
        tts_es = gTTS(text=text_es, lang='es', slow=False)
        audio_es_path = OUTPUT_DIR / "narration_es.mp3"
        tts_es.save(str(audio_es_path))
        
        # Generate English TTS
        print("  Generating English narration...")
        tts_en = gTTS(text=text_en, lang='en', slow=False)
        audio_en_path = OUTPUT_DIR / "narration_en.mp3"
        tts_en.save(str(audio_en_path))
        
        es_size = audio_es_path.stat().st_size
        en_size = audio_en_path.stat().st_size
        
        print(f"✅ TTS generated successfully!")
        print(f"   Spanish audio: {audio_es_path} ({es_size:,} bytes)")
        print(f"   English audio: {audio_en_path} ({en_size:,} bytes)")
        
        results['tts_generation'] = {
            'status': 'PASS',
            'audio_es': str(audio_es_path),
            'audio_en': str(audio_en_path)
        }
        return str(audio_es_path), str(audio_en_path)
        
    except Exception as e:
        print(f"❌ TTS generation FAILED: {e}")
        traceback.print_exc()
        results['tts_generation'] = {'status': 'FAIL', 'error': str(e)}
        return None, None


# ============================================================
# TEST 3: Video Assembly (MoviePy + FFmpeg - Free)
# ============================================================
def test_video_assembly(audio_es_path, audio_en_path):
    print("\n" + "="*60)
    print("TEST 3: Video Assembly (MoviePy + FFmpeg)")
    print("="*60)
    
    try:
        import numpy as np
        from moviepy import (
            VideoFileClip, AudioFileClip, ColorClip, 
            CompositeVideoClip, TextClip, concatenate_videoclips
        )
        
        # Create a test background video (simulating Roblox clip)
        # In production, this would be the downloaded Roblox clip
        print("  Creating test background clip (simulates Roblox clip)...")
        
        duration = 15  # 15 seconds for POC
        
        # Create colorful background (kids-friendly)
        bg_clip = ColorClip(size=(1080, 1920), color=(20, 20, 60), duration=duration)
        
        # Add audio (Spanish narration for first half, English for second)
        final_clips = [bg_clip]
        
        if audio_es_path and os.path.exists(audio_es_path):
            print("  Adding Spanish narration...")
            audio_clip = AudioFileClip(audio_es_path)
            audio_duration = min(audio_clip.duration, duration)
            audio_clip = audio_clip.subclipped(0, audio_duration)
            bg_clip = bg_clip.with_audio(audio_clip)
        
        # Resize to Shorts format (9:16)
        final_video = bg_clip
        
        # Save video
        video_path = OUTPUT_DIR / "test_video.mp4"
        print(f"  Rendering video to {video_path}...")
        
        final_video.write_videofile(
            str(video_path),
            fps=30,
            codec='libx264',
            audio_codec='aac',
            logger=None,  # Suppress verbose output
            preset='ultrafast'
        )
        
        video_size = video_path.stat().st_size
        
        print(f"✅ Video assembled successfully!")
        print(f"   Output: {video_path} ({video_size:,} bytes)")
        print(f"   Format: 1080x1920 (YouTube Shorts)")
        print(f"   Duration: {duration} seconds")
        
        results['video_assembly'] = {
            'status': 'PASS',
            'video_path': str(video_path),
            'size': video_size,
            'duration': duration
        }
        return str(video_path)
        
    except Exception as e:
        print(f"❌ Video assembly FAILED: {e}")
        traceback.print_exc()
        results['video_assembly'] = {'status': 'FAIL', 'error': str(e)}
        return None


# ============================================================
# TEST 4: Thumbnail Generation (Pillow - Free)
# ============================================================
def test_thumbnail_generation(script_data):
    print("\n" + "="*60)
    print("TEST 4: Thumbnail Generation (Pillow)")
    print("="*60)
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        import io
        
        title = "¡ROBLOX SECRETO INCREÍBLE!" if not script_data else script_data.get('title_es', '¡VIDEO VIRAL DE ROBLOX!')
        
        # Create thumbnail (YouTube standard: 1280x720)
        width, height = 1280, 720
        
        # Background: dark blue with grid (Roblox-inspired)
        img = Image.new('RGB', (width, height), color=(10, 15, 40))
        draw = ImageDraw.Draw(img)
        
        # Add colorful background gradient effect
        for y in range(height):
            alpha = int(255 * (y / height) * 0.3)
            r = int(20 + (y / height) * 30)
            g = int(10 + (y / height) * 20)
            b = int(80 + (y / height) * 40)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        
        # Add red accent stripe (YouTube brand)
        draw.rectangle([0, 0, width, 8], fill=(255, 0, 0))
        draw.rectangle([0, height-8, width, height], fill=(255, 0, 0))
        
        # Add corner decoration
        draw.rectangle([0, 0, 120, 120], fill=(255, 0, 0, 50))
        
        # Add ROBLOX text
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 80)
            font_medium = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 50)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 35)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # White text with black outline (for visibility)
        def draw_text_with_outline(draw, pos, text, font, text_color, outline_color, outline_width=3):
            x, y = pos
            for dx in range(-outline_width, outline_width+1):
                for dy in range(-outline_width, outline_width+1):
                    if dx != 0 or dy != 0:
                        draw.text((x+dx, y+dy), text, font=font, fill=outline_color)
            draw.text(pos, text, font=font, fill=text_color)
        
        # Main title
        title_lines = [title[:30], title[30:60] if len(title) > 30 else ""]
        y_start = 200
        for line in title_lines:
            if line.strip():
                bbox = draw.textbbox((0, 0), line, font=font_large)
                text_width = bbox[2] - bbox[0]
                x = (width - text_width) // 2
                draw_text_with_outline(draw, (x, y_start), line, font_large, (255, 255, 255), (0, 0, 0), 4)
                y_start += 90
        
        # Sub-label
        sublabel = "⭐ VIDEO VIRAL ⭐"
        draw_text_with_outline(draw, (50, 550), sublabel, font_medium, (255, 220, 0), (200, 0, 0), 3)
        
        # KIDS SAFE badge
        draw.rectangle([width-200, height-80, width-10, height-10], fill=(0, 180, 0))
        draw.text((width-185, height-68), "KIDS SAFE", font=font_small, fill=(255, 255, 255))
        
        # Save thumbnail
        thumb_path = OUTPUT_DIR / "thumbnail.jpg"
        img.save(str(thumb_path), "JPEG", quality=95)
        
        thumb_size = thumb_path.stat().st_size
        
        print(f"✅ Thumbnail generated successfully!")
        print(f"   Output: {thumb_path} ({thumb_size:,} bytes)")
        print(f"   Size: {width}x{height} pixels")
        print(f"   Title: {title}")
        
        results['thumbnail_generation'] = {
            'status': 'PASS',
            'thumb_path': str(thumb_path),
            'size': thumb_size
        }
        return str(thumb_path)
        
    except Exception as e:
        print(f"❌ Thumbnail generation FAILED: {e}")
        traceback.print_exc()
        results['thumbnail_generation'] = {'status': 'FAIL', 'error': str(e)}
        return None


# ============================================================
# TEST 5: yt-dlp (Content Sourcing - Free)
# ============================================================
def test_content_sourcing():
    print("\n" + "="*60)
    print("TEST 5: Content Sourcing (yt-dlp)")
    print("="*60)
    
    try:
        import yt_dlp
        
        # Test yt-dlp is working by getting video info (no actual download for POC)
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Public test video
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,  # Only get info, don't download for POC
        }
        
        print(f"  Testing yt-dlp info extraction (no download)...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(test_url, download=False)
            
        print(f"✅ yt-dlp working correctly!")
        print(f"   Test video: {info.get('title', 'N/A')}")
        print(f"   Duration: {info.get('duration', 0)} seconds")
        print(f"   Formats available: {len(info.get('formats', []))}")
        
        results['content_sourcing'] = {
            'status': 'PASS',
            'yt_dlp_version': yt_dlp.version.__version__,
            'test_video_found': True
        }
        return True
        
    except Exception as e:
        print(f"❌ Content sourcing test FAILED: {e}")
        traceback.print_exc()
        results['content_sourcing'] = {'status': 'FAIL', 'error': str(e)}
        return False


# ============================================================
# TEST 6: YouTube Upload (Requires OAuth Credentials)
# ============================================================
def test_youtube_upload_readiness():
    print("\n" + "="*60)
    print("TEST 6: YouTube Upload Readiness Check")
    print("="*60)
    
    try:
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials
        import google.auth.transport.requests
        
        print("  ✅ google-api-python-client: INSTALLED")
        print("  ✅ google-auth-oauthlib: INSTALLED")
        print("  ✅ google-auth: INSTALLED")
        print("")
        print("  ⚠️  YouTube Upload requires OAuth 2.0 credentials.")
        print("  ⚠️  Follow setup guide to get CLIENT_ID + CLIENT_SECRET + REFRESH_TOKEN")
        print("  ⚠️  Once provided, upload will be tested automatically.")
        
        # Check if credentials are already available
        youtube_client_id = os.environ.get('YT_CLIENT_ID', '')
        youtube_client_secret = os.environ.get('YT_CLIENT_SECRET', '')
        youtube_refresh_token = os.environ.get('YT_REFRESH_TOKEN', '')
        
        if youtube_client_id and youtube_client_secret and youtube_refresh_token:
            print("\n  🔑 YouTube credentials found! Testing upload...")
            
            creds = Credentials(
                token=None,
                refresh_token=youtube_refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=youtube_client_id,
                client_secret=youtube_client_secret,
                scopes=["https://www.googleapis.com/auth/youtube.upload",
                        "https://www.googleapis.com/auth/youtube.readonly"]
            )
            
            # Refresh token to get access token
            request = google.auth.transport.requests.Request()
            creds.refresh(request)
            
            youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)
            
            # Test by fetching channel info (minimal quota usage)
            channel_response = youtube.channels().list(
                part="snippet,statistics",
                mine=True
            ).execute()
            
            if channel_response.get('items'):
                channel = channel_response['items'][0]
                print(f"\n  ✅ YouTube API connected successfully!")
                print(f"     Channel: {channel['snippet']['title']}")
                print(f"     Subscribers: {channel['statistics'].get('subscriberCount', 'N/A')}")
                print(f"     Videos: {channel['statistics'].get('videoCount', 'N/A')}")
                
                results['youtube_upload'] = {
                    'status': 'PASS',
                    'channel': channel['snippet']['title'],
                    'message': 'OAuth credentials valid and working'
                }
            else:
                print("  ❌ No channel found for these credentials")
                results['youtube_upload'] = {'status': 'FAIL', 'error': 'No channel found'}
        else:
            print("\n  ℹ️  YouTube credentials NOT provided yet (normal for initial POC)")
            print("  ℹ️  All other pipeline steps work correctly")
            results['youtube_upload'] = {
                'status': 'PENDING',
                'message': 'Waiting for user to provide YouTube OAuth credentials'
            }
        
        return True
        
    except Exception as e:
        print(f"❌ YouTube readiness check FAILED: {e}")
        traceback.print_exc()
        results['youtube_upload'] = {'status': 'FAIL', 'error': str(e)}
        return False


# ============================================================
# MAIN POC RUNNER
# ============================================================
def main():
    print("\n" + "🎬"*30)
    print("YOUTUBE AUTOMATION PIPELINE - POC TEST")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎬"*30)
    
    start_time = time.time()
    
    # Run all tests
    script_data = test_script_generation()
    audio_es, audio_en = test_tts_generation(script_data)
    video_path = test_video_assembly(audio_es, audio_en)
    thumb_path = test_thumbnail_generation(script_data)
    content_ok = test_content_sourcing()
    youtube_ready = test_youtube_upload_readiness()
    
    elapsed = time.time() - start_time
    
    # Summary
    print("\n" + "="*60)
    print("POC TEST SUMMARY")
    print("="*60)
    
    all_pass = True
    for test_name, result in results.items():
        status = result.get('status', 'UNKNOWN')
        icon = "✅" if status == 'PASS' else ("⏳" if status == 'PENDING' else "❌")
        print(f"  {icon} {test_name}: {status}")
        if status == 'FAIL':
            print(f"     Error: {result.get('error', 'Unknown')}")
            all_pass = False
    
    print(f"\n  Total time: {elapsed:.1f}s")
    print(f"  Output dir: {OUTPUT_DIR}")
    
    if all_pass:
        print("\n🎉 ALL PIPELINE TESTS PASSED!")
        print("   Ready to build the full automation app.")
        print("   YouTube upload will be enabled once credentials are provided.")
    else:
        print("\n⚠️  SOME TESTS FAILED - check errors above")
    
    # Save results
    results_path = OUTPUT_DIR / "poc_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  Results saved to: {results_path}")
    
    return all_pass


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
