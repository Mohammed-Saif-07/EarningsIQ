import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/ws/live")
async def live(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            await websocket.send_text(json.dumps({
                "type": "agent_status",
                "time": datetime.now(timezone.utc).isoformat(),
                "agents": [
                    {"name": "watcher", "status": "ready", "pods": 1},
                    {"name": "ingest", "status": "ready", "pods": 1},
                    {"name": "nlp", "status": "ready", "pods": 2},
                    {"name": "research", "status": "ready", "pods": 1},
                    {"name": "report", "status": "ready", "pods": 1},
                ],
            }))
            await asyncio.sleep(3)
    except WebSocketDisconnect:
        return
