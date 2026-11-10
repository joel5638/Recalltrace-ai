"""Authenticated bidirectional audio relay for OpenAI Realtime API.
Browser sends/receives base64 PCM16 audio events over WebSocket.
"""
import asyncio,json,os
from fastapi import APIRouter,WebSocket,WebSocketDisconnect

router=APIRouter()

@router.websocket("/api/voice/realtime")
async def realtime(ws:WebSocket):
    key=os.getenv("OPENAI_API_KEY")
    if not key:
        await ws.close(code=1013,reason="Realtime API key not configured")
        return
    if os.getenv("RECALLTRACE_ENV","development")!="development":
        from .security import principal
        from fastapi import HTTPException
        try:principal(ws)
        except HTTPException:
            await ws.close(code=1008,reason="Unauthorized");return
    await ws.accept()
    import websockets
    model=os.getenv("OPENAI_REALTIME_MODEL","gpt-realtime")
    try:
        async with websockets.connect("wss://api.openai.com/v1/realtime?model="+model,additional_headers={"Authorization":"Bearer "+key},max_size=2**22) as remote:
            await remote.send(json.dumps({"type":"session.update","session":{"instructions":"You are RecallTrace, a supplier quality assistant. Never claim an external action was taken. Ask for a lot ID when needed. Do not invent evidence or shipment counts.","input_audio_format":"pcm16","output_audio_format":"pcm16","turn_detection":{"type":"server_vad"}}}))
            async def upstream():
                while True:
                    event=await ws.receive_text()
                    data=json.loads(event)
                    if data.get("type") not in ("input_audio_buffer.append","input_audio_buffer.commit","response.create","response.cancel","input_audio_buffer.clear"):
                        continue
                    if len(event)>100000:continue
                    await remote.send(event)
            async def downstream():
                async for event in remote:
                    await ws.send_text(event)
            tasks=[asyncio.create_task(upstream()),asyncio.create_task(downstream())]
            done,pending=await asyncio.wait(tasks,return_when=asyncio.FIRST_COMPLETED)
            for t in pending:t.cancel()
    except (WebSocketDisconnect,Exception):
        try:await ws.close()
        except RuntimeError:pass
