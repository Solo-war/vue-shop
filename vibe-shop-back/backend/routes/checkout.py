from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import JSONResponse
from schemas import CheckoutRequest, CheckoutResponse, PayRequest, PayResponse, DeliveryEtaRequest, DeliveryEtaResponse
from config import DB_FILE
from utils import detect_brand, calc_eta, parse_items
import sqlite3
import datetime
import json
import random

router = APIRouter()


@router.post("/delivery-eta", response_model=DeliveryEtaResponse)
def delivery_eta(req: DeliveryEtaRequest):
    days, eta_date, distance = calc_eta(req.items, req.geo_lat, req.geo_lon)
    return DeliveryEtaResponse(distance_km=distance, eta_days=days, eta_date=eta_date)


@router.post("/checkout", response_model=CheckoutResponse)
def checkout(req: CheckoutRequest, authorization: str | None = Header(default=None)):
    if not req.items:
        raise HTTPException(status_code=400, detail="Корзина пуста")

    amount = sum(item.price * item.qty for item in req.items)
    order_id = f"ORD-{int(datetime.datetime.utcnow().timestamp())}-{random.randint(100,999)}"

    created_at = datetime.datetime.utcnow().isoformat()
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute(
        "INSERT INTO orders (order_id, address, items, amount, created_at, geo_lat, geo_lon, username) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            order_id,
            req.address,
            json.dumps([i.dict() for i in req.items], ensure_ascii=False),
            amount,
            created_at,
            str(req.geo_lat) if req.geo_lat is not None else None,
            str(req.geo_lon) if req.geo_lon is not None else None,
            None,
        ),
    )
    con.commit()
    con.close()

    days, eta_date, distance = calc_eta(req.items, req.geo_lat, req.geo_lon) if (req.geo_lat is not None and req.geo_lon is not None) else (None, None, None)
    return CheckoutResponse(order_id=order_id, amount=amount, eta_days=days, eta_date=eta_date, distance_km=distance)


@router.post("/pay-mock", response_model=PayResponse)
def pay_mock(req: PayRequest):
    card = req.card_number.replace(" ", "")
    if card == "4000000000009995":
        brand = "visa_decline"
        status = "declined"
        message = "Платёж отклонён"
        txn = None
    else:
        brand = detect_brand(card)
        if brand == 'unknown' or (not card.isdigit()) or len(card) != 16:
            raise HTTPException(status_code=400, detail="Номер карты некорректен")
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

    items_for_calc = []
    try:
        itms = json.loads(row[0]) if row and row[0] else []
        for it in itms:
            class _I: ...
            o = _I(); o.id = it.get("id"); o.qty = it.get("qty", 1); items_for_calc.append(o)
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

