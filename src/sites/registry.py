"""
Private research-site registry: where site data lives, how paths are kept inside it, and the site schema.

Layout (private, never committed)::

    private/sites/<SITE_ID>/site.yaml
    private/sites/<SITE_ID>/boundary.kml            original, byte-for-byte
    private/sites/<SITE_ID>/boundary.geojson        derived
    private/sites/<SITE_ID>/validation_report.json  geometry checks + provenance (no coordinates)

``site.yaml`` holds identity, a reference point, optional comparison points and expected geometry figures.
Boundary geometry is kept separate from satellite, weather and crop-model configuration:
``processing_profiles`` is reserved and intentionally empty in Phase 1.

Every filesystem path is built through ``safe_join``: single plain components only, no traversal, no
absolute paths, and no symlinks/junctions anywhere below the private root.
"""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PRIVATE_DIR_ENV = "MANGOTWIN_PRIVATE_DIR"
SITES_SUBDIR = "sites"
SITE_ID_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,63}$")
FILE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")
SITE_FILE = "site.yaml"
SCHEMA_VERSION = 1
MAX_CONFIG_BYTES = 64 * 1024

_TOP_KEYS = {"schema_version", "site_id", "site_type", "reference_point", "comparison_points", "boundary",
             "processing_profiles"}
_BOUNDARY_KEYS = {"kml", "geojson", "report", "expected"}
_EXPECTED_KEYS = {"area_m2", "area_tolerance_pct", "perimeter_m", "perimeter_tolerance_pct"}


class SiteError(ValueError):
    """Site configuration problem (messages never include coordinates)."""


class SiteNotFound(SiteError):
    pass


class PrivatePathError(SiteError):
    """A path would escape the private directory, or the private directory is not safely excluded."""


# --- locations and path safety ----------------------------------------------------------------------------------

def private_root(override: "str | Path | None" = None) -> Path:
    """The private directory: explicit override, else $MANGOTWIN_PRIVATE_DIR, else <repo>/private."""
    chosen = override or os.environ.get(PRIVATE_DIR_ENV)
    return Path(chosen) if chosen else PROJECT_ROOT / "private"


def check_site_id(site_id: str) -> str:
    if not isinstance(site_id, str) or not SITE_ID_RE.match(site_id):
        raise SiteError("site_id must match ^[A-Z][A-Z0-9_]{2,63}$")
    return site_id


def _same(a: str, b: str) -> bool:
    return os.path.normcase(a) == os.path.normcase(b)


def safe_join(root: "str | Path", *parts: str) -> Path:
    """``root/part1/part2`` where every part is ONE plain name; nothing may be a symlink or junction."""
    root = Path(root)
    if root.is_symlink():
        raise PrivatePathError("the private directory must not be a symbolic link")
    base = Path(os.path.abspath(root))
    candidate = base
    for part in parts:
        if (not isinstance(part, str) or not part or part in (".", "..") or "/" in part or "\\" in part
                or ":" in part or Path(part).is_absolute() or Path(part).drive):
            raise PrivatePathError("path component is not a plain name")
        candidate = candidate / part
        if candidate.is_symlink() or (candidate.exists() and not _same(os.path.realpath(candidate), str(candidate))):
            raise PrivatePathError("symbolic links or junctions are not allowed inside the private directory")
    if candidate != base and not (candidate == base or base in candidate.parents):
        raise PrivatePathError("path escapes the private directory")
    return candidate


def _git_check_ignore(path: Path) -> bool | None:
    """True if git ignores ``path``, False if not, None if that cannot be determined."""
    try:
        rel = path.relative_to(PROJECT_ROOT.resolve())
    except ValueError:
        return None
    try:
        result = subprocess.run(["git", "-C", str(PROJECT_ROOT), "check-ignore", "-q", "--", rel.as_posix()],
                                capture_output=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    return {0: True, 1: False}.get(result.returncode)


def ensure_private_location(root: "str | Path", ignore_checker: Callable[[Path], "bool | None"] = _git_check_ignore) -> Path:
    """Refuse a private directory inside the repository unless Git is verified to ignore it."""
    root_abs = Path(os.path.realpath(root))
    inside = PROJECT_ROOT.resolve() in (root_abs, *root_abs.parents)
    if inside:
        verdict = ignore_checker(root_abs / "probe-file")
        if verdict is not True:
            raise PrivatePathError("the private directory is inside the repository but is not verified as "
                                   "ignored by Git; refusing to write private data there")
    return root_abs


def write_private_bytes(root: "str | Path", parts: tuple[str, ...], data: bytes) -> Path:
    """Atomically write ``data`` at ``root/<parts>`` (creating directories), refusing any escape."""
    target = safe_join(root, *parts)
    directory = target.parent
    base = Path(os.path.abspath(root))
    # create intermediate directories one validated component at a time
    cur = base
    cur.mkdir(parents=True, exist_ok=True)
    for part in parts[:-1]:
        cur = safe_join(cur, part)
        cur.mkdir(exist_ok=True)
    tmp = safe_join(directory, f".{target.name}.{os.getpid()}.tmp")
    try:
        with open(tmp, "xb") as fh:
            fh.write(data)
        os.replace(tmp, target)
    finally:
        if tmp.exists():
            tmp.unlink()
    return target


# --- site schema --------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Point:
    latitude: float
    longitude: float


@dataclass(frozen=True)
class ComparisonPoint:
    label: str
    point: Point
    expected: str                      # "inside" | "outside"


@dataclass(frozen=True)
class ExpectedGeometry:
    area_m2: float | None = None
    area_tolerance_pct: float = 0.05
    perimeter_m: float | None = None
    perimeter_tolerance_pct: float = 0.1


@dataclass(frozen=True)
class SiteConfig:
    site_id: str
    site_type: str
    reference_point: Point
    comparison_points: tuple[ComparisonPoint, ...]
    kml_name: str
    geojson_name: str
    report_name: str
    expected: ExpectedGeometry
    directory: Path = field(compare=False)
    processing_profiles: dict = field(default_factory=dict, compare=False)


def _number(value: Any, label: str, lo: float, hi: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not (lo <= float(value) <= hi):
        raise SiteError(f"{label} must be a number between {lo} and {hi}")
    return float(value)


def _point(value: Any, label: str) -> Point:
    if not isinstance(value, dict) or set(value) != {"latitude", "longitude"}:
        raise SiteError(f"{label} must contain exactly latitude and longitude")
    return Point(_number(value["latitude"], f"{label}.latitude", -90, 90),
                 _number(value["longitude"], f"{label}.longitude", -180, 180))


def _file_name(value: Any, label: str) -> str:
    if not isinstance(value, str) or not FILE_NAME_RE.match(value):
        raise SiteError(f"{label} must be a plain file name")
    return value


def parse_site_config(raw: Any, directory: Path) -> SiteConfig:
    if not isinstance(raw, dict):
        raise SiteError("site.yaml must be a mapping")
    unknown = set(raw) - _TOP_KEYS
    if unknown:
        raise SiteError("unknown top-level key(s): " + ", ".join(sorted(map(str, unknown))))
    if raw.get("schema_version") != SCHEMA_VERSION:
        raise SiteError(f"schema_version must be {SCHEMA_VERSION}")
    site_id = check_site_id(raw.get("site_id"))
    if site_id != directory.name:
        raise SiteError("site_id does not match its directory name")
    site_type = raw.get("site_type")
    if not isinstance(site_type, str) or not re.match(r"^[a-z][a-z0-9_]{2,40}$", site_type):
        raise SiteError("site_type must be a lowercase identifier")
    ref = _point(raw.get("reference_point"), "reference_point")

    comps = []
    for i, item in enumerate(raw.get("comparison_points") or []):
        if not isinstance(item, dict) or set(item) != {"label", "latitude", "longitude", "expected"}:
            raise SiteError(f"comparison_points[{i}] must contain label, latitude, longitude, expected")
        if item["expected"] not in ("inside", "outside"):
            raise SiteError(f"comparison_points[{i}].expected must be 'inside' or 'outside'")
        label = _file_name(item["label"], f"comparison_points[{i}].label")
        comps.append(ComparisonPoint(label, _point({"latitude": item["latitude"], "longitude": item["longitude"]},
                                                   f"comparison_points[{i}]"), item["expected"]))

    boundary = raw.get("boundary") or {}
    if not isinstance(boundary, dict) or set(boundary) - _BOUNDARY_KEYS:
        raise SiteError("boundary has missing or unknown keys")
    exp_raw = boundary.get("expected") or {}
    if not isinstance(exp_raw, dict) or set(exp_raw) - _EXPECTED_KEYS:
        raise SiteError("boundary.expected has unknown keys")
    expected = ExpectedGeometry(
        area_m2=None if "area_m2" not in exp_raw else _number(exp_raw["area_m2"], "expected.area_m2", 1, 1e9),
        area_tolerance_pct=_number(exp_raw.get("area_tolerance_pct", 0.05), "expected.area_tolerance_pct", 0, 100),
        perimeter_m=None if "perimeter_m" not in exp_raw else _number(exp_raw["perimeter_m"], "expected.perimeter_m", 1, 1e7),
        perimeter_tolerance_pct=_number(exp_raw.get("perimeter_tolerance_pct", 0.1), "expected.perimeter_tolerance_pct", 0, 100),
    )
    profiles = raw.get("processing_profiles") or {}
    if profiles:
        raise SiteError("processing_profiles is reserved and must be empty in Phase 1")
    return SiteConfig(
        site_id=site_id, site_type=site_type, reference_point=ref, comparison_points=tuple(comps),
        kml_name=_file_name(boundary.get("kml", "boundary.kml"), "boundary.kml"),
        geojson_name=_file_name(boundary.get("geojson", "boundary.geojson"), "boundary.geojson"),
        report_name=_file_name(boundary.get("report", "validation_report.json"), "boundary.report"),
        expected=expected, directory=directory)


# --- registry --------------------------------------------------------------------------------------------------------

def list_site_ids(root: "str | Path | None" = None) -> list[str]:
    """Registered private sites. Empty (never an error) when the private directory does not exist."""
    sites = Path(private_root(root)) / SITES_SUBDIR
    try:
        names = sorted(p.name for p in sites.iterdir() if p.is_dir() and not p.is_symlink()
                       and SITE_ID_RE.match(p.name) and (p / SITE_FILE).is_file())
    except OSError:
        return []
    return names


def load_site_config(site_id: str, root: "str | Path | None" = None) -> SiteConfig:
    check_site_id(site_id)
    base = private_root(root)
    directory = safe_join(base, SITES_SUBDIR, site_id)
    config_path = safe_join(base, SITES_SUBDIR, site_id, SITE_FILE)
    if not config_path.is_file():
        raise SiteNotFound(f"no private configuration for site {site_id}")
    if config_path.stat().st_size > MAX_CONFIG_BYTES:
        raise SiteError("site.yaml is larger than the safety limit")
    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, UnicodeDecodeError):
        raise SiteError("site.yaml is not valid YAML") from None
    return parse_site_config(raw, directory)
