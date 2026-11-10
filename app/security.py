"""OIDC JWT verification for deployed mode and local developer mode."""
import os
from fastapi import HTTPException,Request

def principal(request:Request):
    issuer=os.getenv("OIDC_ISSUER")
    if not issuer:
        if os.getenv("RECALLTRACE_ENV","development")!="development":
            raise HTTPException(503,"OIDC_ISSUER required outside development")
        return {"sub":"local-developer","roles":["investigator","approver","admin"]}
    from jose import jwt,JWTError
    from jose.utils import base64url_decode
    import httpx
    auth=request.headers.get("authorization","")
    if not auth.startswith("Bearer "):raise HTTPException(401,"Bearer token required")
    token=auth[7:]
    try:
        with httpx.Client(timeout=5) as c:
            cfg=c.get(issuer.rstrip("/")+"/.well-known/openid-configuration");cfg.raise_for_status()
            jwks=c.get(cfg.json()["jwks_uri"]);jwks.raise_for_status()
        claims=jwt.decode(token,jwks.json(),algorithms=["RS256"],audience=os.environ["OIDC_AUDIENCE"],issuer=issuer)
        return {"sub":claims["sub"],"roles":claims.get("roles",[])}
    except (JWTError,KeyError,ValueError,httpx.HTTPError):raise HTTPException(401,"Invalid token")

def require_role(role):
    def guard(request:Request):
        user=principal(request)
        if role not in user["roles"] and "admin" not in user["roles"]:raise HTTPException(403,"Insufficient role")
        return user
    return guard
