"""OceanGuard AI - inference pipeline (top-level /ml package).

These files mirror the implementation under backend/app/ml so the project
satisfies the monorepo layout described in the spec. The actual code lives
in backend.app.ml so the FastAPI service can use it directly without a
separate package on sys.path.

This module simply re-exports the public symbols. Replace any of these
files with custom training / evaluation code when migrating from demo mode
to a real trained model.
"""
from __future__ import annotations

import os
import sys

_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from app.ml.inference import (  # noqa: E402,F401
    InferenceEngine,
    Prediction,
    get_inference_engine,
    reset_inference_engine,
)


__all__ = ["InferenceEngine", "Prediction", "get_inference_engine", "reset_inference_engine"]