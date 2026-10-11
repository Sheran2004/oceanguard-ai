"""Model loading utilities. The real implementation would call ultralytics.

To keep the demo runnable without GPU/PyTorch we detect whether the requested
model file actually exists and otherwise fall back to a deterministic
"DemoModelBundle" that returns structured placeholder predictions.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.utils.config import get_settings


@dataclass
class ModelBundle:
    """Represents a loaded (or demo) model."""
    name: str
    version: str
    model_type: str
    path: Path
    is_real: bool
    description: str = ""

    def summary(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "model_type": self.model_type,
            "path": str(self.path),
            "is_real": self.is_real,
            "description": self.description,
        }


def load_model(model_path: Optional[Path] = None) -> ModelBundle:
    """Load a real model if available, otherwise return the demo bundle.

    The function never raises. It is safe to call at module import time.
    """
    settings = get_settings()
    path = model_path or settings.model_path_abs
    name = settings.model_name
    version = settings.model_version
    model_type = settings.model_type

    # Real model: try a lazy import. If ultralytics isn't installed we fall back.
    if settings.enable_demo_mode is False and path.exists() and path.suffix in {".pt", ".onnx", ".weights"}:
        try:  # pragma: no cover - depends on optional deps
            from ultralytics import YOLO  # type: ignore

            _model = YOLO(str(path))
            return ModelBundle(
                name=name,
                version=version,
                model_type=model_type,
                path=path,
                is_real=True,
                description=f"Loaded real model from {path}",
            )
        except Exception:
            pass

    return ModelBundle(
        name=name,
        version=version,
        model_type=f"{model_type}-demo",
        path=path if path.exists() else Path("(no file)"),
        is_real=False,
        description=(
            "DEMO INFERENCE — NOT A VALIDATED DEPLOYMENT MODEL. "
            "Predictions are deterministically generated for prototype demonstration."
        ),
    )