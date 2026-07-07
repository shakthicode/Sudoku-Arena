# 📡 API Documentation

**Sudoko-Arena REST API** — served locally by [backend/server.py](../backend/server.py) at http://localhost:8888.

---

## Base URL

```text
http://localhost:8888
```

---

## Authentication

- Public endpoints do not require authentication.
- User mutation endpoints require a Bearer token in the Authorization header.
- Admin endpoints require HTTP Basic Auth using the credentials from [.env](../.env).

```text
Authorization: Bearer <session_token>
Authorization: Basic <base64(username:password)>
```

---

## Endpoints

### POST /api/auth/register

Create a new account.

Request body:

```json
{
  "username": "GridMaster",
  "email": "user@example.com",
  "password": "securepassword",
  "avatar": "🧩"
}
```

Success response `201`:

```json
{
  "message": "Account created successfully",
  "user": {
    "id": "uuid",
    "username": "GridMaster",
    "email": "user@example.com",
    "avatar": "🧩",
    "level": 1,
    "xp": 0,
    "rank": "Novice",
    "token": "session-token"
  }
}
```

---

### POST /api/auth/login

Authenticate a user and receive a new session token.

Request body:

```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

Success response `200`:

```json
{
  "message": "Login successful",
  "user": {
    "id": "uuid",
    "username": "GridMaster",
    "token": "session-token"
  }
}
```

---

### POST /api/users/update

Update a user's profile data, XP, achievements, and progress.

Authorization: Bearer token.

Example body:

```json
{
  "id": "uuid",
  "xp": 2400,
  "rank": "Advanced",
  "achievements": ["first_victory", "speed_runner"]
}
```

---

### POST /api/games/save

Save a completed or in-progress game record for the authenticated user.

Authorization: Bearer token.

Example body:

```json
{
  "userId": "uuid",
  "difficulty": "Hard",
  "status": "completed",
  "timeElapsed": 342,
  "mistakesCount": 1,
  "hintsUsed": 2,
  "score": 4750,
  "won": true
}
```

---

### GET /api/progress

Fetch the current campaign progress and any in-progress resume state for a user.

Authorization: Bearer token.

Response shape:

```json
{
  "progress": {
    "campaignProgress": { "Easy": 3 },
    "resumeProgress": {
      "difficulty": "Easy",
      "campaignPhase": "Easy",
      "campaignRound": 2,
      "isBoss": false
    }
  }
}
```

---

### POST /api/progress/save

Persist campaign progress and resume data for a user.

Authorization: Bearer token.

Example body:

```json
{
  "userId": "uuid",
  "campaignProgress": { "Easy": 3 },
  "resumeProgress": {
    "difficulty": "Easy",
    "campaignPhase": "Easy",
    "campaignRound": 2,
    "isBoss": false
  }
}
```

---

### GET /api/leaderboard

Fetch the current global leaderboard.

Response:

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

### POST /api/leaderboard/update

Update a user's leaderboard entry.

Authorization: Bearer token.

Example body:

```json
{
  "id": "uuid",
  "username": "GridMaster",
  "avatar": "🧩",
  "score": 24800,
  "games": 47
}
```

---

### GET /api/users

Admin-only endpoint to list all registered users.

Authorization: Basic Auth.

---

### GET /api/games

Admin-only endpoint to list stored game records.

Authorization: Basic Auth.

## Status Code Summary

| Code | Meaning                     |
| ---- | --------------------------- |
| 200  | Success                     |
| 201  | Created                     |
| 204  | No Content (CORS preflight) |
| 400  | Bad Request                 |
| 401  | Unauthorized                |
| 404  | Not Found                   |
| 409  | Conflict (duplicate)        |
