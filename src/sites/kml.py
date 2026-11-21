"""
Minimal, defensive KML polygon reader (standard library only).

Reads exactly ONE ``Polygon`` outer ring from a Google Earth KML. It rejects XML with DTD/entity
declarations (entity-expansion attacks), oversized input, multiple polygons/MultiGeometry with several
polygons, and inner rings (holes). KML coordinates are ``longitude,latitude[,altitude]``.

Error messages never contain coordinates or file contents.
"""

from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass

MAX_KML_BYTES = 2 * 1024 * 1024
_FORBIDDEN = re.compile(rb"<!\s*(DOCTYPE|ENTITY)", re.IGNORECASE)


class KmlError(ValueError):
    """The KML could not be read as a single valid polygon."""


@dataclass(frozen=True)
class KmlPolygon:
    ring: list[tuple[float, float]]     # (lon, lat) exactly as listed, closed or not (validated elsewhere)
    point_placemarks: int               # informational: Points are ignored, never used as the boundary
    altitude_present: bool              # altitude values are dropped


def _local(tag) -> str:
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def _parse_coordinates(text: str) -> tuple[list[tuple[float, float]], bool]:
    ring: list[tuple[float, float]] = []
    altitude = False
    for index, token in enumerate(text.split(), start=1):
        parts = token.split(",")
        if len(parts) not in (2, 3):
            raise KmlError(f"coordinate {index} is not 'longitude,latitude[,altitude]'")
        try:
            values = [float(p) for p in parts]
        except ValueError:
            raise KmlError(f"coordinate {index} is not numeric") from None
        if not all(math.isfinite(v) for v in values):
            raise KmlError(f"coordinate {index} is not finite")
        lon, lat = values[0], values[1]
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            raise KmlError(f"coordinate {index} is outside the valid longitude/latitude range")
        if len(values) == 3 and values[2] != 0:
            altitude = True
        ring.append((lon, lat))
    return ring, altitude


def parse_kml_polygon(data: bytes) -> KmlPolygon:
    if len(data) > MAX_KML_BYTES:
        raise KmlError("KML file is larger than the 2 MiB safety limit")
    if _FORBIDDEN.search(data):
        raise KmlError("KML with DTD or entity declarations is not accepted")
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        raise KmlError("KML is not well-formed XML") from None

    polygons = [el for el in root.iter() if _local(el.tag) == "Polygon"]
    if not polygons:
        raise KmlError("KML contains no Polygon")
    if len(polygons) > 1:
        raise KmlError(f"KML contains {len(polygons)} polygons; exactly one is required")
    polygon = polygons[0]

    children = {_local(c.tag): c for c in polygon}
    if any(_local(el.tag) == "innerBoundaryIs" for el in polygon):
        raise KmlError("polygons with inner rings (holes) are not supported")
    outer = children.get("outerBoundaryIs")
    if outer is None:
        raise KmlError("Polygon has no outer boundary")
    rings = [el for el in outer.iter() if _local(el.tag) == "LinearRing"]
    if len(rings) != 1:
        raise KmlError("outer boundary must contain exactly one LinearRing")
    coords = [el for el in rings[0].iter() if _local(el.tag) == "coordinates"]
    if len(coords) != 1 or not (coords[0].text or "").strip():
        raise KmlError("LinearRing must contain one non-empty coordinates element")
    ring, altitude = _parse_coordinates(coords[0].text)
    points = sum(1 for el in root.iter() if _local(el.tag) == "Point")
    return KmlPolygon(ring=ring, point_placemarks=points, altitude_present=altitude)
