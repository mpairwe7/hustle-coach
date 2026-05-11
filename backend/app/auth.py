"""JWT authentication, credit system, and progress tracking for HustleScale.

SQLite-backed with WAL mode.
50 free credits on signup, 1 credit per chat message.
Progress tracking: milestones, business profiles, impact stats.
"""

from __future__ import annotations

import json
import logging
import os
import random
import sqlite3
import threading
import time
import uuid

import bcrypt
import jwt

logger = logging.getLogger(__name__)

JWT_SECRET = os.getenv("JWT_SECRET", "")
if not JWT_SECRET:
    import secrets
    JWT_SECRET = secrets.token_urlsafe(48)
    logger.warning("JWT_SECRET not set — using random secret (tokens will invalidate on restart)")
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "72"))
FREE_CREDITS = int(os.getenv("FREE_CREDITS", "50"))
DB_PATH = os.getenv("AUTH_DB_PATH", "data/hustle_scale_auth.db")

_db_lock = threading.Lock()


def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    with _db_lock:
        conn = _get_db()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                name TEXT DEFAULT '',
                credits INTEGER DEFAULT 0,
                api_key TEXT DEFAULT '',
                plan TEXT DEFAULT 'free',
                business_type TEXT DEFAULT '',
                location TEXT DEFAULT '',
                age INTEGER DEFAULT 0,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS usage_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                credits_used INTEGER DEFAULT 0,
                timestamp REAL NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS business_profiles (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                business_name TEXT DEFAULT '',
                business_type TEXT DEFAULT '',
                location TEXT DEFAULT '',
                startup_capital_ugx INTEGER DEFAULT 0,
                monthly_revenue_ugx INTEGER DEFAULT 0,
                monthly_profit_ugx INTEGER DEFAULT 0,
                employees INTEGER DEFAULT 0,
                started_at REAL,
                stage TEXT DEFAULT 'idea',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS milestones (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                category TEXT DEFAULT 'general',
                completed INTEGER DEFAULT 0,
                completed_at REAL,
                created_at REAL NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS feedback_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT DEFAULT '',
                message_id TEXT NOT NULL,
                rating INTEGER DEFAULT 0,
                comment TEXT DEFAULT '',
                timestamp REAL NOT NULL
            );
        """)
        conn.commit()
        conn.close()


def signup(email: str, password: str, name: str = "", business_type: str = "", location: str = "", age: int = 0) -> dict:
    """Create a new user account with free credits."""
    user_id = str(uuid.uuid4())
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    now = time.time()

    with _db_lock:
        conn = _get_db()
        try:
            conn.execute(
                "INSERT INTO users (id, email, password, name, credits, business_type, location, age, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (user_id, email.lower(), hashed, name, FREE_CREDITS, business_type, location, age, now, now),
            )
            # Create default milestones for the user
            _create_default_milestones(conn, user_id, now)
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            raise ValueError("Email already registered")
        conn.close()

    token = _create_token(user_id, email)
    return {"token": token, "user_id": user_id, "credits": FREE_CREDITS}


def _create_default_milestones(conn: sqlite3.Connection, user_id: str, now: float):
    """Create default business journey milestones for a new user."""
    milestones = [
        ("Choose your business idea", "Decide what business you want to start based on your skills, location, and capital", "planning"),
        ("Create your business plan", "Use HustleScale to generate a detailed business plan with budget and break-even", "planning"),
        ("Research your market", "Talk to potential customers and check prices of supplies in your area", "planning"),
        ("Register your business", "Get a trading license from KCCA or your district and register with URA for TIN", "registration"),
        ("Open a business bank/mobile money account", "Separate your business money from personal money", "registration"),
        ("Buy initial supplies", "Purchase your first stock or equipment based on your business plan", "launch"),
        ("Find your first 5 customers", "Start selling and get feedback from your first customers", "launch"),
        ("Track income and expenses for 1 month", "Keep daily records of all money coming in and going out", "launch"),
        ("Reach break-even", "Your total income covers all your costs — you are no longer losing money", "growth"),
        ("Hire your first helper", "When demand grows, bring someone to help you serve more customers", "growth"),
        ("Save 3 months emergency fund", "Put aside enough money to cover 3 months of business expenses", "growth"),
        ("Join or form a cooperative/VSLA", "Pool resources with other entrepreneurs for bulk buying and mutual support", "growth"),
    ]
    for title, desc, category in milestones:
        mid = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO milestones (id, user_id, title, description, category, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (mid, user_id, title, desc, category, now),
        )


def login(email: str, password: str) -> dict:
    """Authenticate and return JWT token."""
    with _db_lock:
        conn = _get_db()
        row = conn.execute(
            "SELECT id, password, credits FROM users WHERE email = ?",
            (email.lower(),),
        ).fetchone()
        conn.close()

    if not row:
        raise ValueError("Invalid email or password")

    if not bcrypt.checkpw(password.encode(), row["password"].encode()):
        raise ValueError("Invalid email or password")

    token = _create_token(row["id"], email)
    return {"token": token, "user_id": row["id"], "credits": row["credits"]}


def deduct_credit(user_id: str) -> bool:
    """Deduct 1 credit. Returns False if insufficient."""
    with _db_lock:
        conn = _get_db()
        row = conn.execute(
            "SELECT credits, api_key FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not row:
            conn.close()
            return False

        if row["api_key"]:
            conn.close()
            return True

        if row["credits"] <= 0:
            conn.close()
            return False

        conn.execute(
            "UPDATE users SET credits = credits - 1, updated_at = ? WHERE id = ?",
            (time.time(), user_id),
        )
        conn.execute(
            "INSERT INTO usage_log (user_id, action, credits_used, timestamp) VALUES (?, ?, ?, ?)",
            (user_id, "chat", 1, time.time()),
        )
        conn.commit()
        conn.close()
        return True


def get_user(user_id: str) -> dict | None:
    """Get user profile."""
    with _db_lock:
        conn = _get_db()
        row = conn.execute(
            "SELECT id, email, name, credits, plan, business_type, location, age FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        conn.close()
    if row:
        return dict(row)
    return None


def verify_token(token: str) -> dict | None:
    """Verify JWT and return payload."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except jwt.InvalidTokenError:
        return None


# ─── Progress Tracking ───

def get_milestones(user_id: str) -> list[dict]:
    """Get all milestones for a user."""
    with _db_lock:
        conn = _get_db()
        rows = conn.execute(
            "SELECT id, title, description, category, completed, completed_at FROM milestones WHERE user_id = ? ORDER BY created_at",
            (user_id,),
        ).fetchall()
        conn.close()
    return [dict(r) for r in rows]


def update_milestone(user_id: str, milestone_id: str, completed: bool = True) -> bool:
    """Mark a milestone as completed or uncompleted."""
    with _db_lock:
        conn = _get_db()
        row = conn.execute(
            "SELECT id FROM milestones WHERE id = ? AND user_id = ?",
            (milestone_id, user_id),
        ).fetchone()
        if not row:
            conn.close()
            return False
        conn.execute(
            "UPDATE milestones SET completed = ?, completed_at = ? WHERE id = ?",
            (1 if completed else 0, time.time() if completed else None, milestone_id),
        )
        conn.commit()
        conn.close()
    return True


def get_business_profile(user_id: str) -> dict | None:
    """Get user's business profile."""
    with _db_lock:
        conn = _get_db()
        row = conn.execute(
            "SELECT * FROM business_profiles WHERE user_id = ? ORDER BY updated_at DESC LIMIT 1",
            (user_id,),
        ).fetchone()
        conn.close()
    if row:
        return dict(row)
    return None


def upsert_business_profile(user_id: str, data: dict) -> dict:
    """Create or update business profile."""
    now = time.time()
    with _db_lock:
        conn = _get_db()
        existing = conn.execute(
            "SELECT id FROM business_profiles WHERE user_id = ?", (user_id,)
        ).fetchone()

        if existing:
            sets = ", ".join(f"{k} = ?" for k in data if k not in ("id", "user_id", "created_at"))
            vals = [data[k] for k in data if k not in ("id", "user_id", "created_at")]
            vals.extend([now, user_id])
            conn.execute(
                f"UPDATE business_profiles SET {sets}, updated_at = ? WHERE user_id = ?",
                vals,
            )
        else:
            profile_id = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO business_profiles (id, user_id, business_name, business_type, location, "
                "startup_capital_ugx, monthly_revenue_ugx, monthly_profit_ugx, employees, stage, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    profile_id, user_id,
                    data.get("business_name", ""),
                    data.get("business_type", ""),
                    data.get("location", ""),
                    data.get("startup_capital_ugx", 0),
                    data.get("monthly_revenue_ugx", 0),
                    data.get("monthly_profit_ugx", 0),
                    data.get("employees", 0),
                    data.get("stage", "idea"),
                    now, now,
                ),
            )
        conn.commit()
        conn.close()
    return get_business_profile(user_id) or {}


def get_impact_stats() -> dict:
    """Get national impact statistics."""
    with _db_lock:
        conn = _get_db()
        total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        total_profiles = conn.execute("SELECT COUNT(*) FROM business_profiles").fetchone()[0]
        launched = conn.execute(
            "SELECT COUNT(*) FROM business_profiles WHERE stage IN ('launched', 'growing', 'scaling')"
        ).fetchone()[0]
        jobs = conn.execute(
            "SELECT COALESCE(SUM(employees), 0) FROM business_profiles"
        ).fetchone()[0]
        capital = conn.execute(
            "SELECT COALESCE(SUM(startup_capital_ugx), 0) FROM business_profiles"
        ).fetchone()[0]
        milestones_done = conn.execute(
            "SELECT COUNT(*) FROM milestones WHERE completed = 1"
        ).fetchone()[0]
        regions = conn.execute(
            "SELECT COUNT(DISTINCT location) FROM business_profiles WHERE location != ''"
        ).fetchone()[0]
        conn.close()

    return {
        "total_users": total_users,
        "businesses_planned": total_profiles,
        "businesses_launched": launched,
        "jobs_created": jobs,
        "total_capital_mobilised_ugx": capital,
        "regions_reached": regions,
        "milestones_completed": milestones_done,
    }


def save_feedback(message_id: str, rating: int, comment: str = "", user_id: str = "") -> None:
    """Save user feedback."""
    with _db_lock:
        conn = _get_db()
        conn.execute(
            "INSERT INTO feedback_log (user_id, message_id, rating, comment, timestamp) VALUES (?, ?, ?, ?, ?)",
            (user_id, message_id, rating, comment, time.time()),
        )
        conn.commit()
        conn.close()


# ─── Password Reset ───

_reset_codes: dict[str, tuple[str, float]] = {}  # email -> (code, expiry_timestamp)
_reset_lock = threading.Lock()
RESET_CODE_EXPIRY = 600  # 10 minutes


def request_password_reset(email: str) -> dict:
    """Generate a reset token (in production, email this to the user)."""
    email = email.lower().strip()
    code = f"{random.randint(0, 999999):06d}"
    expiry = time.time() + RESET_CODE_EXPIRY

    # Check if email exists, but always return the same generic message
    with _db_lock:
        conn = _get_db()
        row = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

    if row:
        with _reset_lock:
            _reset_codes[email] = (code, expiry)
        logger.info("Password reset code generated for %s", email)

    # Always return the same message to avoid revealing whether the email exists
    return {
        "message": "If an account with that email exists, a reset code has been sent.",
    }


def reset_password(email: str, code: str, new_password: str) -> dict:
    """Reset password using the code."""
    email = email.lower().strip()

    with _reset_lock:
        stored = _reset_codes.get(email)

    if not stored:
        raise ValueError("Invalid or expired reset code")

    stored_code, expiry = stored
    if time.time() > expiry:
        with _reset_lock:
            _reset_codes.pop(email, None)
        raise ValueError("Invalid or expired reset code")

    if stored_code != code:
        raise ValueError("Invalid or expired reset code")

    # Update password
    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    with _db_lock:
        conn = _get_db()
        conn.execute(
            "UPDATE users SET password = ?, updated_at = ? WHERE email = ?",
            (hashed, time.time(), email),
        )
        conn.commit()
        conn.close()

    # Clear the code
    with _reset_lock:
        _reset_codes.pop(email, None)

    return {"message": "Password has been reset successfully."}


def _create_token(user_id: str, email: str) -> str:
    return jwt.encode(
        {
            "sub": user_id,
            "email": email,
            "exp": time.time() + (JWT_EXPIRY_HOURS * 3600),
            "iat": time.time(),
        },
        JWT_SECRET,
        algorithm="HS256",
    )
