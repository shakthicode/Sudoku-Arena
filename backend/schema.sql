-- ============================================================
-- Sudoko-Arena – PostgreSQL Database Schema
-- For Spring Boot backend integration
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- USERS
-- ============================================================
CREATE TABLE users (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username      VARCHAR(32)  NOT NULL UNIQUE,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,  -- BCrypt
    avatar        VARCHAR(10)  NOT NULL DEFAULT '🧩',
    level         INTEGER      NOT NULL DEFAULT 1,
    xp            INTEGER      NOT NULL DEFAULT 0,
    rank          VARCHAR(32)  NOT NULL DEFAULT 'Novice',
    games_played  INTEGER      NOT NULL DEFAULT 0,
    games_won     INTEGER      NOT NULL DEFAULT 0,
    total_score   BIGINT       NOT NULL DEFAULT 0,
    best_time_sec INTEGER,
    streak        INTEGER      NOT NULL DEFAULT 0,
    max_streak    INTEGER      NOT NULL DEFAULT 0,
    hints_used    INTEGER      NOT NULL DEFAULT 0,
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMPTZ
);

CREATE INDEX idx_users_email    ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_total_score ON users(total_score DESC);

-- ============================================================
-- PUZZLES
-- ============================================================
CREATE TABLE puzzles (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    puzzle_data     CHAR(81)    NOT NULL,  -- 81-char string, 0=empty
    solution_data   CHAR(81)    NOT NULL,
    difficulty      VARCHAR(16) NOT NULL CHECK (difficulty IN ('Easy','Medium','Hard','Expert','Nightmare')),
    cells_filled    INTEGER     NOT NULL,
    is_daily        BOOLEAN     NOT NULL DEFAULT FALSE,
    daily_date      DATE,                  -- set when is_daily=TRUE
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_puzzles_daily ON puzzles(daily_date) WHERE is_daily = TRUE;
CREATE INDEX idx_puzzles_difficulty ON puzzles(difficulty);

-- ============================================================
-- GAMES
-- ============================================================
CREATE TABLE games (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id        UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    puzzle_id      UUID        NOT NULL REFERENCES puzzles(id),
    difficulty     VARCHAR(16) NOT NULL,
    status         VARCHAR(16) NOT NULL DEFAULT 'in_progress'
                   CHECK (status IN ('in_progress','completed','abandoned','failed')),
    -- Saved state (for auto-resume)
    board_state    CHAR(81),
    notes_state    TEXT,       -- JSON: 9x9 array of candidate arrays
    -- Progress
    time_elapsed   INTEGER     NOT NULL DEFAULT 0,  -- seconds
    mistakes_count INTEGER     NOT NULL DEFAULT 0,
    hints_used     INTEGER     NOT NULL DEFAULT 0,
    undo_count     INTEGER     NOT NULL DEFAULT 0,
    -- Result
    score          INTEGER,
    won            BOOLEAN,
    completed_at   TIMESTAMPTZ,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_games_user_id   ON games(user_id);
CREATE INDEX idx_games_puzzle_id ON games(puzzle_id);
CREATE INDEX idx_games_status    ON games(status);
CREATE INDEX idx_games_created_at ON games(created_at DESC);

-- ============================================================
-- SCORES
-- ============================================================
CREATE TABLE scores (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id         UUID    NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    user_id         UUID    NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    base_score      INTEGER NOT NULL DEFAULT 0,
    difficulty_bonus INTEGER NOT NULL DEFAULT 0,
    time_penalty    INTEGER NOT NULL DEFAULT 0,
    hint_penalty    INTEGER NOT NULL DEFAULT 0,
    mistake_penalty INTEGER NOT NULL DEFAULT 0,
    total_score     INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_scores_user_id ON scores(user_id);
CREATE INDEX idx_scores_total   ON scores(total_score DESC);

-- ============================================================
-- ACHIEVEMENTS
-- ============================================================
CREATE TABLE achievements (
    id          VARCHAR(64) PRIMARY KEY,
    name        VARCHAR(128) NOT NULL,
    description TEXT         NOT NULL,
    icon        VARCHAR(10)  NOT NULL,
    rarity      VARCHAR(16)  NOT NULL CHECK (rarity IN ('common','uncommon','rare','legendary')),
    xp_reward   INTEGER      NOT NULL DEFAULT 50
);

-- Seed achievements
INSERT INTO achievements (id, name, description, icon, rarity, xp_reward) VALUES
('first_victory',    'First Victory',       'Win your first game',                   '🏆', 'common',    100),
('speed_runner',     'Speed Runner',        'Finish a game in under 5 minutes',       '⚡', 'uncommon',  150),
('perfectionist',    'Perfectionist',       'Complete a game with zero mistakes',     '💎', 'rare',      250),
('genius',           'Genius',              'Complete Expert difficulty',             '🧠', 'rare',      300),
('nightmare_slayer', 'Nightmare Slayer',    'Complete Nightmare difficulty',          '👹', 'legendary', 500),
('consistent',       'Consistent Player',  'Maintain a 7-day streak',               '🔥', 'uncommon',  200),
('hint_free',        'Purist',              'Complete a game without hints',          '🎯', 'uncommon',  175),
('century',          'Century',             'Play 100 games',                         '💯', 'rare',      400),
('daily_warrior',    'Daily Warrior',       'Complete 30 daily challenges',           '📅', 'rare',      350),
('fast_5',           'Lightning',           'Complete 5 games in one day',            '🌩', 'uncommon',  200),
('no_undo',          'Iron Mind',           'Win without using undo',                 '🪨', 'uncommon',  175),
('comeback',         'Comeback Kid',        'Win after making 2 mistakes',            '💪', 'common',    100),
('early_bird',       'Early Bird',          'Play before 8 AM',                       '🌅', 'common',    75),
('night_owl',        'Night Owl',           'Play after midnight',                    '🦉', 'common',    75),
('weekender',        'Weekend Warrior',     'Play on the weekend',                    '🎉', 'common',    75);

-- ============================================================
-- USER ACHIEVEMENTS (junction)
-- ============================================================
CREATE TABLE user_achievements (
    user_id        UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    achievement_id VARCHAR(64) NOT NULL REFERENCES achievements(id),
    unlocked_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, achievement_id)
);

CREATE INDEX idx_user_achievements_user ON user_achievements(user_id);

-- ============================================================
-- STREAKS
-- ============================================================
CREATE TABLE streaks (
    id           UUID  PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id      UUID  NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    streak_date  DATE  NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, streak_date)
);

CREATE INDEX idx_streaks_user_id ON streaks(user_id);
CREATE INDEX idx_streaks_date    ON streaks(streak_date);

-- ============================================================
-- LEADERBOARD SNAPSHOTS (materialized for performance)
-- ============================================================
CREATE TABLE leaderboard_snapshots (
    id           UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id      UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    period_type  VARCHAR(16) NOT NULL CHECK (period_type IN ('global','weekly','monthly','daily')),
    period_key   VARCHAR(32),  -- '2025-W27' for weekly, '2025-07' for monthly, '2025-07-03' for daily
    rank         INTEGER     NOT NULL,
    score        BIGINT      NOT NULL,
    games_played INTEGER     NOT NULL DEFAULT 0,
    computed_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_lb_unique ON leaderboard_snapshots(user_id, period_type, period_key);
CREATE INDEX idx_lb_period ON leaderboard_snapshots(period_type, period_key, rank);

-- ============================================================
-- REFRESH TOKEN TABLE (for JWT refresh)
-- ============================================================
CREATE TABLE refresh_tokens (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  VARCHAR(255) NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ  NOT NULL,
    revoked     BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_refresh_tokens_user   ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_hash   ON refresh_tokens(token_hash);

-- ============================================================
-- TRIGGER: auto-update updated_at
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at  BEFORE UPDATE ON users  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_games_updated_at  BEFORE UPDATE ON games  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- VIEWS
-- ============================================================

-- Global leaderboard view
CREATE OR REPLACE VIEW view_global_leaderboard AS
SELECT
    u.id, u.username, u.avatar, u.rank, u.total_score, u.games_played, u.games_won,
    RANK() OVER (ORDER BY u.total_score DESC) AS global_rank
FROM users u
WHERE u.is_active = TRUE;

-- Weekly leaderboard
CREATE OR REPLACE VIEW view_weekly_leaderboard AS
SELECT
    u.id, u.username, u.avatar,
    COALESCE(SUM(s.total_score), 0) AS weekly_score,
    COUNT(g.id) AS weekly_games,
    RANK() OVER (ORDER BY COALESCE(SUM(s.total_score), 0) DESC) AS weekly_rank
FROM users u
LEFT JOIN games  g ON g.user_id = u.id AND g.completed_at >= DATE_TRUNC('week', NOW()) AND g.status = 'completed'
LEFT JOIN scores s ON s.game_id = g.id
WHERE u.is_active = TRUE
GROUP BY u.id, u.username, u.avatar;
