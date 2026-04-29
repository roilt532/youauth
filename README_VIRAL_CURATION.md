# 🚀 YouTube Shorts Automation - Viral Content Curation

Sistema profesional de automatización para YouTube Shorts que **descubre, analiza y renarrá contenido viral LEGAL** de múltiples plataformas.

## 🎯 Características Principales

### ✅ 100% Legal y Ético
- **Creative Commons**: Videos con licencia CC de YouTube
- **Dominio Público**: Stock footage de Pexels/Pixabay
- **Contenido Público**: Posts de Reddit convertidos a video
- **Zero Copyright Issues**: Solo contenido legalmente reutilizable

### 🧠 IA Avanzada
- **Gemini 1.5 Flash**: Análisis de viralidad y generación de scripts
- **edge-tts**: Voces naturales de Microsoft Neural TTS
- **Pollinations.ai**: Generación de thumbnails con IA

### 📊 Curación Inteligente
- **Multi-Plataforma**: YouTube, Reddit, Pexels
- **Scoring Viral**: Algoritmo que evalúa views, engagement, recency
- **Filtros Avanzados**: Edad de contenido (1-3 años ideal), duración, views mínimos

### 🎬 Optimización para Shorts
- **Formato 9:16**: Automático
- **Subtítulos**: Palabra por palabra (estilo TikTok)
- **Hooks Psicológicos**: Primeros 3 segundos optimizados
- **Retención**: Cortes cada 2-3 segundos

### 🔄 Automatización Total
- **GitHub Actions**: Cron jobs diarios
- **Zero Emergent Credits**: Todo gratis (Gemini free tier)
- **Anti-Detection**: Delays aleatorios, variedad de posting times

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────┐
│   CONTENT DISCOVERY ENGINE          │
├─────────────────────────────────────┤
│ • YouTube CC Scraper (yt-dlp)       │
│ • Reddit API / Scraper (PRAW)       │
│ • Pexels Stock Videos               │
│ • Viral Scoring Algorithm           │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   VIRAL ANALYSIS (Gemini AI)        │
├─────────────────────────────────────┤
│ • Por qué es viral?                 │
│ • Factores psicológicos             │
│ • Estrategia de renarraci\u00f3n        │
│ • Hooks optimizados                 │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   SCRIPT GENERATION (Gemini)        │
├─────────────────────────────────────┤
│ • Narrativa única (no copia)        │
│ • 55-60 segundos                    │
│ • COPPA compliant (kids safe)       │
│ • Call-to-action                    │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   TTS NARRATION (edge-tts)          │
├─────────────────────────────────────┤
│ • Voces naturales español           │
│ • Microsoft Neural                  │
│ • Gratis e ilimitado                │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   VIDEO COMPILATION (MoviePy)       │
├─────────────────────────────────────┤
│ • Video source descargado           │
│ • Audio overlay                     │
│ • 9:16 format                       │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   SHORTS OPTIMIZATION                │
├─────────────────────────────────────┤
│ • Subtítulos animados               │
│ • Efectos de retención              │
│ • Cortes rápidos                    │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   THUMBNAIL + UPLOAD                │
├─────────────────────────────────────┤
│ • AI thumbnail (Pollinations)       │
│ • YouTube API upload                │
│ • Metadata optimizado SEO           │
└─────────────────────────────────────┘
```

---

## 📦 Módulos Creados

### `/backend/pipeline/content_discovery.py`
Descubre contenido viral legal de múltiples fuentes:
- `discover_viral_content()`: Busca en YouTube CC, Reddit, Pexels
- `download_viral_video()`: Descarga el video seleccionado
- `ViralContent`: Clase con scoring algorithm

### `/backend/pipeline/viral_analyzer.py`
Analiza por qué el contenido es viral:
- `analyze_viral_content()`: Identifica factores psicológicos
- `generate_renarracion_script()`: Crea narrativa única

### `/backend/pipeline/shorts_optimizer.py`
Optimiza videos para máxima retención:
- `optimize_for_shorts()`: Formato 9:16, subtítulos, efectos
- `add_animated_subtitles()`: Subtítulos palabra por palabra

### `/backend/pipeline/pipeline_runner.py` (Actualizado)
Orquesta todo el flujo con 9 pasos:
1. Content Discovery
2. Viral Analysis
3. Script Generation
4. TTS Narration
5. Video Source Download
6. Video Compilation
7. Shorts Optimization
8. Thumbnail Generation
9. YouTube Upload

---

## 🔑 Configuración

### 1. Gemini API Key (Gratis)
```bash
# Obtén tu key aquí: https://aistudio.google.com/app/apikey
export GEMINI_API_KEY="AIzaSy..."
```

### 2. YouTube OAuth
Ya configurado en tu cuenta. Los tokens están en GitHub Secrets:
- `YT_CLIENT_ID`
- `YT_CLIENT_SECRET`
- `YT_REFRESH_TOKEN`

### 3. GitHub Secrets
Agrega en tu repo `roilt532/youauth` → Settings → Secrets:
```
GEMINI_API_KEY=AIzaSyCCIlk2lFa40CSDfRxmawHepRDGVrzKF80
YT_CLIENT_ID=<tu_client_id>
YT_CLIENT_SECRET=<tu_client_secret>
YT_REFRESH_TOKEN=<tu_refresh_token>
```

---

## 🚀 Uso

### Opción 1: GitHub Actions (Recomendado)
El workflow corre automáticamente:
- **Diario**: 5pm UTC
- **Variado**: Martes/Jueves 2:30pm UTC

O dispara manualmente:
1. Ve a GitHub → Actions → "YouTube Automation Daily"
2. Click en "Run workflow"
3. Selecciona opciones (content_type, language)

### Opción 2: Local
```bash
export GEMINI_API_KEY="tu_key"
export YT_CLIENT_ID="..."
export YT_CLIENT_SECRET="..."
export YT_REFRESH_TOKEN="..."

python automation/run_daily.py
```

---

## 🎯 Nichos Disponibles

- **`roblox`**: Gaming, clips de Roblox virales
- **`curiosity`**: Datos curiosos, ciencia, hechos asombrosos
- **`story`**: Historias de Reddit, cuentos cortos
- **`animated`**: Contenido animado para niños

---

## 📊 Métricas de Éxito

### Filtros de Contenido Viral
- ✅ Mínimo 100,000 views
- ✅ Al menos 1 año de antigüedad
- ✅ Duración: 10 seg - 5 min
- ✅ Licencia: Creative Commons o dominio público

### Scoring Algorithm
```python
viral_score = log10(views) * 10 + recency_bonus + duration_penalty
```

Factores:
- **Views**: Logarítmico (1M views = score 60)
- **Recency**: +20 si 1-3 años, +10 si >3 años
- **Duration**: Penaliza videos >3 min

---

## 🛠️ Tech Stack

### Backend
- **FastAPI**: API server
- **MoviePy**: Video editing
- **yt-dlp**: Video downloading
- **edge-tts**: Text-to-speech
- **Pillow**: Image processing
- **BeautifulSoup**: Web scraping

### IA Services
- **Google Gemini 1.5 Flash**: Script generation, viral analysis
- **Pollinations.ai**: AI thumbnails
- **Microsoft Neural TTS**: Natural voices

### Infrastructure
- **GitHub Actions**: Cron automation
- **MongoDB**: Data storage (opcional)

---

## 📈 Roadmap Futuro

- [ ] A/B testing de títulos
- [ ] Analytics dashboard
- [ ] Multi-channel support
- [ ] Auto-comment replies con IA
- [ ] Trending topics detector
- [ ] TikTok/Instagram reels export

---

## ⚠️ Importante

### Legal
- ✅ Solo usa contenido con licencia Creative Commons
- ✅ Agrega valor con renarraci\u00f3n única
- ✅ Cumple con COPPA (kids content)
- ✅ No viola copyright

### Costos
- ✅ **$0/mes**: Gemini free tier (1500 requests/day)
- ✅ **$0/mes**: edge-tts ilimitado
- ✅ **$0/mes**: Pollinations.ai gratis
- ✅ **$0/mes**: GitHub Actions (2000 min/mes)

### Rate Limits
- Gemini: 1500 requests/día (free tier)
- Reddit scraping: ~60 requests/minuto
- YouTube scraping: Ilimitado con yt-dlp

---

## 📞 Soporte

Si tienes problemas:
1. Revisa los logs en GitHub Actions
2. Verifica que GEMINI_API_KEY esté configurado
3. Asegúrate de que los tokens de YouTube sean válidos

---

## 🎉 ¡Listo!

Tu canal de YouTube está 100% automatizado con contenido viral legal. El sistema descubre, analiza, renarrá y sube videos diariamente sin intervención manual.

**Zero dependencias de Emergent. Zero costos. 100% automatizado.**
