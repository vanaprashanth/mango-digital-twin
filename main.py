"""
Convenience entry point. Delegates to the pipeline runner.

    python main.py                                -> full pipeline (fetch weather + soil + run risk engines)
    python main.py --skip-fetch                   -> recompute risk scores from cached raw data only
    python main.py --skip-soil-fetch              -> fetch weather, reuse cached soil CSV, run risk engines
                                                     (recommended for automated daily refresh to avoid
                                                     transient SoilGrids API timeouts)
    python main.py --refresh-sentinel2            -> full pipeline + refresh Sentinel-2 vegetation index
                                                     time series from Google Earth Engine before running
                                                     downstream freshness-aware steps.
                                                     Skips gracefully if GEE credentials are unavailable.
    python main.py --skip-soil-fetch \
                   --refresh-sentinel2            -> recommended for GitHub Actions daily refresh:
                                                     skip slow SoilGrids API, refresh Sentinel-2 if
                                                     GEE_SERVICE_ACCOUNT_KEY secret is configured.
"""

from src.pipeline.run_pipeline import main as run_pipeline_main

if __name__ == "__main__":
    run_pipeline_main()
