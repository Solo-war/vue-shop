from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse
from fastapi import Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pathlib import Path
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
import math
import json
import datetime
import sqlite3
import ast

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- РўРІРѕР№ С„Р°Р№Р» СЃ РїСЂРѕРґСѓРєС‚Р°РјРё ---
DATA_FILE = Path(__file__).parent / "static" / "products.json"

DB_FILE = Path(__file__).parent / "mock_payments.db"

# --- JWT РЅР°СЃС‚СЂРѕР№РєРё ---
SECRET_KEY = "supersecretkey"   # Р·Р°РјРµРЅРё РЅР° СЃРІРѕР№ РєР»СЋС‡!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- SQLite ---
DATABASE_URL = "sqlite:///./users.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

#  РРЅРёС†РёР°Р»РёР·Р°С†РёСЏ Р‘Р”
def init_db():
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT,
        address TEXT,
        items TEXT,
        amount INTEGER,
        created_at TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT,
        status TEXT,
        amount INTEGER,
        card_last4 TEXT,
        card_brand TEXT,
        created_at TEXT
    )
    """)
    # Extend orders table with geo coords if not present
    try: cur.execute("ALTER TABLE orders ADD COLUMN geo_lat TEXT")
    except Exception: pass
    try: cur.execute("ALTER TABLE orders ADD COLUMN geo_lon TEXT")
    except Exception: pass
    # Attach username to orders for per-user history
    try: cur.execute("ALTER TABLE orders ADD COLUMN username TEXT")
    except Exception: pass
    # Reviews table for products
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

init_db()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String, default="user")

Base.metadata.create_all(bind=engine)

# --- РҐСЌС€РёСЂРѕРІР°РЅРёРµ РїР°СЂРѕР»РµР№ ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# РџРѕРґС…РѕРґСЏС‰РёРµ РїР°СЂРѕР»Рё
ALLOWED_TEST_CARDS = {
    "4242424242424242": "visa",      # тестовая успешная
    "4000000000009995": "visa_decline",  # тестовая decline (ошибка)
}

def luhn_check(num: str) -> bool:
    if not num.isdigit():
        return False
    total = 0
    dbl = False
    for d in reversed(num):
        n = int(d)
        if dbl:
            n *= 2
            if n > 9:
                n -= 9
        total += n
        dbl = not dbl
    return total % 10 == 0

def detect_brand(num: str) -> str:
    # Visa
    if len(num) in (13,16,19) and num.startswith('4'):
        return 'visa'
    # MasterCard ranges: 51-55 or 2221-2720 (16 digits)
    if len(num) == 16 and num.isdigit():
        first2 = int(num[:2])
        first4 = int(num[:4])
        first6 = int(num[:6])
        if 51 <= first2 <= 55:
            return 'mastercard'
        if 2221 <= first4 <= 2720 or 222100 <= first6 <= 272099:
            return 'mastercard'
    # MIR 2200-2204 (16 digits)
    if len(num) == 16 and num.isdigit():
        first4 = int(num[:4])
        if 2200 <= first4 <= 2204:
            return 'mir'
    return 'unknown'


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict, expires_delta: int = None):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(
        minutes=expires_delta or ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# Ensure default admin exists for development/demo convenience
def ensure_admin_user():
    db = SessionLocal()
    try:
        # If no admin exists, create default admin/admin
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

ensure_admin_user()

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "user"

class UserOut(BaseModel):
    id: int
    username: str
    role: str
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

# Auth helpers to access current user and restrict admin endpoints
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def require_admin(user: User = Depends(get_current_user)) -> User:
    if getattr(user, "role", None) != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

class OrderRequest(BaseModel):
    address: str
    items: list[dict]   # [{id, name, price, qty}]

class OrderResponse(BaseModel):
    order_id: int
    delivery_time: str


class Item(BaseModel):
    id: int
    name: str
    price: int
    qty: int

class CheckoutRequest(BaseModel):
    address: str
    items: list[Item]
    geo_lat: float | None = None
    geo_lon: float | None = None

class CheckoutResponse(BaseModel):
    order_id: str
    amount: int
    eta_days: int | None = None
    eta_date: str | None = None
    distance_km: int | None = None

class PayRequest(BaseModel):
    order_id: str
    # Р’РђР–РќРћ: СЌС‚РѕС‚ API РїСЂРёРЅРёРјР°РµС‚ card_number С‚РѕР»СЊРєРѕ СЂР°РґРё DEMO вЂ” РЅРѕ СЃРµСЂРІРµСЂ РЅРµ СЃРѕС…СЂР°РЅСЏРµС‚ РїРѕР»РЅС‹Р№ РЅРѕРјРµСЂ.
    card_number: str = Field(..., description="РўРѕР»СЊРєРѕ РўР•РЎРўРћР’Р«Р• РЅРѕРјРµСЂР° (РЅРµ РІРІРѕРґРёС‚Рµ СЂРµР°Р»СЊРЅС‹Рµ РґР°РЅРЅС‹Рµ)")
    exp_month: str
    exp_year: str
    name: str

class PayResponse(BaseModel):
    status: str
    message: str
    transaction_id: str | None = None
    delivery_time: str | None = None


# Haversine helpers and ETA calculation
NOVOSIB = (55.0084, 82.9357)

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))

def calc_eta(items: list[Item], geo_lat: float | None, geo_lon: float | None) -> tuple[int, str, int]:
    total_qty = sum(i.qty for i in items) if items else 0
    unique_ids = len({i.id for i in items}) if items else 0
    distance = 0
    if geo_lat is not None and geo_lon is not None:
        try:
            distance = int(round(haversine_km(geo_lat, geo_lon, NOVOSIB[0], NOVOSIB[1])))
        except Exception:
            distance = 0
    days = 1 + math.ceil(total_qty * 0.5) + math.ceil(unique_ids * 0.3) + math.ceil(distance / 700)
    days = max(1, min(days, 28))
    eta_date = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime("%d.%m.%Y")
    return days, eta_date, distance

class DeliveryEtaRequest(BaseModel):
    geo_lat: float
    geo_lon: float
    items: list[Item]

class DeliveryEtaResponse(BaseModel):
    distance_km: int
    eta_days: int
    eta_date: str

@app.post("/delivery-eta", response_model=DeliveryEtaResponse)
def delivery_eta(req: DeliveryEtaRequest):
    days, eta_date, distance = calc_eta(req.items, req.geo_lat, req.geo_lon)
    return DeliveryEtaResponse(distance_km=distance, eta_days=days, eta_date=eta_date)

# --- Auth API ---
@app.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_pw = get_password_hash(user.password)
    new_user = User(username=user.username, password_hash=hashed_pw, role="user")  # С„РёРєСЃ: РІСЃРµРіРґР° "user"
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = create_access_token({"sub": user.username, "role": user.role})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/me", response_model=UserOut)
def read_users_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/health/live")
async def health() -> dict:
    return {"status": "ok"}

@app.get("/products")
async def products():
    try:
        with DATA_FILE.open(encoding="utf-8") as f:
            data = json.load(f)
        return JSONResponse(content=data)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/checkout", response_model=CheckoutResponse)
def checkout(req: CheckoutRequest, authorization: str | None = Header(default=None)):
    if not req.items:
        raise HTTPException(status_code=400, detail="РљРѕСЂР·РёРЅР° РїСѓСЃС‚Р°")

    amount = sum(item.price * item.qty for item in req.items)

    order_id = f"ORD-{random.randint(100000,999999)}"
    created_at = datetime.datetime.utcnow().isoformat()

    # Try to decode username from Bearer token if provided
    username = None
    try:
        if authorization and authorization.lower().startswith("bearer "):
            token = authorization.split(" ", 1)[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
    except Exception:
        username = None

    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute(
        "INSERT INTO orders (order_id, address, items, amount, created_at, geo_lat, geo_lon, username) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            order_id,
            req.address,
            str([item.dict() for item in req.items]),
            amount,
            created_at,
            str(req.geo_lat) if req.geo_lat is not None else None,
            str(req.geo_lon) if req.geo_lon is not None else None,
            username,
        )
    )
    con.commit()
    con.close()

    days, eta_date, distance = calc_eta(req.items, req.geo_lat, req.geo_lon) if (req.geo_lat is not None and req.geo_lon is not None) else (None, None, None)
    return CheckoutResponse(order_id=order_id, amount=amount, eta_days=days, eta_date=eta_date, distance_km=distance)


@app.post("/pay-mock", response_model=PayResponse)
def pay_mock(req: PayRequest):
    # Принимаем валидные (Luhn) номера Visa/MasterCard/Мир. Спецномер — decline.
    card = req.card_number.replace(" ", "")
    if card == "4000000000009995":
        brand = "visa_decline"
        status = "declined"
        message = "Оплата отклонена"
        txn = None
    else:
        brand = detect_brand(card)
        if brand == 'unknown' or (not card.isdigit()) or len(card) != 16:
            raise HTTPException(status_code=400, detail="Номер карты недействителен")
        status = "succeeded"
        message = "Оплата прошла успешно"
        txn = f"TXN-{random.randint(1000000,9999999)}"

    last4 = card[-4:]

    created_at = datetime.datetime.utcnow().isoformat()
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute(
        "INSERT INTO payments (order_id, status, amount, card_last4, card_brand, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (req.order_id, status, 0, last4, brand, created_at)
    )
    con.commit()
    con.close()

    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("SELECT items, geo_lat, geo_lon FROM orders WHERE order_id = ?", (req.order_id,))
    row = cur.fetchone()
    con.close()

    total_items = 1
    if row and row[0]:
        import json
        try:
            items = json.loads(row[0])   # СЃРїРёСЃРѕРє С‚РѕРІР°СЂРѕРІ
            total_items = sum(item.get("qty", 1) for item in items)
        except Exception:
            pass

    # Compute ETA based on stored coords and items
    items_for_calc = []
    try:
        itms = json.loads(row[0]) if row and row[0] else []
        for it in itms:
            class _I: pass
            o=_I(); o.id=it.get("id"); o.qty=it.get("qty",1); items_for_calc.append(o)
    except Exception:
        pass
    geo_lat = None; geo_lon = None
    try:
        geo_lat = float(row[1]) if row and row[1] is not None else None
        geo_lon = float(row[2]) if row and row[2] is not None else None
    except Exception:
        pass
    days, delivery, _ = calc_eta(items_for_calc, geo_lat, geo_lon)
    return PayResponse(status=status, message=message, transaction_id=txn, delivery_time=delivery)

# ---- Product Reviews ----
class ReviewIn(BaseModel):
    rating: int
    text: str
    author: str | None = None

class ReviewOut(BaseModel):
    id: int
    product_id: str
    rating: int
    text: str
    author: str | None
    created_at: str

@app.get("/reviews/{product_id}")
def get_reviews(product_id: str):
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute(
        "SELECT id, product_id, rating, text, author, created_at FROM reviews WHERE product_id = ? ORDER BY id DESC",
        (str(product_id),)
    )
    rows = cur.fetchall()
    con.close()
    result = []
    for r in rows:
        rid, pid, rating, text, author, created_at = r
        result.append({
            "id": rid,
            "product_id": pid,
            "rating": int(rating) if rating is not None else 0,
            "text": text or "",
            "author": author,
            "created_at": created_at or "",
        })
    return result

@app.post("/reviews/{product_id}", response_model=ReviewOut)
def add_review(product_id: str, body: ReviewIn, user: User | None = Depends(lambda: None)):
    # If user is authenticated, prefer their username
    author = None
    try:
        # Try to read current user, but ignore failures (allow anonymous)
        author = getattr(user, "username", None)
    except Exception:
        author = None
    if not author:
        author = body.author or "Гость"
    rating = max(1, min(int(body.rating), 5)) if isinstance(body.rating, int) else 5
    created_at = datetime.datetime.utcnow().isoformat()

    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute(
        "INSERT INTO reviews (product_id, rating, text, author, created_at) VALUES (?, ?, ?, ?, ?)",
        (str(product_id), int(rating), body.text, author, created_at)
    )
    con.commit()
    rid = cur.lastrowid
    con.close()
    return ReviewOut(id=rid, product_id=str(product_id), rating=int(rating), text=body.text, author=author, created_at=created_at)

def _parse_items(items_raw: str):
    if items_raw is None:
        return []
    try:
        data = json.loads(items_raw)
        if isinstance(data, list):
            return data
    except Exception:
        pass
    try:
        data = ast.literal_eval(items_raw)
        if isinstance(data, list):
            return [dict(x) if isinstance(x, dict) else x for x in data]
    except Exception:
        pass
    return []

@app.get("/admin/orders")
def admin_orders(_: User = Depends(require_admin)):
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute(
        "SELECT order_id, address, items, amount, created_at, geo_lat, geo_lon FROM orders ORDER BY id DESC"
    )
    rows = cur.fetchall()
    con.close()
    result = []
    for r in rows:
        order_id, address, items_raw, amount, created_at, geo_lat, geo_lon = r
        result.append(
            {
                "order_id": order_id,
                "address": address,
                "items": _parse_items(items_raw),
                "amount": amount,
                "created_at": created_at,
                "geo_lat": geo_lat,
                "geo_lon": geo_lon,
            }
        )
    return result

@app.get("/admin/payments")
def admin_payments(_: User = Depends(require_admin)):
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute(
        "SELECT order_id, status, amount, card_last4, card_brand, created_at FROM payments ORDER BY id DESC"
    )
    rows = cur.fetchall()
    con.close()
    result = []
    for r in rows:
        order_id, status, amount, card_last4, card_brand, created_at = r
        result.append(
            {
                "order_id": order_id,
                "status": status,
                "amount": amount,
                "card_last4": card_last4,
                "card_brand": card_brand,
                "created_at": created_at,
            }
        )
    return result

class OrderItemOut(BaseModel):
    id: int
    name: str
    price: int
    qty: int

class OrderOut(BaseModel):
    order_id: str
    address: str
    amount: int
    created_at: str
    items: list[OrderItemOut]
    payment_status: str | None = None
    payment_card_last4: str | None = None
    payment_card_brand: str | None = None
    payment_created_at: str | None = None

@app.get("/my-orders", response_model=list[OrderOut])
def my_orders(token: str = Depends(oauth2_scheme)):
    # Decode the username from token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute(
        "SELECT order_id, address, items, amount, created_at FROM orders WHERE username = ? ORDER BY id DESC",
        (username,),
    )
    rows = cur.fetchall()

    results: list[OrderOut] = []
    for r in rows:
        order_id, address, items_raw, amount, created_at = r
        parsed_items = _parse_items(items_raw)
        items: list[OrderItemOut] = []
        for it in parsed_items:
            try:
                items.append(OrderItemOut(id=int(it.get("id")), name=str(it.get("name")), price=int(it.get("price")), qty=int(it.get("qty", 1))))
            except Exception:
                pass

        # Last payment info for this order
        cur2 = con.cursor()
        cur2.execute(
            "SELECT status, card_last4, card_brand, created_at FROM payments WHERE order_id = ? ORDER BY id DESC LIMIT 1",
            (order_id,),
        )
        p = cur2.fetchone()
        payment_status = p[0] if p else None
        payment_last4 = p[1] if p else None
        payment_brand = p[2] if p else None
        payment_created = p[3] if p else None

        results.append(
            OrderOut(
                order_id=order_id,
                address=address,
                amount=int(amount or 0),
                created_at=created_at,
                items=items,
                payment_status=payment_status,
                payment_card_last4=payment_last4,
                payment_card_brand=payment_brand,
                payment_created_at=payment_created,
            )
        )

    con.close()
    return results

@app.get("/")
async def root():
    return {"status": "ok"}
