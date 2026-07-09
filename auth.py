import os
import hashlib
import secrets
from datetime import datetime, timedelta

DATABASE_URL = os.environ.get("DATABASE_URL", "")

if DATABASE_URL:
    import psycopg2
    import psycopg2.extras

    def get_db():
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        return conn

    def init_db():
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                api_key TEXT UNIQUE NOT NULL,
                plan TEXT DEFAULT 'free',
                requests_today INTEGER DEFAULT 0,
                requests_limit INTEGER DEFAULT 10,
                last_request_date TEXT,
                paid_until TEXT,
                created_at TEXT DEFAULT NOW()
            )
        """)
        conn.commit()
        cur.close()
        conn.close()

    def db_execute(query, params=None):
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(query, params)
        result = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        return result

    def db_execute_returning(query, params=None):
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(query, params)
        result = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        return result

    def db_update(query, params=None):
        conn = get_db()
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        cur.close()
        conn.close()

else:
    import sqlite3

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

    def db_execute(query, params=None):
        conn = get_db()
        if params:
            cur = conn.execute(query, params)
        else:
            cur = conn.execute(query)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def db_update(query, params=None):
        conn = get_db()
        if params:
            conn.execute(query, params)
        else:
            conn.execute(query)
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
    try:
        api_key = generate_api_key()
        db_update(
            "INSERT INTO users (email, password_hash, api_key) VALUES (%s, %s, %s)" if DATABASE_URL else
            "INSERT INTO users (email, password_hash, api_key) VALUES (?, ?, ?)",
            (email, hash_password(password), api_key),
        )
        return {"success": True, "api_key": api_key, "email": email}
    except Exception:
        return {"success": False, "error": "Email уже зарегистрирован"}


def login(email: str, password: str) -> dict:
    users = db_execute(
        "SELECT * FROM users WHERE email = %s" if DATABASE_URL else
        "SELECT * FROM users WHERE email = ?",
        (email,),
    )
    if not users:
        return {"success": False, "error": "Неверный email или пароль"}
    user = users[0]
    if not check_password(password, user["password_hash"]):
        return {"success": False, "error": "Неверный email или пароль"}
    return {"success": True, "api_key": user["api_key"], "email": email}


def check_api_key(api_key: str, count: bool = True) -> dict:
    try:
        users = db_execute(
            "SELECT * FROM users WHERE api_key = %s" if DATABASE_URL else
            "SELECT * FROM users WHERE api_key = ?",
            (api_key,),
        )
    except Exception as e:
        return {"valid": False, "error": f"Ошибка базы данных: {e}"}

    if not users:
        return {"valid": False, "error": "Неверный API ключ"}

    user = users[0]
    today = datetime.now().strftime("%Y-%m-%d")

    if user["last_request_date"] != today:
        db_update(
            "UPDATE users SET requests_today = 0, last_request_date = %s WHERE api_key = %s" if DATABASE_URL else
            "UPDATE users SET requests_today = 0, last_request_date = ? WHERE api_key = ?",
            (today, api_key),
        )

    try:
        users = db_execute(
            "SELECT * FROM users WHERE api_key = %s" if DATABASE_URL else
            "SELECT * FROM users WHERE api_key = ?",
            (api_key,),
        )
        user = users[0]
    except Exception as e:
        return {"valid": False, "error": f"Ошибка базы данных: {e}"}

    if user["requests_today"] >= user["requests_limit"]:
        return {"valid": False, "error": "Лимит запросов исчерпан. Обновите план."}

    if count:
        db_update(
            "UPDATE users SET requests_today = requests_today + 1 WHERE api_key = %s" if DATABASE_URL else
            "UPDATE users SET requests_today = requests_today + 1 WHERE api_key = ?",
            (api_key,),
        )

    return {
        "valid": True,
        "email": user["email"],
        "plan": user["plan"],
        "remaining": user["requests_limit"] - user["requests_today"] - (1 if count else 0),
    }


def set_plan(email: str, plan: str, days: int = 30, requests: int = 0, create_if_missing: bool = False):
    limits = {"free": 10, "starter": 100, "pro": 500, "enterprise": 9999, "custom": 0}
    paid_until = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

    users = db_execute(
        "SELECT id, requests_limit FROM users WHERE email = %s" if DATABASE_URL else
        "SELECT id, requests_limit FROM users WHERE email = ?",
        (email,),
    )

    if plan == "custom" and requests > 0 and users:
        current_limit = users[0].get("requests_limit", 0) if isinstance(users[0], dict) else 0
        req_limit = current_limit + requests
    else:
        req_limit = requests if requests > 0 else limits.get(plan, 10)

    if not users and create_if_missing:
        api_key = generate_api_key()
        default_password = "paid123"
        db_update(
            "INSERT INTO users (email, password_hash, api_key, plan, requests_limit, paid_until) VALUES (%s, %s, %s, %s, %s, %s)" if DATABASE_URL else
            "INSERT INTO users (email, password_hash, api_key, plan, requests_limit, paid_until) VALUES (?, ?, ?, ?, ?, ?)",
            (email, hash_password(default_password), api_key, plan, req_limit, paid_until),
        )
    elif users:
        db_update(
            "UPDATE users SET plan = %s, requests_limit = %s, paid_until = %s WHERE email = %s" if DATABASE_URL else
            "UPDATE users SET plan = ?, requests_limit = ?, paid_until = ? WHERE email = ?",
            (plan, req_limit, paid_until, email),
        )


ADMIN_KEY = "admin_snaic13_secret_2026"

KNOWN_USERS = {
    "serega.mashirov@gmail.com": {"password": "snaic13g", "plan": "enterprise"},
    "valerialepehina39@gmail.com": {"password": "123456", "plan": "enterprise"},
}


def auto_restore():
    for email, info in KNOWN_USERS.items():
        users = db_execute(
            "SELECT * FROM users WHERE email = %s" if DATABASE_URL else
            "SELECT * FROM users WHERE email = ?",
            (email,),
        )
        if not users:
            register(email, info["password"])
            set_plan(email, info["plan"], 36500)
            print(f"[RESTORE] Created user {email} with {info['plan']} plan")
        else:
            user = users[0]
            if user.get("plan") != info["plan"]:
                set_plan(email, info["plan"], 36500)
                print(f"[RESTORE] Fixed plan for {email}")


init_db()
auto_restore()
