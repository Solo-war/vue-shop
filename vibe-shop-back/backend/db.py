from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from config import DATABASE_URL, DB_FILE
import sqlite3

# SQLAlchemy (users)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String, default="user")


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_sqlite():
    """Create/extend SQLite tables used for orders, payments, reviews."""
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT,
            address TEXT,
            items TEXT,
            amount INTEGER,
            created_at TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT,
            status TEXT,
            amount INTEGER,
            card_last4 TEXT,
            card_brand TEXT,
            created_at TEXT
        )
        """
    )
    # Extend orders table with extra columns if missing
    try:
        cur.execute("ALTER TABLE orders ADD COLUMN geo_lat TEXT")
    except Exception:
        pass
    try:
        cur.execute("ALTER TABLE orders ADD COLUMN geo_lon TEXT")
    except Exception:
        pass
    try:
        cur.execute("ALTER TABLE orders ADD COLUMN username TEXT")
    except Exception:
        pass
    # Reviews table
    try:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT,
                rating INTEGER,
                text TEXT,
                author TEXT,
                created_at TEXT
            )
            """
        )
    except Exception:
        pass
    con.commit()
    con.close()


def ensure_admin_user():
    """Create default admin/admin user if no admin exists (dev convenience)."""
    from security import get_password_hash  

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.role == "admin").first()
        if not admin:
            try:
                hashed_pw = get_password_hash("admin")
                user = User(username="admin", password_hash=hashed_pw, role="admin")
                db.add(user)
                db.commit()
            except Exception:
                db.rollback()
    finally:
        db.close()

