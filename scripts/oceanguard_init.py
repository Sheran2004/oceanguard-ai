"""Helper: ensure DB schema + base users exist.  Called by start.ps1.

Patches the passlib/bcrypt version-check warning so the script runs silently.
"""
from __future__ import annotations
import sys
from pathlib import Path

# Suppress passlib's "trapped error reading bcrypt version" noise on bcrypt 4.x
# by giving bcrypt a synthetic __about__ attribute before passlib loads.
try:
    import bcrypt as _bcrypt
    if not hasattr(_bcrypt, "__about__"):
        _bcrypt.__about__ = type("about", (), {"__version__": _bcrypt.__version__})()
except Exception:
    pass

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.database.seed import ensure_base_data
from app.models.database import SessionLocal, init_db
from app.models.orm import Scan, User

init_db()
ensure_base_data()
db = SessionLocal()
print(f"USERS={db.query(User).count()}")
print(f"SCANS={db.query(Scan).count()}")
db.close()
