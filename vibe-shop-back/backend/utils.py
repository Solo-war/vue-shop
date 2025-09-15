import datetime
import json
import math
import re
import shutil
from pathlib import Path

from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from config import (
    BACK_IMAGES_ROOT,
    BACK_TEE_IMAGES_DIR,
    FRONT_TEE_IMAGES_DIR,
    DATA_FILE,
    NOVOSIB,
)


def ensure_images_synced() -> None:
    try:
        BACK_TEE_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        back_has_any = any(BACK_TEE_IMAGES_DIR.glob("*"))
        if (not back_has_any) and FRONT_TEE_IMAGES_DIR.exists():
            for p in FRONT_TEE_IMAGES_DIR.iterdir():
                if p.is_file() and re.search(r"\.(jpe?g|png|webp)$", p.name, flags=re.I):
                    shutil.copy2(p, BACK_TEE_IMAGES_DIR / p.name)
    except Exception:
        pass


def mount_images(app: FastAPI) -> None:
    try:
        BACK_IMAGES_ROOT.mkdir(parents=True, exist_ok=True)
        app.mount("/images", StaticFiles(directory=str(BACK_IMAGES_ROOT)), name="images")
    except Exception:
        pass


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
    if len(num) in (13, 16, 19) and num.startswith("4"):
        return "visa"
    if len(num) == 16 and num.isdigit():
        first2 = int(num[:2])
        first4 = int(num[:4])
        first6 = int(num[:6])
        if 51 <= first2 <= 55:
            return "mastercard"
        if 2221 <= first4 <= 2720 or 222100 <= first6 <= 272099:
            return "mastercard"
    if len(num) == 16 and num.isdigit():
        first4 = int(num[:4])
        if 2200 <= first4 <= 2204:
            return "mir"
    return "unknown"


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def calc_eta(items: list, geo_lat: float | None, geo_lon: float | None) -> tuple[int, str, int]:
    total_qty = sum(getattr(i, "qty", 0) for i in items) if items else 0
    unique_ids = len({getattr(i, "id", None) for i in items}) if items else 0
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


def parse_items(items_raw: str):
    if items_raw is None:
        return []
    try:
        data = json.loads(items_raw)
        if isinstance(data, list):
            return data
    except Exception:
        pass
    try:
        import ast

        data = ast.literal_eval(items_raw)
        if isinstance(data, list):
            return [dict(x) if isinstance(x, dict) else x for x in data]
    except Exception:
        pass
    return []

