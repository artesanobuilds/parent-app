"""Offline ZIP → nearby-towns lookup for grounding the discovery radius.

The research agent used to receive only a bare ZIP + a soft "within about N miles"
sentence, so it invented town names from LLM memory and anchored on the nearest
famous city (e.g. Santa Rosa for 95448) — never searching smaller towns well
inside the radius (Sebastopol). This module gives the radius real geographic
grounding: it enumerates the actual towns within the radius so the prompt can
tell the agent to cover a spread of them.

Data: a bundled, gzipped trim of the GeoNames US postal dataset (public domain,
CC-BY) at `data/us_zip_centroids.csv.gz` — `zip,lat,lng,city,state`, one centroid
per ZIP. Deterministic, no runtime network (Railway is egress-only), no new
runtime dependency (stdlib csv + math). Loaded once into memory on first use;
callers run in the research worker, off the request path.
"""
from __future__ import annotations

import csv
import gzip
import math
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_DATA_PATH = Path(__file__).resolve().parent / "data" / "us_zip_centroids.csv.gz"

# zip -> (lat, lng, city, state). Loaded lazily under a lock.
_ZIPS: Optional[Dict[str, Tuple[float, float, str, str]]] = None
_LOAD_LOCK = threading.Lock()

_EARTH_RADIUS_MI = 3958.7613


def _load() -> Dict[str, Tuple[float, float, str, str]]:
    global _ZIPS
    if _ZIPS is not None:
        return _ZIPS
    with _LOAD_LOCK:
        if _ZIPS is not None:  # another thread won the race
            return _ZIPS
        table: Dict[str, Tuple[float, float, str, str]] = {}
        try:
            with gzip.open(_DATA_PATH, "rt", encoding="utf-8", newline="") as f:
                for row in csv.DictReader(f):
                    try:
                        table[row["zip"]] = (
                            float(row["lat"]), float(row["lng"]),
                            row["city"], row["state"],
                        )
                    except (KeyError, ValueError):
                        continue
        except FileNotFoundError:
            # Missing dataset must not break discovery — callers degrade to the
            # old bare-ZIP behavior when the table is empty.
            pass
        _ZIPS = table
        return _ZIPS


# (city_lower, state_upper) -> (lat, lng). Built lazily from the same table.
_CITY_INDEX: Optional[Dict[Tuple[str, str], Tuple[float, float]]] = None


def _city_index() -> Dict[Tuple[str, str], Tuple[float, float]]:
    global _CITY_INDEX
    if _CITY_INDEX is not None:
        return _CITY_INDEX
    with _LOAD_LOCK:
        if _CITY_INDEX is not None:
            return _CITY_INDEX
        idx: Dict[Tuple[str, str], Tuple[float, float]] = {}
        for lat, lng, city, state in _load().values():
            key = (city.strip().lower(), state.strip().upper())
            idx.setdefault(key, (lat, lng))  # first ZIP centroid for the town
        _CITY_INDEX = idx
        return _CITY_INDEX


def distance_for_city(
    postal_code: Optional[str], city: Optional[str], region: Optional[str] = None
) -> Optional[float]:
    """Straight-line miles from `postal_code` to `city` (in `region`/state), for
    the "Nearest" sort. Returns None when the ZIP or town can't be resolved (the
    candidate then sorts last under Nearest). If `region` is missing, prefer a
    same-state match with the origin, else any state with that city name."""
    if not postal_code or not city:
        return None
    origin = _load().get(str(postal_code).strip()[:5])
    if origin is None:
        return None
    olat, olng, _, ostate = origin
    idx = _city_index()
    cl = city.strip().lower()
    coords = None
    if region:
        coords = idx.get((cl, region.strip().upper()))
    if coords is None:
        coords = idx.get((cl, ostate.strip().upper()))  # same state as the parent
    if coords is None:  # any state with that town name
        coords = next((v for (c, _s), v in idx.items() if c == cl), None)
    if coords is None:
        return None
    return round(_haversine_mi(olat, olng, coords[0], coords[1]), 1)


def _haversine_mi(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return _EARTH_RADIUS_MI * 2 * math.asin(math.sqrt(a))


def nearby_towns(
    postal_code: Optional[str],
    radius_miles: float,
    *,
    max_towns: int = 20,
    outer_band: int = 5,
) -> List[Dict[str, object]]:
    """Distinct towns within `radius_miles` of `postal_code`, deduped by
    (city, state), returned nearest-first with the origin town first.

    When more towns fall in the radius than `max_towns`, the selection SPANS the
    radius rather than just taking the closest cluster: it keeps the nearest
    `max_towns - outer_band` towns AND the farthest `outer_band` towns inside the
    radius. That way a 50-mile search actually reaches the far towns the parent
    asked for (Petaluma, Sonoma, Napa…) instead of stopping ~16 miles out — while
    still guaranteeing the dense nearby cluster.

    Returns `[{"city": str, "state": str, "distance_mi": float}, ...]`, or `[]`
    when the ZIP is unknown or the dataset is missing — the caller then degrades
    to the old un-grounded behavior (a plain "within N miles" instruction).
    """
    if not postal_code or radius_miles <= 0:
        return []
    table = _load()
    zc = str(postal_code).strip()[:5]
    origin = table.get(zc)
    if origin is None:
        return []
    olat, olng, ocity, ostate = origin

    # Best (shortest) distance per (city, state) within the radius.
    best: Dict[Tuple[str, str], float] = {}
    for lat, lng, city, state in table.values():
        d = _haversine_mi(olat, olng, lat, lng)
        if d > radius_miles:
            continue
        key = (city, state)
        if key not in best or d < best[key]:
            best[key] = d

    best[(ocity, ostate)] = 0.0  # origin always included, distance 0
    ordered = sorted(best.items(), key=lambda kv: kv[1])

    if len(ordered) > max_towns and outer_band > 0:
        # Nearest cluster + the farthest band inside the radius, re-sorted so the
        # combined list stays nearest-first (and any overlap is de-duplicated).
        near = ordered[: max_towns - outer_band]
        far = ordered[-outer_band:]
        merged = {key: dist for key, dist in near}
        for key, dist in far:
            merged.setdefault(key, dist)
        ordered = sorted(merged.items(), key=lambda kv: kv[1])
    else:
        ordered = ordered[:max_towns]

    return [
        {"city": city, "state": state, "distance_mi": round(dist, 1)}
        for (city, state), dist in ordered
    ]


# ── Timezone from ZIP (vertical expansion Phase 4 — registration windows) ────
# A state→IANA map is deliberately coarse: registration-window notifications
# care about the LOCAL DAY, and a state-level tz gets that right for the beta
# footprint (split-tz states default to their dominant zone). Falls back to
# Pacific — the beta metro — when the ZIP is unknown.

_STATE_TZ = {
    "AL": "America/Chicago", "AK": "America/Anchorage", "AZ": "America/Phoenix",
    "AR": "America/Chicago", "CA": "America/Los_Angeles", "CO": "America/Denver",
    "CT": "America/New_York", "DE": "America/New_York", "DC": "America/New_York",
    "FL": "America/New_York", "GA": "America/New_York", "HI": "Pacific/Honolulu",
    "ID": "America/Boise", "IL": "America/Chicago", "IN": "America/Indiana/Indianapolis",
    "IA": "America/Chicago", "KS": "America/Chicago", "KY": "America/New_York",
    "LA": "America/Chicago", "ME": "America/New_York", "MD": "America/New_York",
    "MA": "America/New_York", "MI": "America/Detroit", "MN": "America/Chicago",
    "MS": "America/Chicago", "MO": "America/Chicago", "MT": "America/Denver",
    "NE": "America/Chicago", "NV": "America/Los_Angeles", "NH": "America/New_York",
    "NJ": "America/New_York", "NM": "America/Denver", "NY": "America/New_York",
    "NC": "America/New_York", "ND": "America/Chicago", "OH": "America/New_York",
    "OK": "America/Chicago", "OR": "America/Los_Angeles", "PA": "America/New_York",
    "RI": "America/New_York", "SC": "America/New_York", "SD": "America/Chicago",
    "TN": "America/Chicago", "TX": "America/Chicago", "UT": "America/Denver",
    "VT": "America/New_York", "VA": "America/New_York", "WA": "America/Los_Angeles",
    "WV": "America/New_York", "WI": "America/Chicago", "WY": "America/Denver",
}

DEFAULT_TZ = "America/Los_Angeles"


def tz_for_postal(postal_code: Optional[str]) -> str:
    """IANA timezone for a US ZIP, defaulting to the beta metro's Pacific."""
    if postal_code:
        entry = _load().get(str(postal_code).strip()[:5])
        if entry:
            return _STATE_TZ.get(entry[3].strip().upper(), DEFAULT_TZ)
    return DEFAULT_TZ
