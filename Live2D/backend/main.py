"""
本文件为 Live2D 后端 API 的主入口，基于 FastAPI 实现。
- 提供静态资源服务（/static）
- 支持 WebSocket 实时通信（/ws/live2d）
- 提供 RESTful API 用于触发模型动作（/api/v1/live2d/trigger-action）
- 支持跨域请求（CORS）
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any
import json


from fastapi import WebSocket, WebSocketDisconnect
import interactions as interactions_router


app = FastAPI(title="Live2D Backend API")


# --- CORS 中间件 ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- 静态文件服务 ---
BASE_DIR = Path(__file__).resolve().parent
STATIC_FILES_DIR = BASE_DIR / "static"  # 指向 backend/app/static/

# 将整个 /static 目录映射到 URL 路径 /static
app.mount("/static", StaticFiles(directory=STATIC_FILES_DIR),
          name="static_assets")

# --- API 路由 ---
app.include_router(interactions_router.router,
                   prefix="/api/v1/live2d", tags=["Live2D Interactions"])


@app.get("/")
async def read_root():
    return {"message": "Welcome! Model assets are served from /static/"}


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(
            f"New client connected: {websocket.client}. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(
                f"Client disconnected: {websocket.client}. Total clients: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        print(
            f"Broadcasting message: {message} to {len(self.active_connections)} clients")
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Error sending to {connection.client}: {e}")
                # 可以选择在这里移除无效连接
                # self.disconnect(connection)


manager = ConnectionManager()


@app.websocket("/ws/live2d")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"Client {websocket.client} disconnected (WebSocketDisconnect)")
    except Exception as e:
        manager.disconnect(websocket)
        print(f"Client {websocket.client} disconnected due to error: {e}")


# --- 一个示例 API 端点，用于从后端触发动作 ---
class ModelCommand(BaseModel):
    command_type: str  # e.g., "motion", "expression"
    payload: Dict[str, Any]


@app.post("/api/v1/live2d/trigger-action")
async def trigger_live2d_action(command: ModelCommand):
    """
    一个HTTP端点，用于从其他后端服务或管理员界面触发模型动作。
    命令会通过WebSocket广播给所有连接的前端。
    """
    message_to_send = json.dumps({
        "type": command.command_type,
        "data": command.payload
    })
    await manager.broadcast(message_to_send)
    return {"message": "Command sent to connected clients", "command": command}

