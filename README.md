# DocumentTrust India

AI-based **Fake Identity & Document Screening System** for detecting tampering, inconsistencies, and potential fraud signals in identity documents and certificates.

This monorepo contains a **FastAPI forensic backend**, a **React (Vite) frontend**, Docker orchestration, and a dedicated **`tests/`** suite.

---

## Tech Stack

| Layer | Technologies |
|-------|--------------|
| **Backend** | Python 3.11, FastAPI, Uvicorn, Pydantic, OpenCV, EasyOCR, Transformers |
| **Forensics** | EXIF/XMP metadata, ELA, OCR layout heuristics, ViT inference |
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS v4, Shadcn UI, Lucide React |
| **Deployment** | Docker, Docker Compose, Nginx |
| **Storage** | Local filesystem (`backend/temp/uploads/`, `backend/temp/heatmaps/`) |

---

## Project Structure

```
Document-Trust-India/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI + CORS + static mounts
│   │   ├── api/v1/endpoints/upload.py  # POST /api/v1/upload (analyze)
│   │   ├── core/config.py
│   │   ├── schemas/
│   │   │   ├── analysis.py             # Frontend analysis response
│   │   │   └── forensics.py
│   │   └── services/
│   │       ├── metadata_analyzer.py
│   │       ├── ela_detector.py
│   │       ├── ocr_layout.py
│   │       ├── model_inference.py
│   │       ├── risk_engine.py
│   │       ├── pipeline.py
│   │       └── storage.py
│   ├── temp/uploads/                   # Uploaded documents
│   ├── temp/heatmaps/                  # ELA heatmap artifacts
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/                            # React UI
│   ├── Dockerfile
│   └── nginx.conf
├── tests/                              # Manual/integration tests (separate)
│   ├── fixtures/
│   ├── helpers/
│   └── manual/
├── docker-compose.yml
└── README.md
```

---

## Prerequisites

- **Python** 3.10+ (3.11 recommended for Docker parity)
- **Node.js** 18+ and **npm**
- **Docker** & **Docker Compose** (optional, for container deployment)
- **Tesseract OCR** (optional fallback): `sudo apt-get install tesseract-ocr`

---

## Quick Start (Local Development)

Run the backend and frontend in **separate terminals**.

### 1. Backend (FastAPI)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 7676
```

| Resource | URL |
|----------|-----|
| API base | http://localhost:7676 |
| Swagger UI | http://localhost:7676/docs |
| Health check | http://localhost:7676/health |
| Static uploads | http://localhost:7676/static/uploads/ |
| Static heatmaps | http://localhost:7676/static/heatmaps/ |

### 2. Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

| Resource | URL |
|----------|-----|
| App | http://localhost:5173 |

---

## Docker Deployment (Module 4)

Build and run both services with persistent volumes:

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend (Nginx) | http://localhost:8080 |
| Backend API | http://localhost:7676 |
| API via Nginx proxy | http://localhost:8080/api/v1/... |

Docker details:

- **Backend** image: Python 3.11-slim, OpenCV/OCR system libs, cached pip wheels
- **Frontend** image: Node 22 build stage → Nginx runtime
- **Volumes**: `backend_uploads`, `backend_heatmaps`, `model_cache`
- **Health checks** on both containers

Stop services:

```bash
docker compose down
```

---

## API Reference

### `GET /health`

```json
{ "status": "ok", "service": "DocumentTrust India" }
```

### `POST /api/v1/upload`

Upload and analyze a document in one request.

**Request:** `multipart/form-data` with field `file`  
**Allowed types:** `image/jpeg`, `image/png`, `application/pdf`

**Example:**

```bash
curl -X POST "http://localhost:7676/api/v1/upload" \
  -H "accept: application/json" \
  -F "file=@/path/to/document.jpg"
```

**Success response (200):**

```json
{
  "status": "success",
  "risk_score": 85,
  "risk_level": "HIGH",
  "reasons": [
    "Software manipulation signature detected: Adobe Photoshop",
    "Localized compression anomalies detected via ELA"
  ],
  "original_image_url": "/static/uploads/<uuid>.jpg",
  "heatmap_image_url": "/static/heatmaps/<uuid>_ela.png",
  "extracted_fields": {
    "text_block_1": "AADHAAR",
    "text_block_1_confidence": 0.91
  },
  "anomaly_score": 0.74,
  "inference_method": "transformers_vit",
  "component_scores": {
    "metadata": 25,
    "ela": 30,
    "layout": 0,
    "deep_learning": 25
  }
}
```

---

## Testing

All test scripts live under **`tests/`**, separate from application code. See [`tests/README.md`](tests/README.md).

```bash
# From repository root (backend venv activated)

# Module 1 — metadata, ELA, OCR/layout
python tests/manual/test_module1_forensics.py path/to/document.jpg

# Module 2 — risk engine pipeline
python tests/manual/test_module2_risk_engine.py path/to/document.jpg

# Module 3 — API upload + static asset workflow (in-process TestClient)
python tests/manual/test_module3_api_workflow.py

# Run all manual tests
python tests/manual/run_all.py path/to/document.jpg
```

Place reusable sample files in `tests/fixtures/`.

---

## Configuration

Settings: `backend/app/core/config.py` (override via `backend/.env`).

| Variable | Default | Description |
|----------|---------|-------------|
| `API_HOST` | `0.0.0.0` | Bind host |
| `API_PORT` | `7676` | Bind port |
| `DEBUG` | `true` | Auto-reload for local dev |
| `ENABLE_TRANSFORMERS_INFERENCE` | `true` | ViT inference toggle |
| `HF_MODEL_ID` | `google/vit-base-patch16-224` | Hugging Face model |
| `ELA_MEAN_ERROR_THRESHOLD` | `8.0` | ELA risk trigger |
| `ELA_PEAK_ANOMALY_THRESHOLD` | `2.5` | ELA peak trigger |
| `DL_ANOMALY_THRESHOLD` | `0.7` | Deep learning risk trigger |

Risk weights: metadata **+25**, ELA **+30**, layout **+20**, deep learning **+25**.

Risk levels: **LOW** (< 30), **MEDIUM** (30–65), **HIGH** (> 65).

---

## Forensic Pipeline Overview

1. **MetadataAnalyzer** — EXIF/XMP/PDF metadata, editing software signatures
2. **ELADetector** — Error Level Analysis heatmap generation
3. **OCRLayoutAnalyzer** — text extraction + layout inconsistency heuristics
4. **ModelInferenceService** — ViT-based anomaly scoring with CV fallback
5. **RiskEngine** — weighted aggregation into `risk_score` / `risk_level`
6. **DocumentAnalyzerPipeline** — orchestrates analysis for the API

---

## Roadmap

- [x] FastAPI backend + upload endpoint
- [x] React frontend upload UI
- [x] Module 1 forensic services (metadata, ELA, OCR/layout)
- [x] Module 2 ML inference + risk engine
- [x] Module 3 API pipeline + static asset serving
- [x] Module 4 Docker Compose orchestration
- [x] Dedicated `tests/` folder
- [ ] Frontend API service layer + results dashboard wiring

---

## License

See [LICENSE](LICENSE).
