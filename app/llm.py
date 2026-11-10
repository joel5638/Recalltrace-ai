import os
import httpx

async def complete(messages, temperature=0):
    key=os.getenv("OPENAI_API_KEY","").strip()
    if not key:
        return None
    url=os.getenv("OPENAI_BASE_URL","https://api.openai.com/v1").rstrip("/")+"/chat/completions"
    payload={"model":os.getenv("OPENAI_MODEL","gpt-4o-mini"),"messages":messages,"temperature":temperature,"max_tokens":650}
    try:
        async with httpx.AsyncClient(timeout=25) as client:
            response=await client.post(url,headers={"Authorization":f"Bearer {key}"},json=payload)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
    except (httpx.HTTPError,KeyError,IndexError,TypeError,ValueError):
        return None
