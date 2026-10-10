
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

from .config import APP_NAME, CORS_ORIGINS, MAX_UPLOAD_MB
from .db import connect, serialize
from .schemas import RecordCreate
from .services import ALLOWED, extract, summarize

logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Verify database connectivity at startup.
    conn = connect()
    conn.close()
    yield


app = FastAPI(
    title=APP_NAME,
    description=(
        "Student MVP for organizing medical documents. "
        "Not a diagnostic service."
    ),
    lifespan=lifespan,
)

# Configure CORS once. Set CORS_ORIGINS in config.py
# to the exact frontend origins you trust.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


def get_db():
    """Open a database connection and translate unexpected DB errors."""
    try:
        return connect()
    except Exception as exc:
        logger.exception("Database connection failed")
        raise HTTPException(
            status_code=503,
            detail="The database is temporarily unavailable.",
        ) from exc


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": APP_NAME,
        "mode": "student-project-mvp",
    }


@app.get("/api/records")
def list_records():
    conn = get_db()
    try:
        rows = conn.execute(
            """
            SELECT * FROM records
            ORDER BY COALESCE(document_date, '') DESC, id DESC
            """
        ).fetchall()
        return [serialize(row) for row in rows]
    except Exception as exc:
        logger.exception("Could not list records")
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve records.",
        ) from exc
    finally:
        conn.close()


@app.get("/api/records/{record_id}")
def get_record(record_id: int):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM records WHERE id = ?",
            (record_id,),
        ).fetchone()

        if row is None:
            raise HTTPException(status_code=404, detail="Record not found")

        return serialize(row)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Could not retrieve record")
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve the record.",
        ) from exc
    finally:
        conn.close()


@app.post("/api/records")
def create_record(payload: RecordCreate):
    if not payload.name.strip():
        raise HTTPException(
            status_code=422,
            detail="Record name cannot be empty.",
        )

    conn = get_db()
    try:
        cur = conn.execute(
            """
            INSERT INTO records
            (name, document_type, document_date, language,
             extracted_text, summary, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.name.strip(),
                payload.type,
                payload.date,
                payload.language,
                payload.text,
                payload.summary,
                "Needs review",
            ),
        )
        conn.commit()

        row = conn.execute(
            "SELECT * FROM records WHERE id = ?",
            (cur.lastrowid,),
        ).fetchone()
        return serialize(row)

    except Exception as exc:
        conn.rollback()
        logger.exception("Could not create record")
        raise HTTPException(
            status_code=500,
            detail="Could not save the record.",
        ) from exc
    finally:
        conn.close()


@app.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form("Other medical record"),
    document_date: str = Form(""),
    language: str = Form("Unknown"),
):
    filename = Path(file.filename or "document").name

    if Path(filename).suffix.lower() not in ALLOWED:
        await file.close()
        raise HTTPException(
            status_code=415,
            detail="Upload a PDF, PNG, JPG, JPEG, or WEBP file.",
        )

    try:
        # Read at most one byte beyond the configured limit.
        data = await file.read(MAX_UPLOAD_BYTES + 1)

        if not data:
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is empty.",
            )

        if len(data) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"Maximum upload size is {MAX_UPLOAD_MB} MB.",
            )

        # OCR and AI calls are blocking; avoid blocking the async event loop.
        try:
            text, extraction_method = await run_in_threadpool(
                extract, data, filename
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(
                status_code=422,
                detail=str(exc),
            ) from exc

        summary, summary_method = await run_in_threadpool(
            summarize, text, document_type
        )

        name = Path(filename).stem[:180] or "Medical document"

        conn = get_db()
        try:
            cur = conn.execute(
                """
                INSERT INTO records
                (name, document_type, document_date, language,
                 original_filename, extracted_text, summary, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    document_type,
                    document_date,
                    language,
                    filename,
                    text,
                    summary,
                    "Needs review",
                ),
            )
            conn.commit()

            row = conn.execute(
                "SELECT * FROM records WHERE id = ?",
                (cur.lastrowid,),
            ).fetchone()

            record = serialize(row)

        except Exception as exc:
            conn.rollback()
            logger.exception("Could not save uploaded document")
            raise HTTPException(
                status_code=500,
                detail="Document processing completed, but saving failed.",
            ) from exc
        finally:
            conn.close()

        return {
            **record,
            "extractionMethod": extraction_method,
            "summaryMethod": summary_method,
            "needsHumanReview": True,
            "notice": (
                "Verify extracted details against the original document. "
                "This application does not diagnose or recommend treatment."
            ),
        }

    finally:
        await file.close()


@app.delete("/api/records/{record_id}")
def delete_record(record_id: int):
    conn = get_db()
    try:
        cur = conn.execute(
            "DELETE FROM records WHERE id = ?",
            (record_id,),
        )
        conn.commit()

        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Record not found")

        return {"deleted": True, "id": record_id}

    except HTTPException:
        raise
    except Exception as exc:
        conn.rollback()
        logger.exception("Could not delete record")
        raise HTTPException(
            status_code=500,
            detail="Could not delete the record.",
        ) from exc
    finally:
        conn.close()
