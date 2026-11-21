"""Synthetic fixtures for the research-site tests. Every coordinate here is invented: nothing is real."""

from __future__ import annotations

import math
from pathlib import Path

import yaml

# Invented location (central India, nowhere near any real research site).
LON0, LAT0 = 80.0, 20.0
SITE_ID = "TEST_SITE_001"

E2 = 0.00669437999014131705
E = math.sqrt(E2)
B = 6356752.314245179


def graticule_area(lon1: float, lon2: float, lat1: float, lat2: float) -> float:
    """Exact WGS84 area (m2) of the region bounded by two meridians and two parallels."""
    def f(deg):
        s = math.sin(math.radians(deg))
        return s / (2 * (1 - E2 * s * s)) + math.log((1 + E * s) / (1 - E * s)) / (4 * E)
    return B * B * math.radians(abs(lon2 - lon1)) * abs(f(lat2) - f(lat1))


def meridian_arc(lat1: float, lat2: float, steps: int = 2000) -> float:
    """WGS84 meridian arc length (m) by Simpson integration of the meridional radius of curvature."""
    a = 6378137.0
    h = math.radians(lat2 - lat1) / steps

    def m(deg):
        s = math.sin(math.radians(deg))
        return a * (1 - E2) / (1 - E2 * s * s) ** 1.5
    total = m(lat1) + m(lat2)
    for i in range(1, steps):
        total += (4 if i % 2 else 2) * m(lat1 + (lat2 - lat1) * i / steps)
    return total * h / 3


def square(lon0: float = LON0, lat0: float = LAT0, d: float = 0.001):
    """Closed counter-clockwise ring, d degrees on a side (about 100 m for d=0.001)."""
    return [(lon0, lat0), (lon0 + d, lat0), (lon0 + d, lat0 + d), (lon0, lat0 + d), (lon0, lat0)]


def coords_text(ring, altitude: bool = False) -> str:
    return " ".join(f"{lon!r},{lat!r}" + (",12.5" if altitude else "") for lon, lat in ring)


def kml(ring=None, *, namespace: bool = True, altitude: bool = False, holes: bool = False,
        extra_polygon: bool = False, points: int = 0, raw_coordinates: str | None = None) -> bytes:
    ring = ring if ring is not None else square()
    ns = ' xmlns="http://www.opengis.net/kml/2.2"' if namespace else ""
    text = raw_coordinates if raw_coordinates is not None else coords_text(ring, altitude)
    inner = ""
    if holes:
        inner = f"<innerBoundaryIs><LinearRing><coordinates>{coords_text(square(LON0 + 0.0003, LAT0 + 0.0003, 0.0002))}</coordinates></LinearRing></innerBoundaryIs>"
    polygon = (f"<Polygon><outerBoundaryIs><LinearRing><coordinates>{text}</coordinates></LinearRing>"
               f"</outerBoundaryIs>{inner}</Polygon>")
    body = f"<Placemark><name>synthetic</name>{polygon}</Placemark>"
    if extra_polygon:
        body += f"<Placemark>{polygon}</Placemark>"
    for _ in range(points):
        body += f"<Placemark><Point><coordinates>{LON0},{LAT0}</coordinates></Point></Placemark>"
    return f'<?xml version="1.0" encoding="UTF-8"?><kml{ns}><Document>{body}</Document></kml>'.encode("utf-8")


def make_private(tmp_path: Path, ring=None, *, site_id: str = SITE_ID, expected: dict | None = None,
                 reference=None, comparison=None, write_kml: bool = False, extra: dict | None = None) -> Path:
    """Create ``<tmp>/private/sites/<site_id>/site.yaml`` (+ optional boundary.kml). Returns the private root."""
    ring = ring if ring is not None else square()
    root = tmp_path / "private"
    site_dir = root / "sites" / site_id
    site_dir.mkdir(parents=True)
    lon, lat = reference if reference is not None else (LON0 + 0.0005, LAT0 + 0.0005)
    cfg = {
        "schema_version": 1, "site_id": site_id, "site_type": "mango_orchard",
        "reference_point": {"latitude": lat, "longitude": lon},
        "comparison_points": comparison if comparison is not None else [
            {"label": "original_study_point", "latitude": LAT0 + 0.01, "longitude": LON0 + 0.01, "expected": "outside"}],
        "boundary": {"expected": expected or {}},
    }
    cfg.update(extra or {})
    (site_dir / "site.yaml").write_text(yaml.safe_dump(cfg), encoding="utf-8")
    if write_kml:
        (site_dir / "boundary.kml").write_bytes(kml(ring))
    return root
