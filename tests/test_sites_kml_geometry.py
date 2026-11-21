"""KML parsing and geometry validation for the research-site tools (synthetic polygons only)."""

from __future__ import annotations

import math
import random

import pytest

from sites_fakes import LAT0, LON0, graticule_area, kml, meridian_arc, square
from src.sites import geometry as geo
from src.sites.kml import MAX_KML_BYTES, KmlError, parse_kml_polygon


# --- KML parsing -------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("namespace", [True, False])
def test_parses_a_polygon_with_or_without_the_kml_namespace(namespace):
    parsed = parse_kml_polygon(kml(namespace=namespace))
    assert parsed.ring == square() and parsed.point_placemarks == 0 and not parsed.altitude_present


def test_altitude_is_dropped_and_flagged_and_points_are_ignored():
    parsed = parse_kml_polygon(kml(altitude=True, points=2))
    assert parsed.altitude_present and parsed.point_placemarks == 2
    assert all(len(p) == 2 for p in parsed.ring)


@pytest.mark.parametrize("data,fragment", [
    (kml(extra_polygon=True), "2 polygons"),
    (kml(holes=True), "inner rings"),
    (b"<kml><Document></Document></kml>", "no Polygon"),
    (b"<kml><Document>", "not well-formed"),
    (kml(raw_coordinates=""), "non-empty"),
    (kml(raw_coordinates="80.0,20.0 abc,def 80.1,20.1"), "not numeric"),
    (kml(raw_coordinates="80.0 20.0"), "longitude,latitude"),
    (kml(raw_coordinates="1,2,3,4 5,6"), "longitude,latitude"),
    (kml(raw_coordinates="80.0,95.0 81.0,20.0"), "range"),
    (kml(raw_coordinates="nan,20.0 81.0,20.0"), "finite"),
])
def test_rejects_unusable_kml(data, fragment):
    with pytest.raises(KmlError, match=fragment):
        parse_kml_polygon(data)


def test_rejects_entity_expansion_and_oversized_input():
    bomb = (b'<?xml version="1.0"?><!DOCTYPE lolz [<!ENTITY a "aaaaaaaaaa"><!ENTITY b "&a;&a;&a;&a;&a;">]>'
            b"<kml><Document>&b;</Document></kml>")
    with pytest.raises(KmlError, match="DTD"):
        parse_kml_polygon(bomb)
    with pytest.raises(KmlError, match="2 MiB"):
        parse_kml_polygon(b" " * (MAX_KML_BYTES + 1))


def test_kml_errors_never_contain_coordinates():
    secret = "200.123456789,10.987654321"
    with pytest.raises(KmlError) as exc:
        parse_kml_polygon(kml(raw_coordinates=f"{secret} 80.0,20.0"))
    assert "123456789" not in str(exc.value) and "987654321" not in str(exc.value)


# --- exact reference values ----------------------------------------------------------------------------------------------

@pytest.mark.parametrize("lat0", [0.0, 13.0, 20.0, 45.0, -33.0])
def test_area_matches_the_exact_wgs84_graticule_formula(lat0):
    ring = square(LON0, lat0, 0.002)                                    # about 220 m on a side
    rep = geo.validate_ring(ring)
    exact = graticule_area(LON0, LON0 + 0.002, lat0, lat0 + 0.002)
    assert rep.valid and rep.area_m2 == pytest.approx(exact, rel=1e-7)


def test_orchard_sized_area_is_accurate_to_a_tiny_fraction_of_a_percent():
    ring = square(LON0, LAT0, 0.0022)                                   # roughly 5-6 ha
    rep = geo.validate_ring(ring)
    assert 4.5e4 < rep.area_m2 < 7e4
    assert abs(rep.area_m2 - graticule_area(LON0, LON0 + 0.0022, LAT0, LAT0 + 0.0022)) / rep.area_m2 < 1e-8


@pytest.mark.parametrize("lat1,lat2", [(0.0, 1.0), (13.0, 13.009), (45.0, 45.5)])
def test_meridian_distance_matches_numeric_integration(lat1, lat2):
    d = geo.geodesic_distance(80.0, lat1, 80.0, lat2)
    assert d == pytest.approx(meridian_arc(lat1, lat2), abs=1e-4)


def test_vincenty_classic_flinders_peak_to_buninyong():
    # Vincenty (1975) worked example: 54972.271 m
    lat1 = -(37 + 57 / 60 + 3.72030 / 3600)
    lon1 = 144 + 25 / 60 + 29.52440 / 3600
    lat2 = -(37 + 39 / 60 + 10.15610 / 3600)
    lon2 = 143 + 55 / 60 + 35.38390 / 3600
    assert geo.geodesic_distance(lon1, lat1, lon2, lat2) == pytest.approx(54972.271, abs=0.005)


def test_zero_distance_and_symmetry():
    assert geo.geodesic_distance(80, 20, 80, 20) == 0.0
    a = geo.geodesic_distance(80.0, 20.0, 80.002, 20.001)
    assert a == pytest.approx(geo.geodesic_distance(80.002, 20.001, 80.0, 20.0), abs=1e-9)


def test_independent_check_against_pyproj_geodesic_polygons():
    pyproj = pytest.importorskip("pyproj")
    geod = pyproj.Geod(ellps="WGS84")
    rng = random.Random(7)
    for _ in range(25):
        cx, cy = LON0 + rng.uniform(-0.5, 0.5), LAT0 + rng.uniform(-5, 5)
        n = rng.randint(4, 9)
        pts = []
        for k in range(n):                                              # star-shaped => simple polygon
            ang = 2 * math.pi * k / n
            r = rng.uniform(0.002, 0.005)
            pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
        ring = pts + [pts[0]]
        rep = geo.validate_ring(ring)
        area, perim = geod.polygon_area_perimeter([p[0] for p in ring], [p[1] for p in ring])
        assert rep.valid
        assert rep.area_m2 == pytest.approx(abs(area), rel=2e-6)
        assert rep.perimeter_m == pytest.approx(perim, abs=2e-3)


# --- structural validity --------------------------------------------------------------------------------------------------------

def test_valid_square_report():
    rep = geo.validate_ring(square())
    assert rep.valid and rep.errors == [] and rep.vertex_count == 4
    assert rep.orientation_input == "counter-clockwise" and rep.normalized_ring[0] == rep.normalized_ring[-1]
    assert rep.area_ha == pytest.approx(rep.area_m2 / 10_000) and rep.area_acres > 0


def test_clockwise_ring_is_normalised_with_the_same_measurements():
    ccw = geo.validate_ring(square())
    cw = geo.validate_ring(list(reversed(square())))
    assert cw.valid and cw.orientation_input == "clockwise" and "clockwise_orientation_normalised" in cw.warnings
    assert cw.area_m2 == pytest.approx(ccw.area_m2, rel=1e-12) and cw.perimeter_m == pytest.approx(ccw.perimeter_m, abs=1e-9)
    assert geo._signed_area(geo.project_ring(cw.normalized_ring)) > 0


def test_start_vertex_does_not_change_the_measurements():
    ring = square()[:-1]
    base = geo.validate_ring(ring + [ring[0]])
    shifted = ring[2:] + ring[:2]
    other = geo.validate_ring(shifted + [shifted[0]])
    assert other.area_m2 == pytest.approx(base.area_m2, rel=1e-12)


@pytest.mark.parametrize("ring,code", [
    (square()[:-1], "ring_not_closed"),                                           # open ring
    ([(80, 20), (80.001, 20), (80, 20)], "too_few_vertices"),
    ([(80, 20), (80.001, 20.001), (80.002, 20.002), (80, 20)], "degenerate_area"),   # collinear
    ([(80, 20), (80.002, 20.002), (80.002, 20), (80, 20.002), (80, 20)], "self_intersecting"),   # bow-tie
    ([(80, 20), (80.002, 20), (80.002, 20.002), (80.003, 20.002), (80.001, 20.002), (80, 20.002), (80, 20)], "zero_width_spike"),
    ([(80, 20), (80.002, 20), (80.001, 20.001), (80.002, 20.002), (80, 20.002), (80.001, 20.001), (80, 20)], "self_intersecting"),  # touching at a vertex
    ([(80, 20), (80.001, 20), (80.001, float("nan")), (80, 20)], "non_finite_coordinate"),
    ([(80, 20), (80.001, 20), (80.001, 95.0), (80, 20)], "coordinate_out_of_range"),
    ([(80, 20), (80.8, 20), (80.8, 20.8), (80, 20.8), (80, 20)], "extent_too_large_for_a_parcel"),
])
def test_invalid_geometries_are_rejected_with_a_code(ring, code):
    rep = geo.validate_ring(ring)
    assert not rep.valid and code in rep.errors and rep.area_m2 is None and rep.normalized_ring is None


def test_too_many_vertices_rejected():
    ring = [(80 + i * 1e-7, 20) for i in range(geo.MAX_VERTICES + 5)] + [(80, 20)]
    assert "too_many_vertices" in geo.validate_ring(ring).errors


def test_duplicate_consecutive_vertices_warn_and_are_removed():
    ring = [(80, 20), (80, 20), (80.001, 20), (80.001, 20.001), (80, 20.001), (80, 20)]
    rep = geo.validate_ring(ring)
    assert rep.valid and "duplicate_consecutive_vertices_removed" in rep.warnings and rep.vertex_count == 4


def test_validation_messages_contain_no_coordinates():
    rep = geo.validate_ring([(80.123456789, 20.987654321), (80.5, 20.5), (80.123456789, 20.987654321)])
    text = " ".join(rep.errors + rep.warnings)
    assert "123456789" not in text and "987654321" not in text


# --- point location --------------------------------------------------------------------------------------------------------------------

def test_point_location_inside_outside_boundary():
    ring = geo.validate_ring(square(d=0.002)).normalized_ring
    assert geo.locate_point(LON0 + 0.001, LAT0 + 0.001, ring) == "inside"
    assert geo.locate_point(LON0 + 0.01, LAT0 + 0.01, ring) == "outside"
    assert geo.locate_point(LON0 + 0.001, LAT0, ring) == "boundary"
    assert geo.locate_point(LON0, LAT0, ring) == "boundary"                       # a vertex


def test_concave_polygon_notch_is_outside():
    ring = [(80, 20), (80.003, 20), (80.003, 20.003), (80.002, 20.003), (80.002, 20.001), (80.001, 20.001),
            (80.001, 20.003), (80, 20.003), (80, 20)]
    rep = geo.validate_ring(ring)
    assert rep.valid
    assert geo.locate_point(80.0015, 20.002, rep.normalized_ring) == "outside"    # inside the notch
    assert geo.locate_point(80.0005, 20.002, rep.normalized_ring) == "inside"


def test_invalid_point_coordinates_raise():
    ring = geo.validate_ring(square()).normalized_ring
    with pytest.raises(geo.GeometryError):
        geo.locate_point(200.0, 20.0, ring)
