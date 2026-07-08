"""
Sudoku-Arena – Secure Local REST API Server
==========================================
Serves index.html and handles user data via REST endpoints.
Data is persisted in database/users/, database/games/, database/leaderboard.json.

Security:
  - Admin credentials loaded from .env (never hardcoded)
  - Passwords stored as bcrypt hashes (SHA-256 migrated on login)
  - All mutating endpoints require Bearer token authorization
  - Admin endpoints require HTTP Basic Authentication
  - User IDs validated as UUID v4 before any filesystem path is constructed
"""

import json
import re
import os
import hashlib
import uuid
import sys
import base64
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone
import threading

# ── Optional dependency: python-dotenv ────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed – fall back to OS environment variables

# ── Optional dependency: bcrypt ───────────────────────────────────────────────
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False
    print("  [WARN]  bcrypt not installed. Run: pip install bcrypt")
    print("          Falling back to SHA-256 hashing (less secure).")

# Fix Unicode output on Windows terminals
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ── Environment-based configuration ───────────────────────────────────────────
PORT           = int(os.environ.get("PORT", 8888))

# ── File paths ─────────────────────────────────────────────────────────────────
BASE_DIR         = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(BASE_DIR) == "backend":
    ROOT_DIR     = os.path.dirname(BASE_DIR)
else:
    ROOT_DIR     = BASE_DIR

DATA_DIR         = os.path.join(ROOT_DIR, "database")
LEADERBOARD_FILE = os.path.join(DATA_DIR, "leaderboard.json")
INDEX_FILE       = os.path.join(ROOT_DIR, "frontend", "index.html")

os.makedirs(DATA_DIR, exist_ok=True)

# ── Thread-safe JSON file helpers ─────────────────────────────────────────────
_lock = threading.Lock()

def read_json(path, default):
    """Thread-safe JSON read with fallback default."""
    with _lock:
        if not os.path.exists(path):
            return default
        with open(path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return default

def write_json(path, data):
    """Thread-safe atomic JSON write."""
    with _lock:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

# ── Per-user storage helper functions ──────────────────────────────────────────
USERS_DIR = os.path.join(DATA_DIR, "users")
GAMES_DIR = os.path.join(DATA_DIR, "games")

os.makedirs(USERS_DIR, exist_ok=True)
os.makedirs(GAMES_DIR, exist_ok=True)

def read_user(user_id):
    """Read a specific user's JSON file."""
    path = os.path.join(USERS_DIR, f"{user_id}.json")
    return read_json(path, None)

def write_user(user_id, data):
    """Write a specific user's JSON file."""
    path = os.path.join(USERS_DIR, f"{user_id}.json")
    write_json(path, data)

def read_user_games(user_id):
    """Read a specific user's games JSON file."""
    path = os.path.join(GAMES_DIR, f"{user_id}.json")
    return read_json(path, [])

def write_user_games(user_id, data):
    """Write a specific user's games JSON file."""
    path = os.path.join(GAMES_DIR, f"{user_id}.json")
    write_json(path, data)

def read_all_users():
    """Read all user JSON files and return a consolidated dict."""
    users = {}
    if os.path.exists(USERS_DIR):
        for filename in os.listdir(USERS_DIR):
            if filename.endswith(".json"):
                uid = filename[:-5]
                u_data = read_user(uid)
                if u_data:
                    users[uid] = u_data
    return users

def read_all_games():
    """Read all games JSON files and return a consolidated dict."""
    games = {}
    if os.path.exists(GAMES_DIR):
        for filename in os.listdir(GAMES_DIR):
            if filename.endswith(".json"):
                uid = filename[:-5]
                games[uid] = read_user_games(uid)
    return games


def sanitize_user_data(user_data):
    """Return a safe user payload suitable for API responses."""
    if not isinstance(user_data, dict):
        return {}
    return {k: v for k, v in user_data.items() if k != "password_hash"}

# ── Migration of legacy monolithic database files ─────────────────────────────
def migrate_legacy_db():
    users_file = os.path.join(DATA_DIR, "users.json")
    games_file = os.path.join(DATA_DIR, "games.json")
    
    # Migrate users
    if os.path.exists(users_file):
        print("  📦  Migrating legacy users.json to per-user JSON files...")
        legacy_users = read_json(users_file, {})
        for uid, u_data in legacy_users.items():
            write_user(uid, u_data)
        try:
            os.rename(users_file, users_file + ".bak")
            print("  ✅  Successfully migrated users.json and renamed to users.json.bak")
        except Exception as e:
            print(f"  [WARN] Could not rename users.json: {e}")
            
    # Migrate games
    if os.path.exists(games_file):
        print("  📦  Migrating legacy games.json to per-user JSON files...")
        legacy_games = read_json(games_file, {})
        for uid, g_list in legacy_games.items():
            write_user_games(uid, g_list)
        try:
            os.rename(games_file, games_file + ".bak")
            print("  ✅  Successfully migrated games.json and renamed to games.json.bak")
        except Exception as e:
            print(f"  [WARN] Could not rename games.json: {e}")

migrate_legacy_db()

# ── UUID validation ───────────────────────────────────────────────────────────
_UUID_RE = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE
)

def is_valid_uuid(val):
    """Return True only if val is a canonical UUID string (8-4-4-4-12 hex).
    This prevents path-traversal attacks where an attacker could craft a
    user_id like '../../../etc/passwd' to escape the database directory.
    """
    return bool(val and isinstance(val, str) and _UUID_RE.match(val))


# ── Password hashing helpers ───────────────────────────────────────────────────

def hash_password(password):
    """
    Hash a plaintext password.
    Uses bcrypt if available; falls back to SHA-256.
    Returns a string suitable for storing in users.json.
    """
    if BCRYPT_AVAILABLE:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, stored_hash):
    """
    Verify a plaintext password against a stored hash.
    Supports both bcrypt ($2b$ prefix) and legacy SHA-256 hashes.
    Automatically migrates SHA-256 hashes to bcrypt on first successful login.
    """
    if stored_hash.startswith("$2b$") or stored_hash.startswith("$2a$"):
        # bcrypt hash
        if BCRYPT_AVAILABLE:
            return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
        return False
    # Legacy SHA-256 hash — compare directly
    return hashlib.sha256(password.encode()).hexdigest() == stored_hash

# ── Request Handler ────────────────────────────────────────────────────────────
class SudokuHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        """Custom compact logger with timestamp."""
        print(f"  [{datetime.now().strftime('%H:%M:%S')}]  {format % args}")

    def send_json(self, code, data):
        """Send a JSON response with CORS headers."""
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(body)

    def send_html(self):
        """Serve the main index.html file."""
        with open(INDEX_FILE, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_body(self):
        """Parse JSON request body safely."""
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {}

    # ── CORS preflight ──────────────────────────────────────────────────────
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    # ── GET ─────────────────────────────────────────────────────────────────
    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path

        # Serve index.html
        if path == "/" or path == "/index.html":
            self.send_html()
            return

        # GET /api/leaderboard  → public
        if path == "/api/leaderboard":
            lb = read_json(LEADERBOARD_FILE, [])
            self.send_json(200, {"leaderboard": lb})
            return

        # GET /api/games  → protected per-user endpoint (requires userId)
        if path == "/api/games":
            qs  = parse_qs(parsed.query)
            uid = qs.get("userId", [None])[0]
            if not uid:
                self.send_json(400, {"error": "userId required"})
                return
            if not is_valid_uuid(uid):
                self.send_json(400, {"error": "Invalid userId format"})
                return
            self.send_json(200, {"games": read_user_games(uid)})
            return

        # GET /api/progress → protected per-user progress endpoint
        if path == "/api/progress":
            qs = parse_qs(parsed.query)
            uid = qs.get("userId", [None])[0]
            if not uid:
                self.send_json(400, {"error": "userId required"})
                return
            if not is_valid_uuid(uid):
                self.send_json(400, {"error": "Invalid userId format"})
                return
            auth = self.headers.get("Authorization", "")
            if not auth.startswith("Bearer "):
                self.send_json(401, {"error": "Unauthorized access"})
                return
            req_token = auth[7:]
            user_data = read_user(uid)
            if not user_data or user_data.get("token") != req_token:
                self.send_json(401, {"error": "Unauthorized access"})
                return
            self.send_json(200, {"progress": {
                "campaignProgress": user_data.get("campaignProgress", {}),
                "resumeProgress": user_data.get("resumeProgress", None),
            }})
            return

        self.send_json(404, {"error": "Endpoint not found", "path": path})

    # ── POST ────────────────────────────────────────────────────────────────
    def do_POST(self):
        path = urlparse(self.path).path
        body = self.read_body()

        # ── POST /api/auth/register ──────────────────────────────────────
        if path == "/api/auth/register":
            username = (body.get("username") or "").strip()
            email    = (body.get("email")    or "").strip().lower()
            password = (body.get("password") or "")
            avatar   = body.get("avatar", "🧩")

            if not username or len(username) < 3:
                self.send_json(400, {"error": "Username must be at least 3 characters"})
                return
            if not email or "@" not in email:
                self.send_json(400, {"error": "Invalid email address"})
                return
            if not password or len(password) < 6:
                self.send_json(400, {"error": "Password must be at least 6 characters"})
                return

            users = read_all_users()

            for u in users.values():
                if u["email"] == email:
                    self.send_json(409, {"error": "Email already registered"})
                    return
                if u["username"].lower() == username.lower():
                    self.send_json(409, {"error": "Username already taken"})
                    return

            user_id  = str(uuid.uuid4())
            token    = uuid.uuid4().hex
            new_user = {
                "id":            user_id,
                "username":      username,
                "email":         email,
                "password_hash": hash_password(password),
                "token":         token,
                "avatar":        avatar,
                "level":         1,
                "xp":            0,
                "rank":          "Novice",
                "loginCount":    1,
                "gamesPlayed":   0,
                "gamesWon":      0,
                "totalScore":    0,
                "bestTime":      None,
                "streak":        0,
                "maxStreak":     0,
                "hintsUsed":     0,
                "achievements":  [],
                "recentGames":   [],
                "streakDays":    [],
                "campaignProgress": {},
                "resumeProgress": None,
                "createdAt":     datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "updatedAt":     datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            }
            write_user(user_id, new_user)
            print(f"  ✅  New user registered: {username} ({email})")

            # Seed initial entry in leaderboard.json
            try:
                lb = read_json(LEADERBOARD_FILE, [])
                if not any(e.get("id") == user_id for e in lb):
                    lb.append({
                        "id": user_id,
                        "username": username,
                        "avatar": avatar,
                        "score": 0,
                        "games": 0,
                        "level": 1,
                        "rank": "Novice"
                    })
                    lb.sort(key=lambda x: x.get("score", 0), reverse=True)
                    for i, e in enumerate(lb):
                        e["rank"] = i + 1
                    write_json(LEADERBOARD_FILE, lb)
            except Exception as le:
                print(f"  [WARN] Could not seed leaderboard entry for new user: {le}")

            safe_user = sanitize_user_data(new_user)
            self.send_json(201, {"message": "Account created successfully", "user": safe_user})
            return

        # ── POST /api/auth/login ─────────────────────────────────────────
        if path == "/api/auth/login":
            email    = (body.get("email")    or "").strip().lower()
            password = (body.get("password") or "")

            if not email or not password:
                self.send_json(400, {"error": "Email and password are required"})
                return

            users = read_all_users()
            found = next((u for u in users.values() if u["email"] == email), None)

            if not found:
                self.send_json(401, {"error": "No account found with this email"})
                return

            if not verify_password(password, found["password_hash"]):
                self.send_json(401, {"error": "Incorrect password"})
                return

            # Migrate legacy SHA-256 hash to bcrypt on first successful login
            if BCRYPT_AVAILABLE and not found["password_hash"].startswith("$2"):
                found["password_hash"] = hash_password(password)
                print(f"  🔒  Password migrated to bcrypt for: {found['username']}")

            # Rotate session token on every login
            token = uuid.uuid4().hex
            found["token"]       = token
            found["lastLoginAt"] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            found["loginCount"]  = found.get("loginCount", 0) + 1
            found["activeSession"] = {
                "token": token,
                "loginIp": self.client_address[0],
                "userAgent": self.headers.get("User-Agent", "Unknown"),
                "loginTime": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            }
            write_user(found["id"], found)
            print(f"  🔐  User logged in: {found['username']}")

            safe_user = sanitize_user_data(found)
            self.send_json(200, {"message": "Login successful", "user": safe_user})
            return

        # ── Bearer token authorization helper (UUID-validated) ─────────────────
        def is_authorized(user_id):
            """Validate UUID format first, then check Bearer token."""
            if not is_valid_uuid(user_id):
                return False
            auth = self.headers.get("Authorization", "")
            if not auth.startswith("Bearer "):
                return False
            req_token = auth[7:]
            user_data = read_user(user_id)
            return bool(user_data and user_data.get("token") == req_token)

        # ── POST /api/users/update ──────────────────────────────────────
        if path == "/api/users/update":
            user_id = body.get("id")
            if not user_id:
                self.send_json(400, {"error": "User ID required"})
                return
            if not is_valid_uuid(user_id):
                self.send_json(400, {"error": "Invalid user ID format"})
                return
            if not is_authorized(user_id):
                self.send_json(401, {"error": "Unauthorized access"})
                return

            user_data = read_user(user_id)
            if not user_data:
                self.send_json(404, {"error": "User not found"})
                return

            # Protected fields — never overwrite via update endpoint
            protected = {"id", "email", "password_hash", "token", "createdAt"}
            for k, v in body.items():
                if k not in protected:
                    user_data[k] = v
            user_data["updatedAt"] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            write_user(user_id, user_data)

            safe_user = sanitize_user_data(user_data)
            self.send_json(200, {"message": "User updated", "user": safe_user})
            return

        # ── POST /api/games/save ────────────────────────────────────────
        if path == "/api/games/save":
            user_id = body.get("userId")
            if not user_id:
                self.send_json(400, {"error": "userId required"})
                return
            if not is_valid_uuid(user_id):
                self.send_json(400, {"error": "Invalid userId format"})
                return
            if not is_authorized(user_id):
                self.send_json(401, {"error": "Unauthorized access"})
                return

            user_games = read_user_games(user_id)

            game_entry = {
                "id":           body.get("gameId", str(uuid.uuid4())),
                "difficulty":   body.get("difficulty"),
                "status":       body.get("status", "in_progress"),
                "boardState":   body.get("boardState"),
                "notesState":   body.get("notesState"),
                "timeElapsed":  body.get("timeElapsed", 0),
                "mistakesCount":body.get("mistakesCount", 0),
                "hintsUsed":    body.get("hintsUsed", 0),
                "score":        body.get("score"),
                "won":          body.get("won"),
                "savedAt":      datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            }

            existing_idx = next(
                (i for i, g in enumerate(user_games) if g.get("id") == game_entry["id"]),
                None
            )
            if existing_idx is not None:
                user_games[existing_idx] = game_entry
            else:
                user_games.insert(0, game_entry)
                user_games = user_games[:50]  # keep last 50 entries per user

            write_user_games(user_id, user_games)

            # Update user's updatedAt field to mark activity
            try:
                user_data = read_user(user_id)
                if user_data:
                    user_data["updatedAt"] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
                    write_user(user_id, user_data)
            except Exception as ue:
                print(f"  [WARN] Could not update user updatedAt on game save: {ue}")

            self.send_json(200, {"message": "Game saved", "gameId": game_entry["id"]})
            return

        # ── POST /api/progress/save ─────────────────────────────────────
        if path == "/api/progress/save":
            user_id = body.get("userId")
            if not user_id:
                self.send_json(400, {"error": "userId required"})
                return
            if not is_valid_uuid(user_id):
                self.send_json(400, {"error": "Invalid userId format"})
                return
            auth = self.headers.get("Authorization", "")
            if not auth.startswith("Bearer "):
                self.send_json(401, {"error": "Unauthorized access"})
                return
            req_token = auth[7:]
            user_data = read_user(user_id)
            if not user_data or user_data.get("token") != req_token:
                self.send_json(401, {"error": "Unauthorized access"})
                return

            if isinstance(body.get("campaignProgress"), dict):
                user_data["campaignProgress"] = body["campaignProgress"]
            if body.get("resumeProgress") is not None:
                user_data["resumeProgress"] = body["resumeProgress"]
            elif "resumeProgress" in body:
                user_data["resumeProgress"] = None
            user_data["updatedAt"] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            write_user(user_id, user_data)
            self.send_json(200, {"message": "Progress saved", "progress": {
                "campaignProgress": user_data.get("campaignProgress", {}),
                "resumeProgress": user_data.get("resumeProgress", None),
            }})
            return

        # ── POST /api/leaderboard/update ────────────────────────────────
        if path == "/api/leaderboard/update":
            entry   = body
            user_id = entry.get("id")
            if not user_id:
                self.send_json(400, {"error": "User ID required"})
                return
            if not is_valid_uuid(user_id):
                self.send_json(400, {"error": "Invalid user ID format"})
                return
            if not is_authorized(user_id):
                self.send_json(401, {"error": "Unauthorized access"})
                return

            lb       = read_json(LEADERBOARD_FILE, [])
            existing = next((e for e in lb if e.get("id") == user_id), None)
            if existing:
                existing["score"] = entry.get("score", existing["score"])
                existing["games"] = entry.get("games", existing["games"])
            else:
                lb.append(entry)

            lb.sort(key=lambda e: e.get("score", 0), reverse=True)
            for i, e in enumerate(lb):
                e["rank"] = i + 1

            write_json(LEADERBOARD_FILE, lb)
            new_rank = next((e["rank"] for e in lb if e.get("id") == user_id), None)
            self.send_json(200, {"message": "Leaderboard updated", "rank": new_rank})
            return

        self.send_json(404, {"error": "Endpoint not found", "path": path})

    # ── PUT — delegates to POST handler ────────────────────────────────────
    def do_PUT(self):
        self.do_POST()


# ── Entry Point ────────────────────────────────────────────────────────────────
def main():
    # Bind to 127.0.0.1 for maximum robustness (avoiding IPv6 dual-stack resolution bugs on Windows)
    server = HTTPServer(("127.0.0.1", PORT), SudokuHandler)

    # Write PID file to logs/server.pid
    pid_file = os.path.join(ROOT_DIR, "logs", "server.pid")
    try:
        os.makedirs(os.path.dirname(pid_file), exist_ok=True)
        with open(pid_file, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
    except Exception as e:
        print(f"  [WARN] Could not write PID file: {e}")

    print()
    print("  +================================================+")
    print("  |          Sudoku-Arena Local Server             |")
    print("  +================================================+")
    print(f"  |  URL  : http://127.0.0.1:{PORT}                    |")
    print(f"  |  Data : database/                              |")
    print(f"  |  Users: database/users/                        |")
    print(f"  |  Games: database/games/                        |")
    print(f"  |  LB   : database/leaderboard.json              |")
    print("  |  Press Ctrl+C to stop the server               |")
    print("  +================================================+")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")
        server.shutdown()
    finally:
        if os.path.exists(pid_file):
            try:
                os.remove(pid_file)
            except Exception:
                pass

if __name__ == "__main__":
    main()
