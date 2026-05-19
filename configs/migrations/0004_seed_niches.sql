-- Seed the 5 niches used in the generate matrix.
-- science is active (paused=0), all others start paused (paused=1).
-- INSERT OR IGNORE makes this re-runnable without overwriting existing counters.

INSERT OR IGNORE INTO niches_state (niche_id, paused) VALUES
    ('science',          0),
    ('history',          1),
    ('mystery',          1),
    ('curiosities',      1),
    ('gaming_minecraft', 1);
