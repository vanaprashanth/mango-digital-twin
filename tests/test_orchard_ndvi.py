"""Phase 2A orchard raw-band NDVI: synthetic rasters only (no real imagery, no real boundary).

Pure-function tests run everywhere. Tests that write GeoTIFFs need ``rasterio`` (installed in the project's
.venv, not in the default interpreter) and are skipped when it is missing.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import shapely
from shapely.geometry import Polygon

from sites_fakes import LAT0, LON0, SITE_ID, kml, make_private, meridian_arc
from src.isro import orchard_ndvi as nd
from src.sites import validate_boundary as vb
from src.sites.registry import PROJECT_ROOT

REPO = Path(PROJECT_ROOT)
PX = 24.0


def needs_rasterio():
    return pytest.importorskip("rasterio")


# --- NDVI validity ---------------------------------------------------------------------------------------------------------

def test_ndvi_values_and_every_invalid_reason():
    red = np.ma.masked_array([1000, 0, 500, 1000, 40000, 3000], mask=[0, 0, 0, 1, 0, 0])
    nir = np.ma.masked_array([3000, 0, 0, 3000, 40000, 500], mask=[0, 0, 0, 0, 0, 0])
    ndvi, valid, counts = nd.compute_ndvi(red, nir)
    assert valid.tolist() == [True, False, False, False, True, True]
    assert ndvi[0] == pytest.approx(0.5) and ndvi[4] == 0.0 and ndvi[5] == pytest.approx(-5 / 7)
    assert np.isnan(ndvi[[1, 2, 3]]).all()
    assert counts == {"masked": 1, "non_finite": 0, "non_positive_dn": 2, "bad_denominator": 0}


def test_non_finite_and_zero_denominator_are_never_valid():
    red = np.array([np.nan, 5.0, 0.0, 0.0])
    nir = np.array([4.0, np.inf, 0.0, 7.0])
    ndvi, valid, counts = nd.compute_ndvi(red, nir)
    assert not valid.any() and np.isnan(ndvi).all()
    assert counts["non_finite"] == 2 and counts["non_positive_dn"] == 2


def test_denominator_that_overflows_to_zero_or_inf_is_rejected():
    red = np.array([-5.0, 1e308])
    nir = np.array([5.0, 1e308])                      # signed data: 0 denominator; and inf denominator
    _, valid, counts = nd.compute_ndvi(red, nir)
    assert not valid.any()
    assert counts["non_positive_dn"] == 1 and counts["bad_denominator"] == 1


def test_summary_statistics():
    s = nd.summarize(np.array([0.2, 0.4, 0.6, 0.8]))
    assert s == {"count": 4, "mean": pytest.approx(0.5), "median": pytest.approx(0.5), "minimum": 0.2,
                 "maximum": 0.8, "std": pytest.approx(np.std([0.2, 0.4, 0.6, 0.8]))}
    assert nd.summarize(np.array([]))["mean"] is None
    w = nd.summarize(np.array([0.0, 1.0]), np.array([3.0, 1.0]))
    assert w["mean"] == pytest.approx(0.25) and w["std"] == pytest.approx(math.sqrt(0.1875))


# --- pixel inclusion on an exact grid (no reprojection involved) -------------------------------------------------------

def grid(n=12):
    return nd.Grid(0.0, n * PX, PX, PX, n, n)           # top-left at (0, n*24); pixel (r,c) spans x[c*24,(c+1)*24]


def test_aligned_rectangle_has_no_boundary_pixels():
    poly = Polygon([(2 * PX, 2 * PX), (7 * PX, 2 * PX), (7 * PX, 6 * PX), (2 * PX, 6 * PX)])
    m = nd.inclusion(poly, grid())
    assert m["center"].sum() == m["fully_inside"].sum() == m["any_overlap"].sum() == 5 * 4
    assert np.isclose(m["fraction"].sum(), poly.area / PX ** 2)


def test_half_pixel_offset_creates_mixed_edge_pixels_and_orders_the_modes():
    poly = Polygon([(2.5 * PX, 2.5 * PX), (7.5 * PX, 2.5 * PX), (7.5 * PX, 6.5 * PX), (2.5 * PX, 6.5 * PX)])
    m = nd.inclusion(poly, grid())
    assert m["fully_inside"].sum() == 4 * 3                              # 5x4 aligned block minus the half-covered rim
    assert m["any_overlap"].sum() == 6 * 5
    assert m["fully_inside"].sum() <= m["center"].sum() <= m["any_overlap"].sum()
    assert np.isclose(m["fraction"].sum(), poly.area / PX ** 2)          # coverage fractions are exact
    assert sorted(set(np.round(m["fraction"][m["any_overlap"]], 6))) == [0.25, 0.5, 1.0]


def test_pixel_centre_exactly_on_the_edge_is_included_and_tangent_pixels_are_not_overlapped():
    poly = Polygon([(2.5 * PX, 2 * PX), (6 * PX, 2 * PX), (6 * PX, 6 * PX), (2.5 * PX, 6 * PX)])
    m = nd.inclusion(poly, grid())
    assert m["center"][:, 2].sum() == 4                                   # column whose centre lies ON the left edge
    assert m["any_overlap"][:, 1].sum() == 0                               # the neighbour merely touches nothing
    assert m["any_overlap"][:, 2].sum() == 4 and m["fully_inside"][:, 2].sum() == 0


def test_area_weighted_statistics_use_exact_coverage():
    poly = Polygon([(2.5 * PX, 2.5 * PX), (7.5 * PX, 2.5 * PX), (7.5 * PX, 6.5 * PX), (2.5 * PX, 6.5 * PX)])
    m = nd.inclusion(poly, grid())
    ndvi = np.full((12, 12), 0.4)
    valid = np.ones((12, 12), dtype=bool)
    s = nd.area_weighted_statistics(ndvi, valid, m["fraction"])
    assert s["mean"] == pytest.approx(0.4) and s["std"] == pytest.approx(0.0, abs=1e-12) and s["valid_area_fraction"] == 1.0
    valid[6:8, 4:6] = False
    assert nd.area_weighted_statistics(ndvi, valid, m["fraction"])["valid_area_fraction"] < 1.0


def test_densified_ring_has_no_long_edges_and_keeps_the_corners():
    ring = [(LON0, LAT0), (LON0 + 0.002, LAT0), (LON0 + 0.002, LAT0 + 0.002), (LON0, LAT0 + 0.002), (LON0, LAT0)]
    dense = nd.densify_ring(ring, 5.0)
    assert len(dense) > len(ring) and set(ring) <= set(dense)
    from src.sites.geometry import geodesic_distance
    assert max(geodesic_distance(*a, *b) for a, b in zip(dense, dense[1:])) <= 5.0 + 1e-6


def test_reprojection_matches_the_utm_definition_on_the_central_meridian():
    pyproj = pytest.importorskip("pyproj")
    wkt = pyproj.CRS.from_epsg(32644).to_wkt()
    (x, y), = nd.reproject_ring([(81.0, 20.0)], wkt)
    assert x == pytest.approx(500000.0, abs=1e-6)                         # false easting on the central meridian
    assert y == pytest.approx(0.9996 * meridian_arc(0.0, 20.0), abs=1e-3)  # k0 * meridian arc from the equator


# --- rasters (rasterio) --------------------------------------------------------------------------------------------------------

def _utm(epsg):
    from pyproj import Transformer
    return (Transformer.from_crs("EPSG:4326", f"EPSG:{epsg}", always_xy=True),
            Transformer.from_crs(f"EPSG:{epsg}", "EPSG:4326", always_xy=True))


class Scene:
    """A 40x40 north-up uint16 raster pair around (LON0, LAT0) in a chosen UTM zone, plus its geometry."""

    def __init__(self, tmp_path, date="2026-10-07", epsg=32644, red=1000, nir=3000, shift=(0.0, 0.0), nodata=None,
                 red_fn=None, nir_fn=None, size=40):
        rasterio = needs_rasterio()
        from rasterio.transform import from_origin
        fwd, self.inv = _utm(epsg)
        ce, cn = fwd.transform(LON0, LAT0)
        self.e0 = round(ce / PX) * PX - size // 2 * PX + shift[0]              # raster top-left corner
        self.n0 = round(cn / PX) * PX + size // 2 * PX + shift[1]
        self.size, self.epsg, self.date = size, epsg, date
        self.transform = from_origin(self.e0, self.n0, PX, PX)
        r = np.full((size, size), red, dtype="uint16") if red_fn is None else red_fn(size)
        n = np.full((size, size), nir, dtype="uint16") if nir_fn is None else nir_fn(size)
        self.red, self.nir = r, n
        folder = tmp_path / "imagery" / f"resourcesat2a_{date.replace('-', '')}" / "RA_SYNTHETIC_PRODUCT"
        folder.mkdir(parents=True)
        for name, arr in (("BAND3.tif", r), ("BAND4.tif", n)):
            with rasterio.open(folder / name, "w", driver="GTiff", height=size, width=size, count=1, dtype="uint16",
                               crs=f"EPSG:{epsg}", transform=self.transform, nodata=nodata) as dst:
                dst.write(arr, 1)
        self.red_path, self.nir_path, self.imagery = folder / "BAND3.tif", folder / "BAND4.tif", tmp_path / "imagery"

    def ring_from_utm(self, x1, y1, x2, y2):
        """Closed CCW lon/lat ring for a UTM rectangle given as offsets (m) from the raster's centre pixel corner."""
        cx, cy = self.e0 + self.size // 2 * PX, self.n0 - self.size // 2 * PX
        corners = [(cx + x1, cy + y1), (cx + x2, cy + y1), (cx + x2, cy + y2), (cx + x1, cy + y2)]
        lonlat = [self.inv.transform(*c) for c in corners]
        return lonlat + [lonlat[0]]

    def expected(self, x1, y1, x2, y2):
        """Independent analytic pixel sets for the same UTM rectangle (no polygon library involved)."""
        cx, cy = self.e0 + self.size // 2 * PX, self.n0 - self.size // 2 * PX
        xa, xb, ya, yb = cx + x1, cx + x2, cy + y1, cy + y2
        cols, rows = np.meshgrid(np.arange(self.size), np.arange(self.size))
        left, right = self.e0 + cols * PX, self.e0 + (cols + 1) * PX
        top, bottom = self.n0 - rows * PX, self.n0 - (rows + 1) * PX
        centre = ((left + right) / 2 >= xa) & ((left + right) / 2 <= xb) & ((top + bottom) / 2 >= ya) & ((top + bottom) / 2 <= yb)
        full = (left >= xa) & (right <= xb) & (bottom >= ya) & (top <= yb)
        overlap = (np.minimum(right, xb) > np.maximum(left, xa)) & (np.minimum(top, yb) > np.maximum(bottom, ya))
        return {"center": centre, "fully_inside": full, "any_overlap": overlap, "area": (xb - xa) * (yb - ya)}


RECT = (-5 * PX + 7.3, -4 * PX + 9.1, 5 * PX + 7.3, 4 * PX + 9.1)        # 10 x 8 pixels, offset 7-9 m from the grid


@pytest.mark.parametrize("epsg", [32644, 32643])
def test_polygon_is_reprojected_into_each_rasters_own_crs(tmp_path, epsg):
    s = Scene(tmp_path, epsg=epsg)
    result = nd.analyze_scene(s.date, s.red_path, s.nir_path, s.ring_from_utm(*RECT), hash_files=False)
    exp = s.expected(*RECT)
    assert result["raster"]["crs_epsg"] == epsg
    assert result["polygon"]["area_in_raster_crs_m2"] == pytest.approx(exp["area"], rel=1e-4)
    for mode in nd.INCLUSION_MODES:
        assert result["inclusion"][mode]["selected_pixels"] == int(exp[mode].sum()), mode
    c = result["inclusion"]["center"]
    assert (c["mean"], c["median"], c["minimum"], c["maximum"]) == (pytest.approx(0.5),) * 4 and c["std"] == pytest.approx(0, abs=1e-12)


def test_edge_pixels_are_reported_and_the_modes_bracket_the_primary(tmp_path):
    s = Scene(tmp_path)
    r = nd.analyze_scene(s.date, s.red_path, s.nir_path, s.ring_from_utm(*RECT), hash_files=False)
    inc = r["inclusion"]
    assert inc["fully_inside"]["selected_pixels"] <= inc["center"]["selected_pixels"] <= inc["any_overlap"]["selected_pixels"]
    b = r["boundary_pixels"]
    assert b["partially_covered_pixels"] == inc["any_overlap"]["selected_pixels"] - inc["fully_inside"]["selected_pixels"] > 0
    assert 0 < b["share_of_center_pixels_that_are_partially_covered"] < 1
    assert inc["area_weighted"]["mean"] == pytest.approx(0.5)


def test_statistics_match_an_independent_numpy_computation(tmp_path):
    s = Scene(tmp_path, nir_fn=lambda n: (2000 + 40 * np.arange(n)[None, :] + 15 * np.arange(n)[:, None]).astype("uint16"))
    r = nd.analyze_scene(s.date, s.red_path, s.nir_path, s.ring_from_utm(*RECT), hash_files=False)
    sel = s.expected(*RECT)["center"]
    ndvi = (s.nir.astype(float) - s.red) / (s.nir.astype(float) + s.red)
    v = ndvi[sel]
    c = r["inclusion"]["center"]
    assert c["valid_pixels"] == v.size and c["valid_fraction"] == 1.0
    assert (c["mean"], c["median"], c["minimum"], c["maximum"], c["std"]) == pytest.approx(
        (v.mean(), np.median(v), v.min(), v.max(), v.std()))


def test_declared_nodata_zero_dn_and_valid_fraction(tmp_path):
    def holes(value):
        def make(n):
            a = np.full((n, n), value, dtype="uint16")
            a[19:21, 19:21] = 0                       # 4 zero-DN pixels inside the polygon (centre of the raster)
            return a
        return make
    s = Scene(tmp_path, red_fn=holes(1000), nir_fn=holes(3000))
    r = nd.analyze_scene(s.date, s.red_path, s.nir_path, s.ring_from_utm(*RECT), hash_files=False)
    c = r["inclusion"]["center"]
    assert c["selected_pixels"] - c["valid_pixels"] == 4
    assert c["valid_fraction"] == pytest.approx(1 - 4 / c["selected_pixels"])
    assert r["invalid_pixels_among_center_selection"]["non_positive_dn"] == 4


def test_masked_nodata_values_are_excluded_via_the_raster_mask(tmp_path):
    def with_nodata(value):
        def make(n):
            a = np.full((n, n), value, dtype="uint16")
            a[18:20, 18:22] = 65535                   # declared nodata inside the polygon: 8 pixels
            return a
        return make
    s = Scene(tmp_path, nodata=65535, red_fn=with_nodata(1000), nir_fn=with_nodata(3000))
    r = nd.analyze_scene(s.date, s.red_path, s.nir_path, s.ring_from_utm(*RECT), hash_files=False)
    c = r["inclusion"]["center"]
    assert r["raster"]["nodata_declared"] == 65535
    assert c["selected_pixels"] - c["valid_pixels"] == 8 and r["invalid_pixels_among_center_selection"]["masked"] == 8
    assert c["mean"] == pytest.approx(0.5)            # nodata (65535) never leaks into the statistics


def test_pixels_where_either_band_is_zero_have_no_valid_denominator(tmp_path):
    s = Scene(tmp_path, red_fn=lambda n: np.where(np.arange(n)[None, :] % 2 == 0, 0, 1000).astype("uint16") * np.ones((n, 1), dtype="uint16"))
    r = nd.analyze_scene(s.date, s.red_path, s.nir_path, s.ring_from_utm(*RECT), hash_files=False)
    c = r["inclusion"]["center"]
    assert c["valid_fraction"] == pytest.approx(0.5) and r["invalid_pixels_among_center_selection"]["non_positive_dn"] == c["selected_pixels"] - c["valid_pixels"]


def test_all_invalid_pixels_give_empty_statistics_not_errors(tmp_path):
    s = Scene(tmp_path, red=0, nir=0)
    c = nd.analyze_scene(s.date, s.red_path, s.nir_path, s.ring_from_utm(*RECT), hash_files=False)["inclusion"]["center"]
    assert c["valid_pixels"] == 0 and c["valid_fraction"] == 0 and c["mean"] is None


def test_only_a_small_window_is_read_and_always_masked(tmp_path, monkeypatch):
    rasterio = needs_rasterio()
    s = Scene(tmp_path, size=400)
    reads = []

    class Spy:
        def __init__(self, ds):
            self._ds = ds

        def __getattr__(self, name):
            return getattr(self._ds, name)

        def __enter__(self):
            self._ds.__enter__()
            return self

        def __exit__(self, *a):
            return self._ds.__exit__(*a)

        def read(self, *a, **k):
            reads.append(k)
            return self._ds.read(*a, **k)

    class Shim:
        @staticmethod
        def open(path, *a, **k):
            return Spy(rasterio.open(path, *a, **k))

    from rasterio.windows import Window
    monkeypatch.setattr(nd, "_require_rasterio", lambda: (Shim, Window))
    nd.analyze_scene(s.date, s.red_path, s.nir_path, s.ring_from_utm(*RECT), hash_files=False)
    assert len(reads) == 2
    for k in reads:
        assert k.get("masked") is True and k["window"].width * k["window"].height < 0.02 * 400 * 400


def test_polygon_outside_the_raster_misaligned_bands_and_bad_inputs_are_errors(tmp_path):
    s = Scene(tmp_path, size=40)
    far = s.ring_from_utm(-30 * PX, -30 * PX, -25 * PX, -25 * PX)
    with pytest.raises(nd.AnalysisError, match="not entirely inside"):
        nd.analyze_scene(s.date, s.red_path, s.nir_path, far, hash_files=False)
    partly = s.ring_from_utm(15 * PX, -3 * PX, 25 * PX, 3 * PX)           # crosses the raster edge: never clipped silently
    with pytest.raises(nd.AnalysisError, match="not entirely inside"):
        nd.analyze_scene(s.date, s.red_path, s.nir_path, partly, hash_files=False)
    other = Scene(tmp_path / "other", shift=(PX, 0.0))
    with pytest.raises(nd.AnalysisError, match="not aligned"):
        nd.analyze_scene(s.date, s.red_path, other.nir_path, s.ring_from_utm(*RECT), hash_files=False)
    with pytest.raises(nd.AnalysisError, match="YYYY-MM-DD"):
        nd.find_scene_bands(s.imagery, "../../etc")
    with pytest.raises(nd.AnalysisError, match="calendar"):
        nd.find_scene_bands(s.imagery, "2026-13-45")
    with pytest.raises(nd.AnalysisError, match="no scene directory"):
        nd.find_scene_bands(s.imagery, "2026-01-01")
    (s.red_path.parent / "copy").mkdir()
    (s.red_path.parent / "copy" / "BAND3.tif").write_bytes(b"x")
    with pytest.raises(nd.AnalysisError, match="exactly one BAND3.tif"):
        nd.find_scene_bands(s.imagery, s.date)


def test_a_missing_rasterio_gives_a_clear_message_not_a_traceback(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "rasterio", None)
    monkeypatch.setitem(sys.modules, "rasterio.windows", None)
    with pytest.raises(nd.AnalysisError, match="rasterio is required"):
        nd.analyze_scene("2026-10-07", tmp_path / "a.tif", tmp_path / "b.tif", [(0, 0), (1, 0), (1, 1), (0, 0)])


# --- end to end on a synthetic private site -------------------------------------------------------------------------------------------

def build_site(tmp_path):
    """Private synthetic site validated by the real Phase 1 CLI, plus two synthetic scenes on different grids."""
    needs_rasterio()
    first = Scene(tmp_path, date="2026-10-07", nir=3000)
    second = Scene(tmp_path, date="2026-10-31", shift=(PX / 2, -PX / 3), nir=2500)      # different grid and values
    ring = first.ring_from_utm(*RECT)
    cx_lon = sum(p[0] for p in ring[:-1]) / 4
    cy_lat = sum(p[1] for p in ring[:-1]) / 4
    root = make_private(tmp_path, ring, reference=(cx_lon, cy_lat), expected={}, comparison=[])
    site_dir = root / "sites" / SITE_ID
    (site_dir / "boundary.kml").write_bytes(kml(ring))
    code, report, _ = vb.run(SITE_ID, private_dir=root, ignore_checker=lambda p: True)
    assert code == 0 and report["all_checks_passed"]
    return root, first, second, ring


def test_end_to_end_outputs_are_private_labelled_and_make_no_comparative_claims(tmp_path, capsys, caplog):
    root, first, second, ring = build_site(tmp_path)
    code, results, lines = nd.run(SITE_ID, imagery_dir=first.imagery, private_dir=root, ignore_checker=lambda p: True)
    assert code == 0
    out = root / "sites" / SITE_ID / "analysis" / "resourcesat_ndvi"
    assert sorted(p.name for p in out.iterdir()) == ["ndvi_distribution.png", "ndvi_statistics.csv", "ndvi_statistics.json"]
    assert (out / "ndvi_distribution.png").read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    data = json.loads((out / "ndvi_statistics.json").read_text())
    assert [s["date"] for s in data["scenes"]] == ["2026-10-07", "2026-10-31"]
    a, b = (s["inclusion"]["center"] for s in data["scenes"])
    assert a["mean"] == pytest.approx(0.5) and b["mean"] == pytest.approx((2500 - 1000) / 3500)
    assert data["scenes"][0]["bands"]["red"]["sha256"] and data["label"].startswith("EXPLORATORY - uncalibrated")
    csv_text = (out / "ndvi_statistics.csv").read_text()
    assert csv_text.count("\n") == 1 + 2 * 3 and "exploratory uncalibrated raw-band NDVI" in csv_text

    everything = json.dumps(data) + csv_text + "\n".join(lines) + caplog.text + capsys.readouterr().out
    for lon, lat in ring:
        assert f"{lon:.5f}" not in everything and f"{lat:.5f}" not in everything
    assert str(tmp_path) not in everything
    for forbidden in ("difference", "delta", "change", "growth", "health improved", "increase", "decrease", "mango presence detected"):
        assert forbidden not in json.dumps({k: v for k, v in data.items() if k != "label"}).lower().replace(
            "no inference about vegetation growth, crop health or mango presence", ""), forbidden
    assert "no difference between dates is computed" in data["label"]


def test_nothing_is_written_outside_the_private_site_directory(tmp_path):
    root, first, _, _ = build_site(tmp_path)
    before = {p.relative_to(tmp_path) for p in tmp_path.rglob("*")}
    assert nd.run(SITE_ID, imagery_dir=first.imagery, private_dir=root, ignore_checker=lambda p: True)[0] == 0
    new = {p.relative_to(tmp_path) for p in tmp_path.rglob("*")} - before
    assert new and all(p.parts[:3] == ("private", "sites", SITE_ID) and p.parts[3] == "analysis" for p in new)


def test_dry_run_writes_nothing(tmp_path):
    root, first, _, _ = build_site(tmp_path)
    assert nd.run(SITE_ID, imagery_dir=first.imagery, private_dir=root, dry_run=True, ignore_checker=lambda p: True)[0] == 0
    assert not (root / "sites" / SITE_ID / "analysis").exists()


def test_unvalidated_boundary_is_refused(tmp_path):
    root, first, _, _ = build_site(tmp_path)
    report = root / "sites" / SITE_ID / "validation_report.json"
    data = json.loads(report.read_text())
    data["all_checks_passed"] = False
    report.write_text(json.dumps(data))
    code, results, lines = nd.run(SITE_ID, imagery_dir=first.imagery, private_dir=root, ignore_checker=lambda p: True)
    assert code == 2 and results is None and "not passed Phase 1 validation" in " ".join(lines)


def test_private_directory_inside_the_repo_must_be_ignored(tmp_path):
    code, _, lines = nd.run(SITE_ID, private_dir=REPO / "unignored_probe_dir", ignore_checker=lambda p: False)
    assert code == 2 and "not verified" in " ".join(lines)


def test_run_is_reproducible(tmp_path):
    root, first, _, _ = build_site(tmp_path)
    a = nd.run(SITE_ID, imagery_dir=first.imagery, private_dir=root, dry_run=True, ignore_checker=lambda p: True)[1]
    b = nd.run(SITE_ID, imagery_dir=first.imagery, private_dir=root, dry_run=True, ignore_checker=lambda p: True)[1]
    assert a["scenes"] == b["scenes"]


# --- isolation ---------------------------------------------------------------------------------------------------------------------------

def test_existing_experiment_and_requirements_are_untouched():
    for path in ("src/isro/bhoonidhi/compare_ndvi.py", "requirements.txt", "requirements-cloud.txt", "configs/config.yaml"):
        assert subprocess.run(["git", "-C", str(REPO), "diff", "--quiet", "HEAD", "--", path]).returncode == 0, path
    assert "rasterio" not in (REPO / "requirements.txt").read_text(encoding="utf-8")


def test_production_code_does_not_import_the_orchard_analysis():
    for base in ("app", "src", "scripts"):
        for f in (REPO / base).rglob("*.py"):
            if f.name in ("orchard_ndvi.py", "orchard_boa_ndvi.py") or "__pycache__" in f.parts:
                continue
            assert "orchard_ndvi" not in f.read_text(encoding="utf-8-sig", errors="ignore"), f
    assert "orchard_ndvi" not in (REPO / "main.py").read_text(encoding="utf-8-sig")
    for wf in (REPO / ".github" / "workflows").glob("*.yml"):
        assert "orchard_ndvi" not in wf.read_text(encoding="utf-8")
