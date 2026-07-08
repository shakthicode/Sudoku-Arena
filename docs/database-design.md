# 🗄️ Database Design Documentation

Sudoku-Arena currently uses **local JSON flat files** for lightweight persistence. This document covers the current schema, sample records, and a production migration strategy.

---

## Current Storage Engine

| Directory / File | Purpose |
|------|---------|
| `database/users/` | User profiles, authentication, progression |
| `database/games/` | Match history and board states |
| `database/leaderboard.json` | Global ranked leaderboard |

> ⚠️ The `database/` directory is excluded from version control via `.gitignore` to protect user privacy.

---

## 1. `users.json`

Stores all registered user accounts as a flat object keyed by UUID.

### Schema

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (UUID) | Unique user identifier |
| `username` | string | Display name (unique) |
| `email` | string | Login email (unique, lowercase) |
| `password_hash` | string | bcrypt hash (SHA-256 for legacy) |
| `token` | string | Current session Bearer token (rotated on login) |
| `avatar` | string | Emoji avatar |
| `level` | integer | Current level (1–100) |
| `xp` | integer | Total experience points |
| `rank` | string | Title: Novice → Grandmaster |
| `gamesPlayed` | integer | Total games started |
| `gamesWon` | integer | Total games won |
| `totalScore` | integer | Cumulative score |
| `bestTime` | integer \| null | Best completion time in seconds |
| `streak` | integer | Current daily streak |
| `maxStreak` | integer | All-time best streak |
| `hintsUsed` | integer | Total hints consumed |
| `achievements` | string[] | List of unlocked achievement IDs |
| `recentGames` | object[] | Last 10 game summaries |
| `streakDays` | string[] | ISO date strings of active streak days |
| `campaignProgress` | object | Map of difficulty/phase to completed rounds |
| `resumeProgress` | object \| null | Saved state for resuming the current game session |
| `createdAt` | ISO datetime | Account creation timestamp |
| `updatedAt` | ISO datetime | Last profile update timestamp |
| `lastLoginAt` | ISO datetime | Most recent successful login |

### Sample Record

```json
{
  "a1b2c3d4-...": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "username": "GridMaster",
    "email": "user@example.com",
    "password_hash": "$2b$12$...(bcrypt hash)...",
    "token": "3f9e2a1b4c8d7e6f...",
    "avatar": "🧩",
    "level": 5,
    "xp": 2400,
    "rank": "Advanced",
    "gamesPlayed": 23,
    "gamesWon": 19,
    "totalScore": 24800,
    "bestTime": 287,
    "streak": 7,
    "maxStreak": 14,
    "hintsUsed": 12,
    "achievements": ["first_victory", "speed_runner", "perfectionist"],
    "recentGames": [],
    "streakDays": ["2025-07-01", "2025-07-02"],
    "campaignProgress": {
      "Easy": 3
    },
    "resumeProgress": {
      "difficulty": "Easy",
      "campaignPhase": "Easy",
      "campaignRound": 2,
      "isBoss": false
    },
    "createdAt": "2025-06-01T10:00:00Z",
    "updatedAt": "2025-07-05T12:00:00Z",
    "lastLoginAt": "2025-07-05T11:55:00Z"
  }
}
```

---

## 2. `games.json`

Stores game history per user. Keyed by user UUID, each containing an array of game records (capped at 50).

### Schema

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (UUID) | Unique game session ID |
| `difficulty` | string | Easy / Medium / Hard / Expert / Nightmare |
| `status` | string | `in_progress`, `completed`, `abandoned` |
| `boardState` | number[][] | 9×9 board at time of save |
| `notesState` | object | Candidate note values per cell |
| `timeElapsed` | integer | Seconds elapsed |
| `mistakesCount` | integer | Number of mistakes (max 3) |
| `hintsUsed` | integer | Number of hints taken (max 5) |
| `score` | integer \| null | Final calculated score |
| `won` | boolean \| null | `true` = won, `false` = lost, `null` = in-progress |
| `savedAt` | ISO datetime | Timestamp of last save |

### Sample Record

```json
{
  "a1b2c3d4-...": [
    {
      "id": "game-uuid-string",
      "difficulty": "Hard",
      "status": "completed",
      "boardState": [[5,3,4,6,7,8,9,1,2], ...],
      "notesState": {},
      "timeElapsed": 342,
      "mistakesCount": 1,
      "hintsUsed": 2,
      "score": 4750,
      "won": true,
      "savedAt": "2025-07-05T12:34:56Z"
    }
  ]
}
```

---

## 3. `leaderboard.json`

Stores a flat, sorted array of the top-ranked players.

### Schema

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (UUID) | User ID |
| `username` | string | Display name |
| `avatar` | string | Emoji avatar |
| `score` | integer | Total cumulative score |
| `games` | integer | Total games played |
| `rank` | integer | Computed rank position (1 = highest) |

### Sample Record

```json
[
  {
    "id": "uuid-string",
    "username": "NeuralNinja",
    "avatar": "🤖",
    "score": 48200,
    "games": 342,
    "rank": 1
  }
]
```

---

## Production Database Migration

### Why Migrate?

The JSON flat file approach works well for a single-user local environment but has critical limitations at scale:

| Concern | JSON Files | PostgreSQL |
|---------|-----------|------------|
| Concurrency | Single-threaded lock | ACID transactions |
| Query capability | None (full file read) | SQL indexing |
| Data integrity | No foreign keys | Enforced relational integrity |
| Scalability | Files on disk | Connection pooling |

---

### Recommended PostgreSQL Schema

```sql
-- ── Users ──────────────────────────────────────────────────────────────────
CREATE TABLE users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username      VARCHAR(50)  UNIQUE NOT NULL,
    email         VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    session_token VARCHAR(255),
    avatar        VARCHAR(10)  DEFAULT '🧩',
    level         INT          DEFAULT 1,
    xp            INT          DEFAULT 0,
    rank          VARCHAR(30)  DEFAULT 'Novice',
    games_played  INT          DEFAULT 0,
    games_won     INT          DEFAULT 0,
    total_score   INT          DEFAULT 0,
    best_time     INT,
    streak        INT          DEFAULT 0,
    max_streak    INT          DEFAULT 0,
    hints_used    INT          DEFAULT 0,
    created_at    TIMESTAMPTZ  DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  DEFAULT NOW(),
    last_login_at TIMESTAMPTZ
);

-- ── Achievements ────────────────────────────────────────────────────────────
CREATE TABLE user_achievements (
    user_id        UUID REFERENCES users(id) ON DELETE CASCADE,
    achievement_id VARCHAR(50) NOT NULL,
    unlocked_at    TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, achievement_id)
);

-- ── Game Records ────────────────────────────────────────────────────────────
CREATE TABLE games (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    difficulty      VARCHAR(20) NOT NULL,
    status          VARCHAR(20) DEFAULT 'in_progress',
    time_elapsed    INT         DEFAULT 0,
    mistakes_count  INT         DEFAULT 0,
    hints_used      INT         DEFAULT 0,
    score           INT,
    won             BOOLEAN,
    saved_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_games_user_id ON games(user_id);
CREATE INDEX idx_games_difficulty ON games(difficulty);

-- ── Leaderboard View ────────────────────────────────────────────────────────
CREATE VIEW leaderboard AS
    SELECT
        id,
        username,
        avatar,
        total_score  AS score,
        games_played AS games,
        RANK() OVER (ORDER BY total_score DESC) AS rank
    FROM users
    ORDER BY total_score DESC;
```

### Migration Steps

1. **Set up PostgreSQL** locally or via cloud (Supabase/Railway/Render).
2. **Run the schema SQL** above to create tables.
3. **Migrate existing data** from `data/users.json` and `data/games.json` using a one-time Python migration script.
4. **Update `server.py`** to use `psycopg2` or `SQLAlchemy` instead of JSON reads/writes.
5. **Update `.env`** to include `DATABASE_URL`.
6. **Remove JSON dependency** after validation.
