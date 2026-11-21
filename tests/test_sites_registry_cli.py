"""Registry, private-path safety and the boundary conversion CLI (synthetic data only)."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
from pathlib import Path

import pytest
import yaml

from sites_fakes import LAT0, LON0, SITE_ID, graticule_area, kml, make_private, meridian_arc, square
from src.sites import registry as reg
from src.sites import validate_boundary as vb

REPO = Path(reg.PROJECT_ROOT)
SIDE = 0.002
EXPECTED_AREA = graticule_area(LON0, LON0 + SIDE, LAT0, LAT0 + SIDE)


def _perimeter():
    east_west = 0.0
    import math
    # parallel arc length (WGS84): N cos(phi) dlambda
    for lat in (LAT0, LAT0 + SIDE):
        s = math.sin(math.radians(lat))
        east_west += 6378137.0 / math.sqrt(1 - reg_e2() * s * s) * math.cos(math.radians(lat)) * math.radians(SIDE)
    return east_west + 2 * meridian_arc(LAT0, LAT0 + SIDE)


def reg_e2():
    return 0.00669437999014131705


def symlink_or_skip(link: Path, target: Path, directory: bool = False):
    try:
        os.symlink(target, link, target_is_directory=directory)
    except (OSError, NotImplementedError):
        pytest.skip("symbolic links are not available in this environment")


def ready(tmp_path, **kw):
    expected = kw.pop("expected", {"area_m2": EXPECTED_AREA, "perimeter_m": _perimeter(),
                                   "area_tolerance_pct": 0.01, "perimeter_tolerance_pct": 0.02})
    kw.setdefault("reference", (LON0 + SIDE / 2, LAT0 + SIDE / 2))
    return make_private(tmp_path, square(d=SIDE), expected=expected, **kw)


# --- public repository without private data ---------------------------------------------------------------------------

def test_registry_is_empty_and_not_an_error_when_private_is_absent(tmp_path, monkeypatch):
    missing = tmp_path / "nope"
    assert reg.list_site_ids(missing) == []
    with pytest.raises(reg.SiteNotFound):
        reg.load_site_config(SITE_ID, missing)
    monkeypatch.setenv(reg.PRIVATE_DIR_ENV, str(missing))
    assert reg.list_site_ids() == [] and reg.private_root() == missing


def test_default_private_root_is_inside_the_repository(monkeypatch):
    monkeypatch.delenv(reg.PRIVATE_DIR_ENV, raising=False)
    assert reg.private_root() == REPO / "private"


def test_cli_without_private_data_is_a_clean_usage_error(tmp_path, capsys):
    assert vb.main(["--site-id", SITE_ID, "--private-dir", str(tmp_path / "none")]) == 2
    assert "no private configuration" in capsys.readouterr().out


# --- site schema ------------------------------------------------------------------------------------------------------------------

def test_example_configuration_is_valid_synthetic_and_public():
    raw = yaml.safe_load((REPO / "configs" / "sites.example.yaml").read_text(encoding="utf-8"))
    site = reg.parse_site_config(raw, Path("EXAMPLE_ORCHARD_000"))
    assert abs(site.reference_point.latitude) < 1 and abs(site.reference_point.longitude) < 1
    assert site.processing_profiles == {} and site.comparison_points[0].expected == "outside"
    assert "SYNTHETIC" in (REPO / "configs" / "sites.example.yaml").read_text(encoding="utf-8")


@pytest.mark.parametrize("patch,fragment", [
    ({"surprise": 1}, "unknown top-level"),
    ({"schema_version": 2}, "schema_version"),
    ({"site_id": "WRONG_NAME_001"}, "does not match"),
    ({"site_id": "lower"}, "site_id"),
    ({"site_type": "Mango Orchard"}, "site_type"),
    ({"reference_point": {"latitude": 91.0, "longitude": 10.0}}, "reference_point.latitude"),
    ({"reference_point": {"latitude": 1.0}}, "exactly latitude and longitude"),
    ({"comparison_points": [{"label": "x", "latitude": 1, "longitude": 1, "expected": "near"}]}, "inside' or 'outside"),
    ({"boundary": {"geojson": "../escape.json"}}, "plain file name"),
    ({"boundary": {"kml": "/abs/path.kml"}}, "plain file name"),
    ({"boundary": {"kml": "sub/dir.kml"}}, "plain file name"),
    ({"boundary": {"unknown": 1}}, "boundary"),
    ({"processing_profiles": {"satellite": {"x": 1}}}, "reserved"),
])
def test_site_config_is_strict(tmp_path, patch, fragment):
    root = make_private(tmp_path)
    cfg = yaml.safe_load((root / "sites" / SITE_ID / "site.yaml").read_text())
    cfg.update(patch)
    (root / "sites" / SITE_ID / "site.yaml").write_text(yaml.safe_dump(cfg))
    with pytest.raises(reg.SiteError, match=fragment):
        reg.load_site_config(SITE_ID, root)


def test_site_config_errors_do_not_echo_coordinate_values(tmp_path):
    root = make_private(tmp_path)
    cfg = yaml.safe_load((root / "sites" / SITE_ID / "site.yaml").read_text())
    cfg["reference_point"] = {"latitude": 123.456789, "longitude": 10.0}
    (root / "sites" / SITE_ID / "site.yaml").write_text(yaml.safe_dump(cfg))
    with pytest.raises(reg.SiteError) as exc:
        reg.load_site_config(SITE_ID, root)
    assert "456789" not in str(exc.value)


@pytest.mark.parametrize("bad", ["../etc", "a/b", "lower_case", "AB", "X" * 65, "", "BAD ID", "..", "A\\B"])
def test_site_ids_cannot_traverse(bad):
    with pytest.raises(reg.SiteError):
        reg.check_site_id(bad)


def test_valid_config_loads(tmp_path):
    site = reg.load_site_config(SITE_ID, ready(tmp_path))
    assert site.site_id == SITE_ID and reg.list_site_ids(tmp_path / "private") == [SITE_ID]
    assert site.expected.area_m2 == pytest.approx(EXPECTED_AREA)


# --- path safety --------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("part", ["..", ".", "", "a/b", "a\\b", "/etc/passwd", "C:\\x", "C:", "x:y"])
def test_safe_join_rejects_traversal_and_non_plain_names(tmp_path, part):
    with pytest.raises(reg.PrivatePathError):
        reg.safe_join(tmp_path, "sites", part)


def test_safe_join_accepts_plain_names_inside_the_root(tmp_path):
    p = reg.safe_join(tmp_path, "sites", SITE_ID, "boundary.geojson")
    assert tmp_path.resolve() in [Path(os.path.realpath(p)), *Path(os.path.realpath(p)).parents]


def test_symlinked_directory_is_refused(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    root = tmp_path / "private"
    (root / "sites").mkdir(parents=True)
    symlink_or_skip(root / "sites" / SITE_ID, outside, directory=True)
    with pytest.raises(reg.PrivatePathError):
        reg.safe_join(root, "sites", SITE_ID, "boundary.geojson")
    with pytest.raises(reg.PrivatePathError):
        reg.write_private_bytes(root, ("sites", SITE_ID, "boundary.geojson"), b"x")
    assert list(outside.iterdir()) == []


def test_symlinked_output_file_is_refused_and_its_target_untouched(tmp_path):
    root = ready(tmp_path)
    victim = tmp_path / "victim.txt"
    victim.write_text("original")
    symlink_or_skip(root / "sites" / SITE_ID / "boundary.geojson", victim)
    (root / "sites" / SITE_ID / "boundary.kml").write_bytes(kml(square(d=SIDE)))
    code, report, lines = vb.run(SITE_ID, private_dir=root, ignore_checker=lambda p: True)
    assert code == 2 and any("symbolic" in l for l in lines)
    assert victim.read_text() == "original"


def test_symlinked_private_root_is_refused(tmp_path):
    real = ready(tmp_path)
    link = tmp_path / "linked_private"
    symlink_or_skip(link, real, directory=True)
    with pytest.raises(reg.PrivatePathError):
        reg.safe_join(link, "sites")


def test_private_directory_inside_the_repo_must_be_verified_as_ignored():
    root = REPO / "private_probe_dir"          # never created
    with pytest.raises(reg.PrivatePathError, match="not verified"):
        reg.ensure_private_location(root, ignore_checker=lambda p: False)
    with pytest.raises(reg.PrivatePathError, match="not verified"):
        reg.ensure_private_location(root, ignore_checker=lambda p: None)      # git unavailable: refuse
    assert reg.ensure_private_location(root, ignore_checker=lambda p: True)


def test_a_private_directory_outside_the_repo_needs_no_git_check(tmp_path):
    assert reg.ensure_private_location(tmp_path / "private", ignore_checker=lambda p: pytest.fail("not consulted"))


def test_the_default_private_location_is_really_git_ignored():
    for rel in ("private/sites/X/site.yaml", "private/sites/X/boundary.kml", "private/sites/X/boundary.geojson",
                "private/sites/X/validation_report.json"):
        result = subprocess.run(["git", "-C", str(REPO), "check-ignore", "-q", "--", rel])
        assert result.returncode == 0, rel


# --- the CLI end to end ------------------------------------------------------------------------------------------------------------

def test_cli_end_to_end_with_a_synthetic_orchard(tmp_path, capsys, caplog):
    caplog.set_level(logging.DEBUG)
    root = ready(tmp_path)
    fake_home = tmp_path / "synthetic_local_user_123"          # an invented OS user directory, never a real one
    downloads = fake_home / "Downloads"
    downloads.mkdir(parents=True)
    source = downloads / "Owner Family Orchard.kml"
    source.write_bytes(kml(square(d=SIDE)))
    code = vb.main(["--site-id", SITE_ID, "--kml", str(source), "--private-dir", str(root)])
    out = capsys.readouterr().out
    assert code == 0, out
    site_dir = root / "sites" / SITE_ID
    assert sorted(p.name for p in site_dir.iterdir()) == ["boundary.geojson", "boundary.kml", "site.yaml", "validation_report.json"]
    assert (site_dir / "boundary.kml").read_bytes() == source.read_bytes()                 # byte-for-byte original
    report = json.loads((site_dir / "validation_report.json").read_text())
    assert report["all_checks_passed"] and report["provenance"]["sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    names = {c["name"] for c in report["checks"]}
    assert {"polygon_structure", "area_matches_reference", "perimeter_matches_reference", "reference_point_inside",
            "comparison_point_original_study_point_outside"} <= names
    gj = json.loads((site_dir / "boundary.geojson").read_text())
    coords = gj["features"][0]["geometry"]["coordinates"][0]
    assert gj["features"][0]["geometry"]["type"] == "Polygon" and coords[0] == coords[-1] and len(coords) == 5
    assert report["geometry"]["area_m2"] == pytest.approx(EXPECTED_AREA, rel=1e-6)

    # privacy: nothing leaked to stdout, logs, the report, or the file system outside the private dir
    haystack = out + caplog.text + (site_dir / "validation_report.json").read_text()
    for needle in (str(LON0), "80.002", "20.002", "Owner", "Family", str(tmp_path),
                   "synthetic_local_user_123", "Downloads"):
        assert needle not in haystack, needle
    assert sorted(p.name for p in tmp_path.iterdir()) == ["private", "synthetic_local_user_123"]
    assert [p.name for p in downloads.iterdir()] == ["Owner Family Orchard.kml"]              # nothing written beside the source


def test_cli_reuses_an_already_imported_kml_and_is_idempotent(tmp_path, capsys):
    root = ready(tmp_path, write_kml=True)
    assert vb.main(["--site-id", SITE_ID, "--private-dir", str(root)]) == 0
    first = (root / "sites" / SITE_ID / "boundary.geojson").read_text()
    assert vb.main(["--site-id", SITE_ID, "--private-dir", str(root)]) == 0
    assert (root / "sites" / SITE_ID / "boundary.geojson").read_text() == first


def test_dry_run_writes_nothing(tmp_path, capsys):
    root = ready(tmp_path, write_kml=True)
    before = sorted(p.name for p in (root / "sites" / SITE_ID).iterdir())
    assert vb.main(["--site-id", SITE_ID, "--private-dir", str(root), "--dry-run"]) == 0
    assert sorted(p.name for p in (root / "sites" / SITE_ID).iterdir()) == before
    assert "nothing was written" in capsys.readouterr().out


def test_importing_a_different_kml_needs_force(tmp_path, capsys):
    root = ready(tmp_path, write_kml=True)
    other = tmp_path / "other.kml"
    other.write_bytes(kml(square(d=0.003)))
    assert vb.main(["--site-id", SITE_ID, "--private-dir", str(root), "--kml", str(other)]) == 2
    assert "--force" in capsys.readouterr().out
    assert vb.main(["--site-id", SITE_ID, "--private-dir", str(root), "--kml", str(other), "--force"]) == 1   # area no longer matches


@pytest.mark.parametrize("ring,fragment", [
    (square(d=0.003), "area_matches_reference"),
    ([(LON0, LAT0), (LON0 + SIDE, LAT0 + SIDE), (LON0 + SIDE, LAT0), (LON0, LAT0 + SIDE), (LON0, LAT0)], "polygon_structure"),
])
def test_failed_validation_exits_1_and_invalid_polygons_write_no_geojson(tmp_path, capsys, ring, fragment):
    root = ready(tmp_path)
    (root / "sites" / SITE_ID / "boundary.kml").write_bytes(kml(ring))
    code = vb.main(["--site-id", SITE_ID, "--private-dir", str(root)])
    out = capsys.readouterr().out
    assert code == 1 and f"[FAIL] {fragment}" in out
    assert (root / "sites" / SITE_ID / "boundary.geojson").exists() == (fragment != "polygon_structure")


def test_reference_point_outside_and_comparison_point_inside_fail(tmp_path, capsys):
    root = ready(tmp_path, reference=(LON0 + 0.05, LAT0 + 0.05), write_kml=True)
    assert vb.main(["--site-id", SITE_ID, "--private-dir", str(root), "--dry-run"]) == 1
    assert "[FAIL] reference_point_inside" in capsys.readouterr().out
    other = tmp_path / "second"
    other.mkdir()
    root2 = ready(other, comparison=[{"label": "wrongly_expected", "latitude": LAT0 + SIDE / 2,
                                      "longitude": LON0 + SIDE / 2, "expected": "outside"}], write_kml=True)
    assert vb.main(["--site-id", SITE_ID, "--private-dir", str(root2), "--dry-run"]) == 1


def test_swapped_latitude_longitude_kml_is_caught_by_the_reference_point_check(tmp_path, capsys):
    root = ready(tmp_path)
    swapped = [(lat, lon) for lon, lat in square(d=SIDE)]                 # lat/lon order mistake
    (root / "sites" / SITE_ID / "boundary.kml").write_bytes(kml(swapped))
    assert vb.main(["--site-id", SITE_ID, "--private-dir", str(root), "--dry-run"]) == 1
    assert "[FAIL] reference_point_inside" in capsys.readouterr().out


def test_missing_kml_is_a_usage_error_and_invalid_kml_a_validation_error(tmp_path, capsys):
    root = ready(tmp_path)
    assert vb.main(["--site-id", SITE_ID, "--private-dir", str(root)]) == 2
    (root / "sites" / SITE_ID / "boundary.kml").write_bytes(b"<kml><Document></Document></kml>")
    assert vb.main(["--site-id", SITE_ID, "--private-dir", str(root)]) == 1
    assert not (root / "sites" / SITE_ID / "boundary.geojson").exists()


def test_cli_refuses_a_private_directory_inside_the_repo_that_is_not_ignored(monkeypatch):
    monkeypatch.setattr(reg, "_git_check_ignore", lambda p: False)
    code, _, lines = vb.run(SITE_ID, private_dir=REPO / "not_ignored_private_dir",
                            ignore_checker=lambda p: False)
    assert code == 2 and "not verified" in " ".join(lines)
    assert not (REPO / "not_ignored_private_dir").exists()


def test_outputs_cannot_be_redirected_by_configuration(tmp_path):
    root = ready(tmp_path, write_kml=True)
    cfg = yaml.safe_load((root / "sites" / SITE_ID / "site.yaml").read_text())
    cfg["boundary"]["geojson"] = "..\\..\\..\\escape.geojson"
    (root / "sites" / SITE_ID / "site.yaml").write_text(yaml.safe_dump(cfg))
    code, _, lines = vb.run(SITE_ID, private_dir=root, ignore_checker=lambda p: True)
    assert code == 2 and not (tmp_path / "escape.geojson").exists() and not (root.parent / "escape.geojson").exists()
