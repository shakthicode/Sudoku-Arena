# 🏗️ System Architecture Documentation

This document describes the high-level architecture, flowcharts, and backend integrations of **Sudoko-Arena**.

---

## 🗺️ High-Level System Architecture

```mermaid
graph TD
    A[React SPA Frontend] -->|HTTP Requests| B[Python http.server Backend]
    B -->|Read / Write| C[(Local JSON Database)]
    C -->|users.json| D[Profiles & Auth]
    C -->|games.json| E[Match History]
    C -->|leaderboard.json| F[Global Rankings]
```

### 1. Frontend Layer
- **Technology Stack**: React 18, TailwindCSS CDN, Babel standalone parser, and Space Grotesk/Inter Google Fonts.
- **Engine Rules**: Custom algorithmic generator with backtracking solver to ensure single-solution boards across 5 difficulties: Easy, Medium, Hard, Expert, and Nightmare.
- **Routing**: Client-side state-based routing. Route guards protect paths `/dashboard`, `/game`, and `/results`.

### 2. Backend Layer
- **Technology Stack**: Single-threaded Python 3 HTTP REST engine built on `BaseHTTPRequestHandler`.
- **Database Persistence Layer**: Uses synchronized local JSON flat files using threading locks (`threading.Lock()`) to prevent race conditions during write/read operations.
- **Security Middleware**: Supports custom Basic HTTP Authentication validator for administrative routes and custom Bearer Token parser for standard API mutations.

---

## 🔄 Sequence Flows

### 1. Authentication & Auto-Logout Flow

```mermaid
sequenceDiagram
    actor User
    participant Browser as React SPA
    participant Server as Python API
    participant DB as JSON DB

    Note over Browser: Page Re-entry / Refresh Triggered
    Browser->>Browser: useEffect: force logout (clear session state)
    User->>Browser: Input Email & Password
    Browser->>Server: POST /api/auth/login
    Server->>DB: Read users.json & verify password (bcrypt check)
    alt Valid Credentials
        Server->>Server: Generate UUID session token
        Server->>DB: Write updated user session token
        Server-->>Browser: 200 OK + User profile & token
        Browser->>Browser: Store token in LocalStorage
    else Invalid Credentials
        Server-->>Browser: 401 Unauthorized (Error alert)
    end
```

### 2. Game Progress & Save Flow

```mermaid
sequenceDiagram
    actor Player
    participant Game as Game Loop (SPA)
    participant Server as Python API
    participant DB as JSON DB

    Player->>Game: Cell update / Notes mode toggled
    Game->>Game: Save Game State to LocalStorage (client caching)
    Note over Game: On Win / Loss / Abandon
    Game->>Server: POST /api/games/save (Authorization: Bearer token)
    Server->>Server: Verify token is valid
    alt Token Valid
        Server->>DB: Append/Update game in games.json
        Server-->>Game: 200 OK
    else Token Invalid / Missing
        Server-->>Game: 401 Unauthorized
    end
```

### 3. Leaderboard Submission Flow

```mermaid
sequenceDiagram
    actor Player
    participant SPA as React SPA
    participant Server as Python API
    participant DB as JSON DB

    SPA->>SPA: Calculate score (XP, time bonus, mistake penalty)
    SPA->>Server: POST /api/leaderboard/update (Authorization: Bearer token)
    Server->>Server: Verify session token matches payload
    alt Valid
        Server->>DB: Read leaderboard.json
        Server->>Server: Sort and assign rank (Top 50)
        Server->>DB: Write updated rankings
        Server-->>SPA: 200 OK (returns new global rank)
    else Invalid
        Server-->>SPA: 401 Unauthorized
    end
```
