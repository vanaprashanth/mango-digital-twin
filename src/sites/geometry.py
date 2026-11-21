"""
Polygon validation and WGS84 geodesic measurements (standard library only).

Methodology
-----------
* Area: exact on the WGS84 ellipsoid. Vertices are projected with the ellipsoidal Lambert azimuthal
  EQUAL-AREA projection (Snyder, "Map Projections - A Working Manual", eqs. 24-1..24-27) centred on the
  polygon, then the shoelace formula is applied. Because the projection preserves area exactly, the only
  approximation is that polygon edges are straight in the projection rather than geodesics; for parcel-sized
  polygons the sagitta is far below a millimetre.
* Perimeter: sum of WGS84 geodesic edge lengths from Vincenty's inverse formula (sub-millimetre for the
  short edges of a parcel).
* Validity: closed ring, enough vertices, finite in-range values, no self-intersection/touching, no
  zero-width spikes, non-degenerate area, sane parcel-scale extent. Orientation is normalised to
  counter-clockwise (RFC 7946) for output.
* Point location: ray casting in the same equal-area plane, with an on-boundary tolerance.

Error and warning messages never contain coordinates.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

# --- WGS84 ----------------------------------------------------------------------------------------------
SEMI_MAJOR = 6378137.0
FLATTENING = 1 / 298.257223563
SEMI_MINOR = SEMI_MAJOR * (1 - FLATTENING)
E2 = FLATTENING * (2 - FLATTENING)
E = math.sqrt(E2)

MIN_DISTINCT_VERTICES = 3
MAX_VERTICES = 5000
MAX_EXTENT_M = 50_000.0          # a research parcel, not a region; catches swapped/foreign geometry
MIN_AREA_M2 = 1.0
BOUNDARY_TOLERANCE_M = 0.01
SQUARE_METRES_PER_HECTARE = 10_000.0
SQUARE_METRES_PER_ACRE = 4046.8564224

Ring = list[tuple[float, float]]    # (longitude, latitude), closed: first == last


class GeometryError(ValueError):
    """A geometric computation could not be completed."""


# --- projection ---------------------------------------------------------------------------------------------

def _q(sin_phi: float) -> float:
    return (1 - E2) * (sin_phi / (1 - E2 * sin_phi ** 2)
                       - (1 / (2 * E)) * math.log((1 - E * sin_phi) / (1 + E * sin_phi)))


_QP = _q(1.0)


class EqualAreaProjection:
    """Ellipsoidal Lambert azimuthal equal-area projection on WGS84, centred on (lon0, lat0)."""

    def __init__(self, lon0: float, lat0: float):
        phi0 = math.radians(lat0)
        sin0 = math.sin(phi0)
        self._lam0 = math.radians(lon0)
        self._rq = SEMI_MAJOR * math.sqrt(_QP / 2)
        self._beta0 = math.asin(_q(sin0) / _QP)
        self._d = SEMI_MAJOR * math.cos(phi0) / math.sqrt(1 - E2 * sin0 ** 2) / (self._rq * math.cos(self._beta0))

    def forward(self, lon: float, lat: float) -> tuple[float, float]:
        phi = math.radians(lat)
        lam = math.radians(lon) - self._lam0
        lam = (lam + math.pi) % (2 * math.pi) - math.pi
        beta = math.asin(max(-1.0, min(1.0, _q(math.sin(phi)) / _QP)))
        denom = 1 + math.sin(self._beta0) * math.sin(beta) + math.cos(self._beta0) * math.cos(beta) * math.cos(lam)
        if denom <= 1e-12:
            raise GeometryError("a point is too far from the projection centre")
        b = self._rq * math.sqrt(2 / denom)
        x = b * self._d * math.cos(beta) * math.sin(lam)
        y = (b / self._d) * (math.cos(self._beta0) * math.sin(beta)
                             - math.sin(self._beta0) * math.cos(beta) * math.cos(lam))
        return x, y


def ring_centre(ring: Ring) -> tuple[float, float]:
    pts = ring[:-1] if len(ring) > 1 and ring[0] == ring[-1] else ring
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)


def project_ring(ring: Ring) -> list[tuple[float, float]]:
    proj = EqualAreaProjection(*ring_centre(ring))
    return [proj.forward(lon, lat) for lon, lat in ring]


# --- geodesic distance (Vincenty inverse) -----------------------------------------------------------------

def geodesic_distance(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """WGS84 geodesic distance in metres."""
    if lon1 == lon2 and lat1 == lat2:
        return 0.0
    big_l = math.radians(lon2 - lon1)
    u1 = math.atan((1 - FLATTENING) * math.tan(math.radians(lat1)))
    u2 = math.atan((1 - FLATTENING) * math.tan(math.radians(lat2)))
    sin_u1, cos_u1, sin_u2, cos_u2 = math.sin(u1), math.cos(u1), math.sin(u2), math.cos(u2)
    lam = big_l
    for _ in range(200):
        sin_lam, cos_lam = math.sin(lam), math.cos(lam)
        sin_sigma = math.hypot(cos_u2 * sin_lam, cos_u1 * sin_u2 - sin_u1 * cos_u2 * cos_lam)
        if sin_sigma == 0:
            return 0.0
        cos_sigma = sin_u1 * sin_u2 + cos_u1 * cos_u2 * cos_lam
        sigma = math.atan2(sin_sigma, cos_sigma)
        sin_alpha = cos_u1 * cos_u2 * sin_lam / sin_sigma
        cos2_alpha = 1 - sin_alpha ** 2
        cos_2sm = cos_sigma - 2 * sin_u1 * sin_u2 / cos2_alpha if cos2_alpha else 0.0
        c = FLATTENING / 16 * cos2_alpha * (4 + FLATTENING * (4 - 3 * cos2_alpha))
        prev = lam
        lam = big_l + (1 - c) * FLATTENING * sin_alpha * (
            sigma + c * sin_sigma * (cos_2sm + c * cos_sigma * (-1 + 2 * cos_2sm ** 2)))
        if abs(lam - prev) < 1e-12:
            break
    else:
        raise GeometryError("geodesic distance did not converge")
    u_sq = cos2_alpha * (SEMI_MAJOR ** 2 - SEMI_MINOR ** 2) / SEMI_MINOR ** 2
    big_a = 1 + u_sq / 16384 * (4096 + u_sq * (-768 + u_sq * (320 - 175 * u_sq)))
    big_b = u_sq / 1024 * (256 + u_sq * (-128 + u_sq * (74 - 47 * u_sq)))
    d_sigma = big_b * sin_sigma * (cos_2sm + big_b / 4 * (
        cos_sigma * (-1 + 2 * cos_2sm ** 2)
        - big_b / 6 * cos_2sm * (-3 + 4 * sin_sigma ** 2) * (-3 + 4 * cos_2sm ** 2)))
    return SEMI_MINOR * big_a * (sigma - d_sigma)


# --- planar helpers --------------------------------------------------------------------------------------------

def _signed_area(pts: list[tuple[float, float]]) -> float:
    total = 0.0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        total += x1 * y2 - x2 * y1
    return total / 2


def _cross(o, a, b) -> float:
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


TOUCH_TOLERANCE_M = 1e-3         # endpoints this close to another edge count as touching (parallels are
                                 # slightly curved in the equal-area plane, so exact collinearity never occurs)
SPIKE_ANGLE_RAD = 1e-4


def _segments_touch(a, b, c, d, eps: float = 1e-9) -> bool:
    """True if segments ab and cd properly cross, or an endpoint of one lies within TOUCH_TOLERANCE_M of the other."""
    d1, d2, d3, d4 = _cross(c, d, a), _cross(c, d, b), _cross(a, b, c), _cross(a, b, d)
    if ((d1 > eps and d2 < -eps) or (d1 < -eps and d2 > eps)) and ((d3 > eps and d4 < -eps) or (d3 < -eps and d4 > eps)):
        return True
    return (_distance_to_segment(a, c, d) <= TOUCH_TOLERANCE_M or _distance_to_segment(b, c, d) <= TOUCH_TOLERANCE_M
            or _distance_to_segment(c, a, b) <= TOUCH_TOLERANCE_M or _distance_to_segment(d, a, b) <= TOUCH_TOLERANCE_M)


def _has_self_intersection(pts: list[tuple[float, float]]) -> bool:
    """``pts`` = distinct vertices (no closing duplicate). Non-adjacent edges must not touch."""
    n = len(pts)
    edges = [(pts[i], pts[(i + 1) % n]) for i in range(n)]
    for i in range(n):
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue                      # adjacent through the closing edge
            if _segments_touch(*edges[i], *edges[j]):
                return True
    return False


def _has_spike(pts: list[tuple[float, float]]) -> bool:
    n = len(pts)
    for i in range(n):
        p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % n]
        v1, v2 = (p1[0] - p0[0], p1[1] - p0[1]), (p2[0] - p1[0], p2[1] - p1[1])
        n1, n2 = math.hypot(*v1), math.hypot(*v2)
        if n1 == 0 or n2 == 0:
            continue
        cross = v1[0] * v2[1] - v1[1] * v2[0]
        dot = v1[0] * v2[0] + v1[1] * v2[1]
        if abs(cross) <= SPIKE_ANGLE_RAD * n1 * n2 and dot < 0:
            return True
    return False


def _distance_to_segment(p, a, b) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    seg = dx * dx + dy * dy
    t = 0.0 if seg == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / seg))
    return math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy))


# --- validation ---------------------------------------------------------------------------------------------

@dataclass
class RingReport:
    valid: bool
    errors: list[str] = field(default_factory=list)       # machine-readable codes, no coordinates
    warnings: list[str] = field(default_factory=list)
    vertex_count: int = 0                                   # distinct vertices (closing duplicate excluded)
    orientation_input: str | None = None                    # "counter-clockwise" | "clockwise"
    area_m2: float | None = None
    perimeter_m: float | None = None
    extent_m: float | None = None                           # larger side of the projected bounding box
    normalized_ring: Ring | None = None                     # closed, counter-clockwise, duplicates removed

    @property
    def area_ha(self) -> float | None:
        return None if self.area_m2 is None else self.area_m2 / SQUARE_METRES_PER_HECTARE

    @property
    def area_acres(self) -> float | None:
        return None if self.area_m2 is None else self.area_m2 / SQUARE_METRES_PER_ACRE


def validate_ring(ring: Ring) -> RingReport:
    """Structural validity plus WGS84 area/perimeter. Never raises for bad geometry; see ``errors``."""
    rep = RingReport(valid=False)
    if len(ring) > MAX_VERTICES + 1:
        rep.errors.append("too_many_vertices")
        return rep
    if any(not (math.isfinite(lon) and math.isfinite(lat)) for lon, lat in ring):
        rep.errors.append("non_finite_coordinate")
        return rep
    if any(not (-180 <= lon <= 180 and -90 <= lat <= 90) for lon, lat in ring):
        rep.errors.append("coordinate_out_of_range")
        return rep
    if len(ring) < 2 or ring[0] != ring[-1]:
        rep.errors.append("ring_not_closed")
        return rep

    distinct: Ring = [ring[0]]
    duplicates = 0
    for p in ring[1:-1]:
        if p == distinct[-1]:
            duplicates += 1
        else:
            distinct.append(p)
    if distinct[-1] == distinct[0] and len(distinct) > 1:
        distinct.pop()
        duplicates += 1
    rep.vertex_count = len(distinct)
    if duplicates:
        rep.warnings.append("duplicate_consecutive_vertices_removed")
    if len(distinct) < MIN_DISTINCT_VERTICES:
        rep.errors.append("too_few_vertices")
        return rep

    closed = distinct + [distinct[0]]
    try:
        plane = project_ring(closed)
    except GeometryError:
        rep.errors.append("projection_failed")
        return rep
    xs, ys = [p[0] for p in plane], [p[1] for p in plane]
    rep.extent_m = max(max(xs) - min(xs), max(ys) - min(ys))
    if rep.extent_m > MAX_EXTENT_M:
        rep.errors.append("extent_too_large_for_a_parcel")
        return rep

    pts = plane[:-1]
    signed = _signed_area(plane)
    if _has_self_intersection(pts):
        rep.errors.append("self_intersecting")
    if _has_spike(pts):
        rep.errors.append("zero_width_spike")
    if abs(signed) < MIN_AREA_M2:
        rep.errors.append("degenerate_area")
    if rep.errors:
        return rep

    rep.orientation_input = "counter-clockwise" if signed > 0 else "clockwise"
    if signed < 0:
        rep.warnings.append("clockwise_orientation_normalised")
        closed = [closed[0]] + list(reversed(closed[1:-1])) + [closed[0]]
    rep.normalized_ring = closed
    rep.area_m2 = abs(signed)
    try:
        rep.perimeter_m = sum(geodesic_distance(a[0], a[1], b[0], b[1]) for a, b in zip(closed, closed[1:]))
    except GeometryError:
        rep.errors.append("perimeter_failed")
        return rep
    rep.valid = True
    return rep


# --- point location --------------------------------------------------------------------------------------------

def locate_point(lon: float, lat: float, ring: Ring, tolerance_m: float = BOUNDARY_TOLERANCE_M) -> str:
    """'inside' | 'outside' | 'boundary' for a point against a (valid) closed ring."""
    if not (math.isfinite(lon) and math.isfinite(lat) and -180 <= lon <= 180 and -90 <= lat <= 90):
        raise GeometryError("point coordinates are not valid")
    proj = EqualAreaProjection(*ring_centre(ring))
    pts = [proj.forward(a, b) for a, b in ring]
    try:
        px, py = proj.forward(lon, lat)
    except GeometryError:
        return "outside"
    p = (px, py)
    if any(_distance_to_segment(p, a, b) <= tolerance_m for a, b in zip(pts, pts[1:])):
        return "boundary"
    inside = False
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        if (y1 > py) != (y2 > py):
            if px < (x2 - x1) * (py - y1) / (y2 - y1) + x1:
                inside = not inside
    return "inside" if inside else "outside"
