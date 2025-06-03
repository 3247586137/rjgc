"""
该模块用于通过 FastAPI 后端接口触发 Live2D 模型的指定动作。
主要功能:
- 提供 trigger_live2d_motion 函数，向后端发送动作指令，控制 Live2D 模型执行特定动作。
- 支持设置动作组名称、动作索引和优先级。
- 处理 HTTP 请求的异常情况，并输出相应的错误信息。
用法示例:
    trigger_live2d_motion(group_name="Tap@Body", motion_index=0, priority=3)

"""
import requests
import json

# FastAPI 后端的触发API端点 URL(可修改)
FASTAPI_TRIGGER_URL = "http://127.0.0.1:8000/api/v1/live2d/trigger-action"


def trigger_live2d_motion(group_name: str, motion_index: int, priority: int = 2):
    headers = {
        "Content-Type": "application/json"
    }

    command_data = {
        "command_type": "motion",
        "payload": {
            "group": group_name,
            "index": motion_index,
            "priority": priority
        }
    }

    try:
        response = requests.post(
            FASTAPI_TRIGGER_URL, headers=headers, data=json.dumps(command_data))
        response.raise_for_status()  # 如果HTTP请求返回错误状态码 (4xx or 5xx), 则抛出异常
        print(f"指令发送成功: {response.json()}")
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP 错误发生: {http_err} - {response.text}")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"连接错误发生: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        print(f"请求超时: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"请求发生其他错误: {req_err}")
    return None


if __name__ == "__main__":
    print(f"尝试触发 Live2D 模型的 'TapBody' 动作组中的第一个动作 (Hiyori_m04.motion3.json)...")
    trigger_live2d_motion(group_name="Tap@Body", motion_index=0, priority=3)

