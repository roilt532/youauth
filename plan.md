# plan.md

## 1) Objectives
- Prove an end-to-end **fully automated daily pipeline**: topic → bilingual script (ES+EN) → TTS → video edit (Roblox clip + overlays) → thumbnail → YouTube upload.
- Use **free tooling only**: yt-dlp, FFmpeg, MoviePy, gTTS, Pillow, HuggingFace (optional), GitHub Actions, YouTube Data API v3.
- Ensure **kids-safe + COPPA** settings and implement **anti-detection posting behavior** (randomized schedule, varied metadata, gradual ramp).
- Build an MVP **dashboard (React + FastAPI + MongoDB)** to monitor runs, manage queues, templates, and failures.

## 2) Implementation Steps

### Phase 1 — Core Workflow POC (isolation; do not proceed until stable)
**Goal:** minimal scripts that generate & upload 1 video reliably.

User stories:
1. As an operator, I can run one command and get a finished video file generated locally.
2. As an operator, I can upload that video via YouTube API to my channel successfully.
3. As an operator, I can generate bilingual (ES+EN) narration that is synced to video length.
4. As an operator, I can take a Roblox source URL and transform it into a new edited clip with overlays.
5. As an operator, I can re-run the pipeline idempotently without duplicating uploads.

Steps:
1. **Web research**: confirm latest best practices for YouTube Data API upload quotas/scopes + “madeForKids” parameter, and GitHub Actions cron limitations.
2. Repo skeleton: `/poc` with Python scripts + `.env.example`.
3. **YouTube upload POC**
   - Create Google Cloud project, enable YouTube Data API v3.
   - OAuth client (Desktop App) and token caching.
   - Script `poc_upload.py`: upload a sample MP4 + set title/desc/tags/category + set `selfDeclaredMadeForKids=true`.
4. **Roblox clip ingest POC**
   - Script `poc_download_clip.py` using `yt-dlp` (supports YouTube/TikTok/etc. where legal/available).
   - Normalize to 1080x1920 (Shorts) and 60fps using FFmpeg.
5. **Script generation POC (LLM)**
   - Use **Gemini free tier** (or Emergent key if provided later) for: hook + story beats + CTA.
   - Output strict JSON: `{title_es,title_en,script_es,script_en,keywords}`.
6. **TTS POC**
   - Use `gTTS` for ES and EN; generate two tracks.
   - Simple strategy: ES first half + EN second half; compute durations.
7. **Video assembly POC**
   - MoviePy: place Roblox clip base + captions/subtitles + sound effects + background music (royalty-free).
   - Add transformations: speed ramps, zooms, cropping, emoji-like stickers (kid-safe), blur HUD.
8. **Thumbnail POC**
   - Pillow: bold text, high-contrast outline, character cutout (from SD/stock) + Roblox scene frame.
   - Save `thumb.jpg`.
9. **One-shot E2E POC runner**
   - `poc_run.py`: takes a source URL + topic, produces assets, uploads, and writes `run_artifacts.json`.
10. Stabilize: retries, logging, deterministic filenames, and clean failure modes.

Exit gate (must pass): one successful run on a developer machine + one successful run on GitHub Actions (manual dispatch).

---

### Phase 2 — V1 App Development (build around proven core)
**Goal:** dashboard + queue + scheduled runs; no advanced auth initially.

User stories:
1. As an operator, I can see a dashboard of last runs (success/fail, logs, video URL).
2. As an operator, I can add a “content job” (Roblox URL + topic + style template) to a queue.
3. As an operator, I can configure posting window (e.g., 15:00–20:00) and the system picks a random time.
4. As an operator, I can preview generated title/thumbnail before upload (optional approve toggle).
5. As an operator, I can re-run a failed job with one click.

Build:
1. Backend (FastAPI):
   - Models: Job, Run, Template, Asset.
   - Endpoints: create job, list queue, run now, fetch logs/artifacts.
   - Worker interface: call the proven pipeline module from Phase 1.
2. DB (MongoDB): store jobs, templates, run history, dedupe hashes.
3. Frontend (React): queue page, run history, template editor (prompt + video style), settings.
4. GitHub Actions:
   - Workflow: daily schedule + manual dispatch.
   - Caching for python deps; artifact upload of logs.
5. Anti-detection behaviors (MVP):
   - Randomized schedule within a window; varied title patterns; tag rotation; gradual ramp (start 3–4/wk then daily).
   - Rate limiting and max 1 upload/day initially.
6. COPPA defaults: always set made-for-kids; disable comments if desired; kid-safe descriptions.

Conclude Phase 2: 1 round end-to-end testing of dashboard → queue job → action run → upload.

---

### Phase 3 — Feature Expansion (virality + reliability)
User stories:
1. As an operator, I can switch between formats: Shorts (9:16) and Long (16:9).
2. As an operator, I can run multiple content “series” (Roblox, curiosities, mini-stories) with different templates.
3. As an operator, I can auto-generate captions (burn-in) and on-screen bilingual toggles.
4. As an operator, I can enforce a kid-safe filter list (banned words/topics).
5. As an operator, I can see basic analytics per upload (views/retention proxy) and best-performing templates.

Add:
- Template library for hooks (kid-focused), sound effects pack, caption styles.
- Better transformation for fair-use: commentary density, cuts, overlays, pacing changes, on-screen educational framing.
- Content sourcing rules (allowlist domains; avoid risky sources).
- Analytics ingestion via YouTube API (quota-aware) and “winner template” suggestions.
- Robust retry/backoff; job locking; duplicate detection.

Conclude Phase 3: E2E testing across 3 queued jobs and two templates.

---

### Phase 4 — Hardening + Optional Auth
User stories:
1. As an operator, I can restrict dashboard access (login) so my channel settings are protected.
2. As an operator, I can rotate secrets safely without breaking automation.
3. As an operator, I can export/import templates and jobs.
4. As an operator, I can run a “dry-run” that generates assets but does not upload.
5. As an operator, I can see alerts when quotas/errors happen.

Add:
- Auth (simple JWT) + role-based admin.
- Secrets handling guidance: GitHub Secrets + local `.env`.
- Alerting (email/webhook) on failures.
- Compliance checklist for kids content + internal audit log.

## 3) Next Actions (what you do now)
1. Create Google Cloud project → enable YouTube Data API v3 → create OAuth client.
2. Provide/prepare: channel email (for OAuth consent), intended upload category, default language settings.
3. Create GitHub repo and add Secrets placeholders: `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN` (or token file), plus any LLM key if used.
4. Choose 5 seed Roblox source URLs (safe, kid-friendly) for POC testing.
5. Confirm posting format priority: **Shorts-first** (recommended for kids + Roblox) vs mixed.

## 4) Success Criteria
- POC: 1-click run produces MP4 + thumbnail and **uploads successfully** with made-for-kids flag.
- V1: dashboard can queue jobs, run daily via GitHub Actions, and show run history with artifacts.
- Reliability: ≥ 90% successful daily runs over 14 days (with retries) and no duplicate uploads.
- Compliance: videos consistently marked made-for-kids; kid-safe language filter passes.
- Growth proxy: improved CTR/retention vs baseline after template iteration (tracked via analytics module).