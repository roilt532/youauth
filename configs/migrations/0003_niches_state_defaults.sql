-- Fix NULL values left by the old schema that lacked NOT NULL DEFAULT constraints.
-- Turso HRANA batch does not use a unified atomic commit for DDL, so we cannot
-- safely DROP TABLE niches_state (FK from jobs blocks it). Instead we UPDATE
-- existing NULLs to the correct defaults. Fresh-install DBs already have NOT NULL
-- DEFAULT via 0001, so this UPDATE is a no-op for them.
-- paused is set to 1 for any row where it was NULL (opt-in safety default).
-- Also cleans up niches_state_new if it was left by a previously aborted migration.

DROP TABLE IF EXISTS niches_state_new;

UPDATE niches_state
SET
    consecutive_failures   = COALESCE(consecutive_failures, 0),
    total_videos_generated = COALESCE(total_videos_generated, 0),
    total_uploads          = COALESCE(total_uploads, 0),
    paused                 = COALESCE(paused, 1)
WHERE consecutive_failures IS NULL
   OR total_videos_generated IS NULL
   OR total_uploads IS NULL
   OR paused IS NULL;
