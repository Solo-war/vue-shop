from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pathlib import Path
import json
import re

from config import DATA_FILE, BACK_TEE_IMAGES_DIR, FRONT_TEE_IMAGES_DIR

router = APIRouter()


@router.get("/health/live")
async def health() -> dict:
    return {"status": "ok"}


@router.get("/products")
async def products():
    try:
        with DATA_FILE.open(encoding="utf-8") as f:
            data = json.load(f)

        images_map: dict[str, list[str]] = {}
        try:
            scan_dir = BACK_TEE_IMAGES_DIR if BACK_TEE_IMAGES_DIR.exists() else FRONT_TEE_IMAGES_DIR
            if scan_dir.exists():
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
                    def sort_key(n: str) -> tuple[int, str]:
                        m = re.search(r"_(\d+)", n)
                        return (int(m.group(1)) if m else 0, n)
                    sorted_names = sorted(names, key=sort_key)

                    # Heuristic: consider index _6 or keyworded filenames as size-chart
                    def is_chart(n: str) -> bool:
                        if re.search(r"_(6)\.", n):
                            return True
                        return re.search(r"(chart|size|sizing|dimension|guide|table|таблиц|размер)", n, flags=re.I) is not None

                    chart = next((n for n in sorted_names if is_chart(n)), None)
                    non_chart = [n for n in sorted_names if n != chart]
                    take = 4 if chart else 5
                    picked = [n for n in non_chart if re.search(r"_(\d+)\.", n)][:take]
                    if chart:
                        picked.append(chart)
                    if len(picked) == 5:
                        images_map[key] = [f"/images/tees/images/{n}" for n in picked]
        except Exception:
            images_map = {}

        ordered_groups = sorted(images_map.keys(), key=lambda k: int(k)) if images_map else []

        def slugify(name: str) -> str:
            s = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-")
            return s.lower()

        result = []
        for i, item in enumerate(data if isinstance(data, list) else []):
            item = dict(item)
            if i < len(ordered_groups):
                gid = ordered_groups[i]
                imgs = images_map.get(gid) or []
                item["id"] = int(gid)
                if imgs:
                    item["images"] = imgs
                    item["image"] = imgs[0]
            else:
                item.setdefault("id", i)
                imgs = item.get("images") or []
                if imgs:
                    item["image"] = imgs[0]
            if item.get("name"):
                item["slug"] = slugify(str(item["name"]))
            result.append(item)

        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
