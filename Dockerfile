# ── Sensor-Free Mango Digital Twin — Streamlit dashboard image ─────────────
#
# Build:
#   docker build -t mango-digital-twin .
#
# Run (dashboard only — uses the committed sample data):
#   docker run --rm -p 8501:8501 mango-digital-twin
#   Then open http://localhost:8501 in a browser.
#
# Refresh data inside a running container (or one-off):
#   docker run --rm mango-digital-twin python main.py --skip-fetch
#
# Notes:
#   - The container ships with the committed sample CSVs in data/.
#     The dashboard is fully browsable without a live data fetch.
#   - Data is NOT automatically refreshed when the container starts.
#     Run `python main.py` to pull fresh weather + satellite data.
#   - Google Earth Engine authentication requires `earthengine authenticate`
#     and is not performed inside this image (Sentinel-2 pages will show
#     cached data or a "file not found" message without a live GEE session).

FROM python:3.11-slim

# Keeps Python from buffering stdout/stderr (useful for container logs)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# ── Install dependencies ────────────────────────────────────────────────────
# Copy only requirements first so Docker can cache this layer independently
# of the source code.  Rebuilds are fast when only source files change.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy project ────────────────────────────────────────────────────────────
# .dockerignore excludes .git, __pycache__, .venv, logs/*.log, secrets, etc.
COPY . .

# ── Streamlit port ──────────────────────────────────────────────────────────
EXPOSE 8501

# ── Health check ────────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" \
    || exit 1

# ── Start dashboard ─────────────────────────────────────────────────────────
CMD ["streamlit", "run", "app/streamlit_app.py", \
     "--server.address=0.0.0.0", \
     "--server.port=8501", \
     "--server.headless=true"]
