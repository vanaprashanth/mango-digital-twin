"""
Research-site registry and orchard-boundary tools (PHASE 1, ISOLATED).

This package is deliberately NOT imported by the production pipeline, the dashboard, the Cloud Run job
or any workflow. It depends only on the standard library and PyYAML. It never changes
``Config.latitude/longitude``, the remote-sensing coordinates, or any dataset output path.

Private site data (boundary KML/GeoJSON, site configuration, validation report) lives under
``private/sites/<SITE_ID>/`` in the repository root (or ``$MANGOTWIN_PRIVATE_DIR``). That directory is
excluded from Git, Docker build contexts and GCP upload contexts, and the public repository works
normally when it is absent.
"""

SITES_TOOL_VERSION = "1"
