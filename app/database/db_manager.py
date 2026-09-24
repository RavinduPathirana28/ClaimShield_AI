import sqlite3
import json
import time
from app import config

try:
    import sqlalchemy as sa
    from sqlalchemy.orm import declarative_base, sessionmaker
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

if SQLALCHEMY_AVAILABLE:
    Base = declarative_base()

    class UserORM(Base):
        __tablename__ = "users"
        id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
        username = sa.Column(sa.String, unique=True, nullable=False)
        password_hash = sa.Column(sa.String, nullable=False)
        role = sa.Column(sa.String, nullable=False)
        tokens = sa.Column(sa.Float, default=10.0)
        last_request_time = sa.Column(sa.Float, default=0.0)

    class ArticleORM(Base):
        __tablename__ = "articles"
        id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
        title = sa.Column(sa.String, nullable=False)
        content = sa.Column(sa.String, nullable=False)
        source = sa.Column(sa.String, nullable=False)
        url = sa.Column(sa.String)
        date = sa.Column(sa.String, nullable=False)

    class VerificationLogORM(Base):
        __tablename__ = "verification_logs"
        id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
        user_id = sa.Column(sa.String, nullable=False)
        claim = sa.Column(sa.String, nullable=False)
        verdict = sa.Column(sa.String, nullable=False)
        confidence = sa.Column(sa.Float, nullable=False)
        timestamp = sa.Column(sa.String, nullable=False)
        details_json = sa.Column(sa.String, nullable=False)


class DBManager:
    def __init__(self):
        self.use_supabase = False
        self.supabase_client = None
        
        # SQLAlchemy setup
        self.sa_engine = None
        self.SessionLocal = None
        if SQLALCHEMY_AVAILABLE:
            try:
                db_uri = f"sqlite:///{config.SQLITE_DB_PATH}"
                self.sa_engine = sa.create_engine(db_uri, connect_args={"check_same_thread": False})
                Base.metadata.create_all(bind=self.sa_engine)
                self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.sa_engine)
            except Exception as e:
                print(f"SQLAlchemy initialization note: {e}")
        
        # Check if Supabase URL and Key are set
        if config.SUPABASE_URL and config.SUPABASE_KEY:
            try:
                from supabase import create_client
                self.supabase_client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
                self.use_supabase = True
                print("Database: Connected to Supabase Cloud Database.")
            except Exception as e:
                print(f"Database: Failed to connect to Supabase ({e}). Falling back to SQLite.")
                self.use_supabase = False
        else:
            print("Database: Supabase keys not set. Using local SQLite database.")
            
        # Always initialize SQLite just in case (fallback)
        self._init_sqlite()

    def _init_sqlite(self):
        """Initializes local SQLite database tables if they do not exist."""
        conn = sqlite3.connect(config.SQLITE_DB_PATH)
        cursor = conn.cursor()
        try:
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL,
                    tokens REAL DEFAULT 10.0,
                    last_request_time REAL DEFAULT 0.0
                )
            """)

            # Articles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT NOT NULL,
                    url TEXT,
                    date TEXT NOT NULL
                )
            """)

            # Verification Logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS verification_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    claim TEXT NOT NULL,
                    verdict TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    details_json TEXT NOT NULL
                )
            """)

            conn.commit()
        finally:
            conn.close()

    # User Management
    def get_user(self, username: str):
        if self.use_supabase:
            try:
                res = self.supabase_client.table("users").select("*").eq("username", username).execute()
                if res.data and len(res.data) > 0:
                    user = res.data[0]
                    # Ensure numeric fields are cast properly
                    user["tokens"] = float(user.get("tokens", 10.0))
                    user["last_request_time"] = float(user.get("last_request_time", 0.0))
                    return user
                return None
            except Exception as e:
                print(f"[Warning] Supabase get_user error: {e}. Trying SQLite fallback.")
                
        # SQLite fallback/primary
        conn = sqlite3.connect(config.SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None

    def create_user(self, username: str, password_hash: str, role: str = "user"):
        if self.use_supabase:
            try:
                user_data = {
                    "username": username,
                    "password_hash": password_hash,
                    "role": role,
                    "tokens": float(config.RATE_LIMIT_CAPACITY),
                    "last_request_time": float(time.time())
                }
                res = self.supabase_client.table("users").insert(user_data).execute()
                if res.data and len(res.data) > 0:
                    return res.data[0]
                return self.get_user(username)
            except Exception as e:
                print(f"[Warning] Supabase create_user error: {e}. Trying SQLite fallback.")
                
        # SQLite fallback/primary
        conn = sqlite3.connect(config.SQLITE_DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password_hash, role, tokens, last_request_time) VALUES (?, ?, ?, ?, ?)",
                (username, password_hash, role, float(config.RATE_LIMIT_CAPACITY), float(time.time()))
            )
            conn.commit()
        except sqlite3.IntegrityError:
            raise ValueError(f"Username '{username}' already exists.")
        finally:
            conn.close()
        return self.get_user(username)

    def update_user_tokens(self, username: str, tokens: float, last_request_time: float):
        if self.use_supabase:
            try:
                res = self.supabase_client.table("users").update({
                    "tokens": tokens,
                    "last_request_time": last_request_time
                }).eq("username", username).execute()
                return bool(res.data)
            except Exception as e:
                print(f"[Warning] Supabase update_user_tokens error: {e}. Trying SQLite fallback.")

        # SQLite fallback/primary
        conn = sqlite3.connect(config.SQLITE_DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE users SET tokens = ?, last_request_time = ? WHERE username = ?",
                (tokens, last_request_time, username)
            )
            updated = cursor.rowcount > 0
            conn.commit()
            return updated
        finally:
            conn.close()

    def update_user_role(self, username: str, role: str):
        if self.use_supabase:
            try:
                res = self.supabase_client.table("users").update({
                    "role": role
                }).eq("username", username).execute()
                return bool(res.data)
            except Exception as e:
                print(f"[Warning] Supabase update_user_role error: {e}. Trying SQLite fallback.")

        # SQLite fallback/primary
        conn = sqlite3.connect(config.SQLITE_DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE users SET role = ? WHERE username = ?",
                (role, username)
            )
            updated = cursor.rowcount > 0
            conn.commit()
            return updated
        finally:
            conn.close()

    def update_user_password(self, username: str, password_hash: str):
        if self.use_supabase:
            try:
                res = self.supabase_client.table("users").update({
                    "password_hash": password_hash
                }).eq("username", username).execute()
                return bool(res.data)
            except Exception as e:
                print(f"[Warning] Supabase update_user_password error: {e}. Trying SQLite fallback.")

        # SQLite fallback/primary
        conn = sqlite3.connect(config.SQLITE_DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE users SET password_hash = ? WHERE username = ?",
                (password_hash, username)
            )
            updated = cursor.rowcount > 0
            conn.commit()
            return updated
        finally:
            conn.close()

    def get_all_users(self):
        if self.use_supabase:
            try:
                res = self.supabase_client.table("users").select("id, username, role, tokens, last_request_time").execute()
                if res.data is not None:
                    return res.data
            except Exception as e:
                print(f"[Warning] Supabase get_all_users error: {e}. Trying SQLite fallback.")
                
        # SQLite fallback/primary
        conn = sqlite3.connect(config.SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role, tokens, last_request_time FROM users ORDER BY id ASC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    # Articles Corpus
    def get_all_articles(self):
        if self.use_supabase:
            try:
                res = self.supabase_client.table("articles").select("*").execute()
                if res.data is not None:
                    return res.data
            except Exception as e:
                print(f"[Warning] Supabase get_all_articles error: {e}. Trying SQLite fallback.")
                
        # SQLite fallback/primary
        conn = sqlite3.connect(config.SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM articles")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def add_article(self, title: str, content: str, source: str, url: str, date: str):
        if self.use_supabase:
            try:
                article_data = {
                    "title": title,
                    "content": content,
                    "source": source,
                    "url": url,
                    "date": date
                }
                res = self.supabase_client.table("articles").insert(article_data).execute()
                if res.data and len(res.data) > 0:
                    return res.data[0]
                return article_data
            except Exception as e:
                print(f"[Warning] Supabase add_article error: {e}. Trying SQLite fallback.")
                
        # SQLite fallback/primary
        conn = sqlite3.connect(config.SQLITE_DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO articles (title, content, source, url, date) VALUES (?, ?, ?, ?, ?)",
                (title, content, source, url, date)
            )
            article_id = cursor.lastrowid
            conn.commit()
        finally:
            conn.close()
        return {
            "id": article_id,
            "title": title,
            "content": content,
            "source": source,
            "url": url,
            "date": date
        }

    # Verification Logs
    def get_logs_by_user(self, user_id: str):
        if self.use_supabase:
            try:
                res = self.supabase_client.table("verification_logs").select("*").eq("user_id", user_id).order("timestamp", desc=True).execute()
                if res.data is not None:
                    return res.data
            except Exception as e:
                print(f"[Warning] Supabase get_logs_by_user error: {e}. Trying SQLite fallback.")
                
        # SQLite fallback/primary
        conn = sqlite3.connect(config.SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM verification_logs WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def add_log(self, user_id: str, claim: str, verdict: str, confidence: float, details_json: str):
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        if self.use_supabase:
            try:
                log_data = {
                    "user_id": user_id,
                    "claim": claim,
                    "verdict": verdict,
                    "confidence": confidence,
                    "timestamp": timestamp,
                    "details_json": details_json
                }
                res = self.supabase_client.table("verification_logs").insert(log_data).execute()
                if res.data and len(res.data) > 0:
                    return res.data[0]
                return log_data
            except Exception as e:
                print(f"[Warning] Supabase add_log error: {e}. Trying SQLite fallback.")
                
        # SQLite fallback/primary
        conn = sqlite3.connect(config.SQLITE_DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO verification_logs (user_id, claim, verdict, confidence, timestamp, details_json) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, claim, verdict, confidence, timestamp, details_json)
            )
            log_id = cursor.lastrowid
            conn.commit()
        finally:
            conn.close()
        return {
            "id": log_id,
            "user_id": user_id,
            "claim": claim,
            "verdict": verdict,
            "confidence": confidence,
            "timestamp": timestamp,
            "details_json": details_json
        }
