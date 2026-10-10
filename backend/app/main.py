from pathlib import Path
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from .config import APP_NAME, CORS_ORIGINS, MAX_UPLOAD_MB
from .db import connect, serialize
from .schemas import RecordCreate
from .services import ALLOWED, extract, summarize

app = FastAPI(title=APP_NAME, description="Student MVP for organizing medical documents; not a diagnostic service.")
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_credentials=False,
                   allow_methods=["GET","POST","DELETE","OPTIONS"], allow_headers=["*"])

@app.on_event("startup")
def startup():
    conn = connect(); conn.close()

@app.get("/health")
def health():
    return {"status":"ok", "service":APP_NAME, "mode":"student-project-mvp"}

@app.get("/api/records")
def list_records():
    conn = connect()
    try:
        return [serialize(r) for r in conn.execute("SELECT * FROM records ORDER BY COALESCE(document_date,'') DESC,id DESC").fetchall()]
    finally: conn.close()

@app.get("/api/records/{record_id}")
def get_record(record_id: int):
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM records WHERE id=?", (record_id,)).fetchone()
        if not row: raise HTTPException(404, "Record not found")
        return serialize(row)
    finally: conn.close()

@app.post("/api/records")
def create_record(payload: RecordCreate):
    conn = connect()
    try:
        cur = conn.execute("INSERT INTO records(name,document_type,document_date,language,extracted_text,summary,status) VALUES(?,?,?,?,?,?,?)",
            (payload.name.strip(),payload.type,payload.date,payload.language,payload.text,payload.summary,"Needs review"))
        conn.commit()
        return serialize(conn.execute("SELECT * FROM records WHERE id=?", (cur.lastrowid,)).fetchone())
    finally: conn.close()

@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...), document_type: str = Form("Other medical record"),
                          document_date: str = Form(""), language: str = Form("Unknown")):
    filename = Path(file.filename or "document").name
    if Path(filename).suffix.lower() not in ALLOWED:
        raise HTTPException(415, "Unsupported file type. Upload PDF, PNG, JPG, JPEG, or WEBP.")
    data = await file.read()
    if not data: raise HTTPException(400, "The uploaded file is empty.")
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f"File is too large. Maximum size is {MAX_UPLOAD_MB} MB.")
    try:
        text, extraction_method = extract(data, filename)
    except ValueError as exc: raise HTTPException(400, str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(502, str(exc)) from exc
    summary, summary_method = summarize(text, document_type)
    name = Path(filename).stem[:180] or "Medical document"
    # Original files are not retained; extracted text and summary are saved to SQLite.
    conn = connect()
    try:
        cur = conn.execute("INSERT INTO records(name,document_type,document_date,language,original_filename,extracted_text,summary,status) VALUES(?,?,?,?,?,?,?,?)",
            (name,document_type,document_date,language,filename,text,summary,"Needs review"))
        conn.commit()
        row = serialize(conn.execute("SELECT * FROM records WHERE id=?", (cur.lastrowid,)).fetchone())
    finally: conn.close()
    return {**row,"extractionMethod":extraction_method,"summaryMethod":summary_method,
            "needsHumanReview":True,"notice":"Verify all extracted details against the original. This app does not diagnose."}

@app.delete("/api/records/{record_id}")
def delete_record(record_id: int):
    conn = connect()
    try:
        cur = conn.execute("DELETE FROM records WHERE id=?", (record_id,)); conn.commit()
        if cur.rowcount == 0: raise HTTPException(404, "Record not found")
        return {"deleted":True,"id":record_id}
    finally: conn.close()
