# DocumentTrust India

AI-based **Fake Identity & Document Screening System** for detecting tampering, inconsistencies, and potential fraud signals in identity documents and certificates.

This monorepo contains a **FastAPI backend** and a **React (Vite) frontend**. The upload pipeline is implemented; computer vision / ML screening models are planned for upcoming phases.

---

## Tech Stack

| Layer | Technologies |
|-------|--------------|
| **Backend** | Python 3, FastAPI, Uvicorn, Pydantic, aiofiles |
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS v4, Shadcn UI, Lucide React |
| **Storage** | Local filesystem (`backend/temp/uploads/`) |

---

## Project Structure

```
Document-Trust-India/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI entry point + CORS
│   │   ├── api/v1/
│   │   │   ├── api.py              # v1 router aggregator
│   │   │   └── endpoints/
│   │   │       └── upload.py       # POST /api/v1/upload
│   │   ├── core/
│   │   │   └── config.py           # Settings (port, CORS, upload rules)
│   │   ├── schemas/
│   │   │   └── upload.py           # Response models
│   │   └── services/
│   │       └── storage.py          # UUID-based file persistence
│   ├── temp/uploads/               # Uploaded files (gitignored)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── DocumentUpload.tsx  # Drag-and-drop upload UI
│   │   │   ├── layout/             # Navbar, MainLayout
│   │   │   └── ui/                 # Shadcn UI primitives
│   │   ├── pages/
│   │   │   └── HomePage.tsx
│   │   ├── services/               # API layer (Step 3)
│   │   └── lib/                    # Utils & constants
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

---

## Prerequisites

- **Python** 3.10+
- **Node.js** 18+ and **npm**
- A terminal with access to both `backend/` and `frontend/`

---

## Quick Start

Run the backend and frontend in **separate terminals**.

### 1. Backend (FastAPI)

```bash
cd backend

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Start the API server (default port: 7676)
uvicorn app.main:app --reload --host 0.0.0.0 --port 7676
```

Alternative (uses settings from `config.py`):

```bash
cd backend
python -m app.main
```

| Resource | URL |
|----------|-----|
| API base | http://localhost:7676 |
| Swagger UI | http://localhost:7676/docs |
| ReDoc | http://localhost:7676/redoc |
| Health check | http://localhost:7676/health |

### 2. Frontend (React + Vite)

```bash
cd frontend

# Install dependencies
npm install

# Start dev server (default port: 5173)
npm run dev
```

| Resource | URL |
|----------|-----|
| App | http://localhost:5173 |

### 3. Production build (frontend)

```bash
cd frontend
npm run build
npm run preview
```

---

## API Reference

### `GET /health`

Health check endpoint.

**Response:**

```json
{
  "status": "ok",
  "service": "DocumentTrust India"
}
```

### `POST /api/v1/upload`

Upload a single document for screening.

**Request:** `multipart/form-data` with field `file`

**Allowed types:**

- `image/jpeg`
- `image/png`
- `application/pdf`

**Example (curl):**

```bash
curl -X POST "http://localhost:7676/api/v1/upload" \
  -H "accept: application/json" \
  -F "file=@/path/to/document.pdf"
```

**Success response (201):**

```json
{
  "status": "success",
  "filename": "a1b2c3d4e5f6....pdf",
  "original_filename": "document.pdf",
  "path": "/absolute/path/to/backend/temp/uploads/a1b2c3d4....pdf",
  "content_type": "application/pdf"
}
```

**Error responses:**

| Status | Cause |
|--------|-------|
| `400` | Missing filename |
| `415` | Unsupported file type |

---

## Configuration

Backend settings live in `backend/app/core/config.py` and can be overridden via environment variables or a `.env` file in `backend/`.

| Variable | Default | Description |
|----------|---------|-------------|
| `API_HOST` | `0.0.0.0` | Server bind host |
| `API_PORT` | `7676` | Server port |
| `DEBUG` | `true` | Enable auto-reload when using `python -m app.main` |
| `MAX_UPLOAD_SIZE_MB` | `10` | Max upload size (reserved for future enforcement) |

**CORS** is preconfigured for local React dev servers:

- http://localhost:3000
- http://localhost:5173
- http://127.0.0.1:3000
- http://127.0.0.1:5173

Uploaded files are stored under `backend/temp/uploads/` with UUID-based filenames. This directory is gitignored (except `.gitkeep`).

---

## Frontend Features (Phase 3)

- Responsive layout with **DocumentTrust India** branding
- Drag-and-drop document upload with JPEG / PNG / PDF validation
- Image preview and PDF placeholder
- **Analyze Document** button with loading spinner and progress bar
- API service layer and results dashboard — **in progress** (Steps 3–4)

When the analysis API is wired up, the frontend will call:

```
POST http://localhost:7676/api/v1/upload
```

> **Note:** Use port **7676** for the backend (not 8000).

---

## Development Notes

### Add Shadcn UI components

From `frontend/`:

```bash
npx shadcn@latest add button card alert badge
```

If components are created under a literal `@/` folder, move them into `src/components/ui/`.

### Lint frontend

```bash
cd frontend
npm run lint
```

### Future ML dependencies (backend)

Placeholder entries in `backend/requirements.txt` (currently commented):

- `opencv-python-headless`
- `torch` / `torchvision`
- `easyocr`
- `numpy` / `pillow`

Uncomment and install when the computer vision pipeline is implemented.

---

## Roadmap

- [x] FastAPI backend scaffold + upload endpoint
- [x] React frontend scaffold (Vite, Tailwind, Shadcn UI)
- [x] Upload UI with drag-and-drop and loading states
- [ ] API service layer (`src/services/`)
- [ ] ML / CV screening pipeline (backend)
- [ ] Results dashboard (risk score, heatmap comparison)

---

## License

See [LICENSE](LICENSE).
