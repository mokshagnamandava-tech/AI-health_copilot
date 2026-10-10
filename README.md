# Wellnote Health Copilot (student MVP)

React + Vite frontend, FastAPI backend, SQLite, PDF text extraction, optional Google Cloud Vision OCR, and optional OpenAI summaries.

## Run locally
Requirements: Python 3.11+, Node.js 20+.

Backend (from project root):
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r backend/requirements.txt
# Copy backend/.env.example to backend/.env and edit optional settings
uvicorn backend.app.main:app --reload --port 8000
```
API docs: http://localhost:8000/docs

Frontend (second terminal):
```bash
cd frontend
npm install
# Copy .env.example to .env if you need a different API URL
npm run dev
```
Open http://localhost:5173.

## Optional integrations
- Google Cloud Vision: enable Vision API, configure Application Default Credentials or `GOOGLE_APPLICATION_CREDENTIALS`, then set `ENABLE_GOOGLE_VISION=true` in `backend/.env`. Never commit credentials.
- OpenAI summaries: set `OPENAI_API_KEY` in `backend/.env`. The key is used only on the backend. Without it, a non-AI fallback summary is shown.
- OCR documentation: https://cloud.google.com/vision/docs/ocr

## Docker
Copy `backend/.env.example` to `backend/.env`, then run:
```bash
docker compose up --build
```
Frontend: http://localhost:8080. API: http://localhost:8000.

## Features
- Dashboard, upload form, medical records/search, timeline, health profile, settings.
- Upload PDF/image files; selectable PDF text is extracted with PyMuPDF.
- Optional Vision OCR for images and scanned PDFs.
- Optional AI plain-language summaries with cautious safety instructions.
- SQLite records API; delete records from the UI.

## Important limitations
This is a student-project MVP, not a certified medical product. It has no authentication, multi-user authorization, production-grade security, or real ABHA/ABDM integration. Use only fictional or de-identified documents for demos. Do not publicly deploy with real medical records until you implement and test authentication, access controls, HTTPS, private storage, encryption, audit logging, retention/deletion, backups, and applicable privacy requirements. OCR and AI may be wrong; verify every detail against the original. Never guess medicine names or doses. The app does not diagnose or recommend treatment.

FHIR/ABHA note: no actual ABHA/ABDM connection is implemented. FHIR-style mapping is a future task, not a current feature.
