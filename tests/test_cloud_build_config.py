"""Static validation of the Cloud Build source-upload rules and build config.

Nothing here talks to GCP or Docker. The upload set is computed with Git's own
gitignore engine (gcloud uses gitignore syntax for .gcloudignore) in a scratch
repository that holds EMPTY placeholder files, so no real file contents, and in
particular no credential contents, are ever read or copied.
"""

from __future__ import annotations

import fnmatch
import os
import re
import subprocess
from pathlib import Path

import pytest
import yaml

from src.utils.config import PROJECT_ROOT

REPO = Path(PROJECT_ROOT)
IMAGE = "us-east1-docker.pkg.dev/mango-digital-twin-vsp/mangotwin-containers/mangotwin-pipeline"
PRUNE = {".git", ".venv"}  # huge; covered by synthetic probes below

# Names that must never be uploaded (placeholders only; contents never read).
CREDENTIAL_PROBES = [
    "elite-list-421616-d961dc95aa2f.json", "credentials.json", "gcp-service-account.json",
    "my_service_account.json", "deploy-key.json", "id_rsa", "server.pem", "cert.p12", "tls.key",
    ".env", ".env.local", "prod.env", ".netrc", ".streamlit/secrets.toml", "secrets.toml",
    "configs/service-account.json", "configs/credentials.json", "src/secrets.json",
    "src/cloud/.env", "src/cloud/key.pem", ".config/gcloud/application_default_credentials.json",
    ".aws/credentials", ".ssh/id_ed25519",
]
OTHER_EXCLUDED_PROBES = [
    ".git/config", ".git/objects/ab/cdef", ".venv/Lib/site-packages/x.py", "venv/bin/python",
    "data/raw/muthukur_soilgrids.csv", "data/manual/muthukur_irrigation_events.csv",
    "data/processed/muthukur_ml_model_metrics.json", "models/irrigation_priority_model.joblib",
    "src/models/m.pkl", "src/data/x.csv", "configs/data.csv", "logs/pipeline.log",
    "app/streamlit_app.py", "tests/test_x.py", "docs/x.md", "notebooks/n.ipynb", "scripts/s.py",
    ".github/workflows/daily-data-refresh.yml", "Dockerfile", "requirements.txt", "README.md",
    "ml-evaluation-43652374481.zip", "some_new_root_file.txt", "src/__pycache__/x.cpython-312.pyc",
    ".pytest_cache/v/cache/lastfailed", "Dockerfile.pipeline.bak", "cloudbuild.pipeline.yaml",
]


def _uploaded_set(tmp_path: Path, extra_paths) -> set[str]:
    """Paths a gitignore-style engine would NOT exclude, given .gcloudignore."""
    repo = tmp_path / "scratch_repo"
    repo.mkdir()
    paths = set(extra_paths)
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in PRUNE]
        rel_root = Path(root).relative_to(REPO)
        for name in files:
            paths.add((rel_root / name).as_posix())
    for rel in paths:
        target = repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.touch()  # empty placeholder; real contents are never read
    (repo / ".gitignore").write_text((REPO / ".gcloudignore").read_text(encoding="utf-8"), encoding="utf-8")
    env = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull}
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, env=env)
    out = subprocess.run(
        ["git", "-c", "core.excludesFile=", "ls-files", "--others", "--exclude-standard", "-z"],
        cwd=repo, check=True, capture_output=True, text=True, env=env,
    ).stdout
    listed = {p for p in out.split("\0") if p}
    listed.discard(".gitignore")  # scratch artefact of this test, not a repo file
    return listed


@pytest.fixture(scope="module")
def uploaded(tmp_path_factory):
    return _uploaded_set(tmp_path_factory.mktemp("gcloudignore"), CREDENTIAL_PROBES + OTHER_EXCLUDED_PROBES)


# --- .gcloudignore -------------------------------------------------------------

def test_gcloudignore_exists_and_is_default_deny():
    lines = [l.strip() for l in (REPO / ".gcloudignore").read_text(encoding="utf-8").splitlines()]
    assert "/*" in lines
    for needed in ("!/Dockerfile.pipeline", "!/requirements-cloud.txt", "!/main.py", "!/configs/", "!/src/"):
        assert needed in lines


@pytest.mark.parametrize("path", CREDENTIAL_PROBES)
def test_credential_style_files_are_never_uploaded(uploaded, path):
    assert path not in uploaded, path


@pytest.mark.parametrize("path", OTHER_EXCLUDED_PROBES)
def test_git_venv_data_models_and_other_files_are_not_uploaded(uploaded, path):
    assert path not in uploaded, path


def test_real_credential_json_in_repo_root_is_excluded_without_reading_it(uploaded):
    root_jsons = [p.name for p in REPO.glob("*.json")]
    for name in root_jsons:
        assert name not in uploaded, name
    # and independent of its name: no .json file of any kind is in the upload set
    assert not [p for p in uploaded if p.lower().endswith(".json")]


def test_upload_set_contains_exactly_the_sources_dockerfile_pipeline_needs(uploaded):
    for required in ("Dockerfile.pipeline", "requirements-cloud.txt", "main.py", "configs/config.yaml",
                     "src/cloud/run_pipeline_job.py", "src/pipeline/run_pipeline.py", "src/utils/config.py"):
        assert required in uploaded, required
    allowed_exact = {"Dockerfile.pipeline", "requirements-cloud.txt", "main.py", ".dockerignore"}
    stray = [p for p in uploaded
             if p not in allowed_exact and not p.startswith("configs/") and not (p.startswith("src/") and p.endswith((".py", ".yaml", ".yml", ".txt", ".md")))]
    assert not stray, stray
    assert not [p for p in uploaded if p.startswith(("data/", "models/", "logs/", ".git/", ".venv/", "tests/", "app/"))]


def test_every_dockerfile_pipeline_copy_source_is_uploaded(uploaded):
    copies = [l.split()[1] for l in (REPO / "Dockerfile.pipeline").read_text(encoding="utf-8").splitlines()
              if l.startswith("COPY ")]
    assert copies
    for src in copies:
        assert (REPO / src).exists(), src
        assert any(p == src or p.startswith(src.rstrip("/") + "/") for p in uploaded), f"{src} not uploaded"


def test_upload_set_has_no_generated_or_cache_files(uploaded):
    banned = ("*.pyc", "*.csv", "*.joblib", "*.pkl", "*.log", "*.zip", "*.json", "*.pem", "*.key")
    for p in uploaded:
        assert not any(fnmatch.fnmatch(p.rsplit("/", 1)[-1], b) for b in banned), p
        assert "__pycache__" not in p


# --- cloudbuild.pipeline.yaml ----------------------------------------------------

@pytest.fixture(scope="module")
def build():
    return yaml.safe_load((REPO / "cloudbuild.pipeline.yaml").read_text(encoding="utf-8"))


def test_builds_with_dockerfile_pipeline(build):
    step = build["steps"][0]
    assert step["name"] == "gcr.io/cloud-builders/docker"
    args = step["args"]
    assert args[0] == "build" and args[args.index("-f") + 1] == "Dockerfile.pipeline"
    assert args[-1] == "."
    assert not any("--build-arg" == a or "--no-cache" == a for a in args)


def test_pushes_to_expected_artifact_registry_image(build):
    assert build["images"] == [f"{IMAGE}:$BUILD_ID"]
    tag_args = [a for a in build["steps"][0]["args"] if a.startswith(IMAGE)]
    assert tag_args == [f"{IMAGE}:$BUILD_ID"]
    assert ":latest" not in (REPO / "cloudbuild.pipeline.yaml").read_text(encoding="utf-8").replace("mutable \"latest\"", "")


def test_build_config_has_no_secrets_iam_or_deploy_actions(build):
    raw = (REPO / "cloudbuild.pipeline.yaml").read_text(encoding="utf-8")
    text = "\n".join(l for l in raw.splitlines() if not l.lstrip().startswith("#"))  # code, not comments
    assert not re.search(r"(?i)private_key|BEGIN [A-Z ]*KEY|(?<!\*)\.json|secretEnv|availableSecrets|serviceAccount|"
                         r"add-iam|set-iam|gcloud run|deploy|auth activate|GOOGLE_APPLICATION_CREDENTIALS", text)
    assert "serviceAccount" not in build and "availableSecrets" not in build


def test_image_verification_step_never_starts_the_pipeline(build):
    step = next(s for s in build["steps"] if s["id"] == "verify-image-contents")
    script = step["args"][-1]
    runs = [l for l in script.splitlines() if "docker run" in l]
    assert runs and all("--entrypoint" in l for l in runs)
    assert "run_pipeline_job" not in script and "main.py" not in script
    assert "set -euo pipefail" in script and "exit 1" in script
    for pattern in ("*.json", ".env*", "*.pem", "*.joblib", "/app/data"):
        assert pattern in script


def test_build_is_bounded_and_logging_does_not_need_extra_bucket(build):
    assert build["timeout"].endswith("s") and int(build["timeout"][:-1]) <= 3600
    assert build["options"]["logging"] == "CLOUD_LOGGING_ONLY"


def test_uses_python_312_base_in_pipeline_dockerfile():
    assert "FROM python:3.12" in (REPO / "Dockerfile.pipeline").read_text(encoding="utf-8")
