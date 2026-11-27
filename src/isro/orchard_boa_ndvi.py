"""
Private orchard Resourcesat-2A LISS-3 BOA-reflectance NDVI statistics (PHASE 2B, EXPLORATORY).

    .venv/Scripts/python.exe -m src.isro.orchard_boa_ndvi --site-id MANGO_ORCHARD_001

Input: two atmospherically corrected ("BOA") LISS-3 products, ``resourcesat2a_boa_<YYYYMMDD>/<product>/`` with
BAND2-BAND5 GeoTIFFs and ``BAND_META.txt``. Red = BAND3, NIR = BAND4. NDVI is computed from REFLECTANCE:
reflectance = DN x ScaleFactor, where the scale factor is parsed from each scene's own metadata.

ATMOSPHERICALLY CORRECTED, BUT QUALITY SCREENING IS INCOMPLETE
  * No independent cloud/shadow mask has been verified; CloudPercent is "-NA-"; the Quality code "Q" has not
    been interpreted. Numerically valid pixels are therefore NOT claimed to be cloud-free.
  * Results are per-date statistics only. No difference between dates is computed, and nothing is inferred about
    vegetation growth, mango health, crop yield or orchard productivity.

METADATA VALIDATION (each scene's actual BAND_META.txt; nothing is assumed from file names alone)
  Required and checked: ProcessingLevel == AtmosphericallyCorrectedProduct; DateOfPass == the requested date;
  OTSProductID encodes that same date and equals the scene directory holding the bands; ScaleFactor parsed as a
  positive decimal equal to the expected 0.0001 (a different scale is rejected, never silently used); ValidRange
  "0-N" with N x ScaleFactor == 1 (reflectance 0-1); UTM / WGS_84 / zone; NoScans x NoPixels; 24 m output
  resolution. Missing, "-NA-", duplicated-conflicting or inconsistent required fields are rejected.

RASTER VALIDATION (per scene, headers only)
  All four bands must share CRS, size, transform, pixel type and declared nodata; CRS must be the WGS84 UTM zone
  named in the metadata; size and pixel size must equal the metadata; pixel type must be unsigned 16-bit; a declared
  nodata value must not lie inside the valid DN range; the raster extent must agree with the metadata corner.
  The two dates are processed independently; their pixel grids are never assumed identical (the relation is
  reported as a diagnostic).

POLYGON, INCLUSION AND VALID PIXELS: identical to the L2 analysis (src/isro/orchard_ndvi.py): the validated WGS84
  polygon is reprojected into each raster's CRS; PRIMARY inclusion = pixel centre inside or on the boundary;
  sensitivity = any_overlap / fully_inside / coverage-weighted. Valid pixel: unmasked, finite, DN > 0 (DN 0 is
  background), DN <= ValidRange maximum, reflectance denominator != 0. Rejected pixels are counted by reason.
  Only small masked windows are read.

OUTPUTS: private/sites/<SITE_ID>/analysis/resourcesat_boa_ndvi/ only (separate from the L2 results). They contain no
coordinates, polygon geometry or paths.
"""

from __future__ import annotations

import argparse
import io
import json
import logging
import math
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon

from src.isro import orchard_ndvi as l2
from src.isro.orchard_ndvi import (
    DEFAULT_IMAGERY_DIR,
    INCLUSION_MODES,
    MAX_WINDOW_PIXELS,
    WINDOW_PADDING_PIXELS,
    AnalysisError,
    Grid,
    area_weighted_statistics,
    densify_ring,
    inclusion,
    load_boundary,
    mode_statistics,
    reproject_ring,
    sha256_file,
    summarize,
)
from src.sites import SITES_TOOL_VERSION
from src.sites.registry import (
    SITES_SUBDIR,
    PrivatePathError,
    SiteError,
    ensure_private_location,
    private_root,
    write_private_bytes,
)

log = logging.getLogger("mangotwin.orchard_boa_ndvi")

ANALYSIS_ID = "resourcesat2a_liss3_boa_orchard_reflectance_ndvi"
OUTPUT_SUBDIR = ("analysis", "resourcesat_boa_ndvi")          # never the L2 directory (resourcesat_ndvi)
LABEL = ("EXPLORATORY - atmospherically corrected (BOA) reflectance NDVI, quality screening incomplete: no "
         "independent cloud/shadow mask has been verified, CloudPercent is unavailable and the Quality code 'Q' "
         "has not been interpreted. Numerically valid pixels are NOT claimed to be cloud-free. Not field "
         "validated. No inference about vegetation growth, mango health, crop yield or orchard productivity is "
         "made, and no difference between dates is computed.")
DEFAULT_DATES = ("2026-10-07", "2026-10-31")
EXPECTED_PROCESSING_LEVEL = "AtmosphericallyCorrectedProduct"
EXPECTED_SCALE = Decimal("0.0001")
EXPECTED_PIXEL_SIZE_M = 24.0
EXPECTED_DTYPE = "uint16"
BANDS = ("BAND2.tif", "BAND3.tif", "BAND4.tif", "BAND5.tif")
RED_FILE, NIR_FILE = "BAND3.tif", "BAND4.tif"
META_FILE = "BAND_META.txt"
MAX_META_BYTES = 256 * 1024
REQUIRED_META = ("ProcessingLevel", "ProductID", "OTSProductID", "DateOfPass", "ScaleFactor", "ValidRange",
                 "MapProjection", "ZoneNo", "Ellipsoid", "NoScans", "NoPixels", "OutputResolutionAcross",
                 "Sensor", "SatID", "BandNumbers", "FalseNorthing", "ProdULMapX", "ProdULMapY")
PROVENANCE_KEYS = ("ProcessingLevel", "ProductID", "OTSProductID", "DateOfPass", "GenerationDateTime", "SatID",
                   "Sensor", "ProdType", "ScaleFactor", "ValidRange", "SourceAOD", "SourceWaterVapor", "SourceOzone",
                   "Quality", "CloudPercent", "OutputResolutionAcross", "NoScans", "NoPixels", "MapProjection",
                   "ZoneNo", "Ellipsoid")
_MONTHS = {m: i for i, m in enumerate(
    ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"), start=1)}
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_OTS_RE = re.compile(r"^RA\d(\d{2})([A-Z]{3})(\d{4})")
_RANGE_RE = re.compile(r"^(\d+)-(\d+)$")


# --- BAND_META.txt ------------------------------------------------------------------------------------------------

def parse_band_meta(text: str) -> dict[str, str]:
    """``Key=Value`` lines -> dict (whitespace trimmed). Conflicting duplicate keys are an error."""
    if len(text.encode("utf-8", errors="ignore")) > MAX_META_BYTES:
        raise AnalysisError("BAND_META.txt is larger than the safety limit")
    meta: dict[str, str] = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        key, value = (part.strip() for part in line.split("=", 1))
        if not key:
            continue
        if key in meta and meta[key] != value:
            raise AnalysisError(f"BAND_META.txt lists {key} twice with different values")
        meta[key] = value
    return meta


@dataclass(frozen=True)
class BoaMetadata:
    raw: dict
    date: str
    ots_product_id: str
    scale: Decimal
    valid_min: int
    valid_max: int
    epsg: int
    rows: int
    cols: int
    pixel_size_m: float
    upper_left: tuple[float, float]


def _required(meta: dict, key: str) -> str:
    value = meta.get(key, "")
    if not value or value.upper() == "-NA-":
        raise AnalysisError(f"required metadata field {key} is missing or not available")
    return value


def _int(meta: dict, key: str) -> int:
    try:
        return int(_required(meta, key))
    except ValueError:
        raise AnalysisError(f"metadata field {key} is not an integer") from None


def _float(meta: dict, key: str) -> float:
    try:
        value = float(_required(meta, key))
    except ValueError:
        raise AnalysisError(f"metadata field {key} is not a number") from None
    if not math.isfinite(value):
        raise AnalysisError(f"metadata field {key} is not finite")
    return value


def validate_metadata(meta: dict, expected_date: str, scene_dir_name: str,
                      expected_scale: Decimal = EXPECTED_SCALE) -> BoaMetadata:
    """Reject anything that is not the intended BOA product for ``expected_date``. The scale used downstream is
    the one PARSED here; ``expected_scale`` is only the value the metadata is required to state."""
    for key in REQUIRED_META:
        _required(meta, key)
    if meta["ProcessingLevel"] != EXPECTED_PROCESSING_LEVEL:
        raise AnalysisError(f"ProcessingLevel is not {EXPECTED_PROCESSING_LEVEL}")
    if (meta["Sensor"], meta["SatID"], meta["BandNumbers"]) != ("L3", "IRS-R2A", "2345"):
        raise AnalysisError("the product is not a Resourcesat-2A LISS-3 four-band (2345) product")

    try:
        passed = datetime.strptime(meta["DateOfPass"].upper(), "%d-%b-%Y").date()
    except ValueError:
        raise AnalysisError("DateOfPass is not a DD-MON-YYYY date") from None
    if passed.isoformat() != expected_date:
        raise AnalysisError("DateOfPass does not match the requested acquisition date")
    ots = meta["OTSProductID"]
    m = _OTS_RE.match(ots)
    if not m or _MONTHS.get(m.group(2)) is None or \
            datetime(int(m.group(3)), _MONTHS[m.group(2)], int(m.group(1))).date().isoformat() != expected_date:
        raise AnalysisError("the product ID does not encode the requested acquisition date")
    if ots != scene_dir_name:
        raise AnalysisError("the product ID does not match the scene directory that holds the bands")
    if not meta["ProductID"].isdigit():
        raise AnalysisError("ProductID is not numeric")

    try:
        scale = Decimal(meta["ScaleFactor"])
    except InvalidOperation:
        raise AnalysisError("ScaleFactor is not a number") from None
    if not scale.is_finite() or scale <= 0:
        raise AnalysisError("ScaleFactor must be a positive number")
    if scale != expected_scale:
        raise AnalysisError("ScaleFactor is not the expected reflectance scale")
    rng = _RANGE_RE.match(meta["ValidRange"])
    if not rng:
        raise AnalysisError("ValidRange is not 'min-max'")
    vmin, vmax = int(rng.group(1)), int(rng.group(2))
    if vmin != 0 or vmax <= 0 or Decimal(vmax) * scale != 1:
        raise AnalysisError("ValidRange x ScaleFactor does not describe reflectance 0-1")

    if meta["MapProjection"].upper() != "UTM" or meta["Ellipsoid"].upper() != "WGS_84":
        raise AnalysisError("only WGS84 UTM products are supported")
    zone = _int(meta, "ZoneNo")
    if not 1 <= zone <= 60 or _float(meta, "FalseNorthing") != 0.0:
        raise AnalysisError("only northern-hemisphere UTM zones are supported")
    rows, cols = _int(meta, "NoScans"), _int(meta, "NoPixels")
    if rows <= 0 or cols <= 0:
        raise AnalysisError("NoScans/NoPixels must be positive")
    res = _float(meta, "OutputResolutionAcross")
    if res != EXPECTED_PIXEL_SIZE_M:
        raise AnalysisError("OutputResolutionAcross is not 24 m")
    return BoaMetadata(raw=dict(meta), date=expected_date, ots_product_id=ots, scale=scale, valid_min=vmin,
                       valid_max=vmax, epsg=32600 + zone, rows=rows, cols=cols, pixel_size_m=res,
                       upper_left=(_float(meta, "ProdULMapX"), _float(meta, "ProdULMapY")))


# --- scene discovery and raster validation -----------------------------------------------------------------------------------

def find_boa_scene(imagery_dir: Path, date: str) -> Path:
    """The single product directory (holding BAND_META.txt) under resourcesat2a_boa_<YYYYMMDD>/."""
    if not _DATE_RE.match(date):
        raise AnalysisError("dates must look like YYYY-MM-DD")
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise AnalysisError("not a valid calendar date") from None
    base = Path(imagery_dir) / f"resourcesat2a_boa_{date.replace('-', '')}"
    if not base.is_dir():
        raise AnalysisError(f"no BOA scene directory for {date}")
    metas = sorted(base.rglob(META_FILE))
    if len(metas) != 1:
        raise AnalysisError(f"expected exactly one {META_FILE} for {date}, found {len(metas)}")
    return metas[0].parent


def _require_rasterio():
    return l2._require_rasterio()


def validate_rasters(scene_dir: Path, md: BoaMetadata, rasterio) -> dict:
    """Header-only checks of all four bands against each other and against the metadata."""
    infos = []
    for name in BANDS:
        path = scene_dir / name
        if not path.is_file():
            raise AnalysisError(f"{name} is missing from the scene")
        with rasterio.open(path) as src:
            infos.append({"name": name, "crs": src.crs, "shape": src.shape, "transform": src.transform,
                          "dtype": str(src.dtypes[0]), "nodata": src.nodata, "count": src.count})
    ref = infos[0]
    for info in infos[1:]:
        if (info["crs"] != ref["crs"] or info["shape"] != ref["shape"] or info["transform"] != ref["transform"]
                or info["dtype"] != ref["dtype"] or info["nodata"] != ref["nodata"]):
            raise AnalysisError(f"{info['name']} is not aligned with {ref['name']} (CRS, size, transform, type or nodata)")
    if ref["count"] != 1 or any(i["count"] != 1 for i in infos):
        raise AnalysisError("each band must be a single-band raster")
    if ref["crs"] is None or ref["crs"].to_epsg() != md.epsg:
        raise AnalysisError("the raster CRS is not the WGS84 UTM zone named in the metadata")
    if ref["shape"] != (md.rows, md.cols):
        raise AnalysisError("the raster size does not match NoScans x NoPixels")
    t = ref["transform"]
    if t.b != 0 or t.d != 0 or t.e >= 0 or t.a <= 0:
        raise AnalysisError("only north-up rasters are supported")
    if abs(t.a - md.pixel_size_m) > 1e-6 or abs(-t.e - md.pixel_size_m) > 1e-6:
        raise AnalysisError("the raster pixel size does not match the metadata")
    if ref["dtype"] != EXPECTED_DTYPE:
        raise AnalysisError(f"unexpected pixel type {ref['dtype']} (expected {EXPECTED_DTYPE})")
    nodata = ref["nodata"]
    if nodata is not None and (md.valid_min < nodata <= md.valid_max or nodata < 0):
        raise AnalysisError("the declared nodata value lies inside the valid DN range")
    half = md.pixel_size_m / 2
    ulx, uly = md.upper_left
    convention = None
    for label, dx in (("pixel_corner", 0.0), ("pixel_centre", half)):
        if abs(t.c + dx - ulx) < 1e-3 and abs(t.f - dx - uly) < 1e-3:
            convention = label
    if convention is None:
        raise AnalysisError("the raster extent disagrees with the metadata corner")
    return {"crs_epsg": md.epsg, "shape": [md.rows, md.cols], "pixel_size_m": md.pixel_size_m, "dtype": ref["dtype"],
            "nodata_declared": nodata, "metadata_corner_convention": convention,
            "bands_validated": list(BANDS), "origin_phase": (float(t.c) % md.pixel_size_m, float(t.f) % md.pixel_size_m)}


# --- reflectance NDVI (pure numpy) ---------------------------------------------------------------------------------------------

def reflectance_ndvi(red, nir, scale: Decimal, valid_min: int, valid_max: int):
    """NDVI from reflectance = DN x scale.

    Returns (ndvi, red_reflectance, nir_reflectance, valid mask, reason counts). Rejection reasons, in order:
    masked (raster nodata), non_finite, background_zero (DN == 0 in either band), out_of_valid_range (DN outside
    ValidRange), bad_denominator. ``red``/``nir`` may be masked arrays.
    """
    s = float(scale)
    masked = np.ma.getmaskarray(red) | np.ma.getmaskarray(nir)
    r_dn = np.ma.getdata(red).astype("float64")
    n_dn = np.ma.getdata(nir).astype("float64")
    finite = np.isfinite(r_dn) & np.isfinite(n_dn)
    with np.errstate(all="ignore"):
        zero = (r_dn == 0) | (n_dn == 0)
        in_range = (r_dn >= valid_min) & (r_dn <= valid_max) & (n_dn >= valid_min) & (n_dn <= valid_max)
        red_r, nir_r = r_dn * s, n_dn * s
        denominator = nir_r + red_r
        denom_ok = np.isfinite(denominator) & (denominator != 0)
    live = ~masked & finite
    valid = live & ~zero & in_range & denom_ok
    ndvi = np.full(r_dn.shape, np.nan, dtype="float64")
    with np.errstate(all="ignore"):
        np.divide(nir_r - red_r, denominator, out=ndvi, where=valid)
    reasons = {
        "masked": masked,
        "non_finite": ~masked & ~finite,
        "background_zero": live & zero,
        "out_of_valid_range": live & ~zero & ~in_range,
        "bad_denominator": live & ~zero & in_range & ~denom_ok,
    }
    counts = {k: int(v.sum()) for k, v in reasons.items()}
    return ndvi, red_r, nir_r, valid, counts, reasons


# --- one scene --------------------------------------------------------------------------------------------------------------------------

def analyze_boa_scene(date: str, scene_dir: Path, ring: list[tuple[float, float]], *, hash_files: bool = True,
                      expected_scale: Decimal = EXPECTED_SCALE) -> dict:
    rasterio, Window = _require_rasterio()
    meta_path = scene_dir / META_FILE
    if not meta_path.is_file() or meta_path.stat().st_size > MAX_META_BYTES:
        raise AnalysisError("BAND_META.txt is missing or too large")
    md = validate_metadata(parse_band_meta(meta_path.read_text(encoding="utf-8-sig", errors="replace")),
                           date, scene_dir.name, expected_scale)
    raster = validate_rasters(scene_dir, md, rasterio)

    red_path, nir_path = scene_dir / RED_FILE, scene_dir / NIR_FILE
    with rasterio.open(red_path) as red_src, rasterio.open(nir_path) as nir_src:
        t = red_src.transform
        pw, ph = float(t.a), float(-t.e)
        polygon = Polygon(reproject_ring(densify_ring(ring), red_src.crs.to_wkt()))
        if not polygon.is_valid or polygon.is_empty:
            raise AnalysisError("the reprojected polygon is not valid")
        minx, miny, maxx, maxy = polygon.bounds
        col0 = math.floor((minx - t.c) / pw) - WINDOW_PADDING_PIXELS
        col1 = math.ceil((maxx - t.c) / pw) + WINDOW_PADDING_PIXELS
        row0 = math.floor((t.f - maxy) / ph) - WINDOW_PADDING_PIXELS
        row1 = math.ceil((t.f - miny) / ph) + WINDOW_PADDING_PIXELS
        if col0 < 0 or row0 < 0 or col1 > red_src.width or row1 > red_src.height:
            raise AnalysisError("the orchard polygon is not entirely inside this raster")
        ncols, nrows = col1 - col0, row1 - row0
        if ncols * nrows > MAX_WINDOW_PIXELS:
            raise AnalysisError("the polygon window is unexpectedly large; refusing to read it")
        window = Window(col0, row0, ncols, nrows)
        red = red_src.read(1, window=window, masked=True)          # windowed + masked: never a whole scene
        nir = nir_src.read(1, window=window, masked=True)

    grid = Grid(t.c + col0 * pw, t.f - row0 * ph, pw, ph, nrows, ncols)
    masks = inclusion(polygon, grid)
    ndvi, red_r, nir_r, valid, _, reasons = reflectance_ndvi(red, nir, md.scale, md.valid_min, md.valid_max)
    centre, fraction = masks["center"], masks["fraction"]
    partial = (fraction > 0) & (fraction < l2._FULL)
    inc = {"primary": "center",
           **{mode: mode_statistics(ndvi, valid, masks[mode]) for mode in INCLUSION_MODES},
           "area_weighted": area_weighted_statistics(ndvi, valid, fraction)}
    primary_valid = centre & valid
    means = [inc[m]["mean"] for m in INCLUSION_MODES if inc[m]["mean"] is not None] + \
            ([inc["area_weighted"]["mean"]] if inc["area_weighted"]["mean"] is not None else [])

    meta_info = {k: md.raw[k] for k in PROVENANCE_KEYS if k in md.raw}
    scene = {
        "date": date,
        "processing": {
            "metadata": meta_info,
            "scale_factor_parsed": str(md.scale),
            "valid_range_dn": [md.valid_min, md.valid_max],
            "reflectance": "DN x parsed ScaleFactor",
            "quality": {"quality_code": md.raw.get("Quality"), "quality_code_interpreted": False,
                        "cloud_percent_metadata": md.raw.get("CloudPercent"),
                        "independent_cloud_shadow_mask": "none verified",
                        "cloud_free_claimed": False},
        },
        "files": {name: {"bytes": (scene_dir / name).stat().st_size} for name in BANDS},
        "raster": {k: v for k, v in raster.items() if k != "origin_phase"},
        "polygon": {"area_in_raster_crs_m2": round(float(polygon.area), 3), "pixel_area_m2": grid.pixel_area,
                    "polygon_area_in_pixel_equivalents": round(float(polygon.area / grid.pixel_area), 3)},
        "inclusion": inc,
        "boundary_pixels": {
            "partially_covered_pixels": int(partial.sum()),
            "partially_covered_and_included_by_center": int((partial & centre).sum()),
            "share_of_center_pixels_that_are_partially_covered":
                (float((partial & centre).sum() / centre.sum()) if centre.sum() else None),
            "note": "partially covered pixels are mixed pixels that also contain land outside the orchard",
        },
        "boundary_sensitivity": {
            "mean_ndvi_min_across_inclusion_rules": (min(means) if means else None),
            "mean_ndvi_max_across_inclusion_rules": (max(means) if means else None),
            "mean_ndvi_spread": (max(means) - min(means) if means else None),
            "rules": list(INCLUSION_MODES) + ["area_weighted"],
        },
        "rejected_pixels_among_center_selection": {k: int((v & centre).sum()) for k, v in reasons.items()},
        "reflectance_primary_inclusion": {
            "red": summarize(red_r[primary_valid]), "nir": summarize(nir_r[primary_valid]),
            "note": "reflectance of valid centre-inclusion pixels; plausibility check only"},
    }
    if hash_files:
        scene["files"][META_FILE] = {"bytes": meta_path.stat().st_size, "sha256": sha256_file(meta_path)}
        for name in (RED_FILE, NIR_FILE):
            scene["files"][name]["sha256"] = sha256_file(scene_dir / name)
    scene["_origin_phase"] = raster["origin_phase"]           # popped before output; used for the grid diagnostic
    return scene


def grid_relation(scenes: list[dict]) -> dict | None:
    """Do the dates' pixel grids coincide? Reported as a diagnostic only; each date is processed independently."""
    if len(scenes) < 2:
        return None
    px = EXPECTED_PIXEL_SIZE_M
    base = scenes[0]["_origin_phase"]
    out = []
    for other in scenes[1:]:
        dx = (other["_origin_phase"][0] - base[0]) % px
        dy = (other["_origin_phase"][1] - base[1]) % px
        dx, dy = min(dx, px - dx), min(dy, px - dy)
        out.append({"date": other["date"], "relative_to": scenes[0]["date"],
                    "relative_phase_offset_m": [round(dx, 4), round(dy, 4)],
                    "pixel_grids_coincide": bool(dx < 1e-3 and dy < 1e-3)})
    return {"note": "diagnostic only; scenes are never resampled or assumed aligned", "pairs": out}


# --- outputs ----------------------------------------------------------------------------------------------------------------------------------

CSV_COLUMNS = ["date", "inclusion", "selected_pixels", "valid_pixels", "valid_fraction", "mean", "median", "minimum",
               "maximum", "std", "label"]


def _r(v, nd: int = 6):
    return None if v is None else round(float(v), nd)


def build_csv(results: dict) -> str:
    import csv
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_COLUMNS, lineterminator="\n")
    writer.writeheader()
    for scene in results["scenes"]:
        for mode in INCLUSION_MODES:
            s = scene["inclusion"][mode]
            writer.writerow({"date": scene["date"], "inclusion": mode + (" (primary)" if mode == "center" else ""),
                             "selected_pixels": s["selected_pixels"], "valid_pixels": s["valid_pixels"],
                             "valid_fraction": _r(s["valid_fraction"]), "mean": _r(s["mean"]), "median": _r(s["median"]),
                             "minimum": _r(s["minimum"]), "maximum": _r(s["maximum"]), "std": _r(s["std"]),
                             "label": "exploratory BOA reflectance NDVI; quality screening incomplete"})
    return buf.getvalue()


def render_chart(results: dict) -> bytes:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    scenes = results["scenes"]
    fig, ax = plt.subplots(figsize=(8.5, 1.8 + 1.1 * len(scenes)))
    for i, scene in enumerate(scenes):
        s = scene["inclusion"]["center"]
        if s["valid_pixels"]:
            ax.hlines(i, s["minimum"], s["maximum"], color="#4c8f6a", linewidth=6, alpha=0.5)
            ax.plot(s["mean"], i, "o", color="#1b5e3a", label="mean" if i == 0 else None)
            ax.plot(s["median"], i, "D", color="#c45b1c", label="median" if i == 0 else None)
        ax.text(1.0, i, f"  valid {s['valid_pixels']}/{s['selected_pixels']}", va="center", fontsize=8,
                transform=ax.get_yaxis_transform())
    ax.set_yticks(range(len(scenes)))
    ax.set_yticklabels([s["date"] for s in scenes])
    ax.set_xlabel("NDVI from BOA reflectance (DN x ScaleFactor)")
    ax.set_title("Orchard polygon, pixel-centre inclusion: per-date distribution\nEXPLORATORY - quality screening "
                 "incomplete (no verified cloud/shadow mask); not a growth or health comparison", fontsize=8.5)
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    out = io.BytesIO()
    fig.savefig(out, format="png", dpi=150)
    plt.close(fig)
    return out.getvalue()


# --- orchestration ------------------------------------------------------------------------------------------------------------------------------

def run(site_id: str, *, dates=DEFAULT_DATES, imagery_dir=DEFAULT_IMAGERY_DIR, private_dir=None, chart: bool = True,
        dry_run: bool = False, hash_files: bool = True, ignore_checker=None, expected_scale: Decimal = EXPECTED_SCALE):
    """Library entry point. Returns (exit_code, results-or-None, message lines)."""
    lines: list[str] = []
    try:
        kwargs = {} if ignore_checker is None else {"ignore_checker": ignore_checker}
        root = ensure_private_location(private_root(private_dir), **kwargs)
        site, ring_report = load_boundary(site_id, root)
        scenes = []
        for date in dates:
            scene_dir = find_boa_scene(Path(imagery_dir), date)
            scene = analyze_boa_scene(date, scene_dir, ring_report.normalized_ring, hash_files=hash_files,
                                      expected_scale=expected_scale)
            scenes.append(scene)
            c = scene["inclusion"]["center"]
            lines.append(f"{date}: centre-inclusion valid {c['valid_pixels']}/{c['selected_pixels']} px "
                         f"(fraction {c['valid_fraction']:.3f}), BOA NDVI mean {c['mean']:.4f}, median {c['median']:.4f}, "
                         f"min {c['minimum']:.4f}, max {c['maximum']:.4f}, std {c['std']:.4f}"
                         if c["valid_pixels"] else f"{date}: no valid pixels")
    except (SiteError, PrivatePathError, AnalysisError) as exc:
        return 2, None, [f"error: {exc}"]
    except OSError:
        return 2, None, ["error: could not read a file"]

    relation = grid_relation(scenes)
    for scene in scenes:
        scene.pop("_origin_phase", None)
    results = {
        "analysis": ANALYSIS_ID, "label": LABEL, "site_id": site.site_id,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "tool_version": SITES_TOOL_VERSION,
        "formula": "(NIRr - Redr) / (NIRr + Redr) with reflectance = DN x ScaleFactor; Red = BAND3, NIR = BAND4",
        "method": {"inclusion": "see src/isro/orchard_boa_ndvi.py module documentation", "primary_inclusion": "center",
                   "valid_pixel_rule": "both bands unmasked, finite, DN > 0, DN within ValidRange, denominator != 0",
                   "std": "population (ddof = 0)",
                   "reprojection": "WGS84 polygon densified to <= 5 m and transformed to each raster CRS with pyproj",
                   "reads": "windowed, masked; whole scenes never loaded"},
        "limitations": [
            "No independent cloud/shadow mask has been verified.",
            "CloudPercent is unavailable (-NA-) and the Quality code 'Q' has not been interpreted.",
            "Numerically valid pixels are not claimed to be cloud-free.",
            "No inference about vegetation growth, mango health, crop yield or orchard productivity; no difference between dates is computed.",
        ],
        "grid_alignment_between_dates": relation,
        "scenes": scenes,
        "privacy": "Private. Contains no coordinates or polygon geometry. Keep inside private/ (excluded from Git, Docker and GCP).",
    }
    if dry_run:
        lines.append("dry run: nothing was written")
        return 0, results, lines
    try:
        base = (SITES_SUBDIR, site.site_id, *OUTPUT_SUBDIR)
        write_private_bytes(root, (*base, "boa_ndvi_statistics.json"), (json.dumps(results, indent=2) + "\n").encode("utf-8"))
        write_private_bytes(root, (*base, "boa_ndvi_statistics.csv"), build_csv(results).encode("utf-8"))
        if chart:
            write_private_bytes(root, (*base, "boa_ndvi_distribution.png"), render_chart(results))
    except (PrivatePathError, OSError) as exc:
        return 2, results, lines + [f"error: {exc}" if isinstance(exc, PrivatePathError) else "error: could not write a private file"]
    lines.append("wrote private results (do not commit): " + "/".join(("private", *base)))
    lines.append("EXPLORATORY BOA reflectance NDVI; quality screening incomplete; no growth, health, yield or productivity inference.")
    return 0, results, lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Private orchard BOA-reflectance NDVI statistics (exploratory).")
    parser.add_argument("--site-id", required=True)
    parser.add_argument("--dates", nargs="+", default=list(DEFAULT_DATES))
    parser.add_argument("--imagery-dir", default=str(DEFAULT_IMAGERY_DIR))
    parser.add_argument("--private-dir")
    parser.add_argument("--no-chart", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    code, _, lines = run(args.site_id, dates=args.dates, imagery_dir=Path(args.imagery_dir), private_dir=args.private_dir,
                         chart=not args.no_chart, dry_run=args.dry_run)
    print("\n".join(lines))
    return code


if __name__ == "__main__":
    sys.exit(main())
