"""
Private boundary conversion CLI: KML -> validated GeoJSON + validation report, inside ``private/`` only.

    python -m src.sites.validate_boundary --site-id MANGO_ORCHARD_001 [--kml PATH] [--dry-run] [--force]

Reads ``private/sites/<SITE_ID>/site.yaml`` (reference point, comparison points and expected figures live
THERE, so private coordinates never appear on a command line or in shell history). ``--kml`` imports a KML
once: it is copied byte-for-byte to ``boundary.kml`` in the private directory (its original name and
location are not recorded or printed).

Outputs (all inside the private directory, written atomically, never through symlinks):
    boundary.kml, boundary.geojson, validation_report.json

Nothing prints or logs coordinates, owner details, personal paths or KML contents. Exit status: 0 = every
check passed, 1 = validation failed, 2 = usage or configuration problem.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from src.sites import SITES_TOOL_VERSION
from src.sites.geometry import SQUARE_METRES_PER_ACRE, locate_point, validate_ring
from src.sites.kml import MAX_KML_BYTES, KmlError, parse_kml_polygon
from src.sites.registry import (
    PROJECT_ROOT,
    SITES_SUBDIR,
    PrivatePathError,
    SiteConfig,
    SiteError,
    ensure_private_location,
    load_site_config,
    private_root,
    safe_join,
    write_private_bytes,
)

log = logging.getLogger("mangotwin.sites")

AREA_METHOD = "WGS84 ellipsoidal Lambert azimuthal equal-area projection + shoelace (area-preserving)"
PERIMETER_METHOD = "WGS84 geodesic edge lengths (Vincenty inverse), summed"


def _deviation_pct(measured: float, expected: float) -> float:
    return abs(measured - expected) / expected * 100.0


def _display(root: Path, *parts: str) -> str:
    """Repository-relative display path (never an absolute/personal path)."""
    full = Path(root).joinpath(*parts)
    try:
        return full.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return "/".join(("<private-dir>", *parts))


def build_geojson(site_id: str, ring) -> dict:
    return {
        "type": "FeatureCollection",
        "name": site_id,
        "features": [{
            "type": "Feature",
            "properties": {"site_id": site_id, "crs": "EPSG:4326"},
            "geometry": {"type": "Polygon", "coordinates": [[[lon, lat] for lon, lat in ring]]},
        }],
    }


def evaluate(site: SiteConfig, kml_bytes: bytes) -> tuple[dict, dict | None]:
    """Validate KML bytes against a site config. Returns (report, geojson-or-None). No file access."""
    report: dict = {
        "schema_version": 1,
        "site_id": site.site_id,
        "tool_version": SITES_TOOL_VERSION,
        "validated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "provenance": {
            "source_type": "Google Earth KML",
            "sha256": hashlib.sha256(kml_bytes).hexdigest(),
            "bytes": len(kml_bytes),
        },
        "crs": {"geometry": "EPSG:4326 (WGS84)", "kml_axis_order": "longitude,latitude[,altitude]"},
        "methods": {"area": AREA_METHOD, "perimeter": PERIMETER_METHOD},
        "geometry": {"valid": False, "errors": [], "warnings": []},
        "checks": [],
        "all_checks_passed": False,
        "privacy": "Contains no coordinates. Keep with the private site data.",
    }

    def check(name: str, passed: bool, detail: str) -> None:
        report["checks"].append({"name": name, "passed": bool(passed), "detail": detail})

    try:
        parsed = parse_kml_polygon(kml_bytes)
    except KmlError as exc:
        report["geometry"]["errors"].append(f"kml: {exc}")
        check("kml_parsed", False, str(exc))
        return report, None
    check("kml_parsed", True, "exactly one polygon outer ring read")
    report["provenance"]["point_placemarks_ignored"] = parsed.point_placemarks
    if parsed.altitude_present:
        report["geometry"]["warnings"].append("altitude_values_ignored")

    ring_report = validate_ring(parsed.ring)
    g = report["geometry"]
    g["valid"], g["errors"] = ring_report.valid, list(ring_report.errors)
    g["warnings"] += ring_report.warnings
    g["vertex_count"] = ring_report.vertex_count
    check("polygon_structure", ring_report.valid,
          "closed, non-self-intersecting, non-degenerate" if ring_report.valid else ", ".join(ring_report.errors))
    if not ring_report.valid:
        return report, None

    g.update({
        "orientation_input": ring_report.orientation_input, "orientation_output": "counter-clockwise",
        "area_m2": round(ring_report.area_m2, 4), "area_hectares": round(ring_report.area_ha, 6),
        "area_acres": round(ring_report.area_m2 / SQUARE_METRES_PER_ACRE, 6),
        "perimeter_m": round(ring_report.perimeter_m, 4), "extent_m": round(ring_report.extent_m, 2),
    })

    exp = site.expected
    if exp.area_m2 is not None:
        dev = _deviation_pct(ring_report.area_m2, exp.area_m2)
        check("area_matches_reference", dev <= exp.area_tolerance_pct,
              f"measured {ring_report.area_m2:.2f} m2 vs reference {exp.area_m2:.2f} m2 "
              f"({dev:.4f}% deviation, tolerance {exp.area_tolerance_pct}%)")
    if exp.perimeter_m is not None:
        dev = _deviation_pct(ring_report.perimeter_m, exp.perimeter_m)
        check("perimeter_matches_reference", dev <= exp.perimeter_tolerance_pct,
              f"measured {ring_report.perimeter_m:.2f} m vs reference {exp.perimeter_m:.2f} m "
              f"({dev:.4f}% deviation, tolerance {exp.perimeter_tolerance_pct}%)")

    ring = ring_report.normalized_ring
    ref = site.reference_point
    where = locate_point(ref.longitude, ref.latitude, ring)
    check("reference_point_inside", where == "inside", f"reference point is {where}")
    for comp in site.comparison_points:
        where = locate_point(comp.point.longitude, comp.point.latitude, ring)
        check(f"comparison_point_{comp.label}_{comp.expected}", where == comp.expected,
              f"point '{comp.label}' is {where} (expected {comp.expected})")

    report["all_checks_passed"] = all(c["passed"] for c in report["checks"])
    return report, build_geojson(site.site_id, ring)


def run(site_id: str, *, private_dir=None, kml_source=None, dry_run: bool = False, force: bool = False,
        ignore_checker=None) -> tuple[int, dict | None, list[str]]:
    """Library entry point. Returns (exit_code, report, message lines)."""
    lines: list[str] = []
    try:
        kwargs = {} if ignore_checker is None else {"ignore_checker": ignore_checker}
        root = ensure_private_location(private_root(private_dir), **kwargs)
        site = load_site_config(site_id, root)
        kml_path = safe_join(root, SITES_SUBDIR, site.site_id, site.kml_name)
        if kml_source is not None:
            data = Path(kml_source).read_bytes() if Path(kml_source).is_file() else None
            if data is None:
                raise SiteError("the --kml file was not found")
            if len(data) > MAX_KML_BYTES:
                raise SiteError("the --kml file is larger than the 2 MiB safety limit")
            if kml_path.exists() and kml_path.read_bytes() != data and not force:
                raise SiteError("boundary.kml already exists with different content; use --force to replace it")
        else:
            if not kml_path.is_file():
                raise SiteError("boundary.kml is not in the private site directory; import one with --kml")
            data = kml_path.read_bytes()
    except (SiteError, PrivatePathError, OSError) as exc:
        return 2, None, [f"error: {exc}" if not isinstance(exc, OSError) else "error: could not read a private file"]

    report, geojson = evaluate(site, data)
    lines.append(f"site {site.site_id}: vertices={report['geometry'].get('vertex_count', 'n/a')}, "
                 f"valid={report['geometry']['valid']}")
    for c in report["checks"]:
        lines.append(f"  [{'PASS' if c['passed'] else 'FAIL'}] {c['name']}: {c['detail']}")
    g = report["geometry"]
    if g.get("area_m2") is not None:
        lines.append(f"  area {g['area_m2']:.2f} m2 ({g['area_hectares']:.4f} ha, {g['area_acres']:.3f} acres); "
                     f"perimeter {g['perimeter_m']:.2f} m")

    if dry_run:
        lines.append("dry run: nothing was written")
    elif geojson is not None:
        try:
            if kml_source is not None:
                write_private_bytes(root, (SITES_SUBDIR, site.site_id, site.kml_name), data)
            write_private_bytes(root, (SITES_SUBDIR, site.site_id, site.geojson_name),
                                (json.dumps(geojson, indent=2) + "\n").encode("utf-8"))
            write_private_bytes(root, (SITES_SUBDIR, site.site_id, site.report_name),
                                (json.dumps(report, indent=2) + "\n").encode("utf-8"))
        except (PrivatePathError, OSError) as exc:
            return 2, report, lines + [f"error: {exc}" if isinstance(exc, PrivatePathError) else "error: could not write a private file"]
        lines.append(f"wrote {_display(root, SITES_SUBDIR, site.site_id, site.geojson_name)} and "
                     f"{site.report_name} (private; do not commit)")
    else:
        lines.append("no GeoJSON written because the polygon is not valid")
    return (0 if report["all_checks_passed"] else 1), report, lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a private orchard boundary and convert it to GeoJSON.")
    parser.add_argument("--site-id", required=True)
    parser.add_argument("--kml", help="import this KML into the private site directory (copied, not moved)")
    parser.add_argument("--private-dir", help="override the private directory (default: <repo>/private)")
    parser.add_argument("--dry-run", action="store_true", help="validate only; write nothing")
    parser.add_argument("--force", action="store_true", help="replace an existing boundary.kml with different content")
    args = parser.parse_args(argv)
    code, _, lines = run(args.site_id, private_dir=args.private_dir, kml_source=args.kml,
                         dry_run=args.dry_run, force=args.force)
    print("\n".join(lines))
    return code


if __name__ == "__main__":
    sys.exit(main())
