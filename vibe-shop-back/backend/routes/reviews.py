from fastapi import APIRouter
from schemas import ReviewIn, ReviewOut
from config import DB_FILE
import sqlite3
import datetime

router = APIRouter()


@router.get("/reviews/{product_id}")
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


@router.post("/reviews/{product_id}", response_model=ReviewOut)
def add_review(product_id: str, body: ReviewIn):
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

