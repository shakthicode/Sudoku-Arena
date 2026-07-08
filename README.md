# 🧩 Sudoko-Arena

> A polished local-first Sudoku experience with a Python backend, a single-page frontend, persistent user progress, daily challenges, and a lightweight leaderboard system.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen?logo=python)](https://python.org)
[![React 18](https://img.shields.io/badge/React-18-61dafb?logo=react)](https://react.dev)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-v3-38bdf8?logo=tailwindcss)](https://tailwindcss.com)
[![bcrypt](https://img.shields.io/badge/Auth-bcrypt-orange)](https://pypi.org/project/bcrypt/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

---

## 📸 Current Screenshots

The repository already includes a set of screenshot assets in [screenshots](screenshots). The current files are:

- [screenshots/Admin login page.png](screenshots/Admin%20login%20page.png)
- [screenshots/Admin panel.png](screenshots/Admin%20panel.png)
- [screenshots/Campaign.png](screenshots/Campaign.png)
- [screenshots/Daily Challenge.png](screenshots/Daily%20Challenge.png)
- [screenshots/Dashboard.png](screenshots/Dashboard.png)
- [screenshots/Game.png](screenshots/Game.png)
- [screenshots/Leaderboard.png](screenshots/Leaderboard.png)
- [screenshots/Login.png](screenshots/Login.png)
- [screenshots/profile.png](screenshots/profile.png)
- [screenshots/Result.png](screenshots/Result.png)

---

## ✨ What is in this repo

- A single-page game experience in [frontend/index.html](frontend/index.html)
- A lightweight Python API in [backend/server.py](backend/server.py)
- Per-user JSON persistence under [database](database)
- Automated tests in [tests/test_server.py](tests/test_server.py)
- A Windows launcher in [run.bat](run.bat)

### Core features

- Unique Sudoku puzzle generation with a backtracking solver
- Smart hints with move explanations
- Daily challenge mode
- Campaign progression with boss rounds
- Notes mode, undo/redo, and restart flow
- XP, achievements, streak tracking, and leaderboard updates
- User auth with bcrypt and admin access via HTTP Basic Auth
- Resume progress saving for signed-in users
- Responsive glassmorphism UI for desktop and mobile

---

## 🛠️ Tech Stack

### Frontend

- React 18 via CDN
- Tailwind CSS via CDN
- Babel Standalone for JSX in the browser
- Custom CSS and animation layers for the game UI

### Backend

- Python 3 with the standard library HTTP server
- bcrypt for password hashing
- python-dotenv for environment loading
- UUID-based session tokens and JSON persistence

### Storage

- [database/users](database/users) for per-user profile data
- [database/games](database/games) for saved game history
- [database/leaderboard.json](database/leaderboard.json) for leaderboard snapshots

---

## 🏗️ Architecture

```text
Browser UI (frontend/index.html)
        │
        ▼
Python HTTP API (backend/server.py)
        │
        ▼
Local JSON storage (database/)
```

The frontend sends REST requests to the backend, and the backend reads and writes JSON files for users, games, leaderboard data, and per-user resume progress.

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** available on your PATH — download from [python.org](https://www.python.org/downloads/) and check **"Add python.exe to PATH"** during installation

### 1. Configure the app

```bash
copy .env.example .env
```

Optionally update [.env](.env) values:

```env
PORT=8888
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change_me_in_production
```

### 2. Launch (Windows — Recommended)

**Simply double-click `run.bat`.** The launcher will automatically:

- ✅ Validate your Python version (3.10+ required)
- ✅ Create an isolated `.venv` virtual environment
- ✅ Install `bcrypt` and `python-dotenv` on first run
- ✅ Detect and resolve any port conflicts
- ✅ Start the backend server in the background
- ✅ Wait until the server is ready
- ✅ Open `http://127.0.0.1:8888` in your default browser
- ✅ Cleanly shut down on ENTER keypress

```cmd
run.bat
```

### 3. Manual Launch (any platform)

```bash
# Install dependencies once
pip install -r requirements.txt

# Start the server
python backend/server.py
```

Then open `http://127.0.0.1:8888` in your browser.

> 💡 See [docs/launcher-documentation.md](docs/launcher-documentation.md) for the silent launch and Windows installer packaging guides.

### 4. Build & Local Preview

To verify the production build pipeline locally:

```bash
# Clean install (creates node_modules context if needed)
npm install

# Compile the static frontend assets to dist/
npm run build

# Start a local preview server on the compiled build
npm run preview
```

---

## 🌐 Netlify Deployment

Sudoko-Arena is fully prepared for cloud deployment on **Netlify**.

### Deployment Settings:
- **Build Command**: `npm run build`
- **Publish Directory**: `dist`
- **Environment Variables**: No sensitive backend variables are required in the Netlify cloud since the hosted frontend executes entirely client-side and dynamically falls back to `localStorage` for offline gameplay.
- **API Redirection**: SPA routing and redirects are automatically configured during the build script using a generated `dist/_redirects` rule.

---

## 📡 API Reference

The full REST reference is in [docs/api-documentation.md](docs/api-documentation.md).

Main endpoints:

- POST /api/auth/register
- POST /api/auth/login
- POST /api/users/update
- POST /api/games/save
- GET /api/progress
- POST /api/progress/save
- GET /api/leaderboard
- POST /api/leaderboard/update
- GET /api/users (admin)
- GET /api/games (admin)

---

## 📂 Project Structure

```text
Sudoko-Arena/
├── backend/                      # Python REST API
│   ├── server.py                 # HTTP request handler & routes
│   └── schema.sql                # SQL schema reference (future DB)
├── database/                     # JSON flat-file persistence (git-ignored)
│   ├── users/                    # Per-user profile files
│   ├── games/                    # Per-user game history files
│   └── leaderboard.json          # Global leaderboard snapshot
├── docs/                         # Documentation
│   ├── api-documentation.md      # Full REST API reference
│   ├── architecture.md           # System architecture overview
│   ├── database-design.md        # Data model documentation
│   └── launcher-documentation.md # Windows launcher guide
├── frontend/                     # Single-page app entry point
│   └── index.html                # React + TailwindCSS (CDN)
├── logs/                         # Runtime logs (git-ignored)
├── screenshots/                  # Screenshot assets
├── tests/                        # Pytest test suite
│   └── test_server.py            # 18 unit + integration tests
├── .env.example                  # Example environment variables
├── .gitignore                    # Excludes .venv, logs, database, secrets
├── requirements.txt              # Python dependencies (bcrypt, python-dotenv)
├── run.bat                       # 🚀 Windows release launcher
└── README.md                     # Project overview
```

---

## 🧪 Testing

Run the regression suite with:

```bash
python -m pytest tests/ -v
```

---

## 🗄️ Database and Migration Notes

The current implementation uses JSON files for local persistence. A PostgreSQL-oriented schema is still available in [backend/schema.sql](backend/schema.sql) as a migration reference for future backend evolution.

---

## 🔮 Future Directions

- Move the backend to a more production-oriented framework
- Add a real relational database layer
- Expand the admin tooling and analytics views
- Add richer mobile and offline support
