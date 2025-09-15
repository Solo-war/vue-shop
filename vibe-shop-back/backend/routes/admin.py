from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from security import require_admin, oauth2_scheme
from schemas import OrderItemOut, OrderOut
from config import DB_FILE, DATA_FILE, BACK_TEE_IMAGES_DIR
from utils import parse_items
import sqlite3
import json
import re
from pathlib import Path
from typing import Optional
from jose import jwt
from config import SECRET_KEY, ALGORITHM

router = APIRouter()


@router.get("/admin/orders")
def admin_orders(_: str = Depends(require_admin)):
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
                "items": parse_items(items_raw),
                "amount": amount,
                "created_at": created_at,
                "geo_lat": geo_lat,
                "geo_lon": geo_lon,
            }
        )
    return result


@router.get("/admin/payments")
def admin_payments(_: str = Depends(require_admin)):
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


@router.get("/my-orders")
def my_orders(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
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
        parsed_items = parse_items(items_raw)
        items: list[OrderItemOut] = []
        for it in parsed_items:
            try:
                items.append(
                    OrderItemOut(
                        id=int(it.get("id")),
                        name=str(it.get("name")),
                        price=int(it.get("price")),
                        qty=int(it.get("qty", 1)),
                    )
                )
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


# ===== Admin: Products management =====

def _scan_images_map() -> dict[str, list[str]]:
    images_map: dict[str, list[str]] = {}
    try:
        scan_dir = BACK_TEE_IMAGES_DIR
        scan_dir.mkdir(parents=True, exist_ok=True)
        files = [p.name for p in scan_dir.iterdir() if p.is_file()]
        tmp: dict[str, list[str]] = {}
        for name in files:
            if not re.search(r"\.(jpe?g|png|webp)$", name, flags=re.I):
                continue
            parts = name.split("_", 1)
            if len(parts) < 2:
                continue
            key = parts[0]
            tmp.setdefault(key, []).append(name)
        for key, names in tmp.items():
            def sort_key(n: str):
                m = re.search(r"_(\d+)", n)
                return (int(m.group(1)) if m else 0, n)
            sorted_names = sorted(names, key=sort_key)
            images_map[key] = [f"/images/tees/images/{n}" for n in sorted_names]
    except Exception:
        images_map = {}
    return images_map


@router.get("/admin/products")
def admin_products(_: str = Depends(require_admin)):
    try:
        with DATA_FILE.open(encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            data = []
    except Exception:
        data = []

    images_map = _scan_images_map()
    ordered_groups = sorted(images_map.keys(), key=lambda k: int(k)) if images_map else []

    result = []
    for i, item in enumerate(data):
        item = dict(item)
        pid: Optional[int] = None
        imgs: list[str] = []
        if i < len(ordered_groups):
            gid = ordered_groups[i]
            pid = int(gid)
            imgs = images_map.get(gid, [])
        else:
            pid = i
            imgs = item.get("images") or []
        result.append(
            {
                "index": i,  # position in products.json
                "id": pid,    # numeric id tied to image group when available
                "name": item.get("name"),
                "price": item.get("price"),
                "description": item.get("description"),
                "images": imgs,
            }
        )
    return JSONResponse(content=result)


@router.put("/admin/products/{index}")
def admin_update_product(index: int, payload: dict, _: str = Depends(require_admin)):
    # Update name, price, description for item at given index in products.json
    try:
        with DATA_FILE.open(encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise HTTPException(status_code=500, detail="Invalid products.json format")
        if index < 0 or index >= len(data):
            raise HTTPException(status_code=404, detail="Product index out of range")
        item = dict(data[index]) if isinstance(data[index], dict) else {}
        for key in ("name", "price", "description"):
            if key in payload:
                item[key] = payload[key]
        data[index] = item
        DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/products/{pid}/images")
async def admin_replace_images(
    pid: int,
    files: list[UploadFile] = File(...),
    replace: bool = Query(True, description="Replace existing images for this product id"),
    _: str = Depends(require_admin),
):
    # Save uploaded images for product id as <pid>_1.ext, <pid>_2.ext ...
    BACK_TEE_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    # Optionally remove existing images for this id
    if replace:
        for p in BACK_TEE_IMAGES_DIR.iterdir():
            if p.is_file() and p.name.startswith(f"{pid}_"):
                try:
                    p.unlink()
                except Exception:
                    pass

    counter = 1
    # find max existing suffix to continue numbering if not replacing
    if not replace:
        for p in BACK_TEE_IMAGES_DIR.iterdir():
            m = re.match(rf"^{pid}_(\d+)\.", p.name)
            if m:
                try:
                    counter = max(counter, int(m.group(1)) + 1)
                except Exception:
                    pass

    saved = []
    for f in files:
        try:
            suffix = Path(f.filename).suffix.lower()
            if suffix not in (".jpg", ".jpeg", ".png", ".webp"):
                continue
            name = f"{pid}_{counter}{suffix}"
            target = BACK_TEE_IMAGES_DIR / name
            with open(target, "wb") as out:
                out.write(await f.read())
            saved.append(f"/images/tees/images/{name}")
            counter += 1
        except Exception:
            continue
    return {"saved": saved}


@router.delete("/admin/products/{pid}/images")
def admin_delete_all_images(pid: int, _: str = Depends(require_admin)):
    BACK_TEE_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    deleted = 0
    for p in BACK_TEE_IMAGES_DIR.iterdir():
        if p.is_file() and p.name.startswith(f"{pid}_"):
            try:
                p.unlink()
                deleted += 1
            except Exception:
                pass
    return {"deleted": deleted}


@router.delete("/admin/products/{pid}/images/{filename}")
def admin_delete_image(pid: int, filename: str, _: str = Depends(require_admin)):
    # Delete a specific image if it belongs to this product id
    p = BACK_TEE_IMAGES_DIR / filename
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    if not re.match(rf"^{pid}_", p.name):
        raise HTTPException(status_code=400, detail="Filename does not match product id")
    try:
        p.unlink()
        return {"deleted": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
