"""Phase 2B orchard BOA-reflectance NDVI: synthetic scenes and metadata only (no real imagery or boundary).

Metadata/pure-function tests run everywhere; tests that write GeoTIFFs need ``rasterio`` (the project's .venv) and
are skipped otherwise.
"""

from __future__ import annotations

import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import numpy as np
import pytest

from sites_fakes import SITE_ID, kml, make_private
from src.isro import orchard_boa_ndvi as boa
from src.isro import orchard_ndvi as l2
from src.sites import validate_boundary as vb
from src.sites.registry import PROJECT_ROOT
from test_orchard_ndvi import PX, RECT, Scene, _utm as l2_utm, needs_rasterio

REPO = Path(PROJECT_ROOT)
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def ots_id(date: str) -> str:
    y, m, d = date.split("-")
    return f"RA3{d}{MONTHS[int(m) - 1]}{y}0510230101000064PSANSTUCSRHTDF"


def meta_dict(date="2026-10-07", size=40, e0=500000.0, n0=2000000.0, **over):
    y, m, d = date.split("-")
    base = {
        "ProductID": "2675258211", "OTSProductID": ots_id(date), "SatID": "IRS-R2A", "Sensor": "L3",
        "DateOfPass": f"{d}-{MONTHS[int(m) - 1]}-{y}", "NoOfBands": "4", "BandNumbers": "2345", "ProdType": "Geophysical",
        "GenerationDateTime": "16-Oct-2026 13:42:54", "OutputResolutionAcross": "24.00",
        "ProcessingLevel": "AtmosphericallyCorrectedProduct", "NoScans": str(size), "NoPixels": str(size),
        "MapProjection": "UTM", "Ellipsoid": "WGS_84", "ProdULMapX": f"{e0 + 12:.6f}", "ProdULMapY": f"{n0 - 12:.6f}",
        "FalseEasting": "500000.000000", "FalseNorthing": "0.000000", "ZoneNo": "44",
        "Quality": "Q", "CloudPercent": "-NA-", "ValidRange": "0-10000", "ScaleFactor": "0.0001",
        "SourceAOD": "MODIS", "SourceWaterVapor": "MODIS", "SourceOzone": "MODIS",
    }
    base.update(over)
    return base


def meta_text(meta: dict) -> str:
    return "\n".join(f"{k}= {v} " for k, v in meta.items() if v is not None) + "\n"


# --- metadata (pure) ------------------------------------------------------------------------------------------------------

def test_band_meta_parsing_trims_and_tolerates_noise():
    meta = boa.parse_band_meta("ScaleFactor=0.0001\nQuality= Q \nNote = a=b\nno equals here\n=orphan\nZoneNo=44 \n")
    assert meta == {"ScaleFactor": "0.0001", "Quality": "Q", "Note": "a=b", "ZoneNo": "44"}


def test_conflicting_duplicate_keys_are_rejected_but_identical_duplicates_are_fine():
    assert boa.parse_band_meta("A=1\nA=1\n") == {"A": "1"}
    with pytest.raises(l2.AnalysisError, match="twice"):
        boa.parse_band_meta("ScaleFactor=0.0001\nScaleFactor=0.001\n")
    with pytest.raises(l2.AnalysisError, match="larger"):
        boa.parse_band_meta("A=" + "x" * (boa.MAX_META_BYTES + 1))


def test_valid_metadata_is_parsed_not_assumed():
    md = boa.validate_metadata(meta_dict(), "2026-10-07", ots_id("2026-10-07"))
    assert md.scale == Decimal("0.0001") and (md.valid_min, md.valid_max) == (0, 10000) and md.epsg == 32644
    assert (md.rows, md.cols, md.pixel_size_m) == (40, 40, 24.0)


@pytest.mark.parametrize("key", list(boa.REQUIRED_META))
def test_every_required_field_is_required(key):
    for broken in (None, "", "-NA-"):
        with pytest.raises(l2.AnalysisError, match=key):
            boa.validate_metadata(meta_dict(**{key: broken}), "2026-10-07", ots_id("2026-10-07"))


@pytest.mark.parametrize("over,fragment", [
    ({"ProcessingLevel": "Level2Product"}, "ProcessingLevel"),
    ({"DateOfPass": "08-OCT-2026"}, "acquisition date"),
    ({"DateOfPass": "garbage"}, "DD-MON-YYYY"),
    ({"OTSProductID": ots_id("2026-10-31")}, "does not encode"),
    ({"OTSProductID": "XX307OCT2026"}, "does not encode"),
    ({"ProductID": "abc"}, "numeric"),
    ({"ScaleFactor": "0.0002", "ValidRange": "0-5000"}, "expected reflectance scale"),
    ({"ScaleFactor": "abc"}, "not a number"),
    ({"ScaleFactor": "0"}, "positive"),
    ({"ScaleFactor": "-0.0001"}, "positive"),
    ({"ScaleFactor": "NaN"}, "positive"),
    ({"ValidRange": "0-9000"}, "reflectance 0-1"),
    ({"ValidRange": "10-10000"}, "reflectance 0-1"),
    ({"ValidRange": "nonsense"}, "min-max"),
    ({"Sensor": "L4"}, "LISS-3"),
    ({"BandNumbers": "234"}, "LISS-3"),
    ({"MapProjection": "LCC"}, "WGS84 UTM"),
    ({"Ellipsoid": "GRS80"}, "WGS84 UTM"),
    ({"FalseNorthing": "10000000"}, "northern"),
    ({"ZoneNo": "99"}, "northern"),
    ({"NoScans": "x"}, "integer"),
    ({"NoPixels": "-3"}, "positive"),
    ({"OutputResolutionAcross": "30.00"}, "24 m"),
])
def test_inconsistent_or_unexpected_metadata_is_rejected(over, fragment):
    with pytest.raises(l2.AnalysisError, match=fragment):
        boa.validate_metadata(meta_dict(**over), "2026-10-07", ots_id("2026-10-07"))


def test_product_id_must_match_the_scene_directory():
    with pytest.raises(l2.AnalysisError, match="scene directory"):
        boa.validate_metadata(meta_dict(), "2026-10-07", "SOME_OTHER_DIRECTORY")


def test_the_parsed_scale_not_a_constant_drives_the_conversion_rule():
    meta = meta_dict(ScaleFactor="0.0002", ValidRange="0-5000")
    md = boa.validate_metadata(meta, "2026-10-07", ots_id("2026-10-07"), expected_scale=Decimal("0.0002"))
    assert md.scale == Decimal("0.0002") and md.valid_max == 5000
    red, nir = np.array([500.0]), np.array([3000.0])
    _, red_r, nir_r, valid, *_ = boa.reflectance_ndvi(red, nir, md.scale, md.valid_min, md.valid_max)
    assert red_r[0] == pytest.approx(0.1) and nir_r[0] == pytest.approx(0.6) and valid[0]


# --- reflectance NDVI (pure) ------------------------------------------------------------------------------------------------------

def test_reflectance_ndvi_values_and_range_limits():
    red = np.array([500, 1000, 10000, 10001, 0, 2000, 65535], dtype="float64")
    nir = np.array([3000, 3000, 10000, 5000, 4000, 0, 65535], dtype="float64")
    ndvi, red_r, nir_r, valid, counts, _ = boa.reflectance_ndvi(red, nir, Decimal("0.0001"), 0, 10000)
    assert valid.tolist() == [True, True, True, False, False, False, False]
    assert ndvi[0] == pytest.approx((0.3 - 0.05) / (0.3 + 0.05)) and ndvi[1] == pytest.approx(0.5)
    assert ndvi[2] == 0.0 and red_r[2] == pytest.approx(1.0)               # DN 10000 (reflectance 1.0) is valid
    assert np.isnan(ndvi[~valid]).all()
    assert counts == {"masked": 0, "non_finite": 0, "background_zero": 2, "out_of_valid_range": 2, "bad_denominator": 0}


def test_masks_non_finite_and_denominator_reasons_are_attributed_once():
    red = np.ma.masked_array([1000.0, np.nan, 1000.0, -3.0, -5.0], mask=[1, 0, 0, 0, 0])
    nir = np.ma.masked_array([3000.0, 3000.0, np.inf, 3000.0, 5.0], mask=[0, 0, 0, 0, 0])
    _, _, _, valid, counts, reasons = boa.reflectance_ndvi(red, nir, Decimal("0.0001"), 0, 10000)
    assert not valid.any()
    assert counts["masked"] == 1 and counts["non_finite"] == 2 and counts["out_of_valid_range"] == 2
    total = sum(counts.values())
    assert total == 5 and sum(int(r.sum()) for r in reasons.values()) == 5


def test_negative_values_never_reach_ndvi():
    ndvi, *_ = boa.reflectance_ndvi(np.array([-1.0]), np.array([100.0]), Decimal("0.0001"), 0, 10000)
    assert np.isnan(ndvi[0])


# --- synthetic BOA scenes (rasterio) ---------------------------------------------------------------------------------------------------

class BoaScene(Scene):
    """A 40x40 BOA scene (BAND2-BAND5 + BAND_META.txt) around the synthetic site, in a chosen UTM zone."""

    def __init__(self, tmp_path, date="2026-10-07", epsg=32644, red=500, nir=3000, shift=(0.0, 0.0), nodata=None,
                 red_fn=None, nir_fn=None, size=40, dtype="uint16", meta_over=None, drop_band=None,
                 band_transform_shift=None, other_band_shape=None, ul_override=None):
        rasterio = needs_rasterio()
        from rasterio.transform import from_origin
        fwd, self.inv = l2_utm(epsg)
        ce, cn = fwd.transform(80.0, 20.0)
        self.e0 = round(ce / PX) * PX - size // 2 * PX + shift[0]
        self.n0 = round(cn / PX) * PX + size // 2 * PX + shift[1]
        self.size, self.epsg, self.date = size, epsg, date
        self.transform = from_origin(self.e0, self.n0, PX, PX)
        self.red = np.full((size, size), red, dtype=dtype) if red_fn is None else red_fn(size)
        self.nir = np.full((size, size), nir, dtype=dtype) if nir_fn is None else nir_fn(size)
        self.folder = tmp_path / "imagery" / f"resourcesat2a_boa_{date.replace('-', '')}" / ots_id(date)
        self.folder.mkdir(parents=True)
        self.imagery = tmp_path / "imagery"
        zone = {32644: "44", 32643: "43"}[epsg]
        meta = meta_dict(date, size, self.e0, self.n0, ZoneNo=zone)
        if ul_override:
            meta["ProdULMapX"], meta["ProdULMapY"] = ul_override
        meta.update(meta_over or {})
        (self.folder / "BAND_META.txt").write_text(meta_text(meta), encoding="utf-8")
        filler = np.full((size, size), 800, dtype=dtype)
        arrays = {"BAND2.tif": filler, "BAND3.tif": self.red, "BAND4.tif": self.nir, "BAND5.tif": filler}
        for name, arr in arrays.items():
            if name == drop_band:
                continue
            tr = self.transform
            if band_transform_shift and name == "BAND4.tif":
                tr = from_origin(self.e0 + band_transform_shift[0], self.n0 + band_transform_shift[1], PX, PX)
            data = arr
            if other_band_shape and name == "BAND2.tif":
                data = np.full(other_band_shape, 800, dtype=dtype)
            with rasterio.open(self.folder / name, "w", driver="GTiff", height=data.shape[0], width=data.shape[1],
                               count=1, dtype=dtype, crs=f"EPSG:{epsg}", transform=tr, nodata=nodata) as dst:
                dst.write(data, 1)
        self.red_path, self.nir_path = self.folder / "BAND3.tif", self.folder / "BAND4.tif"


def analyze(s, ring=None, **kw):
    ring = ring if ring is not None else s.ring_from_utm(*RECT)
    return boa.analyze_boa_scene(s.date, s.folder, ring, hash_files=kw.pop("hash_files", False), **kw)


def test_reflectance_ndvi_over_the_polygon(tmp_path):
    s = BoaScene(tmp_path)
    r = analyze(s)
    c = r["inclusion"]["center"]
    exp = s.expected(*RECT)
    assert c["selected_pixels"] == int(exp["center"].sum()) == c["valid_pixels"] and c["valid_fraction"] == 1.0
    assert (c["mean"], c["median"], c["minimum"], c["maximum"]) == (pytest.approx((0.3 - 0.05) / 0.35),) * 4
    refl = r["reflectance_primary_inclusion"]
    assert refl["red"]["mean"] == pytest.approx(0.05) and refl["nir"]["mean"] == pytest.approx(0.30)
    assert r["processing"]["scale_factor_parsed"] == "0.0001" and r["processing"]["valid_range_dn"] == [0, 10000]
    assert r["raster"]["metadata_corner_convention"] == "pixel_centre"


@pytest.mark.parametrize("epsg", [32644, 32643])
def test_polygon_is_reprojected_into_each_rasters_crs(tmp_path, epsg):
    s = BoaScene(tmp_path, epsg=epsg)
    r = analyze(s)
    exp = s.expected(*RECT)
    for mode in l2.INCLUSION_MODES:
        assert r["inclusion"][mode]["selected_pixels"] == int(exp[mode].sum()), mode
    assert r["polygon"]["area_in_raster_crs_m2"] == pytest.approx(exp["area"], rel=1e-4)


def test_rejected_pixels_are_counted_by_reason(tmp_path):
    def with_flaws(value):
        def make(n):
            a = np.full((n, n), value, dtype="uint16")
            a[19:21, 19:21] = 0              # 4 background pixels
            a[22, 18:21] = 10001             # 3 above ValidRange
            a[16, 18:20] = 65535             # 2 far above ValidRange
            return a
        return make
    s = BoaScene(tmp_path, red_fn=with_flaws(500), nir_fn=with_flaws(3000))
    r = analyze(s)
    c = r["inclusion"]["center"]
    rej = r["rejected_pixels_among_center_selection"]
    assert rej["background_zero"] == 4 and rej["out_of_valid_range"] == 5 and rej["masked"] == 0
    assert c["selected_pixels"] - c["valid_pixels"] == 9
    assert c["valid_fraction"] == pytest.approx(1 - 9 / c["selected_pixels"])
    assert c["mean"] == pytest.approx((0.3 - 0.05) / 0.35)                   # rejected pixels never reach the statistics


def test_dn_10000_is_valid_and_declared_zero_nodata_is_masked(tmp_path):
    def make(value):
        def f(n):
            a = np.full((n, n), value, dtype="uint16")
            a[19:21, 19:21] = 10000
            return a
        return f
    s = BoaScene(tmp_path, red_fn=make(500), nir_fn=make(3000), nodata=0)
    r = analyze(s)
    assert r["raster"]["nodata_declared"] == 0
    c = r["inclusion"]["center"]
    assert c["valid_fraction"] == 1.0 and c["minimum"] == pytest.approx(0.0)        # reflectance 1.0 in both bands: NDVI 0

    def holes(value):
        def f(n):
            a = np.full((n, n), value, dtype="uint16")
            a[19:21, 19:21] = 0
            return a
        return f
    s2 = BoaScene(tmp_path / "b", red_fn=holes(500), nir_fn=holes(3000), nodata=0)
    r2 = analyze(s2)
    assert r2["rejected_pixels_among_center_selection"]["masked"] == 4              # declared nodata masks DN 0
    assert r2["inclusion"]["center"]["selected_pixels"] - r2["inclusion"]["center"]["valid_pixels"] == 4


def test_declared_nodata_inside_the_valid_range_is_rejected(tmp_path):
    s = BoaScene(tmp_path, nodata=5000)
    with pytest.raises(l2.AnalysisError, match="nodata"):
        analyze(s)


def test_boundary_weighting_and_sensitivity(tmp_path):
    s = BoaScene(tmp_path, nir_fn=lambda n: (2000 + 30 * np.arange(n)[None, :] + 20 * np.arange(n)[:, None]).astype("uint16"))
    r = analyze(s)
    inc = r["inclusion"]
    assert inc["fully_inside"]["selected_pixels"] <= inc["center"]["selected_pixels"] <= inc["any_overlap"]["selected_pixels"]
    exp = s.expected(*RECT)
    ndvi = (s.nir * 0.0001 - s.red * 0.0001) / (s.nir * 0.0001 + s.red * 0.0001)
    v = ndvi[exp["center"]]
    assert inc["center"]["mean"] == pytest.approx(v.mean()) and inc["center"]["std"] == pytest.approx(v.std())
    ov = ndvi[exp["any_overlap"]]
    assert inc["any_overlap"]["mean"] == pytest.approx(ov.mean())
    assert inc["area_weighted"]["valid_area_fraction"] == 1.0
    sens = r["boundary_sensitivity"]
    assert sens["mean_ndvi_spread"] == pytest.approx(sens["mean_ndvi_max_across_inclusion_rules"] - sens["mean_ndvi_min_across_inclusion_rules"])
    assert sens["mean_ndvi_spread"] > 0
    b = r["boundary_pixels"]
    assert b["partially_covered_pixels"] == inc["any_overlap"]["selected_pixels"] - inc["fully_inside"]["selected_pixels"]


# --- raster validation ----------------------------------------------------------------------------------------------------------------

def test_wrong_pixel_type_is_rejected(tmp_path):
    with pytest.raises(l2.AnalysisError, match="pixel type"):
        analyze(BoaScene(tmp_path, dtype="float32"))


def test_bands_must_align_within_a_scene(tmp_path):
    with pytest.raises(l2.AnalysisError, match="not aligned"):
        analyze(BoaScene(tmp_path, band_transform_shift=(PX, 0.0)))
    with pytest.raises(l2.AnalysisError, match="not aligned"):
        analyze(BoaScene(tmp_path / "b", other_band_shape=(30, 30)))


def test_missing_band_and_extent_and_size_disagreements_are_rejected(tmp_path):
    with pytest.raises(l2.AnalysisError, match="BAND5.tif is missing"):
        analyze(BoaScene(tmp_path, drop_band="BAND5.tif"))
    with pytest.raises(l2.AnalysisError, match="NoScans x NoPixels"):
        analyze(BoaScene(tmp_path / "b", meta_over={"NoScans": "41"}))
    with pytest.raises(l2.AnalysisError, match="extent disagrees"):
        analyze(BoaScene(tmp_path / "c", ul_override=("123456.0", "654321.0")))
    with pytest.raises(l2.AnalysisError, match="CRS is not"):
        analyze(BoaScene(tmp_path / "d", epsg=32643, meta_over={"ZoneNo": "44"}))


def test_metadata_failures_surface_through_the_scene_analysis(tmp_path):
    with pytest.raises(l2.AnalysisError, match="ProcessingLevel"):
        analyze(BoaScene(tmp_path, meta_over={"ProcessingLevel": "Level2Product"}))
    with pytest.raises(l2.AnalysisError, match="acquisition date"):
        analyze(BoaScene(tmp_path / "b", meta_over={"DateOfPass": "08-OCT-2026"}))
    with pytest.raises(l2.AnalysisError, match="expected reflectance scale"):
        analyze(BoaScene(tmp_path / "c", meta_over={"ScaleFactor": "0.0002", "ValidRange": "0-5000"}))


def test_the_two_dates_are_processed_independently_on_unaligned_grids(tmp_path):
    a = BoaScene(tmp_path, date="2026-10-07")
    b = BoaScene(tmp_path, date="2026-10-31", shift=(7.0, -5.0), nir=2500)
    ra, rb = analyze(a), analyze(b)
    for scene, result in ((a, ra), (b, rb)):
        exp = scene.expected(*RECT)
        assert result["inclusion"]["center"]["selected_pixels"] == int(exp["center"].sum())
    rel = boa.grid_relation([dict(ra, _origin_phase=(a.e0 % PX, a.n0 % PX)), dict(rb, _origin_phase=(b.e0 % PX, b.n0 % PX))])
    assert rel["pairs"][0]["pixel_grids_coincide"] is False
    assert rel["pairs"][0]["relative_phase_offset_m"] == [7.0, 5.0]
    c = BoaScene(tmp_path / "c", date="2026-10-31", shift=(2 * PX, -PX))
    same = boa.grid_relation([dict(ra, _origin_phase=(a.e0 % PX, a.n0 % PX)), dict(analyze(c), _origin_phase=(c.e0 % PX, c.n0 % PX))])
    assert same["pairs"][0]["pixel_grids_coincide"] is True
    assert boa.grid_relation([ra]) is None


def test_only_small_masked_windows_are_read(tmp_path, monkeypatch):
    rasterio = needs_rasterio()
    s = BoaScene(tmp_path, size=400)
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
    monkeypatch.setattr(boa, "_require_rasterio", lambda: (Shim, Window))
    analyze(s)
    assert len(reads) == 2
    for k in reads:
        assert k.get("masked") is True and k["window"].width * k["window"].height < 0.02 * 400 * 400


def test_a_missing_rasterio_gives_a_clear_message(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "rasterio", None)
    monkeypatch.setitem(sys.modules, "rasterio.windows", None)
    with pytest.raises(l2.AnalysisError, match="rasterio is required"):
        boa.analyze_boa_scene("2026-10-07", tmp_path, [(0, 0), (1, 0), (1, 1), (0, 0)])


def test_scene_discovery_errors(tmp_path):
    s = BoaScene(tmp_path)
    assert boa.find_boa_scene(s.imagery, s.date) == s.folder
    for bad, match in (("../../x", "YYYY-MM-DD"), ("2026-13-01", "calendar"), ("2026-01-01", "no BOA scene")):
        with pytest.raises(l2.AnalysisError, match=match):
            boa.find_boa_scene(s.imagery, bad)
    (s.folder.parent / "second").mkdir()
    (s.folder.parent / "second" / "BAND_META.txt").write_text("x=1")
    with pytest.raises(l2.AnalysisError, match="exactly one"):
        boa.find_boa_scene(s.imagery, s.date)


# --- end to end -----------------------------------------------------------------------------------------------------------------------------

def build_site(tmp_path):
    needs_rasterio()
    first = BoaScene(tmp_path, date="2026-10-07", nir=3000)
    second = BoaScene(tmp_path, date="2026-10-31", shift=(PX / 2, -PX / 3), nir=2500)
    # L2 scenes for the same dates, in the same imagery directory (to prove the L2 analysis is untouched)
    Scene(tmp_path, date="2026-10-07")
    Scene(tmp_path, date="2026-10-31")
    ring = first.ring_from_utm(*RECT)
    lon = sum(p[0] for p in ring[:-1]) / 4
    lat = sum(p[1] for p in ring[:-1]) / 4
    root = make_private(tmp_path, ring, reference=(lon, lat), expected={}, comparison=[])
    (root / "sites" / SITE_ID / "boundary.kml").write_bytes(kml(ring))
    code, report, _ = vb.run(SITE_ID, private_dir=root, ignore_checker=lambda p: True)
    assert code == 0 and report["all_checks_passed"]
    return root, first, second, ring


def test_end_to_end_outputs_are_private_separate_and_carry_the_limitations(tmp_path, capsys, caplog):
    root, first, second, ring = build_site(tmp_path)
    out = root / "sites" / SITE_ID / "analysis" / "resourcesat_boa_ndvi"
    code, results, lines = boa.run(SITE_ID, imagery_dir=first.imagery, private_dir=root, ignore_checker=lambda p: True)
    assert code == 0, lines
    assert sorted(p.name for p in out.iterdir()) == ["boa_ndvi_distribution.png", "boa_ndvi_statistics.csv", "boa_ndvi_statistics.json"]
    assert (out / "boa_ndvi_distribution.png").read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    data = json.loads((out / "boa_ndvi_statistics.json").read_text())
    assert [s["date"] for s in data["scenes"]] == ["2026-10-07", "2026-10-31"]
    a, b = (s["inclusion"]["center"] for s in data["scenes"])
    assert a["mean"] == pytest.approx((0.3 - 0.05) / 0.35) and b["mean"] == pytest.approx((0.25 - 0.05) / 0.30)
    s0 = data["scenes"][0]
    assert s0["processing"]["metadata"]["ProcessingLevel"] == "AtmosphericallyCorrectedProduct"
    assert s0["processing"]["metadata"]["ScaleFactor"] == "0.0001" and s0["processing"]["quality"]["cloud_free_claimed"] is False
    assert s0["processing"]["quality"]["quality_code_interpreted"] is False
    assert all(s0["files"][n]["sha256"] for n in ("BAND3.tif", "BAND4.tif", "BAND_META.txt"))
    assert data["grid_alignment_between_dates"]["pairs"][0]["pixel_grids_coincide"] is False
    assert "quality screening incomplete" in data["label"] and "NOT claimed to be cloud-free" in data["label"]
    assert csv_rows(out) == 1 + 2 * 3

    everything = json.dumps(data) + (out / "boa_ndvi_statistics.csv").read_text() + "\n".join(lines) + caplog.text + capsys.readouterr().out
    for lon, lat in ring:
        assert f"{lon:.5f}" not in everything and f"{lat:.5f}" not in everything
    assert str(tmp_path) not in everything and '"coordinates"' not in everything and '"geometry"' not in everything
    body = json.dumps({k: v for k, v in data.items() if k not in ("label", "limitations")}).lower()
    for forbidden in ("difference", "delta", "growth", "yield", "productivity", "mango health", "cloud-free", "improv"):
        assert forbidden not in body.replace("cloud_free_claimed", ""), forbidden


def csv_rows(out: Path) -> int:
    return (out / "boa_ndvi_statistics.csv").read_text().count("\n")


def test_l2_outputs_and_behaviour_are_untouched_by_the_boa_analysis(tmp_path):
    root, first, _, _ = build_site(tmp_path)
    assert l2.run(SITE_ID, imagery_dir=first.imagery, private_dir=root, ignore_checker=lambda p: True)[0] == 0
    l2_dir = root / "sites" / SITE_ID / "analysis" / "resourcesat_ndvi"
    before = {p.name: p.read_bytes() for p in l2_dir.iterdir()}
    assert boa.run(SITE_ID, imagery_dir=first.imagery, private_dir=root, ignore_checker=lambda p: True)[0] == 0
    assert {p.name: p.read_bytes() for p in l2_dir.iterdir()} == before
    assert boa.OUTPUT_SUBDIR != l2.OUTPUT_SUBDIR and boa.OUTPUT_SUBDIR[-1] != l2.OUTPUT_SUBDIR[-1]
    data = json.loads((l2_dir / "ndvi_statistics.json").read_text())
    assert data["analysis"] == l2.ANALYSIS_ID and "BOA" not in data["label"]       # still the DN-based L2 result


def test_nothing_is_written_outside_the_boa_directory(tmp_path):
    root, first, _, _ = build_site(tmp_path)
    before = {p.relative_to(tmp_path) for p in tmp_path.rglob("*")}
    assert boa.run(SITE_ID, imagery_dir=first.imagery, private_dir=root, ignore_checker=lambda p: True)[0] == 0
    new = {p.relative_to(tmp_path) for p in tmp_path.rglob("*")} - before
    prefix = ("private", "sites", SITE_ID, "analysis", "resourcesat_boa_ndvi")
    assert new and all(p.parts[:len(prefix)] == prefix[:len(p.parts)] for p in new)        # only the BOA directory tree
    assert {p.name for p in new if len(p.parts) == 6} == {"boa_ndvi_statistics.json", "boa_ndvi_statistics.csv", "boa_ndvi_distribution.png"}


def test_dry_run_writes_nothing_and_runs_are_reproducible(tmp_path):
    root, first, _, _ = build_site(tmp_path)
    a = boa.run(SITE_ID, imagery_dir=first.imagery, private_dir=root, dry_run=True, ignore_checker=lambda p: True)
    b = boa.run(SITE_ID, imagery_dir=first.imagery, private_dir=root, dry_run=True, ignore_checker=lambda p: True)
    assert a[0] == 0 and not (root / "sites" / SITE_ID / "analysis").exists()
    assert a[1]["scenes"] == b[1]["scenes"]


def test_unvalidated_boundary_and_unsafe_private_dir_are_refused(tmp_path):
    root, first, _, _ = build_site(tmp_path)
    report = root / "sites" / SITE_ID / "validation_report.json"
    data = json.loads(report.read_text())
    data["all_checks_passed"] = False
    report.write_text(json.dumps(data))
    code, results, lines = boa.run(SITE_ID, imagery_dir=first.imagery, private_dir=root, ignore_checker=lambda p: True)
    assert code == 2 and results is None and "not passed Phase 1 validation" in " ".join(lines)
    code, _, lines = boa.run(SITE_ID, private_dir=REPO / "unignored_probe_dir", ignore_checker=lambda p: False)
    assert code == 2 and "not verified" in " ".join(lines)


def test_a_bad_scene_aborts_the_whole_run_with_nothing_written(tmp_path):
    root, first, _, _ = build_site(tmp_path)
    meta = next((first.imagery / "resourcesat2a_boa_20261031").rglob("BAND_META.txt"))
    meta.write_text(meta.read_text().replace("AtmosphericallyCorrectedProduct", "Level2Product"))
    code, results, lines = boa.run(SITE_ID, imagery_dir=first.imagery, private_dir=root, ignore_checker=lambda p: True)
    assert code == 2 and results is None and "ProcessingLevel" in " ".join(lines)
    assert not (root / "sites" / SITE_ID / "analysis").exists()


# --- isolation ------------------------------------------------------------------------------------------------------------------------------------

def test_production_code_and_workflows_do_not_import_the_boa_analysis():
    for base in ("app", "src", "scripts"):
        for f in (REPO / base).rglob("*.py"):
            if f.name in ("orchard_ndvi.py", "orchard_boa_ndvi.py") or "__pycache__" in f.parts:
                continue
            assert "orchard_boa_ndvi" not in f.read_text(encoding="utf-8-sig", errors="ignore"), f
    assert "orchard_boa_ndvi" not in (REPO / "main.py").read_text(encoding="utf-8-sig")
    for wf in (REPO / ".github" / "workflows").glob("*.yml"):
        assert "orchard_boa_ndvi" not in wf.read_text(encoding="utf-8")


def test_dependencies_configuration_and_production_paths_are_unchanged():
    for path in ("requirements.txt", "requirements-cloud.txt", "configs/config.yaml", ".github/workflows/daily-data-refresh.yml"):
        assert subprocess.run(["git", "-C", str(REPO), "diff", "--quiet", "HEAD", "--", path]).returncode == 0, path
    from src.utils.config import get_config
    cfg = get_config()
    assert (cfg.latitude, cfg.longitude) == (13.294219, 78.624294)
    assert cfg.path("historical_risk_csv") == REPO / "data" / "processed" / "muthukur_weather_risk_scores.csv"
