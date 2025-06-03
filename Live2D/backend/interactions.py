"""
本模块定义了与 Live2D 互动相关的 FastAPI 路由和数据模型。
通过 POST /interaction 接口，前端可以提交用户与模型的交互信息（如点击部位、时间等），
后端根据交互内容返回相应的动作指令（如说话、表情变化、动作播放等）。
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()


class InteractionPayload(BaseModel):
    model_id: str
    hit_areas: List[str]  # 例如 ["Head"], ["Body", "Arm"]
    timestamp: str


class BackendAction(BaseModel):
    type: str  # 例如 "talk", "change_expression", "play_motion"
    expression: Optional[str] = None
    group: Optional[str] = None
    index: Optional[int] = 0 # 如果需要播放特定索引的动作
    priority: Optional[int] = 3  # 动作优先级 (1=IDLE, 2=NORMAL, 3=FORCE)


class InteractionResponse(BaseModel):
    status: str
    action: Optional[BackendAction] = None  # 更结构化的动作指令


@router.post("/interaction", response_model=InteractionResponse)
async def handle_live2d_interaction(payload: InteractionPayload):
    print(
        f"Received interaction for model '{payload.model_id}': Hit on {payload.hit_areas} at {payload.timestamp}")

    backend_action = None

    if "Head" in payload.hit_areas:
        backend_action = BackendAction(
            type="talk",
            expression="Happy")

    elif "Body" in payload.hit_areas:
        backend_action = BackendAction(
            type="motion",
            group="Tap@Body",
        )

    if backend_action:
        return InteractionResponse(status="success", action=backend_action)
