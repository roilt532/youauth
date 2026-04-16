"""Script Generator - Uses Emergent LLM (Gemini) to generate bilingual kids content scripts"""
import asyncio
import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', 'sk-emergent-bC626Fa91F75964424')

CONTENT_PROMPTS = {
    'roblox': """Eres un experto creador de contenido para niños en YouTube especializado en Roblox.
Generas guiones VIRALES, emocionantes y seguros para niños de 6-12 años (COPPA compliant).
Usa MUCHO entusiasmo, humor infantil, y crea suspenso.""",
    'curiosity': """Eres un experto creador de contenido educativo para niños en YouTube.
Generas curiosidades y datos increíbles que sorprenden a los niños de 6-12 años.
Usa un tono divertido, sorprendente y educativo.""",
    'story': """Eres un maestro cuentacuentos para niños en YouTube.
Generas historias emocionantes, con personajes divertidos y moralejas positivas para niños de 6-12 años.
Usa suspenso, humor y emociones fuertes.""",
    'animated': """Eres un creador de videos animados para niños en YouTube.
Generas guiones para videos animados con personajes adorables y aventuras emocionantes para niños de 4-10 años.
Usa un tono mágico, colorido y muy divertido.""",
}

SCRIPT_PROMPT_TEMPLATE = """Genera un guión para un video de YouTube para niños sobre: {topic}

Tipo de contenido: {content_type}
Formato: {format_type} ({duration_hint})
Idioma principal: {language}

Responde EXACTAMENTE en este formato JSON válido (sin texto adicional, sin ```json):
{{
    "title_es": "título en español MAX 60 chars, muy llamativo con emojis",
    "title_en": "title in english MAX 60 chars, very catchy with emojis",
    "hook_es": "frase de enganche primeros 3 segundos, muy impactante (1-2 oraciones)",
    "hook_en": "hook first 3 seconds, very impactful (1-2 sentences)",
    "script_es": "guión completo en español apropiado para {duration_hint}, con pausas naturales, muy emocionante",
    "script_en": "full script in english for {duration_hint}, natural pauses, very exciting",
    "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8"],
    "category": "Gaming o Education o Entertainment",
    "description_es": "descripción SEO del video en español MAX 300 chars con hashtags",
    "description_en": "SEO video description in english MAX 300 chars with hashtags"
}}"""


async def generate_script(
    topic: str,
    content_type: str = 'roblox',
    language: str = 'bilingual',
    format_type: str = 'short',
    custom_prompt: Optional[str] = None
) -> dict:
    """Generate a bilingual kids content script using Gemini LLM."""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        duration_hint = "60 segundos/seconds" if format_type == 'short' else "5-8 minutos/minutes"
        system_msg = custom_prompt or CONTENT_PROMPTS.get(content_type, CONTENT_PROMPTS['roblox'])
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"script_{content_type}_{language}_{id(topic)}",
            system_message=system_msg
        )
        
        prompt = SCRIPT_PROMPT_TEMPLATE.format(
            topic=topic,
            content_type=content_type,
            format_type=format_type,
            duration_hint=duration_hint,
            language=language
        )
        
        response = await chat.send_message(UserMessage(text=prompt))
        
        # Clean and parse JSON
        content = response.strip()
        if content.startswith('```json'):
            content = content[7:]
        if content.startswith('```'):
            content = content[3:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
        
        script_data = json.loads(content)
        
        # Validate required fields
        required_fields = ['title_es', 'title_en', 'script_es', 'script_en', 'tags']
        for field in required_fields:
            if field not in script_data:
                raise ValueError(f"Missing required field: {field}")
        
        logger.info(f"Script generated for topic: {topic[:50]}")
        return script_data
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse script JSON: {e}")
        # Return fallback script
        return {
            "title_es": f"🎮 {topic[:50]} - Video Increíble!",
            "title_en": f"🎮 {topic[:50]} - Amazing Video!",
            "hook_es": "¡No vas a creer lo que va a pasar en este video!",
            "hook_en": "You won't believe what's going to happen in this video!",
            "script_es": f"¡Hola amigos! Hoy les traigo un video increíble sobre {topic}. ¡Van a flipar con todo lo que vamos a ver hoy! ¡No se pierdan ni un segundo!",
            "script_en": f"Hey friends! Today I have an amazing video about {topic}. You're going to love everything we're going to see today! Don't miss a second!",
            "tags": ["kids", "children", "viral", "roblox", "fun", "gaming", "niños", "español"],
            "category": "Gaming",
            "description_es": f"Video increíble sobre {topic} para niños. ¡Dale like y suscríbete! #kids #viral #roblox",
            "description_en": f"Amazing video about {topic} for kids. Like and subscribe! #kids #viral #roblox"
        }
    except Exception as e:
        logger.error(f"Script generation error: {e}")
        raise
