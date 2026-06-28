"""
Convenience entry point. Delegates to the pipeline runner.

    python main.py                 -> runs the full pipeline (fetch + risk engines)
    python main.py --skip-fetch    -> recompute risk scores from cached raw data only
"""

from src.pipeline.run_pipeline import main as run_pipeline_main

if __name__ == "__main__":
    run_pipeline_main()
