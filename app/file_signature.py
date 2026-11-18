"""
Cache-key helper for the dashboard's file-backed ``st.cache_data`` loaders.

``st.cache_data`` keys a result by the function's arguments, so a loader taking only a path keeps
serving the DataFrame it first read for as long as the server process lives, even after the CSV on
disk is replaced (for example by a data-only commit pulled into a running Streamlit Cloud app).
Passing ``file_signature(path)`` as an ordinary, NON-underscore argument puts the file's
modification time and size into the cache key, so a changed file is re-read automatically.

Not applied in ``gcs_snapshot`` mode: snapshot files live under a run-id-specific path and are
immutable, so the path already identifies the content (see ``src/cloud/data_source_manager.py``).
"""

from __future__ import annotations

import os
from pathlib import Path


def file_signature(path: "Path | str") -> tuple[int, int] | None:
    """(mtime in ns, size in bytes) of a local file, or None if it cannot be stat'ed."""
    try:
        st = os.stat(path)
    except OSError:
        return None
    return (st.st_mtime_ns, st.st_size)


def cache_signature(path: "Path | str", is_snapshot: bool) -> tuple[int, int] | None:
    """The signature to pass to a cached loader: local files only, never for immutable snapshot paths."""
    return None if is_snapshot else file_signature(path)
