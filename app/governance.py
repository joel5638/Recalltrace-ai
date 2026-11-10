import os,re,time
from collections import defaultdict
from threading import Lock
from fastapi import HTTPException,Request

_lock=Lock(); _hits=defaultdict(list)

def check_access(request:Request):
    key=os.getenv('RECALLTRACE_API_KEY','').strip()
    if key and request.headers.get('x-api-key')!=key:raise HTTPException(401,'API key required')
    identity=request.headers.get('x-api-key') or (request.client.host if request.client else 'local')
    now=time.time()
    with _lock:
        _hits[identity]=[t for t in _hits[identity] if now-t<60]
        if len(_hits[identity])>=int(os.getenv('RECALLTRACE_RPM','60')):raise HTTPException(429,'Rate limit exceeded')
        _hits[identity].append(now)

def validate_input(message):
    if re.search(r'(?i)(ignore (all )?(previous|system) instructions|reveal (your )?(system prompt|api key))',message):
        raise HTTPException(400,'Request contains disallowed instruction patterns')
