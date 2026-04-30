"""Script Generator - Uses Google Gemini free API (zero Emergent dependency)"""
import asyncio
import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Gemini free API key (from Google AI Studio - completely free)
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

# Fallback: Emergent key if Gemini not configured (for dashboard usage only)
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

CONTENT_PROMPTS = {
    'roblox': (
        'Eres un experto creador de contenido VIRAL para niños en YouTube especializado en Roblox. '
        'Generas guiónes EXPLOSIVOS, emocionantes y seguros para niños de 6-12 años (COPPA compliant). '
        'Tu estilo: entusiasmo extremo, suspenso, humor infantil, frases cortas y directas.'
    ),
    'curiosity': (
        'Eres un experto creador de contenido educativo VIRAL para niños en YouTube. '
        'Generas curiosidades que dejan boquiabiertos a los niños de 6-12 años. '
        'Tu estilo: datos increíbles, reacciones exageradas, suspenso al revelar.'
    ),
    'story': (
        'Eres un maestro cuentacuentos VIRAL para niños en YouTube. '
        'Generas historias emocionantes con final sorpresa para niños de 6-12 años. '
        'Tu estilo: inicio explosivo, personajes coloridos, giros inesperados.'
    ),
    'animated': (
        'Eres un creador de videos animados VIRALES para niños en YouTube. '
        'Generas guiónes mágicos y aventureros para niños de 4-10 años. '
        'Tu estilo: mágico, colorido, personajes adorables, música de fondo.'
    ),
}

SCRIPT_PROMPT = """Genera un guión para un video de YouTube para niños sobre: {topic}

Tipo: {content_type} | Formato: {format_type} ({duration_hint}) | Idioma: {language}

Respuesta en JSON válido EXACTO (sin ```json, solo el JSON puro):
{{
    "title_es": "título VIRAL en español max 60 chars con emojis 🎮💥",
    "title_en": "VIRAL title in english max 60 chars with emojis 🎮💥",
    "hook_es": "frase de enganche primeros 3 seg en español muy impactante (1-2 oraciones)",
    "hook_en": "hook first 3 seconds english very impactful (1-2 sentences)",
    "script_es": "guión completo español {duration_hint} con pausas naturales, muy emocionante",
    "script_en": "full script english {duration_hint} natural pauses very exciting",
    "thumbnail_prompt": "detailed image prompt in english for AI thumbnail: bright colorful kids youtube thumbnail about {topic}, {content_type} theme, no text, vibrant dramatic lighting, 4K",
    "tags": ["tag1","tag2","tag3","tag4","tag5","tag6","tag7","tag8"],
    "category": "Gaming",
    "description_es": "descripción SEO max 300 chars con hashtags",
    "description_en": "SEO description max 300 chars with hashtags"
}}"""


async def generate_script(
    topic: str,
    content_type: str = 'roblox',
    language: str = 'bilingual',
    format_type: str = 'short',
    custom_prompt: Optional[str] = None
) -> dict:
    """Generate a bilingual kids content script. Uses Gemini free API first."""

    duration_hint = '60 segundos/seconds' if format_type == 'short' else '5-8 minutos/minutes'
    system_msg = custom_prompt or CONTENT_PROMPTS.get(content_type, CONTENT_PROMPTS['roblox'])
    user_prompt = SCRIPT_PROMPT.format(
        topic=topic, content_type=content_type,
        format_type=format_type, duration_hint=duration_hint, language=language
    )

    raw_response = None

    if GEMINI_API_KEY:
        raw_response = await _gemini_generate(system_msg, user_prompt)
    elif EMERGENT_LLM_KEY:
        raw_response = await _emergent_generate(system_msg, user_prompt)
    else:
        logger.warning('No LLM key configured - using fallback script')
        return _fallback_script(topic, content_type)

    return _parse_script(raw_response, topic, content_type)


async def _gemini_generate(system_msg: str, user_prompt: str) -> str:
    """Generate using Google Gemini API with retry and multiple model fallbacks."""
    import time
    
    # Models to try in order (menos a más ocupados)
    models_priority = [
        ('google-genai', 'gemini-1.5-flash'),    # Más estable
        ('google-genai', 'gemini-1.5-pro'),      # Potente y estable
        ('google-genai', 'gemini-2.5-flash'),    # Más nuevo pero más ocupado
        ('legacy', 'gemini-1.5-pro-latest'),
        ('legacy', 'gemini-1.5-flash-latest'),
    ]
    
    max_retries = 2
    last_error = None
    
    for sdk_type, model_name in models_priority:
        for attempt in range(max_retries):
            try:
                if sdk_type == 'google-genai':
                    # Try new SDK
                    from google import genai
                    
                    client = genai.Client(api_key=GEMINI_API_KEY)
                    
                    loop = asyncio.get_event_loop()
                    
                    def _generate():
                        response = client.models.generate_content(
                            model=model_name,
                            contents=f"{system_msg}\n\n{user_prompt}"
                        )
                        return response.text
                    
                    result = await loop.run_in_executor(None, _generate)
                    logger.info(f'✅ Success with {model_name} (attempt {attempt + 1})')
                    return result
                    
                else:
                    # Try legacy SDK
                    import google.generativeai as genai_legacy
                    
                    genai_legacy.configure(api_key=GEMINI_API_KEY)
                    model = genai_legacy.GenerativeModel(
                        model_name=model_name,
                        generation_config={'temperature': 0.9}
                    )
                    
                    loop = asyncio.get_event_loop()
                    response = await loop.run_in_executor(
                        None,
                        lambda: model.generate_content(f"{system_msg}\n\n{user_prompt}")
                    )
                    logger.info(f'✅ Success with {model_name} (legacy SDK)')
                    return response.text
                    
            except ImportError as ie:
                logger.warning(f'SDK import failed: {ie}')
                break  # Skip this SDK type
                
            except Exception as e:
                error_str = str(e)
                last_error = e
                
                # Check if it's a 503 (overloaded)
                if '503' in error_str or 'UNAVAILABLE' in error_str or 'high demand' in error_str:
                    logger.warning(f'⚠️ {model_name} overloaded (503), trying next model...')
                    break  # Don't retry same model, try next one
                    
                # Check if it's a 404 (not found)
                elif '404' in error_str or 'not found' in error_str:
                    logger.warning(f'⚠️ {model_name} not available (404), trying next model...')
                    break  # Don't retry same model, try next one
                
                # Other errors - retry with backoff
                else:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 2  # 2s, 4s
                        logger.warning(f'⚠️ {model_name} failed (attempt {attempt + 1}), retrying in {wait_time}s...')
                        time.sleep(wait_time)
                    else:
                        logger.warning(f'❌ {model_name} failed after {max_retries} attempts')
                        break
    
    # All models failed
    logger.error(f'❌ All Gemini models failed. Last error: {last_error}')
    raise RuntimeError(f'All Gemini models unavailable: {last_error}')


async def _emergent_generate(system_msg: str, user_prompt: str) -> str:
    """Fallback: generate using Emergent LLM key (requires Emergent subscription)."""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f'script_{id(user_prompt)}',
        system_message=system_msg
    )
    return await chat.send_message(UserMessage(text=user_prompt))


def _parse_script(raw: str, topic: str, content_type: str) -> dict:
    """Parse JSON from LLM response."""
    try:
        content = raw.strip()
        for marker in ('```json', '```'):
            if content.startswith(marker):
                content = content[len(marker):]
        if content.endswith('```'):
            content = content[:-3]
        data = json.loads(content.strip())
        required = ['title_es', 'title_en', 'script_es', 'script_en', 'tags']
        for f in required:
            if f not in data:
                raise ValueError(f'Missing field: {f}')
        # Ensure thumbnail_prompt exists
        if 'thumbnail_prompt' not in data:
            data['thumbnail_prompt'] = (
                f'kids youtube thumbnail about {topic}, {content_type} gaming theme, '
                'bright colorful vibrant, dramatic lighting, no text, 4K'
            )
        logger.info(f"Script generated: {data.get('title_es', '')[:50]}")
        return data
    except Exception as e:
        logger.warning(f'Script parse error ({e}), using fallback')
        return _fallback_script(topic, content_type)


def _fallback_script(topic: str, content_type: str = 'roblox') -> dict:
    return {
        'title_es': f'🎮 {topic[:45]}! 💥',
        'title_en': f'🎮 {topic[:45]}! 💥',
        'hook_es': '¡No vas a creer lo que descubrí hoy! ¡Esto lo cambia todo!',
        'hook_en': "You won't believe what I found today! This changes everything!",
        'script_es': f'¡Hola amigos! Hoy les traigo algo INCREÍBLE sobre {topic}. ¡Van a flipar! Este secreto que nadie conoce va a cambiarlo todo en el juego. ¡No se pierdan ni un segundo de este video!',
        'script_en': f'Hey friends! Today I have something AMAZING about {topic}. You are going to love this! This secret that nobody knows is going to change everything in the game!',
        'thumbnail_prompt': f'kids youtube thumbnail {topic} {content_type} gaming theme bright colorful vibrant no text 4K',
        'tags': ['kids', 'children', 'viral', 'roblox', 'fun', 'gaming', 'ni\u00f1os', 'espa\u00f1ol'],
        'category': 'Gaming',
        'description_es': f'Video increíble sobre {topic}. ¡Dale like y suscríbete! #kids #viral #roblox #niños',
        'description_en': f'Amazing video about {topic}. Like and subscribe! #kids #viral #roblox',
    }
