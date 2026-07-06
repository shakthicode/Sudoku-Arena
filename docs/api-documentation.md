# 📡 API Documentation

**Sudoko-Arena REST API** — served by the local Python `backend/server.py` at `http://localhost:8888`.

---

## Base URL

```
http://localhost:8888
```

---

## Authentication

### Public Endpoints
No authentication required.

### User Mutation Endpoints
Require a session **Bearer Token** in the `Authorization` header:

```
Authorization: Bearer <session_token>
```

The token is issued on login and rotated on every new login session.

### Admin Endpoints
Require **HTTP Basic Authentication** using credentials stored in `.env`:

```
Authorization: Basic base64(ADMIN_USERNAME:ADMIN_PASSWORD)
```

---

## Endpoints

---

### 🟢 `POST /api/auth/register`

**Purpose:** Create a new user account.

**Authorization:** None required.

**Request Body:**
```json
{
  "username": "GridMaster",
  "email": "user@example.com",
  "password": "securepassword",
  "avatar": "🧩"
}
```

**Success Response `201`:**
```json
{
  "message": "Account created successfully",
  "user": {
    "id": "uuid-string",
    "username": "GridMaster",
    "email": "user@example.com",
    "avatar": "🧩",
    "level": 1,
    "xp": 0,
    "rank": "Novice",
    "token": "session-token-hex"
  }
}
```

**Error Responses:**
| Code | Reason |
|------|--------|
| 400  | Missing / invalid fields |
| 409  | Email or username already registered |

---

### 🟢 `POST /api/auth/login`

**Purpose:** Log in and receive a fresh session token.

**Authorization:** None required.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Success Response `200`:**
```json
{
  "message": "Login successful",
  "user": {
    "id": "uuid-string",
    "username": "GridMaster",
    "token": "new-session-token-hex",
    ...
  }
}
```

**Error Responses:**
| Code | Reason |
|------|--------|
| 400  | Missing email or password |
| 401  | No account found / Incorrect password |

---

### 🔒 `POST /api/users/update`

**Purpose:** Update the authenticated user's profile, XP, achievements, and stats.

**Authorization:** `Bearer <token>` (must match the user's active session token).

**Request Body:** Any non-protected fields. Protected fields (`id`, `email`, `password_hash`, `token`, `createdAt`) are silently ignored.

```json
{
  "id": "uuid-string",
  "level": 5,
  "xp": 2400,
  "rank": "Advanced",
  "achievements": ["first_victory", "speed_runner"]
}
```

**Success Response `200`:**
```json
{
  "message": "User updated",
  "user": { ... }
}
```

**Error Responses:**
| Code | Reason |
|------|--------|
| 400  | User ID missing |
| 401  | Invalid or expired token |
| 404  | User not found |

---

### 🔒 `POST /api/games/save`

**Purpose:** Save or update a game record for the authenticated user.

**Authorization:** `Bearer <token>`

**Request Body:**
```json
{
  "userId": "uuid-string",
  "gameId": "optional-game-uuid",
  "difficulty": "Hard",
  "status": "completed",
  "boardState": [[...]],
  "notesState": {},
  "timeElapsed": 342,
  "mistakesCount": 1,
  "hintsUsed": 2,
  "score": 4750,
  "won": true
}
```

**Success Response `200`:**
```json
{
  "message": "Game saved",
  "gameId": "game-uuid-string"
}
```

**Error Responses:**
| Code | Reason |
|------|--------|
| 400  | userId missing |
| 401  | Invalid token |

---

### 🔒 `POST /api/leaderboard/update`

**Purpose:** Submit or refresh the authenticated user's leaderboard score.

**Authorization:** `Bearer <token>`

**Request Body:**
```json
{
  "id": "uuid-string",
  "username": "GridMaster",
  "avatar": "🧩",
  "score": 24800,
  "games": 47
}
```

**Success Response `200`:**
```json
{
  "message": "Leaderboard updated",
  "rank": 3
}
```

**Error Responses:**
| Code | Reason |
|------|--------|
| 400  | User ID missing |
| 401  | Invalid token |

---

### 🟢 `GET /api/leaderboard`

**Purpose:** Retrieve the global leaderboard rankings.

**Authorization:** None required.

**Success Response `200`:**
```json
{
  "leaderboard": [
    {
      "id": "uuid",
      "username": "NeuralNinja",
      "avatar": "🤖",
      "score": 48200,
      "games": 342,
      "rank": 1
    }
  ]
}
```

---

### 🔑 `GET /api/users`

**Purpose:** Admin-only endpoint to retrieve all registered user profiles.

**Authorization:** HTTP Basic Auth (`ADMIN_USERNAME:ADMIN_PASSWORD` from `.env`)

**Success Response `200`:**
```json
{
  "users": [
    {
      "id": "uuid",
      "username": "GridMaster",
      "email": "user@example.com",
      "level": 5,
      "xp": 2400,
      "rank": "Advanced",
      "gamesPlayed": 23,
      "gamesWon": 19,
      "totalScore": 24800,
      "streak": 7
    }
  ],
  "total": 1
}
```
> ⚠️ **Note:** `password_hash` is always stripped from the response.

---

### 🔑 `GET /api/games`

**Purpose:** Admin-only endpoint to retrieve all game records.

**Authorization:** HTTP Basic Auth (without `?userId`) — OR user-scoped (with `?userId=<id>`).

**Query Parameters:**

| Param    | Required | Description |
|----------|----------|-------------|
| `userId` | Optional | If provided, returns games for that user only. |

**Success Response `200`:**
```json
{
  "games": {
    "user-uuid": [
      {
        "id": "game-uuid",
        "difficulty": "Hard",
        "status": "completed",
        "score": 4750,
        "timeElapsed": 342,
        "won": true,
        "savedAt": "2025-07-05T12:00:00Z"
      }
    ]
  }
}
```

---

## Error Format

All error responses follow this structure:

```json
{
  "error": "Human-readable error message"
}
```

## Status Code Summary

| Code | Meaning |
|------|---------|
| 200  | Success |
| 201  | Created |
| 204  | No Content (CORS preflight) |
| 400  | Bad Request |
| 401  | Unauthorized |
| 404  | Not Found |
| 409  | Conflict (duplicate) |
