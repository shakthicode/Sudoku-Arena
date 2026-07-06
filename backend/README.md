# Sudoko-Arena – Spring Boot Backend Guide

> This document defines the REST API contract and Spring Boot setup instructions for wiring the frontend to a real backend.

---

## Tech Stack

| Layer          | Technology          |
|----------------|---------------------|
| Framework      | Spring Boot 3.x     |
| Language       | Java 21             |
| Database       | PostgreSQL 15+      |
| Auth           | JWT (JJWT library)  |
| Passwords      | BCrypt              |
| Build          | Maven / Gradle      |
| Migrations     | Flyway              |

---

## Project Setup

### 1. Clone & Configure

```bash
# application.properties
spring.datasource.url=jdbc:postgresql://localhost:5432/sudokoarena
spring.datasource.username=postgres
spring.datasource.password=yourpassword
spring.jpa.hibernate.ddl-auto=validate
spring.flyway.enabled=true
jwt.secret=your-256-bit-secret-key
jwt.expiration=86400000
jwt.refresh-expiration=604800000
```

### 2. Run Migrations

```bash
# Place schema.sql in src/main/resources/db/migration/V1__initial_schema.sql
mvn flyway:migrate
```

### 3. Start Server

```bash
mvn spring-boot:run
# Server runs on http://localhost:8080
```

---

## API Contract

### Base URL
```
http://localhost:8080/api/v1
```

### Authentication

All protected endpoints require:
```
Authorization: Bearer <jwt_token>
```

---

## Endpoints

### Auth

#### POST /auth/register
```json
Request:  { "username": "string", "email": "string", "password": "string", "avatar": "string" }
Response: { "token": "string", "refreshToken": "string", "user": { ...UserDTO } }
```

#### POST /auth/login
```json
Request:  { "email": "string", "password": "string" }
Response: { "token": "string", "refreshToken": "string", "user": { ...UserDTO } }
```

#### POST /auth/refresh
```json
Request:  { "refreshToken": "string" }
Response: { "token": "string" }
```

#### POST /auth/logout
```json
Request:  { "refreshToken": "string" }
Response: { "message": "Logged out" }
```

---

### Users

#### GET /users/me *(protected)*
```json
Response: { UserDTO }
```

#### GET /users/{id}/stats
```json
Response: {
  "gamesPlayed": 42, "gamesWon": 35, "winRate": 83.3,
  "bestTime": 183, "totalScore": 48200, "streak": 7,
  "maxStreak": 14, "achievements": [...],
  "recentGames": [...], "difficultyBreakdown": {...}
}
```

---

### Puzzles

#### GET /puzzles/generate?difficulty=Medium *(protected)*
```json
Response: { "id": "uuid", "puzzleData": "81-char-string", "difficulty": "Medium", "cellsFilled": 35 }
```

#### GET /puzzles/daily
```json
Response: { "id": "uuid", "puzzleData": "81-char-string", "date": "2025-07-03", "difficulty": "Hard" }
```

---

### Games

#### POST /games *(protected)*
```json
Request:  { "puzzleId": "uuid", "difficulty": "Medium" }
Response: { "gameId": "uuid", "createdAt": "..." }
```

#### PUT /games/{id}/save *(protected)*
```json
Request:  {
  "boardState": "81-char-string",
  "notesState": "json-string",
  "timeElapsed": 245,
  "mistakesCount": 1,
  "hintsUsed": 0
}
Response: { "saved": true }
```

#### POST /games/{id}/complete *(protected)*
```json
Request:  { "timeElapsed": 720, "mistakesCount": 0, "hintsUsed": 1, "usedUndo": false }
Response: {
  "score": { "base": 500, "diffBonus": 350, "timePenalty": 60, "hintPenalty": 50, "total": 740 },
  "newAchievements": ["first_victory", "hint_free"],
  "xpGained": 740,
  "levelUp": false,
  "newRank": "Amateur"
}
```

#### GET /games/{id}/resume *(protected)*
```json
Response: { "boardState": "...", "notesState": "...", "timeElapsed": 245, "mistakesCount": 1, "hintsUsed": 0 }
```

---

### Hints

#### POST /games/{id}/hint *(protected)*
```json
Request:  { "row": 3, "col": 5, "currentBoard": "81-char-string" }
Response: { "number": 7, "reason": "The number 7 is the only valid option for this row." }
```

---

### Leaderboard

#### GET /leaderboard?type=global&page=0&size=50
```json
Response: {
  "content": [
    { "rank": 1, "userId": "uuid", "username": "NeuralNinja", "avatar": "🤖", "score": 48200, "gamesPlayed": 342 }
  ],
  "myRank": 15,
  "totalPlayers": 12480
}
```

#### GET /leaderboard/daily?date=2025-07-03

#### GET /leaderboard/weekly?week=2025-W27

#### GET /leaderboard/monthly?month=2025-07

---

### Achievements

#### GET /achievements *(protected)*
```json
Response: {
  "all": [...AchievementDTO],
  "unlocked": ["first_victory", "speed_runner"],
  "locked": ["genius", ...]
}
```

---

## Spring Boot Package Structure

```
src/main/java/com/sudokoarena/
├── SudokoArenaApplication.java
├── config/
│   ├── SecurityConfig.java         ← Spring Security + JWT filter
│   ├── JwtConfig.java
│   └── CorsConfig.java
├── controller/
│   ├── AuthController.java
│   ├── UserController.java
│   ├── PuzzleController.java
│   ├── GameController.java
│   ├── HintController.java
│   ├── LeaderboardController.java
│   └── AchievementController.java
├── service/
│   ├── AuthService.java
│   ├── UserService.java
│   ├── PuzzleGeneratorService.java  ← Port the JS backtracking algo to Java
│   ├── GameService.java
│   ├── ScoreService.java
│   ├── HintService.java
│   ├── AchievementService.java
│   └── LeaderboardService.java
├── repository/
│   ├── UserRepository.java
│   ├── PuzzleRepository.java
│   ├── GameRepository.java
│   ├── ScoreRepository.java
│   ├── AchievementRepository.java
│   └── LeaderboardRepository.java
├── model/
│   ├── User.java
│   ├── Puzzle.java
│   ├── Game.java
│   ├── Score.java
│   ├── Achievement.java
│   └── UserAchievement.java
├── dto/
│   ├── request/
│   │   ├── RegisterRequest.java
│   │   ├── LoginRequest.java
│   │   ├── SaveGameRequest.java
│   │   └── CompleteGameRequest.java
│   └── response/
│       ├── AuthResponse.java
│       ├── UserDTO.java
│       ├── GameResultDTO.java
│       └── LeaderboardDTO.java
├── security/
│   ├── JwtUtil.java
│   ├── JwtAuthFilter.java
│   └── UserDetailsServiceImpl.java
└── exception/
    ├── GlobalExceptionHandler.java
    ├── ResourceNotFoundException.java
    └── UnauthorizedException.java
```

---

## Connecting Frontend to Backend

In the frontend, replace the localStorage stubs in the API layer with real fetch calls:

```javascript
// Before (localStorage stub):
const user = LS.get('sv_user', null);

// After (real API):
const response = await fetch('http://localhost:8080/api/v1/users/me', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const user = await response.json();
```

All API calls are isolated in the app — the service layer in the codebase makes swapping trivial.

---

## Security Checklist

- [x] BCrypt password hashing (strength=12)
- [x] JWT with expiry + refresh tokens
- [x] CORS configured for frontend origin only
- [x] Input validation with `@Valid` + Bean Validation
- [x] SQL injection prevention via JPA repositories
- [x] Rate limiting via Spring AOP or Bucket4j
- [x] HTTPS in production (Render/Railway auto-provision)

---

## Deployment

### Frontend (Vercel)
```bash
# No build step needed — just deploy index.html
# Or use Vite for a proper build if migrating
```

### Backend (Render / Railway)
```bash
# Dockerfile
FROM eclipse-temurin:21-jre
COPY target/sudokoarena-*.jar app.jar
ENTRYPOINT ["java", "-jar", "/app.jar"]
```

### Database (Railway PostgreSQL / Supabase)
```
# Environment variables:
DATABASE_URL=postgresql://...
JWT_SECRET=...
```
