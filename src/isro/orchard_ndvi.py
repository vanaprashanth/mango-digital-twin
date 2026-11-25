"""
Private orchard Resourcesat-2A LISS-3 raw-band NDVI statistics (PHASE 2A, EXPLORATORY).

    .venv/Scripts/python.exe -m src.isro.orchard_ndvi --site-id MANGO_ORCHARD_001

EXPLORATORY, UNCALIBRATED. NDVI here is (NIR - Red) / (NIR + Red) computed directly on the raw digital
numbers (DN) of BAND4 (NIR) and BAND3 (Red). The DNs are NOT converted to radiance or reflectance and no
atmospheric, solar-geometry or sensor-gain correction is applied, so values are not comparable with the
Sentinel-2 NDVI in this project, and the two dates are not radiometrically comparable with each other.
This tool therefore reports per-date statistics only. It deliberately computes NO difference between dates and
makes no statement about vegetation growth, crop health or mango presence.

Isolation: nothing in the production pipeline, dashboard, workflows or GCS publishing imports this module. It
reuses the Phase 1 private site registry and the validated polygon. ``rasterio`` (needed only to read raster
windows) is a local research dependency present in the project's ``.venv``; it is deliberately NOT added to
requirements.txt. Everything else (shapely, pyproj, numpy, matplotlib) is already installed.

POLYGON -> RASTER
  1. The validated WGS84 polygon is densified (<= 5 m between vertices) and transformed to each raster's own CRS
     with pyproj (always_xy). It is never compared with a raster in a different CRS.
  2. Only the polygon's bounding window (+1 pixel) is read, with masked reads, from the Red and NIR bands. Whole
     scenes are never loaded. A polygon that is not entirely inside the raster is an error (never silently clipped).

PIXEL INCLUSION (boundary pixels), for a 24 m pixel and a polygon of about 90 pixel-areas
  center        PRIMARY. A pixel is included when its centre lies inside the polygon or on its boundary.
  any_overlap   Sensitivity (upper bound): every pixel overlapped by the polygon with positive area.
  fully_inside  Sensitivity (lower bound / least mixed): only pixels entirely inside the polygon.
  area_weighted Sensitivity: every overlapped pixel weighted by its exact polygon coverage fraction
                (mean and standard deviation only).
  Boundary (partially covered) pixels are mixed pixels containing non-orchard land; their number and share are
  reported so the effect of the inclusion rule can be judged.

VALID PIXELS
  A pixel is valid when both bands are unmasked (raster nodata, if any), both DNs are > 0 (the products declare
  no nodata value; DN 0 is treated as fill), both are finite, and NIR + Red != 0. Invalid pixels are counted by
  reason. valid_fraction = valid pixels / pixels selected by the inclusion rule.

STATISTICS: count, valid fraction, mean, median, min, max and population standard deviation (ddof = 0).

PRIVACY: results are written ONLY inside private/sites/<SITE_ID>/analysis/resourcesat_ndvi/ (Git/Docker/GCP
excluded). Outputs contain no coordinates and no raster window offsets; logs and console output contain none.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import logging
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import Polygon

from src.sites import SITES_TOOL_VERSION
from src.sites.geometry import geodesic_distance, validate_ring
from src.sites.registry import (
    PROJECT_ROOT,
    SITES_SUBDIR,
    PrivatePathError,
    SiteError,
    ensure_private_location,
    load_site_config,
    private_root,
    safe_join,
    write_private_bytes,
)

log = logging.getLogger("mangotwin.orchard_ndvi")

ANALYSIS_ID = "resourcesat2a_liss3_orchard_raw_band_ndvi"
OUTPUT_SUBDIR = ("analysis", "resourcesat_ndvi")
LABEL = ("EXPLORATORY - uncalibrated raw-band NDVI computed from digital numbers (not reflectance). Not field "
         "validated. No inference about vegetation growth, crop health or mango presence is made, and no "
         "difference between dates is computed.")
DEFAULT_IMAGERY_DIR = PROJECT_ROOT / "data" / "satellite_experiments"
DEFAULT_DATES = ("2026-10-07", "2026-10-31")
RED_FILE, NIR_FILE = "BAND3.tif", "BAND4.tif"
DENSIFY_STEP_M = 5.0
WINDOW_PADDING_PIXELS = 1
MAX_WINDOW_PIXELS = 4_000_000          # the window around one orchard; protects against loading a whole scene
INCLUSION_MODES = ("center", "any_overlap", "fully_inside")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_FULL = 1 - 1e-9


class AnalysisError(ValueError):
    """The analysis cannot be completed (messages never contain coordinates)."""


# --- NDVI and statistics (pure numpy) -------------------------------------------------------------------------------

def compute_ndvi(red, nir) -> tuple[np.ndarray, np.ndarray, dict]:
    """Raw-band NDVI with an explicit validity mask. ``red``/``nir`` may be masked arrays.

    Returns (ndvi float64 with NaN where invalid, valid mask, counts by invalidity reason). A pixel counted as
    invalid is attributed to the first applicable reason: masked, non_finite, non_positive_dn, bad_denominator.
    """
    red_mask = np.ma.getmaskarray(red)
    nir_mask = np.ma.getmaskarray(nir)
    r = np.ma.getdata(red).astype("float64")
    n = np.ma.getdata(nir).astype("float64")
    masked = red_mask | nir_mask
    finite = np.isfinite(r) & np.isfinite(n)
    positive = (r > 0) & (n > 0)
    with np.errstate(all="ignore"):
        denominator = n + r
        usable_denominator = np.isfinite(denominator) & (denominator != 0)
    valid = ~masked & finite & positive & usable_denominator
    ndvi = np.full(r.shape, np.nan, dtype="float64")
    with np.errstate(all="ignore"):
        np.divide(n - r, denominator, out=ndvi, where=valid)
    counts = {
        "masked": int(masked.sum()),
        "non_finite": int((~masked & ~finite).sum()),
        "non_positive_dn": int((~masked & finite & ~positive).sum()),
        "bad_denominator": int((~masked & finite & positive & ~usable_denominator).sum()),
    }
    return ndvi, valid, counts


def summarize(values: np.ndarray, weights: np.ndarray | None = None) -> dict:
    """count/mean/median/min/max/std(ddof=0). With weights only the weighted mean and std are reported."""
    values = np.asarray(values, dtype="float64")
    if values.size == 0:
        return {"count": 0, "mean": None, "median": None, "minimum": None, "maximum": None, "std": None}
    if weights is not None:
        w = np.asarray(weights, dtype="float64")
        total = w.sum()
        mean = float((values * w).sum() / total)
        std = float(math.sqrt(max(float((w * (values - mean) ** 2).sum() / total), 0.0)))
        return {"count": int(values.size), "mean": mean, "median": None, "minimum": None, "maximum": None, "std": std}
    return {"count": int(values.size), "mean": float(values.mean()), "median": float(np.median(values)),
            "minimum": float(values.min()), "maximum": float(values.max()), "std": float(values.std())}


# --- polygon <-> raster grid (shapely / numpy) ----------------------------------------------------------------------------

def densify_ring(ring: list[tuple[float, float]], max_step_m: float = DENSIFY_STEP_M) -> list[tuple[float, float]]:
    """Add vertices so no edge is longer than ``max_step_m`` (linear in lon/lat; edges here are metres long)."""
    out = [ring[0]]
    for (lon1, lat1), (lon2, lat2) in zip(ring, ring[1:]):
        steps = max(1, math.ceil(geodesic_distance(lon1, lat1, lon2, lat2) / max_step_m))
        for k in range(1, steps + 1):
            t = k / steps
            out.append((lon1 + (lon2 - lon1) * t, lat1 + (lat2 - lat1) * t))
    return out


def reproject_ring(ring: list[tuple[float, float]], raster_crs_wkt: str) -> list[tuple[float, float]]:
    from pyproj import CRS, Transformer
    transformer = Transformer.from_crs("EPSG:4326", CRS.from_wkt(raster_crs_wkt), always_xy=True)
    xs, ys = transformer.transform([p[0] for p in ring], [p[1] for p in ring])
    return list(zip(map(float, xs), map(float, ys)))


class Grid:
    """A north-up pixel grid window: origin of the window's top-left corner and square-ish pixel size."""

    def __init__(self, x0: float, y0: float, pixel_w: float, pixel_h: float, nrows: int, ncols: int):
        self.x0, self.y0, self.pw, self.ph, self.nrows, self.ncols = x0, y0, pixel_w, pixel_h, nrows, ncols
        cols, rows = np.meshgrid(np.arange(ncols), np.arange(nrows))
        self.cx = x0 + (cols + 0.5) * pixel_w
        self.cy = y0 - (rows + 0.5) * pixel_h
        self.pixel_area = pixel_w * pixel_h

    def boxes(self):
        left = self.x0 + np.arange(self.ncols) * self.pw
        top = self.y0 - np.arange(self.nrows) * self.ph
        xmin, ymax = np.meshgrid(left, top)
        return shapely.box(xmin, ymax - self.ph, xmin + self.pw, ymax)


def inclusion(polygon: Polygon, grid: Grid) -> dict:
    """Boolean masks for each inclusion mode plus the exact per-pixel coverage fraction (0..1)."""
    centre = shapely.intersects_xy(polygon, grid.cx, grid.cy)
    boxes = grid.boxes()
    overlap_area = shapely.area(shapely.intersection(boxes, polygon))
    fraction = np.clip(overlap_area / grid.pixel_area, 0.0, 1.0)
    return {
        "center": np.asarray(centre, dtype=bool),
        "any_overlap": fraction > 0,
        "fully_inside": fraction >= _FULL,
        "fraction": fraction,
    }


def mode_statistics(ndvi: np.ndarray, valid: np.ndarray, selected: np.ndarray) -> dict:
    n_selected = int(selected.sum())
    in_valid = selected & valid
    stats = summarize(ndvi[in_valid])
    return {"selected_pixels": n_selected, "valid_pixels": int(in_valid.sum()),
            "valid_fraction": (float(in_valid.sum() / n_selected) if n_selected else None), **stats}


def area_weighted_statistics(ndvi, valid, fraction) -> dict:
    covered = fraction > 0
    use = covered & valid
    total_weight = float(fraction[covered].sum())
    valid_weight = float(fraction[use].sum())
    stats = summarize(ndvi[use], fraction[use])
    return {"covered_pixels": int(covered.sum()), "valid_pixels": int(use.sum()),
            "valid_area_fraction": (valid_weight / total_weight if total_weight else None),
            "mean": stats["mean"], "std": stats["std"],
            "note": "coverage-fraction-weighted mean and population std; median/min/max are not defined here"}


# --- boundary and scene discovery ---------------------------------------------------------------------------------------------

def load_boundary(site_id: str, root: Path):
    """The Phase 1 validated polygon (WGS84 ring, counter-clockwise, closed) of a private site."""
    site = load_site_config(site_id, root)
    report_path = safe_join(root, SITES_SUBDIR, site.site_id, site.report_name)
    geojson_path = safe_join(root, SITES_SUBDIR, site.site_id, site.geojson_name)
    if not geojson_path.is_file() or not report_path.is_file():
        raise AnalysisError("run python -m src.sites.validate_boundary first (validated boundary not found)")
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
        gj = json.loads(geojson_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise AnalysisError("the validated boundary or its report is unreadable") from None
    if not report.get("all_checks_passed"):
        raise AnalysisError("the boundary has not passed Phase 1 validation; refusing to analyse it")
    try:
        features = gj["features"]
        if len(features) != 1 or features[0]["geometry"]["type"] != "Polygon" or len(features[0]["geometry"]["coordinates"]) != 1:
            raise KeyError
        ring = [(float(x), float(y)) for x, y in features[0]["geometry"]["coordinates"][0]]
    except (KeyError, TypeError, ValueError):
        raise AnalysisError("the boundary GeoJSON must hold exactly one Polygon with one ring") from None
    rep = validate_ring(ring)
    if not rep.valid:
        raise AnalysisError("the boundary polygon is not valid")
    return site, rep


def find_scene_bands(imagery_dir: Path, date: str) -> tuple[Path, Path]:
    if not _DATE_RE.match(date):
        raise AnalysisError("dates must look like YYYY-MM-DD")
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise AnalysisError("not a valid calendar date") from None
    folder = Path(imagery_dir) / f"resourcesat2a_{date.replace('-', '')}"
    if not folder.is_dir():
        raise AnalysisError(f"no scene directory for {date}")
    found = {}
    for name in (RED_FILE, NIR_FILE):
        matches = sorted(folder.rglob(name))
        if len(matches) != 1:
            raise AnalysisError(f"expected exactly one {name} for {date}, found {len(matches)}")
        found[name] = matches[0]
    return found[RED_FILE], found[NIR_FILE]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --- one scene ------------------------------------------------------------------------------------------------------------------------

def _require_rasterio():
    try:
        import rasterio
        from rasterio.windows import Window
    except ImportError:
        raise AnalysisError("rasterio is required to read the scenes; run this with the project's .venv "
                            "(.venv/Scripts/python.exe -m src.isro.orchard_ndvi ...)") from None
    return rasterio, Window


def analyze_scene(date: str, red_path: Path, nir_path: Path, ring: list[tuple[float, float]], *,
                  hash_files: bool = True) -> dict:
    """Per-date statistics for one scene. ``ring`` is the validated WGS84 polygon (closed)."""
    rasterio, Window = _require_rasterio()
    with rasterio.open(red_path) as red_src, rasterio.open(nir_path) as nir_src:
        if (red_src.crs != nir_src.crs or red_src.transform != nir_src.transform or red_src.shape != nir_src.shape):
            raise AnalysisError("the Red and NIR rasters are not aligned")
        if red_src.crs is None:
            raise AnalysisError("the raster has no CRS")
        t = red_src.transform
        if t.b != 0 or t.d != 0 or t.e >= 0 or t.a <= 0:
            raise AnalysisError("only north-up rasters are supported")
        pw, ph = float(t.a), float(-t.e)

        xy = reproject_ring(densify_ring(ring), red_src.crs.to_wkt())
        polygon = Polygon(xy)
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
        raster_info = {"crs_epsg": red_src.crs.to_epsg(), "pixel_size_m": [pw, ph],
                       "width": red_src.width, "height": red_src.height, "dtype": str(red_src.dtypes[0]),
                       "nodata_declared": red_src.nodata, "window_shape": [nrows, ncols]}

    grid = Grid(t.c + col0 * pw, t.f - row0 * ph, pw, ph, nrows, ncols)
    masks = inclusion(polygon, grid)
    ndvi, valid, dropped = compute_ndvi(red, nir)
    fraction = masks["fraction"]
    centre = masks["center"]
    partial = (fraction > 0) & (fraction < _FULL)
    selected_dropped = {k: int(v) for k, v in zip(
        dropped, [int((c & centre).sum()) for c in _reason_masks(red, nir)])}

    scene = {
        "date": date,
        "bands": {"red": {"file": RED_FILE, "bytes": red_path.stat().st_size},
                  "nir": {"file": NIR_FILE, "bytes": nir_path.stat().st_size}},
        "raster": raster_info,
        "polygon": {"area_in_raster_crs_m2": round(float(polygon.area), 3),
                    "pixel_area_m2": grid.pixel_area,
                    "polygon_area_in_pixel_equivalents": round(float(polygon.area / grid.pixel_area), 3)},
        "inclusion": {
            "primary": "center",
            "center": mode_statistics(ndvi, valid, masks["center"]),
            "any_overlap": mode_statistics(ndvi, valid, masks["any_overlap"]),
            "fully_inside": mode_statistics(ndvi, valid, masks["fully_inside"]),
            "area_weighted": area_weighted_statistics(ndvi, valid, fraction),
        },
        "boundary_pixels": {
            "partially_covered_pixels": int(partial.sum()),
            "partially_covered_and_included_by_center": int((partial & centre).sum()),
            "share_of_center_pixels_that_are_partially_covered":
                (float((partial & centre).sum() / centre.sum()) if centre.sum() else None),
            "note": "partially covered pixels are mixed pixels that also contain land outside the orchard",
        },
        "invalid_pixels_among_center_selection": selected_dropped,
    }
    if hash_files:
        scene["bands"]["red"]["sha256"] = sha256_file(red_path)
        scene["bands"]["nir"]["sha256"] = sha256_file(nir_path)
    return scene


def _reason_masks(red, nir):
    """Masks in the same order as compute_ndvi's counts (masked, non_finite, non_positive_dn, bad_denominator)."""
    red_mask, nir_mask = np.ma.getmaskarray(red), np.ma.getmaskarray(nir)
    r, n = np.ma.getdata(red).astype("float64"), np.ma.getdata(nir).astype("float64")
    masked = red_mask | nir_mask
    finite = np.isfinite(r) & np.isfinite(n)
    positive = (r > 0) & (n > 0)
    with np.errstate(all="ignore"):
        denom_ok = np.isfinite(n + r) & ((n + r) != 0)
    return [masked, ~masked & ~finite, ~masked & finite & ~positive, ~masked & finite & positive & ~denom_ok]


# --- outputs --------------------------------------------------------------------------------------------------------------------------------

CSV_COLUMNS = ["date", "inclusion", "selected_pixels", "valid_pixels", "valid_fraction", "mean", "median", "minimum",
               "maximum", "std", "label"]


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
                             "label": "exploratory uncalibrated raw-band NDVI"})
    return buf.getvalue()


def _r(v, nd: int = 6):
    return None if v is None else round(float(v), nd)


def render_chart(results: dict) -> bytes:
    """Per-date range plot (min-max bar, mean and median markers). No difference between dates is drawn."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    scenes = results["scenes"]
    fig, ax = plt.subplots(figsize=(8, 1.6 + 1.1 * len(scenes)))
    for i, scene in enumerate(scenes):
        s = scene["inclusion"]["center"]
        if s["valid_pixels"]:
            ax.hlines(i, s["minimum"], s["maximum"], color="#4c6fa5", linewidth=6, alpha=0.5)
            ax.plot(s["mean"], i, "o", color="#1b3a6b", label="mean" if i == 0 else None)
            ax.plot(s["median"], i, "D", color="#c45b1c", label="median" if i == 0 else None)
        ax.text(1.0, i, f"  valid {s['valid_pixels']}/{s['selected_pixels']}", va="center", fontsize=8,
                transform=ax.get_yaxis_transform())
    ax.set_yticks(range(len(scenes)))
    ax.set_yticklabels([s["date"] for s in scenes])
    ax.set_xlabel("raw-band NDVI (digital numbers; uncalibrated)")
    ax.set_title("Orchard polygon, pixel-centre inclusion: per-date distribution\nEXPLORATORY - not reflectance, "
                 "not field validated, dates not comparable", fontsize=9)
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    out = io.BytesIO()
    fig.savefig(out, format="png", dpi=150)
    plt.close(fig)
    return out.getvalue()


# --- orchestration ---------------------------------------------------------------------------------------------------------------------------

def run(site_id: str, *, dates=DEFAULT_DATES, imagery_dir=DEFAULT_IMAGERY_DIR, private_dir=None,
        chart: bool = True, dry_run: bool = False, hash_files: bool = True, ignore_checker=None):
    """Library entry point. Returns (exit_code, results-or-None, message lines)."""
    lines: list[str] = []
    try:
        kwargs = {} if ignore_checker is None else {"ignore_checker": ignore_checker}
        root = ensure_private_location(private_root(private_dir), **kwargs)
        site, ring_report = load_boundary(site_id, root)
        ring = ring_report.normalized_ring
        scenes = []
        for date in dates:
            red_path, nir_path = find_scene_bands(Path(imagery_dir), date)
            scene = analyze_scene(date, red_path, nir_path, ring, hash_files=hash_files)
            scenes.append(scene)
            c = scene["inclusion"]["center"]
            lines.append(f"{date}: centre-inclusion valid {c['valid_pixels']}/{c['selected_pixels']} px "
                         f"(fraction {c['valid_fraction']:.3f}), raw-band NDVI mean {c['mean']:.4f}, median {c['median']:.4f}, "
                         f"min {c['minimum']:.4f}, max {c['maximum']:.4f}, std {c['std']:.4f}"
                         if c["valid_pixels"] else f"{date}: no valid pixels")
    except (SiteError, PrivatePathError, AnalysisError) as exc:
        return 2, None, [f"error: {exc}"]
    except OSError:
        return 2, None, ["error: could not read a file"]

    results = {
        "analysis": ANALYSIS_ID,
        "label": LABEL,
        "site_id": site.site_id,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tool_version": SITES_TOOL_VERSION,
        "formula": "(NIR - Red) / (NIR + Red) on raw DN; Red = BAND3, NIR = BAND4",
        "method": {"inclusion": "see src/isro/orchard_ndvi.py module documentation",
                   "primary_inclusion": "center",
                   "valid_pixel_rule": "both bands unmasked, DN > 0, finite, NIR + Red != 0",
                   "std": "population (ddof = 0)", "reprojection": "WGS84 polygon densified to <= 5 m and "
                   "transformed to each raster CRS with pyproj", "reads": "windowed, masked; whole scenes never loaded"},
        "scenes": scenes,
        "privacy": "Private. Contains no coordinates. Keep inside private/ (excluded from Git, Docker and GCP).",
    }
    if dry_run:
        lines.append("dry run: nothing was written")
        return 0, results, lines
    try:
        base = (SITES_SUBDIR, site.site_id, *OUTPUT_SUBDIR)
        write_private_bytes(root, (*base, "ndvi_statistics.json"), (json.dumps(results, indent=2) + "\n").encode("utf-8"))
        write_private_bytes(root, (*base, "ndvi_statistics.csv"), build_csv(results).encode("utf-8"))
        if chart:
            write_private_bytes(root, (*base, "ndvi_distribution.png"), render_chart(results))
    except (PrivatePathError, OSError) as exc:
        return 2, results, lines + [f"error: {exc}" if isinstance(exc, PrivatePathError) else "error: could not write a private file"]
    lines.append("wrote private results (do not commit): " + "/".join(("private", *base)))
    lines.append("EXPLORATORY uncalibrated raw-band NDVI; no growth, health or mango inference is made.")
    return 0, results, lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Private orchard Resourcesat NDVI statistics (exploratory).")
    parser.add_argument("--site-id", required=True)
    parser.add_argument("--dates", nargs="+", default=list(DEFAULT_DATES))
    parser.add_argument("--imagery-dir", default=str(DEFAULT_IMAGERY_DIR))
    parser.add_argument("--private-dir")
    parser.add_argument("--no-chart", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    code, _, lines = run(args.site_id, dates=args.dates, imagery_dir=Path(args.imagery_dir),
                         private_dir=args.private_dir, chart=not args.no_chart, dry_run=args.dry_run)
    print("\n".join(lines))
    return code


if __name__ == "__main__":
    sys.exit(main())
