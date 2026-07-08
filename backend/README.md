# Sudoku-Arena – Python Local REST API Server

> This document describes the **actual** backend for Sudoku-Arena: a lightweight Python 3 HTTP server that runs entirely on your local machine with no external services or databases required.

---

## Tech Stack

| Layer         | Technology                                  |
|---------------|---------------------------------------------|
| Language      | **Python 3** (stdlib only — no framework)   |
| HTTP Server   | `http.server.HTTPServer` (stdlib)           |
| Storage       | Local JSON files (`database/` folder)       |
| Auth          | UUID-based Bearer tokens (session tokens)   |
| Passwords     | `bcrypt` (preferred) or SHA-256 (fallback)  |
| Config        | `.env` file via `python-dotenv` (optional)  |
| Dependencies  | `bcrypt`, `python-dotenv` (both optional)   |

> **No Java. No Spring Boot. No PostgreSQL. No JWT library. No Maven.**  
> The entire server is a single file: `backend/server.py`.

---

## Project Structure

```
backend/
├── server.py          ← The entire REST API server (single file)
└── README.md          ← This file

database/              ← Auto-created on first run
├── users/             ← One JSON file per user  (e.g. <uuid>.json)
├── games/             ← One JSON file per user  (e.g. <uuid>.json)
└── leaderboard.json   ← Global leaderboard list
```

---

## Setup & Running

### Prerequisites

- Python 3.8+
- Optional (but recommended): `bcrypt` and `python-dotenv`

```bash
pip install bcrypt python-dotenv
```

If these are not installed, the server falls back gracefully:
- Passwords are hashed with SHA-256 instead of bcrypt.
- Environment variables are read directly from the OS.

### 1. Configure Environment

Copy `.env.example` to `.env` and set the port (optional):

```bash
# .env
PORT=8888
```

### 2. Start the Server

```bash
# From the project root:
python backend/server.py

# Or from inside the backend/ folder:
python server.py
```

The server binds to `http://127.0.0.1:8888` by default.

### 3. Open the App

Navigate to [http://127.0.0.1:8888](http://127.0.0.1:8888) in your browser.
The server serves `frontend/index.html` automatically.

---

## API Reference

### Base URL
```
http://127.0.0.1:8888/api
```

### Authentication

Protected endpoints require a Bearer token in the `Authorization` header.  
The token is returned by the `/api/auth/login` and `/api/auth/register` endpoints.

```
Authorization: Bearer <token>
```

---

## Endpoints

### Auth

#### `POST /api/auth/register`
```json
Request:
{
  "username": "string (min 3 chars)",
  "email":    "string",
  "password": "string (min 6 chars)",
  "avatar":   "string (emoji, optional)"
}

Response 201:
{
  "message": "Account created successfully",
  "user": { ...UserObject }
}

Response 400: { "error": "Username must be at least 3 characters" }
Response 409: { "error": "Email already registered" }
```

#### `POST /api/auth/login`
```json
Request:
{
  "email":    "string",
  "password": "string"
}

Response 200:
{
  "message": "Login successful",
  "user": { ...UserObject }
}

Response 401: { "error": "Incorrect password" }
```

---

### Users

#### `POST /api/users/update` *(Bearer token required)*
Updates user profile fields. Protected fields (`id`, `email`, `password_hash`, `token`, `createdAt`) are never overwritten.

```json
Request:
{
  "id":          "uuid",
  "username":    "string",
  "avatar":      "string",
  "level":       1,
  "xp":          0,
  "gamesPlayed": 0,
  ...
}

Response 200:
{
  "message": "User updated",
  "user": { ...UserObject }
}
```

---

### Games

#### `GET /api/games?userId=<uuid>`
Returns the saved game history for a user (up to 50 entries).

```json
Response 200:
{
  "games": [ ...GameEntry ]
}
```

#### `POST /api/games/save` *(Bearer token required)*
Saves or updates a game entry for a user.

```json
Request:
{
  "userId":       "uuid",
  "gameId":       "uuid (optional, generated if missing)",
  "difficulty":   "Easy | Medium | Hard | Expert",
  "status":       "in_progress | completed",
  "boardState":   "81-char string",
  "notesState":   "json-string",
  "timeElapsed":  245,
  "mistakesCount": 1,
  "hintsUsed":    0,
  "score":        1200,
  "won":          true
}

Response 200:
{
  "message": "Game saved",
  "gameId": "uuid"
}
```

---

### Progress

#### `GET /api/progress?userId=<uuid>` *(Bearer token required)*
Returns campaign and resume progress for a user.

```json
Response 200:
{
  "progress": {
    "campaignProgress": { ... },
    "resumeProgress":   { ... }
  }
}
```

#### `POST /api/progress/save` *(Bearer token required)*
Saves campaign and/or resume progress.

```json
Request:
{
  "userId":           "uuid",
  "campaignProgress": { ... },
  "resumeProgress":   { ... }
}

Response 200:
{
  "message": "Progress saved",
  "progress": { ... }
}
```

---

### Leaderboard

#### `GET /api/leaderboard`
Returns the full leaderboard sorted by score (public endpoint).

```json
Response 200:
{
  "leaderboard": [
    { "id": "uuid", "username": "...", "avatar": "🧩", "score": 4800, "games": 12, "level": 3, "rank": 1 },
    ...
  ]
}
```

#### `POST /api/leaderboard/update` *(Bearer token required)*
Upserts a user's leaderboard entry and re-ranks all players.

```json
Request:
{
  "id":     "uuid",
  "score":  4800,
  "games":  12
}

Response 200:
{
  "message": "Leaderboard updated",
  "rank": 1
}
```

---

## Data Storage

All data is stored as plain JSON files on your local filesystem — no database engine is needed.

| Location                        | Contents                              |
|---------------------------------|---------------------------------------|
| `database/users/<uuid>.json`    | Full user profile including password hash |
| `database/games/<uuid>.json`    | List of saved game entries per user   |
| `database/leaderboard.json`     | Global leaderboard array (ranked)     |

> **Password hashes** are never returned by any API endpoint. The `sanitize_user_data()` helper strips `password_hash` from all responses.

---

## Security

- **Path traversal protection:** All user IDs are validated as UUID v4 format before being used as filenames (prevents `../../etc/passwd` attacks).
- **Bearer token auth:** Each session generates a new UUID token stored in the user's JSON file. Tokens are rotated on every login.
- **Password hashing:** bcrypt with a random salt (strength 12) when available. Legacy SHA-256 hashes are automatically migrated to bcrypt on the user's next successful login.
- **CORS headers:** All responses include `Access-Control-Allow-Origin: *` for local development.
- **Protected fields:** The `/api/users/update` endpoint never overwrites `id`, `email`, `password_hash`, `token`, or `createdAt`.

---

## Running Tests

```bash
# From the project root:
python -m pytest tests/ -v
```

All 15 automated tests cover registration, login, progress save/load, and path traversal security guards.

---

## Offline / No-Server Mode

The server is **completely optional**. The frontend runs fully in the browser using `localStorage` as a fallback. If the server is not running, all user data (accounts, game saves, progress) is persisted in the browser's local storage automatically.
