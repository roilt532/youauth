"""Viral Analyzer - Analiza contenido viral y genera estrategias de renarración"""
import asyncio
import logging
import os
from typing import Dict, Optional

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')


async def analyze_viral_content(content_data: dict) -> Dict[str, str]:
    """
    Analiza por qué el contenido es viral y genera estrategia de narración.
    
    Returns dict con:
    - viral_factors: Por qué es viral
    - narrative_angle: Ángulo narrativo único
    - hook_strategy: Cómo captar atención primeros 3 seg
    - retention_points: Momentos clave para retención
    """
    
    title = content_data.get('title', '')
    description = content_data.get('description', '')[:500]
    views = content_data.get('views', 0)
    platform = content_data.get('platform', '')
    content_type = content_data.get('content_type', '')
    
    logger.info(f'[ANALYZER] Analizando: "{title[:50]}..." ({views:,} views)')
    
    if not GEMINI_API_KEY:
        logger.warning('[ANALYZER] No Gemini key - usando análisis básico')
        return _basic_analysis(content_data)
    
    prompt = f"""Eres un experto en contenido viral de YouTube para niños y análisis de psicología de retención.

Analiza este contenido viral y genera una estrategia de renarración:

TÍTULO: {title}
DESCRIPCIÓN: {description}
VIEWS: {views:,}
PLATAFORMA: {platform}
TIPO: {content_type}

Responde en JSON EXACTO (sin ```json):
{{
    "viral_factors": "2-3 factores psicológicos que lo hicieron viral (curiosidad, FOMO, sorpresa, etc.)",
    "narrative_angle": "Ángulo narrativo ÚNICO para renarrar (diferente al original, añade valor)",
    "hook_strategy": "Hook primeros 3 segundos en español (1 frase impactante que explote el factor viral)",
    "retention_points": "3 momentos clave para mantener retención (lista separada por |)",
    "title_optimized_es": "Título optimizado en español max 60 chars con emojis",
    "script_outline_es": "Outline del script en español (intro 5s | desarrollo 40s | cierre 10s)"
}}"""
    
    try:
        # Use new google-genai SDK with universal model names
        from google import genai
        
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Try generic model names that are always available
        models_to_try = [
            'gemini-flash-latest',
            'gemini-pro-latest',
            'gemini-2.5-flash',
        ]
        
        loop = asyncio.get_event_loop()
        
        for model_name in models_to_try:
            try:
                def _analyze():
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )
                    return response.text
                
                raw = await loop.run_in_executor(None, _analyze)
                logger.info(f'✅ Viral analysis with {model_name}')
                break  # Success
                
            except Exception as e:
                error_str = str(e)
                if ('503' in error_str or 'UNAVAILABLE' in error_str or 
                    '404' in error_str or 'Not Found' in error_str):
                    logger.warning(f'⚠️ {model_name} unavailable, trying next...')
                    if model_name == models_to_try[-1]:
                        raise
                    continue
                else:
                    raise
        
        import json
        raw = raw.strip()
        for marker in ('```json', '```'):
            if raw.startswith(marker):
                raw = raw[len(marker):]
        if raw.endswith('```'):
            raw = raw[:-3]
        
        analysis = json.loads(raw.strip())
        logger.info(f'[ANALYZER] Análisis completado: {analysis.get("hook_strategy", "")[:50]}...')
        return analysis
    
    except Exception as e:
        logger.warning(f'[ANALYZER] Error en Gemini ({e}), usando fallback')
        return _basic_analysis(content_data)


def _basic_analysis(content_data: dict) -> Dict[str, str]:
    """Análisis básico sin IA"""
    title = content_data.get('title', 'Video viral')
    content_type = content_data.get('content_type', 'roblox')
    
    hooks = {
        'roblox': '¡No vas a creer lo que pasó en este juego!',
        'curiosity': '¡Este dato va a volarte la mente!',
        'story': '¡Escucha esta historia increíble!',
        'animated': '¡Prepárate para una aventura mágica!'
    }
    
    return {
        'viral_factors': 'Contenido entretenido, visualmente atractivo, temática popular',
        'narrative_angle': f'Renarración entusiasta y educativa de: {title[:50]}',
        'hook_strategy': hooks.get(content_type, '¡Esto te va a encantar!'),
        'retention_points': 'Inicio impactante | Momento sorpresa mitad | Cierre memorable',
        'title_optimized_es': f'🔥 {title[:50]}... ¡INCREÍBLE!',
        'script_outline_es': 'Intro explosiva 5s | Desarrollo emocionante 40s | Cierre call-to-action 10s'
    }


async def generate_renarracion_script(
    content_data: dict,
    analysis: dict,
    language: str = 'es'
) -> Dict[str, str]:
    """
    Genera script completo de renarración basado en el análisis viral.
    
    Returns:
    - script_es: Script completo en español
    - script_en: Script completo en inglés (opcional)
    - timestamps: Timestamps sugeridos para edición
    """
    
    logger.info('[SCRIPT GEN] Generando script de renarración...')
    
    if not GEMINI_API_KEY:
        return _basic_script(content_data, analysis, language)
    
    title = content_data.get('title', '')
    narrative_angle = analysis.get('narrative_angle', '')
    hook = analysis.get('hook_strategy', '')
    retention = analysis.get('retention_points', '')
    
    prompt = f"""Genera un script de narración para YouTube Shorts (55-60 segundos) en español.

CONTEXTO ORIGINAL:
Título: {title}
Ángulo narrativo: {narrative_angle}
Hook: {hook}
Puntos de retención: {retention}

REQUISITOS:
- Duración: 55-60 segundos de narración
- Idioma: Español natural, entusiasta, para niños 6-12 años
- Hook impactante primeros 3 segundos
- Pausas naturales cada 8-10 segundos
- Call to action al final (suscribirse, comentar)
- NO mencionar el video original, narrativa 100% propia
- Safe for kids (COPPA compliant)

Responde en JSON EXACTO (sin ```json):
{{
    "script_es": "Script completo en español con pausas naturales...",
    "hook_text": "Frase de hook (primeros 3 seg)",
    "timestamps": "0-3s: Hook | 3-15s: Intro | 15-45s: Desarrollo | 45-55s: Cierre"
}}"""
    
    try:
        # Use new google-genai SDK with universal model names
        from google import genai
        
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        system_instruction = 'Eres un creador experto de scripts virales para YouTube Shorts infantiles.'
        
        # Try generic model names
        models_to_try = [
            'gemini-flash-latest',
            'gemini-pro-latest',
            'gemini-2.5-flash',
        ]
        
        loop = asyncio.get_event_loop()
        
        for model_name in models_to_try:
            try:
                def _generate():
                    response = client.models.generate_content(
                        model=model_name,
                        contents=f"{system_instruction}\n\n{prompt}"
                    )
                    return response.text
                
                raw = await loop.run_in_executor(None, _generate)
                logger.info(f'✅ Script generation with {model_name}')
                break  # Success
                
            except Exception as e:
                error_str = str(e)
                if ('503' in error_str or 'UNAVAILABLE' in error_str or 
                    '404' in error_str or 'Not Found' in error_str):
                    logger.warning(f'⚠️ {model_name} unavailable, trying next...')
                    if model_name == models_to_try[-1]:
                        raise
                    continue
                else:
                    raise
        
        import json
        raw = raw.strip()
        for marker in ('```json', '```'):
            if raw.startswith(marker):
                raw = raw[len(marker):]
        if raw.endswith('```'):
            raw = raw[:-3]
        
        script_data = json.loads(raw.strip())
        logger.info('[SCRIPT GEN] Script generado exitosamente')
        return script_data
    
    except Exception as e:
        logger.warning(f'[SCRIPT GEN] Error ({e}), usando fallback')
        return _basic_script(content_data, analysis, language)


def _basic_script(content_data: dict, analysis: dict, language: str) -> Dict[str, str]:
    """Script básico sin IA"""
    hook = analysis.get('hook_strategy', '¡No te lo vas a creer!')
    title = content_data.get('title', 'este contenido')
    
    script = f"""{hook}

Hoy les traigo algo INCREÍBLE que van a amar. {title[:80]}.

Esto es súper interesante porque... (pausa) ...va a cambiar completamente tu forma de verlo.

Fíjense bien en esto... (pausa) ...¡es alucinante!

Y al final, la mejor parte: (pausa) un final que no se esperaban.

¿Les gustó? ¡Dale like y suscríbete para más contenido increíble!"""
    
    return {
        'script_es': script,
        'hook_text': hook,
        'timestamps': '0-3s: Hook | 3-15s: Intro | 15-45s: Desarrollo | 45-55s: Cierre CTA'
    }
