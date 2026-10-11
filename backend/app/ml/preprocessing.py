"""Sonar image preprocessing utilities.

These helpers are pure functions operating on NumPy arrays. They are designed to
be composable so the inference pipeline can apply any combination of steps.

The implementation avoids heavy deep-learning dependencies so it works even
when PyTorch / Ultralytics are not installed (which is the default for the
hackathon demo).
"""
from __future__ import annotations

import cv2
import numpy as np


def to_grayscale(image: np.ndarray) -> np.ndarray:
    """Convert BGR/RGB image to single-channel grayscale."""
    if image.ndim == 2:
        return image
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def normalize_image(image: np.ndarray) -> np.ndarray:
    """Rescale intensities to the full 0-255 range."""
    if image.dtype != np.uint8:
        img = image.astype(np.float32)
        mn, mx = float(img.min()), float(img.max())
        if mx - mn < 1e-6:
            return np.zeros_like(img, dtype=np.uint8)
        img = (img - mn) / (mx - mn) * 255.0
        return img.astype(np.uint8)
    return image


def apply_clahe(image: np.ndarray, clip_limit: float = 2.0, tile_grid: tuple = (8, 8)) -> np.ndarray:
    """Apply Contrast Limited Adaptive Histogram Equalization."""
    gray = to_grayscale(image)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid)
    return clahe.apply(gray)


def denoise_image(image: np.ndarray, strength: int = 7) -> np.ndarray:
    """Apply Non-Local Means denoising (single-channel fast variant)."""
    gray = to_grayscale(image)
    return cv2.fastNlMeansDenoising(gray, h=strength)


def sharpen_image(image: np.ndarray) -> np.ndarray:
    """Apply an unsharp mask to bring out edges."""
    gray = to_grayscale(image)
    blurred = cv2.GaussianBlur(gray, (0, 0), sigmaX=1.0)
    sharp = cv2.addWeighted(gray, 1.5, blurred, -0.5, 0)
    return sharp


def histogram_equalization(image: np.ndarray) -> np.ndarray:
    """Standard histogram equalization."""
    gray = to_grayscale(image)
    return cv2.equalizeHist(gray)


def enhance_image(
    image: np.ndarray,
    *,
    use_clahe: bool = True,
    use_denoise: bool = True,
    use_sharpen: bool = True,
    normalize: bool = True,
) -> np.ndarray:
    """Pipeline that produces an enhanced side-scan sonar image.

    Returns a single-channel uint8 image. The order of operations matters: we
    denoise before sharpening so we do not amplify noise.
    """
    img = image
    if img.ndim == 3 and img.shape[2] == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if normalize:
        img = normalize_image(img)
    if use_denoise:
        img = denoise_image(img)
    if use_clahe:
        img = apply_clahe(img)
    if use_sharpen:
        img = sharpen_image(img)
    return img


def compute_signal_stats(image: np.ndarray) -> dict:
    """Return basic statistics that the UI / confidence engine can use."""
    gray = to_grayscale(image).astype(np.float32)
    return {
        "mean": float(gray.mean()),
        "std": float(gray.std()),
        "min": float(gray.min()),
        "max": float(gray.max()),
    }