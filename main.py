"""
Convenience entry point. Delegates to the pipeline runner.

    python main.py                   -> full pipeline (fetch weather + soil + run risk engines)
    python main.py --skip-fetch      -> recompute risk scores from cached raw data only
    python main.py --skip-soil-fetch -> fetch weather, reuse cached soil CSV, run risk engines
                                        (recommended for automated daily refresh to avoid
                                        transient SoilGrids API timeouts)
"""

from src.pipeline.run_pipeline import main as run_pipeline_main

if __name__ == "__main__":
    run_pipeline_main()
