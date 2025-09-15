from fastapi import APIRouter, Depends, HTTPException, Request, Body
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from db import User, get_db
from schemas import UserCreate, UserOut, Token
from security import verify_password, get_password_hash, create_access_token, oauth2_scheme, get_current_user

router = APIRouter()


@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_pw = get_password_hash(user.password)
    new_user = User(username=user.username, password_hash=hashed_pw, role="user")
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/token", response_model=Token)
def login(
    request: Request,
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),  # не обязательно
    username: str = Body(None),
    password: str = Body(None),
):
    # 1. Если пришёл form-data (OAuth2PasswordRequestForm)
    if form_data:
        uname = form_data.username
        passwd = form_data.password
    # 2. Если пришёл JSON (username + password)
    elif username and password:
        uname = username
        passwd = password
    else:
        raise HTTPException(status_code=422, detail="username and password required")

    user = db.query(User).filter(User.username == uname).first()
    if not user or not verify_password(passwd, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    token = create_access_token({"sub": user.username, "role": user.role})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
def read_users_me(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    user = get_current_user(token=token, db=db)
    return user

