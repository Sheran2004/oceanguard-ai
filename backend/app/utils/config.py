"""Application configuration loaded from environment variables."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Strongly typed application settings."""

    app_name: str = "OceanGuard AI"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    database_url: str = "sqlite:///./oceanguard.db"

    upload_dir: str = "./uploads"
    report_dir: str = "./reports"
    max_upload_size_mb: int = 25

    model_path: str = "./ml/models/sonar_debris.pt"
    model_type: str = "yolov8"
    model_name: str = "OceanGuard-YOLO-v1"
    model_version: str = "1.0"
    confidence_threshold: float = 0.25
    iou_threshold: float = 0.45
    device: str = "cpu"
    anomaly_threshold: float = 0.65
    enable_demo_mode: bool = True

    classes_config: str = "./config/classes.yaml"

    # ===== Auth / Security =====
    secret_key: str = "change-me-in-production-please-set-env-secret-key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24h
    rate_limit_per_minute: int = 300

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=("settings_",),
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def upload_path(self) -> Path:
        p = Path(self.upload_dir)
        if not p.is_absolute():
            p = PROJECT_ROOT / p
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def report_path(self) -> Path:
        p = Path(self.report_dir)
        if not p.is_absolute():
            p = PROJECT_ROOT / p
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def classes_config_path(self) -> Path:
        p = Path(self.classes_config)
        if not p.is_absolute():
            p = PROJECT_ROOT / p
        return p

    @property
    def model_path_abs(self) -> Path:
        p = Path(self.model_path)
        if not p.is_absolute():
            p = PROJECT_ROOT / p
        return p


@lru_cache
def get_settings() -> Settings:
    return Settings()


def load_classes_config(path: Path | None = None) -> dict:
    """Load classes.yaml and return a normalized dictionary."""
    settings = get_settings()
    cfg_path = path or settings.classes_config_path
    if not cfg_path.exists():
        return {"classes": {}, "priority_rules": {}}
    with open(cfg_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    classes = raw.get("classes", {}) or {}
    normalized = {}
    for key, val in classes.items():
        cid = int(key)
        normalized[cid] = {
            "id": val.get("id", f"class_{cid}"),
            "name": val.get("name", f"Class {cid}"),
            "description": val.get("description", ""),
            "base_priority": val.get("base_priority", "medium"),
            "is_anomaly": bool(val.get("is_anomaly", False)),
        }
    return {
        "classes": normalized,
        "priority_rules": raw.get("priority_rules", {}),
    }