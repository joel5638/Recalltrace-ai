"""Durable approval checkpoints using LangGraph interrupts."""
import os, sqlite3, json
from datetime import datetime, timezone
from langgraph.graph import StateGraph, END
from langgraph.types import interrupt, Command
from typing import TypedDict
from . import store

class ReviewState(TypedDict, total=False):
    session: str
    lot: str
    action: str
    decision: str
    result: str

def gate(state: ReviewState):
    decision = interrupt({"lot": state["lot"], "action": state["action"], "question": "Approve this proposal?"})
    if decision not in ("approved", "rejected"):
        raise ValueError("Invalid decision")
    return {"decision": decision}

def record(state: ReviewState):
    return {"result": "Decision recorded. No external systems were changed."}

builder=StateGraph(ReviewState)
builder.add_node("approval", gate)
builder.add_node("record", record)
builder.set_entry_point("approval")
builder.add_edge("approval", "record")
builder.add_edge("record", END)

async def start_review(session: str, lot: str, action: str):
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
    async with AsyncSqliteSaver.from_conn_string(os.getenv("RECALLTRACE_CHECKPOINT_DB", "recalltrace-checkpoints.db")) as saver:
        graph=builder.compile(checkpointer=saver)
        config={"configurable": {"thread_id": session}}
        result=await graph.ainvoke({"session":session,"lot":lot,"action":action},config=config)
        return {"status":"pending" if "__interrupt__" in result else "complete", "result":str(result.get("result",""))}

async def resume_review(session: str, decision: str):
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
    async with AsyncSqliteSaver.from_conn_string(os.getenv("RECALLTRACE_CHECKPOINT_DB", "recalltrace-checkpoints.db")) as saver:
        graph=builder.compile(checkpointer=saver)
        result=await graph.ainvoke(Command(resume=decision),config={"configurable":{"thread_id":session}})
        return {"status":"complete","decision":result.get("decision"),"result":result.get("result")}
