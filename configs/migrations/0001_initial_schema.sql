CREATE TABLE IF NOT EXISTS schema_versions (
    version     INTEGER PRIMARY KEY,
    applied_at  INTEGER NOT NULL,
    description TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS niches_state (
    niche_id                TEXT    PRIMARY KEY,
    last_run_at             INTEGER,
    last_success_at         INTEGER,
    consecutive_failures    INTEGER NOT NULL DEFAULT 0,
    total_videos_generated  INTEGER NOT NULL DEFAULT 0,
    total_uploads           INTEGER NOT NULL DEFAULT 0,
    paused                  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS jobs (
    id               TEXT    PRIMARY KEY,
    idempotency_key  TEXT    NOT NULL UNIQUE,
    niche_id         TEXT    NOT NULL REFERENCES niches_state(niche_id),
    status           TEXT    NOT NULL CHECK(status IN ('pending','running','done','failed')),
    run_id           TEXT,
    created_at       INTEGER NOT NULL,
    started_at       INTEGER,
    finished_at      INTEGER,
    error            TEXT
);

CREATE TABLE IF NOT EXISTS videos (
    id           TEXT    PRIMARY KEY,
    job_id       TEXT    NOT NULL UNIQUE REFERENCES jobs(id),
    niche_id     TEXT    NOT NULL,
    title        TEXT    NOT NULL,
    script_hash  TEXT    NOT NULL,
    file_sha256  TEXT,
    duration_s   INTEGER NOT NULL,
    r2_key       TEXT,
    r2_bucket    TEXT,
    created_at   INTEGER NOT NULL,
    status       TEXT    NOT NULL CHECK(status IN ('generated','stored','failed'))
);

CREATE TABLE IF NOT EXISTS uploads (
    id                TEXT    PRIMARY KEY,
    video_id          TEXT    NOT NULL UNIQUE REFERENCES videos(id),
    youtube_video_id  TEXT,
    status            TEXT    NOT NULL CHECK(status IN ('pending','uploading','done','failed')),
    privacy           TEXT    NOT NULL DEFAULT 'public',
    scheduled_for     INTEGER,
    uploaded_at       INTEGER,
    quota_units_used  INTEGER NOT NULL DEFAULT 0,
    error             TEXT
);

CREATE TABLE IF NOT EXISTS assets (
    id          TEXT    PRIMARY KEY,
    r2_key      TEXT    NOT NULL UNIQUE,
    asset_type  TEXT    NOT NULL CHECK(asset_type IN ('background','audio','font','model','thumbnail')),
    niche_id    TEXT,
    size_bytes  INTEGER NOT NULL,
    etag        TEXT    NOT NULL,
    verified_at INTEGER,
    created_at  INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS metrics (
    id               TEXT    PRIMARY KEY,
    youtube_video_id TEXT    NOT NULL,
    snapshot_at      INTEGER NOT NULL,
    views            INTEGER NOT NULL,
    likes            INTEGER NOT NULL,
    comments         INTEGER NOT NULL,
    watch_time_s     INTEGER,
    impressions      INTEGER,
    ctr_pct          REAL
);

CREATE INDEX IF NOT EXISTS idx_metrics_video_time
    ON metrics(youtube_video_id, snapshot_at DESC);

CREATE TABLE IF NOT EXISTS youtube_quota_usage (
    day             TEXT    PRIMARY KEY,
    units_consumed  INTEGER NOT NULL DEFAULT 0,
    uploads_count   INTEGER NOT NULL DEFAULT 0,
    last_reset_at   INTEGER NOT NULL
);
