"""Shop discovery via OpenStreetMap (Nominatim geocoding + Overpass API).

Free and key-less, so anyone can run the tool right after cloning.
Please respect the OSM usage policy: keep request rates modest.
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass

USER_AGENT = "shop-research-tool/1.0 (lead research; contact via GitHub issues)"
NOMINATIM = "https://nominatim.openstreetmap.org/search"
OVERPASS = "https://overpass-api.de/api/interpreter"

# Industry presets: label -> list of Overpass tag filters (key=value)
INDUSTRY_PRESETS: dict[str, list[tuple[str, str]]] = {
    "美容室": [("shop", "hairdresser")],
    "カフェ": [("amenity", "cafe")],
    "飲食店": [("amenity", "restaurant"), ("amenity", "fast_food")],
    "居酒屋": [("amenity", "pub"), ("amenity", "bar")],
    "パン屋": [("shop", "bakery")],
    "花屋": [("shop", "florist")],
    "整体・マッサージ": [("shop", "massage"), ("healthcare", "alternative")],
    "歯科": [("amenity", "dentist"), ("healthcare", "dentist")],
    "自動車整備": [("shop", "car_repair")],
    "ペット": [("shop", "pet"), ("amenity", "veterinary")],
    "学習塾": [("amenity", "prep_school"), ("office", "tutoring")],
    "不動産": [("office", "estate_agent")],
}


@dataclass
class Shop:
    name: str
    address: str = ""
    phone: str = ""
    website: str = ""
    category: str = ""
    lat: float | None = None
    lon: float | None = None


def _get_json(url: str, timeout: float = 30.0):
    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:  # transient 5xx / rate limits from OSM services
            last_exc = exc
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"データ取得に失敗しました（3回試行）: {last_exc}")


def geocode(area: str) -> tuple[float, float]:
    params = urllib.parse.urlencode({"q": area, "format": "json", "limit": 1})
    results = _get_json(f"{NOMINATIM}?{params}")
    if not results:
        raise ValueError(f"エリアが見つかりませんでした: {area}")
    return float(results[0]["lat"]), float(results[0]["lon"])


def search_shops(area: str, industry: str, radius_m: int = 1500, limit: int = 50) -> list[Shop]:
    if industry not in INDUSTRY_PRESETS:
        raise ValueError(
            f"未対応の業種です: {industry}（対応: {', '.join(INDUSTRY_PRESETS)}）"
        )
    lat, lon = geocode(area)
    filters = INDUSTRY_PRESETS[industry]
    clauses = []
    for key, value in filters:
        clauses.append(f'node["{key}"="{value}"](around:{radius_m},{lat},{lon});')
        clauses.append(f'way["{key}"="{value}"](around:{radius_m},{lat},{lon});')
    query = f"[out:json][timeout:60];({''.join(clauses)});out center tags {limit * 2};"

    url = f"{OVERPASS}?data={urllib.parse.quote(query)}"
    data = _get_json(url, timeout=90.0)

    shops: list[Shop] = []
    seen: set[str] = set()
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        name = tags.get("name", "").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        addr_parts = [
            tags.get("addr:full", ""),
            "".join(
                tags.get(k, "")
                for k in ("addr:province", "addr:city", "addr:suburb", "addr:quarter")
            ),
            tags.get("addr:street", ""),
            tags.get("addr:housenumber", ""),
        ]
        address = " ".join(p for p in addr_parts if p).strip()
        website = tags.get("website") or tags.get("contact:website") or ""
        phone = tags.get("phone") or tags.get("contact:phone") or ""
        center = el.get("center", {})
        shops.append(
            Shop(
                name=name,
                address=address,
                phone=phone,
                website=website.strip(),
                category=industry,
                lat=center.get("lat", el.get("lat")),
                lon=center.get("lon", el.get("lon")),
            )
        )
        if len(shops) >= limit:
            break
    return shops
