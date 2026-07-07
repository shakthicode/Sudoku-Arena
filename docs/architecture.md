# 🏗️ System Architecture Documentation

This document reflects the current implementation of Sudoko-Arena: a browser-based game served from a single HTML frontend, backed by a Python HTTP server and JSON files.

---

## 🗺️ High-Level Architecture

```text
Browser UI (frontend/index.html)
        │
        ▼
Python HTTP API (backend/server.py)
        │
        ▼
Local JSON storage (database/)
```

### Frontend layer

- A single-page UI built in [frontend/index.html](../frontend/index.html)
- Uses React via CDN, Tailwind CSS, and Babel for in-browser JSX compilation
- Handles gameplay, auth forms, leaderboard views, campaign progression, and results screens

### Backend layer

- A lightweight Python server built on BaseHTTPRequestHandler
- Serves the frontend and exposes JSON REST endpoints
- Validates Bearer tokens for user actions and Basic Auth for admin actions
- Persists user, game, leaderboard, and resume-progress data in JSON files

### Persistence layer

- [database/users](../database/users) stores per-user JSON profiles
- [database/games](../database/games) stores per-user game history
- [database/leaderboard.json](../database/leaderboard.json) stores leaderboard state

---

## 🔄 Main Flows

### Authentication flow

1. The browser sends credentials to POST /api/auth/register or POST /api/auth/login
2. The server verifies the password and issues a UUID-based session token
3. The frontend stores the token locally and sends it back on protected calls

### Game flow

1. The frontend generates or restores a puzzle
2. The user plays the board, uses notes/undo/hints, and the browser keeps local state up to date
3. On win or loss, the UI sends a game result to POST /api/games/save
4. The server updates the per-user game record and updates the saved scoreboard state

### Resume progress flow

1. The frontend calls GET /api/progress after a sign-in to restore campaign state
2. The server reads the user's saved resume-progress payload from the user JSON file
3. The game page rehydrates the board, notes, time spent, and campaign context

### Leaderboard flow

1. The frontend calculates the score after the game ends
2. It sends the result to POST /api/leaderboard/update
3. The server updates the JSON leaderboard and returns the new ranking

---

## 🔐 Security Notes

- Passwords are hashed with bcrypt when available and can fall back to SHA-256 for legacy compatibility
- User IDs are validated as UUIDs before filesystem access to reduce path traversal risk
- Admin routes are protected with HTTP Basic Auth
- Protected game and progress mutations require a valid Bearer token

---

## 🧪 Runtime Notes

The local launcher in [run.bat](../run.bat) starts the Python server and opens the app in the browser. The app is designed to run locally without any external database service.
