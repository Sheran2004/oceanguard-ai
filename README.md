# 🌊 OceanGuard AI

> **Turning Underwater Sonar Imagery into Actionable Marine Intelligence.**

**SIH 2026 — Problem Statement SIH26057**

AI-Powered Underwater Marine Debris & Anomaly Detection System using Side-Scan Sonar Imagery.

This repository contains a complete, production-style prototype built for the Smart India Hackathon 2026. It is a full-stack monorepo with a FastAPI backend, a React + Vite + TypeScript frontend, and a transparent, swappable computer-vision pipeline that runs in two clearly-labeled modes:

* **Real Model Mode** — a real trained detector (e.g. Ultralytics YOLO) loaded from `MODEL_PATH`.
* **Demo Mode** — a deterministic, content-aware placeholder engine used when no validated deployment model is available. Every demo output is clearly labeled `DEMO INFERENCE — NOT A VALIDATED DEPLOYMENT MODEL`.

OceanGuard AI is built around the principle of **decision support, not autonomous decisions**. AI-assisted review priorities are exposed to operators; humans always retain the final say.

---

## 1. Problem Statement

Underwater environments can contain marine debris, discarded fishing gear, plastic waste, metal objects, abandoned equipment and unknown anomalies. Manually inspecting large volumes of side-scan sonar imagery is slow and inconsistent.

**OceanGuard AI** provides:

* automated upload + validation of sonar imagery
* preprocessing (CLAHE, denoising, sharpening, normalization)
* AI-based object detection
* a transparent, rule-based **priority engine** for operator review
* an **anomaly detection layer** that flags unknown patterns
* bounding-box visualization with class, confidence and location
* per-scan AI insights and human review queue
* geospatial aggregation and hotspot analysis (when GPS metadata exists)
* mission management, scan history, temporal comparison
* analytics, PDF report generation, and a feedback dataset for active learning

---

## 2. Repository Structure

```
oceanguard-ai/
├── backend/                  FastAPI application
│   ├── app/
│   │   ├── main.py
│   │   ├── api/               scans, detections, missions, analytics, hotspots, reports, reviews, system
│   │   ├── models/           SQLAlchemy ORM + Pydantic schemas
│   │   ├── services/         scan, detection, priority, anomaly, geo, report, ai-summary
│   │   ├── ml/               inference engine, preprocessing, postprocessing, anomaly detector, visualization
│   │   ├── database/         seeding
│   │   └── utils/            config, helpers
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                 React + Vite + TS application
│   ├── src/
│   │   ├── pages/            Dashboard, Sonar Analysis, Missions, Scans, Detections, Hotspots,
│   │   │                     Analytics, Review, Models, Reports, Settings
│   │   ├── components/       layout, ui, map, charts
│   │   ├── services/         API client
│   │   ├── types/            shared TypeScript types
│   │   └── hooks/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── Dockerfile
├── ml/                       Top-level ML package (re-exports of backend.app.ml)
│   ├── inference.py
│   ├── preprocessing.py
│   ├── postprocessing.py
│   ├── model_loader.py
│   ├── anomaly_detector.py
│   ├── confidence.py
│   └── visualization.py
├── config/
│   └── classes.yaml          Object classes, anomaly flags, priority rules
├── scripts/
│   ├── generate_demo_data.py Synthetic sonar generator + DB seeder
│   ├── start_backend.sh
│   └── start_frontend.sh
├── data/                     Generated demo data (gitignored)
├── reports/                  Generated PDFs
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 3. Tech Stack

**Backend**

* Python 3.11
* FastAPI + Uvicorn
* SQLAlchemy 2 + SQLite (default) / PostgreSQL (optional)
* Pydantic / Pydantic Settings
* OpenCV (headless), NumPy, Pillow, PyYAML
* ReportLab (PDF generation)
* Ultralytics YOLO (optional, lazy-loaded for real model)

**Frontend**

* React 18 + Vite 5 + TypeScript
* Tailwind CSS (custom dark ocean theme)
* Recharts (charts)
* React-Leaflet + OpenStreetMap (geospatial)
* lucide-react (icons)
* React Router v6

**ML / Inference**

* OpenCV-based preprocessing pipeline (CLAHE, denoise, sharpen, normalize)
* Content-aware demo inference engine (Sobel edge saliency → contour extraction → calibrated confidence)
* Multi-method anomaly detection (edge density, contrast, intensity histogram entropy)
* Class-agnostic NMS, IoU, confidence filtering
* Easy swap-in for a real detector (Ultralytics YOLO) via `model_loader.py`

---

## 4. Installation

### Prerequisites

* Python ≥ 3.10
* Node.js ≥ 18
* (Optional) Docker + Docker Compose

### Local Development

```bash
# 1. Clone & enter the project
cd oceanguard-ai

# 2. Backend
python -m pip install -r backend/requirements.txt
cp .env.example .env

# 3. Generate demo data + seed database
python scripts/generate_demo_data.py --clear --scans 8

# 4. Run backend (FastAPI on :8000)
uvicorn app.main:app --app-dir backend --reload

# 5. Frontend (Vite dev server on :5173)
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173> — the Vite dev server proxies `/api/*` to the backend on `:8000`.

### Docker

```bash
docker compose up --build
```

The backend will be exposed on `:8000` and the frontend on `:5173`.

---

## 5. Demo Data

```bash
python scripts/generate_demo_data.py --clear --scans 8
```

This generates:

* 8 synthetic side-scan sonar-like PNG images
* 2 demo missions
* Per-scan locations, anomaly records, detection rows and review records
* Default model registry entry (clearly labeled `demo`)

The generated images and database rows are tagged `DEMO DATA` and must never be presented as real survey output.

---

## 6. AI Pipeline

```
         Sonar Image Upload
                │
                ▼
       File Validation
                │
                ▼
       Preprocessing
       (CLAHE, Denoise, Sharpen, Normalize)
                │
                ▼
     ┌────────────────────┐
     │ Inference Engine   │   ← swappable: real model OR deterministic demo
     └────────────────────┘
                │
                ▼
       Confidence Filter + NMS
                │
                ▼
       Object Classification
                │
                ▼
       Anomaly Detection
       (edge + contrast + entropy)
                │
                ▼
       Priority Engine
       (rule-based, transparent)
                │
                ▼
       Persist + Visualize
```

### Configuration

* `MODEL_PATH` — path to model weights (`.pt`, `.onnx`, etc.).
* `MODEL_TYPE` — `yolov8` | `yolov5` | `demo`.
* `CONFIDENCE_THRESHOLD`, `IOU_THRESHOLD`, `ANOMALY_THRESHOLD` — see `.env.example`.
* `ENABLE_DEMO_MODE` — when `true` (default) and `MODEL_PATH` does not exist, the system falls back to a deterministic content-aware demo engine and **clearly labels** every inference as such.

### Object Classes

Configured via `config/classes.yaml`:

| ID | Name             | Base Priority | Anomaly? |
|----|---------|---------|---------|
| 0  | Marine Debris     | Medium        | —        |
| 1  | Fishing Net       | High          | —        |
| 2  | Plastic Debris    | Medium        | —        |
| 3  | Metal Object      | High          | —        |
| 4  | Man-made Object   | Medium        | —        |
| 5  | Unknown Anomaly   | Review        | Yes      |

Adding a class is a single-file change — no code edits required.

---

## 7. Priority Engine

A transparent, rule-based priority engine returns one of: `LOW`, `MEDIUM`, `HIGH`, `REVIEW`.

Inputs:

* detection confidence
* base priority of the predicted class
* object footprint (relative area)
* cluster density (number of nearby detections)
* anomaly flag

The output is labeled throughout the UI as **"AI-Assisted Review Priority"** — it is NOT a scientifically validated risk score.

---

## 8. API Endpoints (summary)

| Method | Path | Description |
|--------|------|-------------|
| GET    | `/health` | Service health |
| GET    | `/api/system/info` | Active model, classes, thresholds, disclaimer |
| GET    | `/api/models` | Model registry |
| POST   | `/api/scans/upload` | Upload + analyse sonar image |
| POST   | `/api/scans/{id}/analyze` | Re-run inference on existing scan |
| GET    | `/api/scans` | List scans (filter by mission) |
| GET    | `/api/scans/{id}` | Scan detail with detections |
| GET    | `/api/scans/{id}/image` | Original image |
| GET    | `/api/scans/{id}/overlay` | AI-annotated overlay image |
| GET    | `/api/scans/{id}/enhanced` | Preprocessed (enhanced) image |
| POST   | `/api/scans/compare` | Compare two scans (persistent / new / removed) |
| GET    | `/api/detections` | List detections with filters |
| GET    | `/api/detections/{id}` | Detection detail |
| POST   | `/api/detections/{id}/review` | Approve / reject / needs-review |
| GET    | `/api/missions` | List missions |
| GET    | `/api/missions/{id}` | Mission detail |
| POST   | `/api/missions` | Create mission |
| GET    | `/api/analytics/summary` | Aggregate analytics |
| GET    | `/api/analytics/timeline` | Per-scan timeline |
| GET    | `/api/hotspots` | Aggregated hotspot regions |
| GET    | `/api/anomalies` | Anomaly worklist |
| GET    | `/api/reports` | List generated PDFs |
| POST   | `/api/reports/missions/{id}` | Generate PDF report |
| GET    | `/api/reports/{id}/download` | Download PDF |
| GET    | `/api/reviews/export` | Export reviewer dataset as CSV |

Full interactive docs are available at <http://localhost:8000/docs>.

---

## 9. Frontend Pages

| Route                | Purpose |
|----------------------|---------|
| `/dashboard`         | Command-center overview, trends, distribution charts |
| `/sonar-analysis`    | Upload + analyse + visualize + interact with detections |
| `/missions`          | Create, list and inspect missions |
| `/scans`             | Scan history with temporal comparison |
| `/detections`        | Filtered list of all detections across scans |
| `/hotspots`          | Geospatial map + hotspot aggregation |
| `/analytics`         | Detailed charts and distributions |
| `/review`            | Human-in-the-loop approve/reject + CSV export |
| `/models`            | Model registry, classes, thresholds |
| `/reports`           | Generate and download PDF mission reports |
| `/settings`          | Thresholds and disclaimers |

---

## 10. Data Limitations & Disclaimer

This system is built as a **decision-support prototype**. The following are intentional guardrails:

* **No fabricated metrics.** Model accuracy, precision, recall etc. are never displayed unless produced by an actual evaluation run.
* **Demo data is clearly labeled** as `DEMO DATA` in the database and `Demo Dataset` in the UI.
* **Demo coordinates are clearly labeled** in the hotspot map and detection popups.
* **AI explanations use hedged wording** ("consistent with", "likely", "possible", "requires human verification").
* **Unknown anomalies are NEVER claimed to be dangerous** — they are flagged for review.
* **The PDF report includes an explicit disclaimer** that all AI output requires qualified human verification.

---

## 11. Future Improvements

* Train the OceanGuard-YOLO model on a curated, labeled side-scan sonar dataset.
* Add automatic dataset versioning (DVC) and CI evaluation.
* WebSocket-based live inference progress (currently shown via a small progress indicator).
* Mission replay mode (animated timeline of detections per scan).
* Multi-user accounts with role-based access control.
* Federated learning across multiple survey vessels.

---

## 12. License & Acknowledgements

This prototype was prepared for Smart India Hackathon 2026 (Problem Statement SIH26057). The implementation is intentionally modular so that real datasets and trained models can replace the demo engine without touching the API or UI.

> 🌊 _OceanGuard AI — Decision support for the silent world beneath the surface._