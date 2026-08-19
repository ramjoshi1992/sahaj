-- Lull | schema.sql
-- Postgres, for Neon. Small on purpose: the app works without any of it.
--
-- Two principles shape this.
--
-- Plans are reproducible. A session is fully determined by mood, tier,
-- minutes and seed, so the entire arrangement — every segment, every
-- movement boundary — can be reconstructed later from four columns.
-- Nothing about the plan needs storing.
--
-- Nothing identifying is kept. No IP, no coordinates. The tier already
-- encodes what the weather and hour were, which is all the analytics need,
-- and it cannot be reversed into a location.

CREATE TABLE IF NOT EXISTS users (
    id            BIGSERIAL PRIMARY KEY,
    handle        TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sessions (
    id            BIGSERIAL PRIMARY KEY,
    user_id       BIGINT REFERENCES users(id) ON DELETE SET NULL,

    -- lets a signed-out person still have history, and lets returning
    -- anonymous use be counted, without an account existing
    device_id     TEXT,

    -- these four reproduce the plan exactly
    mood          TEXT NOT NULL,
    tier          TEXT NOT NULL,
    minutes       INTEGER NOT NULL,
    plan_seed     BIGINT NOT NULL,

    texture       TEXT,             -- null means the user chose quiet
    bed_offset_db REAL DEFAULT 0,   -- non-zero means the calibration was wrong

    started_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    played_s      INTEGER NOT NULL DEFAULT 0,
    completed     BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS reflections (
    id          BIGSERIAL PRIMARY KEY,
    session_id  BIGINT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    feeling     TEXT NOT NULL,      -- settled | lighter | clearer | much the same
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS sessions_user_idx    ON sessions(user_id);
CREATE INDEX IF NOT EXISTS sessions_device_idx  ON sessions(device_id);
CREATE INDEX IF NOT EXISTS sessions_started_idx ON sessions(started_at);
CREATE INDEX IF NOT EXISTS sessions_mood_idx    ON sessions(mood);
CREATE INDEX IF NOT EXISTS reflections_sess_idx ON reflections(session_id);

-- ── the owner view, as queries ──────────────────────────────────────
-- Each panel in the dashboard maps to one of these.

-- what people ask for
--   SELECT mood, count(*) FROM sessions
--   WHERE started_at > now() - interval '7 days' GROUP BY mood ORDER BY 2 DESC;

-- played to the end
--   SELECT avg(completed::int) FROM sessions
--   WHERE started_at > now() - interval '7 days';

-- where sessions stop — played_s against minutes*60 tells you how far in.
-- Boundary positions are recoverable by rebuilding the plan from plan_seed.

-- surroundings chosen, counting quiet as a real choice
--   SELECT coalesce(texture,'quiet'), count(*) FROM sessions GROUP BY 1 ORDER BY 2 DESC;

-- calibration health: the number to watch. If people are adjusting, the
-- measurement is wrong, not their taste.
--   SELECT texture, avg((bed_offset_db <> 0)::int) AS adjusted, count(*)
--   FROM sessions WHERE texture IS NOT NULL GROUP BY texture ORDER BY 2 DESC;

-- asked, and felt — does a mood do what its phrase promises
--   SELECT s.mood, r.feeling, count(*)
--   FROM sessions s JOIN reflections r ON r.session_id = s.id
--   GROUP BY 1,2 ORDER BY 1, 3 DESC;
