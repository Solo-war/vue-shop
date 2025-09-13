from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse
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
import json
import datetime
import sqlite3

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
# --- Твой файл с продуктами ---
DATA_FILE = Path(__file__).parent / "static" / "products.json"

DB_FILE = Path(__file__).parent / "mock_payments.db"

# --- JWT настройки ---
SECRET_KEY = "supersecretkey"   # замени на свой ключ!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- SQLite ---
DATABASE_URL = "sqlite:///./users.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

#  Инициализация БД
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

# --- Хэширование паролей ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Подходящие пароли
ALLOWED_TEST_CARDS = {
    "4242424242424242": "visa",      # успешная оплата
    "4000000000009995": "visa_decline",  # пример declined (демо)
}


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

class CheckoutResponse(BaseModel):
    order_id: str
    amount: int

class PayRequest(BaseModel):
    order_id: str
    # ВАЖНО: этот API принимает card_number только ради DEMO — но сервер не сохраняет полный номер.
    card_number: str = Field(..., description="Только ТЕСТОВЫЕ номера (не вводите реальные данные)")
    exp_month: str
    exp_year: str
    name: str

class PayResponse(BaseModel):
    status: str
    message: str
    transaction_id: str | None = None
    delivery_time: str | None = None

# --- Auth API ---
@app.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_pw = get_password_hash(user.password)
    new_user = User(username=user.username, password_hash=hashed_pw, role="user")  # фикс: всегда "user"
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
def checkout(req: CheckoutRequest):
    if not req.items:
        raise HTTPException(status_code=400, detail="Корзина пуста")

    amount = sum(item.price * item.qty for item in req.items)

    order_id = f"ORD-{random.randint(100000,999999)}"
    created_at = datetime.datetime.utcnow().isoformat()

    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute(
        "INSERT INTO orders (order_id, address, items, amount, created_at) VALUES (?, ?, ?, ?, ?)",
        (order_id, req.address, str([item.dict() for item in req.items]), amount, created_at)
    )
    con.commit()
    con.close()

    return CheckoutResponse(order_id=order_id, amount=amount)


@app.post("/pay-mock", response_model=PayResponse)
def pay_mock(req: PayRequest):
    # Защита от реальных карт
    card = req.card_number.replace(" ", "")
    if card not in ALLOWED_TEST_CARDS:
        raise HTTPException(
            status_code=400,
            detail="Только тестовые карты разрешены"
        )

    brand = ALLOWED_TEST_CARDS[card]

    if brand == "visa_decline":
        status = "declined"
        message = "Платёж отклонён"
        txn = None
    else:
        status = "succeeded"
        message = "Платёж успешно проведён"
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
    cur.execute("SELECT items FROM orders WHERE id = ?", (req.order_id,))
    row = cur.fetchone()
    con.close()

    total_items = 1
    if row and row[0]:
        import json
        try:
            items = json.loads(row[0])   # список товаров
            total_items = sum(item.get("qty", 1) for item in items)
        except Exception:
            pass

    days = 1 + int(total_items * 0.5) + random.randint(0, 3)

    days = max(1, min(days, 28))

    delivery = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime("%d.%m.%Y")

    return PayResponse(status=status, message=message, transaction_id=txn, delivery_time=delivery)

@app.get("/")
async def root():
    return {"status": "ok"}
