import json
import os
import sqlite3
from pathlib import Path

DB = Path(os.getenv("RECALLTRACE_DB", "recalltrace.db"))

def connection():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    db.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, session TEXT, role TEXT, content TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
    db.execute("CREATE TABLE IF NOT EXISTS investigations (session TEXT PRIMARY KEY, lot TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS proposals (id INTEGER PRIMARY KEY AUTOINCREMENT, session TEXT, lot TEXT, action TEXT, status TEXT DEFAULT 'pending', created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
    db.execute("CREATE TABLE IF NOT EXISTS traces (id INTEGER PRIMARY KEY AUTOINCREMENT, session TEXT, step TEXT, status TEXT, elapsed_ms REAL, detail TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
    db.commit()
    return db

def history(session, limit=16):
    with connection() as db:
        rows = db.execute("SELECT role, content FROM messages WHERE session=? ORDER BY id DESC LIMIT ?", (session,limit)).fetchall()
    return [dict(x) for x in reversed(rows)]

def add_message(session, role, content):
    with connection() as db:
        db.execute("INSERT INTO messages(session,role,content) VALUES(?,?,?)",(session,role,content))

def get_lot(session):
    with connection() as db:
        row=db.execute("SELECT lot FROM investigations WHERE session=?",(session,)).fetchone()
    return row["lot"] if row else None

def set_lot(session,lot):
    with connection() as db:
        db.execute("INSERT INTO investigations(session,lot) VALUES(?,?) ON CONFLICT(session) DO UPDATE SET lot=excluded.lot",(session,lot))

def add_proposals(session,lot,actions):
    with connection() as db:
        existing={r["action"] for r in db.execute("SELECT action FROM proposals WHERE session=? AND lot=?",(session,lot))}
        for action in actions:
            if action not in existing:
                db.execute("INSERT INTO proposals(session,lot,action) VALUES(?,?,?)",(session,lot,action))

def proposals(session):
    with connection() as db:
        return [dict(r) for r in db.execute("SELECT id,lot,action,status FROM proposals WHERE session=? ORDER BY id DESC",(session,))]

def decide(session, proposal_id, decision):
    with connection() as db:
        result=db.execute("UPDATE proposals SET status=? WHERE id=? AND session=? AND status='pending'",(decision,proposal_id,session))
        return result.rowcount == 1

def add_trace(session,step,status,elapsed_ms,detail):
    with connection() as db:
        db.execute("INSERT INTO traces(session,step,status,elapsed_ms,detail) VALUES(?,?,?,?,?)",(session,step,status,elapsed_ms,detail))

def traces(session):
    with connection() as db:
        return [dict(r) for r in db.execute("SELECT step,status,elapsed_ms,detail,created_at FROM traces WHERE session=? ORDER BY id DESC LIMIT 25",(session,))]
