"""
该脚本用于向 FastAPI 后端发送触发表情的 HTTP POST 请求。
通过 trigger_live2d_motion 函数，可以指定表情名称（如 "happy"），
后端收到请求后会根据命令类型和 payload 执行相应动作。
脚本包含异常处理，能捕获并输出请求过程中的各种错误信息。

！注意：由于表情触发后不会恢复，因此实际触发后需要手动恢复表情。
具体方法是指定表情名称为 "normal"。

"""
import requests
import json

# FastAPI 后端的触发API端点 URL(可修改)
FASTAPI_TRIGGER_URL = "http://127.0.0.1:8000/api/v1/live2d/trigger-action"


def trigger_live2d_motion(name: str):
    headers = {
        "Content-Type": "application/json"
    }

    command_data = {
        "command_type": "expression",
        "payload": {
            "name":name
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
    print(f"尝试触发表情...")
    trigger_live2d_motion(name="happy")
