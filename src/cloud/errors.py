"""Shared error type for the Cloud Run job modules."""

from __future__ import annotations


class JobError(RuntimeError):
    """A clear, user-facing failure. Mapped to a non-zero exit status."""
