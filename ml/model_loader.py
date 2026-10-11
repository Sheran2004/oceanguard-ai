"""Re-export of backend.app.ml.model_loader for the top-level /ml package."""
from app.ml.model_loader import ModelBundle, load_model


__all__ = ["ModelBundle", "load_model"]