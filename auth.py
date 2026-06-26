import os
import uuid
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            api_key TEXT UNIQUE NOT NULL,
            plan TEXT DEFAULT 'free',
            requests_today INTEGER DEFAULT 0,
            requests_limit INTEGER DEFAULT 10,
            last_request_date TEXT,
            paid_until TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{h}"


def check_password(password: str, stored: str) -> bool:
    salt, h = stored.split(":")
    return hashlib.sha256((salt + password).encode()).hexdigest() == h


def generate_api_key() -> str:
    return f"ak_{secrets.token_hex(24)}"


def register(email: str, password: str) -> dict:
    conn = get_db()
    try:
        api_key = generate_api_key()
        conn.execute(
            "INSERT INTO users (email, password_hash, api_key) VALUES (?, ?, ?)",
            (email, hash_password(password), api_key),
        )
        conn.commit()
        return {"success": True, "api_key": api_key, "email": email}
    except sqlite3.IntegrityError:
        return {"success": False, "error": "Email уже зарегистрирован"}
    finally:
        conn.close()


def login(email: str, password: str) -> dict:
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    if not user or not check_password(password, user["password_hash"]):
        return {"success": False, "error": "Неверный email или пароль"}
    return {"success": True, "api_key": user["api_key"], "email": email}


def check_api_key(api_key: str) -> dict:
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE api_key = ?", (api_key,)).fetchone()
    if not user:
        conn.close()
        return {"valid": False, "error": "Неверный API ключ"}

    today = datetime.now().strftime("%Y-%m-%d")

    if user["last_request_date"] != today:
        conn.execute(
            "UPDATE users SET requests_today = 0, last_request_date = ? WHERE api_key = ?",
            (today, api_key),
        )
        conn.commit()

    user = conn.execute("SELECT * FROM users WHERE api_key = ?", (api_key,)).fetchone()

    if user["requests_today"] >= user["requests_limit"]:
        conn.close()
        return {"valid": False, "error": "Лимит запросов исчерпан. Обновите план."}

    conn.execute(
        "UPDATE users SET requests_today = requests_today + 1 WHERE api_key = ?",
        (api_key,),
    )
    conn.commit()
    conn.close()

    return {
        "valid": True,
        "email": user["email"],
        "plan": user["plan"],
        "remaining": user["requests_limit"] - user["requests_today"] - 1,
    }


def set_plan(email: str, plan: str, days: int = 30):
    conn = get_db()
    limits = {"free": 10, "starter": 100, "pro": 500, "enterprise": 9999}
    paid_until = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    conn.execute(
        "UPDATE users SET plan = ?, requests_limit = ?, paid_until = ? WHERE email = ?",
        (plan, limits.get(plan, 10), paid_until, email),
    )
    conn.commit()
    conn.close()


init_db()
