# knowledge_store.py — minimal self-hosted agent knowledge commons (SQLite + FastAPI)
# Run: uvicorn knowledge_store:app --host 0.0.0.0 --port 8080
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, UTC
import sqlite3, uuid, math

DB_PATH = "agent_knowledge.db"
app = FastAPI(title="Agent Knowledge Store")

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS knowledge (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                context TEXT NOT NULL,
                confidence REAL DEFAULT 0.5,
                confirmations INTEGER DEFAULT 0,
                contradictions INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                last_used_at TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_confidence ON knowledge(confidence DESC)")
        conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(content, context, content=knowledge, content_rowid=rowid)")
        conn.commit()

class KnowledgeEntry(BaseModel):
    content: str
    context: str
    initial_confidence: float = 0.5

class FeedbackPayload(BaseModel):
    confirmed: bool

@app.on_event("startup")
def startup():
    init_db()

@app.post("/api/query")
def query_knowledge(payload: dict):
    query_text = payload.get("context", "")
    min_confidence = payload.get("min_confidence", 0.5)
    max_results = payload.get("max_results", 10)
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT k.* FROM knowledge k
            JOIN knowledge_fts fts ON k.rowid = fts.rowid
            WHERE fts.knowledge_fts MATCH ?
            AND k.confidence >= ?
            ORDER BY k.confidence DESC LIMIT ?
        """, (query_text, min_confidence, max_results)).fetchall()
        for row in rows:
            conn.execute("UPDATE knowledge SET last_used_at = ? WHERE id = ?",
                         (datetime.now(UTC).isoformat(), row["id"]))
        conn.commit()
    return {"entries": [dict(row) for row in rows]}

@app.post("/api/propose")
def propose_knowledge(entry: KnowledgeEntry):
    eid = str(uuid.uuid4())
    status = "approved" if entry.initial_confidence >= 0.8 else "pending_review"
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT INTO knowledge (id, content, context, confidence, created_at) VALUES (?, ?, ?, ?, ?)",
                     (eid, entry.content, entry.context, entry.initial_confidence, datetime.now(UTC).isoformat()))
        conn.execute("INSERT INTO knowledge_fts(rowid, content, context) SELECT rowid, content, context FROM knowledge WHERE id = ?", (eid,))
        conn.commit()
    return {"id": eid, "status": status}

@app.post("/api/feedback/{entry_id}")
def record_feedback(entry_id: str, payload: FeedbackPayload):
    with sqlite3.connect(DB_PATH) as conn:
        if payload.confirmed:
            conn.execute("UPDATE knowledge SET confirmations = confirmations + 1, confidence = MIN(0.99, confidence + 0.05), last_used_at = ? WHERE id = ?",
                         (datetime.now(UTC).isoformat(), entry_id))
        else:
            conn.execute("UPDATE knowledge SET contradictions = contradictions + 1, confidence = MAX(0.01, confidence - 0.15) WHERE id = ?", (entry_id,))
        conn.commit()
    return {"ok": True}
