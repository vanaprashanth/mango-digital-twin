"""Privacy and isolation guarantees for the research-site tools.

Exclusions are evaluated with Git's own gitignore engine in a scratch repository holding EMPTY placeholder
files (nothing real is read or copied). Docker contexts and gcloud uploads use gitignore-style rules.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

import pytest

from src.utils.config import PROJECT_ROOT, get_config

REPO = Path(PROJECT_ROOT)
PRIVATE_PROBES = [
    "private/sites/MANGO_ORCHARD_001/site.yaml",
    "private/sites/MANGO_ORCHARD_001/boundary.kml",
    "private/sites/MANGO_ORCHARD_001/boundary.geojson",
    "private/sites/MANGO_ORCHARD_001/validation_report.json",
    "private/anything.txt",
]
KML_PROBES = ["boundary.kml", "configs/orchard.kml", "docs/site.KML".lower()]
PUBLIC_GEOJSON_PROBES = ["configs/india_boundary.geojson", "docs/public_map.geojson", "data/processed/example.geojson"]


def _ignored_by(rules_file: Path, probes: list[str], tmp_path: Path) -> dict[str, bool]:
    """For each probe path: would a gitignore-style engine exclude it under ``rules_file``?"""
    repo = tmp_path / "scratch"
    repo.mkdir()
    for rel in probes:
        target = repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.touch()
    (repo / ".gitignore").write_text(rules_file.read_text(encoding="utf-8"), encoding="utf-8")
    env = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull}
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, env=env)
    out = subprocess.run(["git", "-c", "core.excludesFile=", "ls-files", "--others", "--exclude-standard", "-z"],
                         cwd=repo, check=True, capture_output=True, text=True, env=env).stdout
    visible = {p for p in out.split("\0") if p}
    return {rel: rel not in visible for rel in probes}


# --- Git ---------------------------------------------------------------------------------------------------------------------------

def test_private_data_is_ignored_by_git(tmp_path):
    result = _ignored_by(REPO / ".gitignore", PRIVATE_PROBES + KML_PROBES, tmp_path)
    assert all(result.values()), [k for k, v in result.items() if not v]


def test_git_exclusion_is_targeted_and_does_not_block_public_geojson(tmp_path):
    result = _ignored_by(REPO / ".gitignore", PUBLIC_GEOJSON_PROBES, tmp_path)
    assert not any(result.values()), [k for k, v in result.items() if v]


def test_nothing_private_or_kml_is_tracked():
    tracked = subprocess.run(["git", "-C", str(REPO), "ls-files"], capture_output=True, text=True, check=True).stdout.split("\n")
    assert not [t for t in tracked if t.startswith("private/") or t.lower().endswith(".kml")]


# --- Docker build contexts -----------------------------------------------------------------------------------------------------

def test_dockerignore_excludes_private_data_and_never_negates_it(tmp_path):
    result = _ignored_by(REPO / ".dockerignore", PRIVATE_PROBES + KML_PROBES + ["src/private/x.yaml"], tmp_path)
    assert all(result.values()), [k for k, v in result.items() if not v]
    lines = [l.strip() for l in (REPO / ".dockerignore").read_text(encoding="utf-8").splitlines()]
    assert "private/" in lines and "**/private/" in lines
    assert not [l for l in lines if l.startswith("!") and "private" in l]


def test_dashboard_dockerfile_copies_the_whole_context_so_the_ignore_rule_is_what_protects_private():
    text = (REPO / "Dockerfile").read_text(encoding="utf-8")
    assert "COPY . ." in text                               # hence .dockerignore must (and does) exclude private/


def test_pipeline_dockerfile_copies_only_explicit_directories():
    copies = [l.split()[1:] for l in (REPO / "Dockerfile.pipeline").read_text(encoding="utf-8").splitlines()
              if l.strip().startswith("COPY ")]
    assert copies and all(src[0] not in (".", "./", "private") for src in copies)


# --- GCP upload contexts ---------------------------------------------------------------------------------------------------------

def test_gcloudignore_never_uploads_private_data():
    from test_cloud_build_config import _uploaded_set
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        uploaded = _uploaded_set(Path(tmp), PRIVATE_PROBES + KML_PROBES + ["src/private/x.yaml", "configs/private/y.yaml"])
    assert not [p for p in uploaded if p.startswith("private/") or "/private/" in p or p.lower().endswith(".kml")], uploaded
    assert "src/sites/geometry.py" in uploaded              # the (public) code is allowed, the data is not


def test_gcloudignore_has_explicit_private_rules_after_the_allow_list():
    lines = [l.strip() for l in (REPO / ".gcloudignore").read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    for rule in ("private/", "**/private/", "*.kml"):
        assert rule in lines
    assert lines.index("private/") > lines.index("!/src/")


# --- isolation from production ----------------------------------------------------------------------------------------------------

def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
            found |= {f"{node.module}.{a.name}" for a in node.names}
    return found


# Private research tools that are allowed to build on the site registry. Nothing in production may import them.
SANCTIONED_RESEARCH_CONSUMERS = {"src/isro/orchard_ndvi.py"}


def test_no_production_code_imports_the_sites_package():
    offenders = []
    for base in ("app", "src", "scripts"):
        for f in (REPO / base).rglob("*.py"):
            if "src/sites" in f.as_posix() or "__pycache__" in f.parts:
                continue
            if f.relative_to(REPO).as_posix() in SANCTIONED_RESEARCH_CONSUMERS:
                continue
            if any(m == "src.sites" or m.startswith("src.sites.") for m in _imports(f)):
                offenders.append(f.relative_to(REPO).as_posix())
    main = REPO / "main.py"
    if any(m.startswith("src.sites") for m in _imports(main)):
        offenders.append("main.py")
    assert offenders == []
    for wf in (REPO / ".github" / "workflows").glob("*.yml"):
        assert "src.sites" not in wf.read_text(encoding="utf-8")


def test_sites_package_depends_only_on_the_standard_library_pyyaml_and_itself():
    allowed_third_party = {"yaml"}
    stdlib = set(sys.stdlib_module_names)
    for f in (REPO / "src" / "sites").glob("*.py"):
        for module in _imports(f):
            top = module.split(".")[0]
            assert top in stdlib or top in allowed_third_party or module.startswith("src.sites") or module == "src", (f.name, module)


def test_importing_the_sites_package_does_not_pull_in_production_modules():
    code = ("import sys; import src.sites.registry, src.sites.geometry, src.sites.kml, src.sites.validate_boundary; "
            "bad=[m for m in sys.modules if m in ('src.utils.config','src.pipeline','src.cloud','streamlit','src.ml')]; "
            "print(bad); sys.exit(1 if bad else 0)")
    result = subprocess.run([sys.executable, "-c", code], cwd=REPO, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_production_location_and_output_paths_are_unchanged():
    cfg = get_config()
    assert (cfg.latitude, cfg.longitude) == (13.294219, 78.624294)
    assert (cfg.remote_sensing["latitude"], cfg.remote_sensing["longitude"]) == (13.294219, 78.624294)
    assert cfg.path("historical_risk_csv") == REPO / "data" / "processed" / "muthukur_weather_risk_scores.csv"
    assert cfg.path("sentinel2_timeseries_csv") == REPO / "data" / "processed" / "muthukur_sentinel2_index_timeseries.csv"
    text = (REPO / "configs" / "config.yaml").read_text(encoding="utf-8").lower()
    assert "orchard_001" not in text and "sites" not in text.split("paths:")[0]


def test_example_config_coordinates_are_synthetic_and_far_from_any_real_site():
    import math
    import yaml
    raw = yaml.safe_load((REPO / "configs" / "sites.example.yaml").read_text(encoding="utf-8"))
    cfg = get_config()
    for point in [raw["reference_point"], *raw["comparison_points"]]:
        assert abs(point["latitude"] - cfg.latitude) > 10 and abs(point["longitude"] - cfg.longitude) > 70
        assert math.hypot(point["latitude"], point["longitude"]) < 1


def test_public_files_do_not_contain_the_private_reference_coordinates():
    """Runs only on a machine that has the private site file; compares by value, never printing it."""
    from src.sites import registry as reg
    ids = reg.list_site_ids()
    if not ids:
        pytest.skip("no private site data on this machine")
    needles = []
    for site_id in ids:
        site = reg.load_site_config(site_id)
        needles += [f"{site.reference_point.latitude:.4f}", f"{site.reference_point.longitude:.4f}"]
    tracked = subprocess.run(["git", "-C", str(REPO), "ls-files"], capture_output=True, text=True, check=True).stdout.split("\n")
    leaks = []
    for rel in tracked:
        path = REPO / rel
        if not rel or path.suffix.lower() in {".png", ".jpg", ".jpeg", ".zip", ".joblib", ".pkl", ".ico", ".pyc"} or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if any(n in text for n in needles):
            leaks.append(rel)
    assert leaks == [], f"private coordinates found in tracked files: {leaks}"
