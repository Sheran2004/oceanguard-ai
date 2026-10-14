"""Model loading utilities for OceanGuard AI."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.utils.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class ModelBundle:
    """Metadata for a real or demo model."""

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
    """Validate and load the configured model.

    Demo mode is allowed only when explicitly enabled.
    Model-loading failures are logged and raised when demo mode is disabled.
    """
    settings = get_settings()
    path = Path(model_path or settings.model_path_abs)

    name = settings.model_name
    version = settings.model_version
    model_type = settings.model_type

    if settings.enable_demo_mode:
        logger.warning(
            "Demo mode is enabled. Real model inference is disabled."
        )
        return ModelBundle(
            name=name,
            version=version,
            model_type=f"{model_type}-demo",
            path=path,
            is_real=False,
            description="Demo mode enabled; predictions must not be treated as real detections.",
        )

    if not path.is_file():
        raise FileNotFoundError(
            f"Configured model file does not exist: {path}"
        )

    if path.suffix.lower() not in {".pt", ".onnx", ".weights"}:
        raise ValueError(
            f"Unsupported model file extension: {path.suffix}"
        )

    try:
        from ultralytics import YOLO

        # Validate that the trained model can actually be loaded.
        YOLO(str(path))

    except Exception as exc:
        logger.exception("Failed to load OceanGuard model from %s", path)
        raise RuntimeError(
            f"Could not load the configured YOLO model at {path}: {exc}"
        ) from exc

    logger.info("OceanGuard model loaded successfully: %s", path)

    return ModelBundle(
        name=name,
        version=version,
        model_type=model_type,
        path=path,
        is_real=True,
        description=f"Trained YOLO model loaded from {path}",
    )