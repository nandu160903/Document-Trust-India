# DocumentTrust India — Test Suite

Manual and integration tests live here, separate from application source code.

## Layout

```
tests/
├── fixtures/          # Sample documents for manual runs
├── helpers/           # Shared bootstrap utilities
└── manual/            # Runnable verification scripts
    ├── test_module1_forensics.py
    ├── test_module2_risk_engine.py
    ├── test_module3_api_workflow.py
    └── run_all.py
```

## Prerequisites

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run individual tests

From repository root:

```bash
# Module 1 — metadata, ELA, OCR/layout
python tests/manual/test_module1_forensics.py path/to/document.jpg

# Module 2 — full risk scoring pipeline
python tests/manual/test_module2_risk_engine.py path/to/document.jpg

# Module 3 — FastAPI upload + static asset workflow
python tests/manual/test_module3_api_workflow.py
python tests/manual/test_module3_api_workflow.py path/to/document.jpg
```

## Run all tests

```bash
python tests/manual/run_all.py
python tests/manual/run_all.py path/to/document.jpg
```

## Notes

- Module 3 uses FastAPI `TestClient` (in-process) and does not require a running server.
- First EasyOCR / Transformers run may download model weights.
- Generated artifacts are written to `backend/temp/uploads` and `backend/temp/heatmaps`.
