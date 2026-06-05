"""AI 宗门争霸 - 主应用入口"""
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.websockets import WebSocket, WebSocketDisconnect

from app.core.config import settings
from app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="AI 宗门争霸",
    description="电子蛐蛐式大模型 Agent 沙盒游戏",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import worlds, turns, audience, settings, leaderboard
app.include_router(worlds.router)
app.include_router(turns.router)
app.include_router(audience.router)
app.include_router(settings.router)
app.include_router(leaderboard.router)


# WebSocket connections
active_connections: dict[str, list[WebSocket]] = {}


@app.websocket("/ws/worlds/{world_id}")
async def world_websocket(websocket: WebSocket, world_id: str):
    await websocket.accept()
    if world_id not in active_connections:
        active_connections[world_id] = []
    active_connections[world_id].append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle client messages if needed
    except WebSocketDisconnect:
        active_connections[world_id].remove(websocket)
        if not active_connections[world_id]:
            del active_connections[world_id]


async def broadcast_turn(world_id: str, message: dict):
    """向所有连接广播回合结果"""
    if world_id in active_connections:
        for ws in active_connections[world_id]:
            try:
                await ws.send_json(message)
            except Exception:
                pass


@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": "AI 宗门争霸"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
