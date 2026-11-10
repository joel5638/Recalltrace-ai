from pathlib import Path
from uuid import UUID
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from .security import require_role
from . import store
from .enterprise_agent import chat
from .governance import check_access,validate_input
from fastapi import Request,Depends
from fastapi.responses import StreamingResponse
import json
from .data import DOCUMENTS, LOTS

app=FastAPI(title="RecallTrace AI",version="2.0.0")

class Message(BaseModel):
    session: str = Field(min_length=1,max_length=80)
    message: str = Field(min_length=1,max_length=3000)

class Decision(BaseModel):
    session: str
    status: str

def valid_session(value):
    try: UUID(value)
    except ValueError: raise HTTPException(400,"Session must be a UUID")

@app.get("/",response_class=HTMLResponse)
def index():
    return (Path(__file__).parent/"index.html").read_text()

@app.post("/api/chat")
async def send(payload:Message, request:Request):
    check_access(request)
    require_role("investigator")(request)
    validate_input(payload.message)
    valid_session(payload.session)
    return await chat(payload.session,payload.message.strip())

@app.get("/api/session/{session}")
def session_data(session:str, user=Depends(require_role("investigator"))):
    valid_session(session)
    return {"messages":store.history(session,100),"lot":store.get_lot(session),"proposals":store.proposals(session),"traces":store.traces(session)}

@app.post("/api/proposals/{proposal_id}")
def approve(proposal_id:int,payload:Decision, request:Request):
    check_access(request)
    require_role("approver")(request)
    valid_session(payload.session)
    if payload.status not in ("approved","rejected"): raise HTTPException(400,"Invalid decision")
    if not store.decide(payload.session,proposal_id,payload.status): raise HTTPException(404,"Pending proposal not found")
    return {"proposals":store.proposals(payload.session),"notice":"Decision recorded locally. No external action was executed."}

@app.get("/api/evidence/{document_id}")
def evidence(document_id:str, user=Depends(require_role("investigator"))):
    if document_id not in DOCUMENTS: raise HTTPException(404,"Evidence not found")
    return {"id":document_id,**DOCUMENTS[document_id]}

@app.get("/api/lots")
def lots(user=Depends(require_role("investigator"))): return {"lots":list(LOTS)}

@app.get("/health")
def health(): return {"status":"ok"}

@app.get("/api/overview")
def overview(user=Depends(require_role("investigator"))):
    return {"lots":[{"id":key,"component":item["component"],"affected":item["affected"],"shipped":item["shipped"],"on_hand":item["on_hand"],"customers":len(item["customers"]),"evidence_count":len(item["evidence"])} for key,item in LOTS.items()],"totals":{"affected":sum(v["affected"] for v in LOTS.values()),"shipped":sum(v["shipped"] for v in LOTS.values()),"on_hand":sum(v["on_hand"] for v in LOTS.values())}}

@app.get("/api/lot/{lot_id}")
def lot_detail(lot_id:str, user=Depends(require_role("investigator"))):
    lot_id=lot_id.upper()
    if lot_id not in LOTS: raise HTTPException(404,"Lot not found")
    return {"id":lot_id,**LOTS[lot_id],"evidence_details":[{"id":doc_id,**DOCUMENTS[doc_id]} for doc_id in LOTS[lot_id]["evidence"]]}

@app.post('/api/chat/stream')
async def stream(payload:Message,request:Request):
    check_access(request)
    require_role("investigator")(request)
    validate_input(payload.message)
    valid_session(payload.session)
    async def events():
        yield 'event: status\ndata: {"step":"planning"}\n\n'
        result=await chat(payload.session,payload.message.strip())
        yield 'event: result\ndata: '+json.dumps(result)+'\n\n'
    return StreamingResponse(events(),media_type='text/event-stream')

@app.get('/api/metrics')
def metrics(request:Request, user=Depends(require_role("admin"))):
    check_access(request)
    with store.connection() as db:
        counts={table:db.execute('SELECT COUNT(*) FROM '+table).fetchone()[0] for table in ('messages','proposals','traces')}
        statuses=[dict(r) for r in db.execute('SELECT status,COUNT(*) AS count FROM traces GROUP BY status')]
    return {'counts':counts,'trace_statuses':statuses,'mode':'llm' if __import__('os').getenv('OPENAI_API_KEY') else 'local'}


from .observability import install
from .security import require_role
from .voice import router as voice_router
from .workflow import start_review, resume_review
from fastapi import Depends

app.include_router(voice_router)
install(app)

class ReviewRequest(BaseModel):
    session: str
    lot: str
    action: str = Field(min_length=3,max_length=500)

class ReviewDecision(BaseModel):
    decision: str

@app.post("/api/workflows/review")
async def create_review(payload:ReviewRequest,user=Depends(require_role("investigator"))):
    valid_session(payload.session)
    if payload.lot not in LOTS:raise HTTPException(404,"Unknown lot")
    return await start_review(payload.session,payload.lot,payload.action)

@app.post("/api/workflows/{session}/resume")
async def resume(session:str,payload:ReviewDecision,user=Depends(require_role("approver"))):
    valid_session(session)
    if payload.decision not in ("approved","rejected"):raise HTTPException(400,"Invalid decision")
    return await resume_review(session,payload.decision)

@app.post("/api/admin/reindex")
def reindex(user=Depends(require_role("admin"))):
    from .vector_store import index_documents
    return {"indexed":index_documents()}

@app.get("/api/admin/audit")
def audit(user=Depends(require_role("admin"))):
    with store.connection() as db:
        rows=db.execute("SELECT session,step,status,elapsed_ms,created_at FROM traces ORDER BY id DESC LIMIT 100").fetchall()
    return {"events":[dict(r) for r in rows]}
