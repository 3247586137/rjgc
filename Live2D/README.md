# Live2D 互动角色系统 - README

本项目是一个全栈的 Live2D 互动角色解决方案，结合了 FastAPI 后端服务与 Vue.js 3 前端组件。它允许用户通过网页与 Live2D 模型进行实时互动，后端能够控制模型的动作、表情、语音播放，并实现了基于 Web Audio API 的口型同步功能。

## 主要功能

- **Live2D 模型展示**: 在网页中流畅渲染和展示 Live2D Cubism 4 模型。
- **后端驱动交互**: 后端通过 RESTful API 和 WebSocket 实时控制模型的行为。
- **用户点击互动**: 前端捕捉用户对模型的点击事件，并将其发送至后端，后端可根据交互逻辑触发相应反馈。
- **动作与表情控制**: 支持通过指令播放模型预设的动作和切换表情。
- **语音播放与口型同步**: 模型能够根据后端提供的音频文件，实时匹配嘴型动画，实现自然的说话效果。
- **静态资源服务**: 后端负责托管 Live2D 模型文件、音频文件等静态资源。
- **可定制化**: 前端组件支持通过 props 更换模型、调整初始缩放等。

## 技术栈

### 后端 (Backend)

- **Python 3.x**: 主要编程语言。
- **FastAPI**: 高性能 Python Web 框架，用于构建 RESTful API 和 WebSocket 服务。
- **Uvicorn**: ASGI 服务器，用于运行 FastAPI 应用。
- **Pydantic**: 用于数据验证和 API 参数定义。
- **Requests**: (用于 `api_example` 中的示例脚本) Python HTTP 库。

### 前端 (Frontend)

- **Vue.js 3**: 渐进式 JavaScript 框架，用于构建用户界面。
- **PIXI.js (v6.x)**: 高性能 2D WebGL 渲染引擎，作为 Live2D 的渲染基础。
- **pixi-live2d-display**: PIXI.js 的 Live2D 插件，专门用于加载和渲染 Live2D Cubism 模型。
- **Axios**: 基于 Promise 的 HTTP 客户端，用于前端与后端 API 的通信。
- **Web Audio API**: 浏览器内置的音频处理接口，用于实现口型同步中的音频分析。
- **live2dcubismcore.min.js**: Live2D 官方提供的 Cubism Core SDK，是模型运行的核心。

## 项目结构（概览）

```
live2d-interactive-system/
├── backend/                 # 后端 FastAPI 项目
│   ├── main.py              # FastAPI 主应用入口，定义 API 路由和 WebSocket 服务
│   ├── interactions.py      # 处理 Live2D 互动相关的 API 路由
│   ├── api_example/         # 调用后端 API 的 Python 示例脚本
│   │   ├── request_motion.py
│   │   ├── request_expression.py
│   │   └── request_speak.py
│   └── static/              # 存放 Live2D 模型、音频等静态资源的目录
│       └── hiyori_pro_zh/   # 示例模型 Hiyori 的资源
│           └── runtime/
│               └── hiyori_pro_t11.model3.json
│
└── frontend/                # 前端 Vue.js 项目
    ├── public/
    │   ├── index.html       # 单页应用主 HTML 文件
    │   └── live2dcubismcore.min.js # Live2D Cubism Core SDK (需手动放置)
    ├── src/
    │   ├── Live2D.vue       # Live2D 核心 Vue 组件
    │   ├── main.js          # Vue 应用入口文件
    │   └── services/
    │       └── api.js       # Axios 封装，用于与后端 API 通信
    └── package.json         # 项目依赖和脚本配置
```

## 环境准备与安装

### 后端 (Backend)

1.  **Python 环境**: 确保已安装 Python 3.7 或更高版本。
2.  **安装依赖**: 进入 `backend` 目录，运行：
    ```bash
    pip install fastapi uvicorn pydantic requests
    ```

### 前端 (Frontend)

1.  **Node.js 环境**: 确保已安装 Node.js (建议版本 16 及以上) 和 npm (或 yarn)。
    可以通过以下命令检查版本：
    ```sh
    node -v
    npm -v
    ```
    如未安装，请前往 [Node.js 官网](https://nodejs.org/) 下载并安装。
2.  **安装依赖**: 进入 `frontend` 目录，运行：
    ```bash
    npm install pixi.js@6.x pixi-live2d-display axios
    # 如果项目是通过 Vue CLI 创建的，并且有 package-lock.json 或 yarn.lock，
    # 最好运行 npm install 或 yarn install 来安装所有在 lock 文件中记录的依赖。
    ```
3.  **Live2D Cubism Core SDK**:
    - 从 [Live2D 官网](https://www.live2d.com/en/download/cubism-sdk/) 下载 "Cubism Core SDK for Web"。
    - 解压后，找到 `Core` 目录下的 `live2dcubismcore.min.js` 文件。
    - 将此 `live2dcubismcore.min.js` 文件复制到 `frontend/public/` 目录下。
    - **此文件必须存在且能被正确加载，否则 Live2D 模型将无法渲染。**

## 运行项目

### 1. 启动后端服务

进入 `backend` 目录，运行：

```bash
uvicorn main:app --reload
```

- `--reload`: 开发模式，当代码文件更改时，服务器会自动重新加载。
  如果需要指定主机和端口，可以使用 `--host` 和 `--port` 参数。

后端服务启动后，默认监听 `http://0.0.0.0:8000/`。
静态资源（如 Live2D 模型文件、音频文件）应放置在 `backend/static/` 目录下。例如，如果有一个模型位于 `backend/static/my_model/my_model.model3.json`，则其访问 URL 为 `http://localhost:8000/static/my_model/my_model.model3.json`。

### 2. 启动前端开发服务

进入 `frontend` 目录，

首先，确保已安装前端依赖：

```bash
npm install
```

然后，运行以下命令启动前端开发服务器：

```bash
npm run serve
```

前端开发服务器默认运行在 `http://localhost:9001` (具体请查看 `frontend/package.json` 中 `scripts.serve` 的配置或启动时的控制台输出)。

成功启动前后端服务后，在浏览器中打开前端应用的地址即可看到 Live2D 模型。

## 使用方法与功能说明

### 1. 前端 Live2D 组件 (`Live2D.vue`)

前端的核心是 `src/Live2D.vue` 组件，它负责加载和显示 Live2D 模型，并处理与后端的通信。

#### 在其他 Vue 组件中使用:

```vue
<template>
  <div id="app">
    <Live2D
      :modelUrl="'http://localhost:8000/static/hiyori_pro_zh/runtime/hiyori_pro_t11.model3.json'"
      :initialScale="0.2"
    />
  </div>
</template>

<script>
import Live2D from "./components/Live2D.vue"; // 假设 Live2D.vue 在 components 目录下

export default {
  name: "App",
  components: {
    Live2D,
  },
};
</script>
```

#### Props:

- `modelUrl` (String, **必需**): Live2D 模型的 `.model3.json` 文件的完整 URL。前端将从此 URL 加载模型。
- `initialScale` (Number, 可选): 模型初始的缩放比例。默认值为 `0.2`。

### 2. 后端 API 与 WebSocket 控制

后端提供了两种方式来控制前端的 Live2D 模型：通过 RESTful API 发送一次性指令，或通过 WebSocket 进行实时推送。

#### a. 通过 REST API 触发模型行为

- **通用接口**: `POST /api/v1/live2d/trigger-action`
- **请求体 (JSON)**:

  ```json
  {
    "command_type": "motion" | "expression" | "speak", // 指令类型
    "payload": { /* 特定于 command_type 的参数对象 */ }
  }
  ```

- **触发动作 (motion)**:

  ```json
  // 请求体示例
  {
    "command_type": "motion",
    "payload": {
      "group": "Idle", // 动作组名称 (必需)
      "index": 0, // 动作在组内的索引 (可选, 不提供则随机播放组内动作)
      "priority": 2 // 动作优先级 (可选, 1:低, 2:中, 3:高)
    }
  }
  ```

  Python 示例: `backend/api_example/request_motion.py`

- **触发表情 (expression)**:

  ```json
  // 请求体示例
  {
    "command_type": "expression",
    "payload": {
      "name": "happy" // 表情名称 (必需)
    }
  }
  ```

  > **注意**: 表情触发后通常不会自动恢复为默认表情，需要再次发送指令（例如，`name: "normal"`）来改变或恢复。
  > Python 示例: `backend/api_example/request_expression.py`

- **触发说话与口型同步 (speak)**:
  ```json
  // 请求体示例
  {
    "command_type": "speak",
    "payload": {
      "audioUrl": "http://localhost:8000/static/audio/sample.mp3" // 完整的、前端可访问的音频文件URL (必需)
    }
  }
  ```
  Python 示例: `backend/api_example/request_speak.py`

#### b. 前端用户交互反馈 (REST API)

当用户在前端点击 Live2D 模型时，前端会向以下接口发送交互信息：

- **接口**: `POST /api/v1/live2d/interaction`
- **请求体 (JSON) 示例**:
  ```json
  {
    "model_id": "hiyori_pro_zh", // 当前模型的ID (通常从模型URL中解析得到)
    "hit_areas": ["Head"], // 被点击的区域名称数组 (例如 "Head", "Body")
    "timestamp": "2025-05-17T12:00:00Z" // 点击事件发生的时间戳 (ISO 8601格式)
  }
  ```
- 后端接收到此信息后，可以根据预设的逻辑（例如，点击头部播放特定语音或动作）通过 WebSocket 向前端推送相应的指令。
- **返回示例**:
  ```json
  {
    "status": "success",
    "action": {
      // 后端决定执行的动作，会通过WebSocket发送给前端
      "type": "motion", // 或 "expression", "speak"
      "group": "Tap@Head", // 示例
      "index": 0
    }
  }
  ```

#### c. WebSocket 实时通信

- **WebSocket 地址**: `ws://localhost:8000/ws/live2d` (请根据后端实际运行地址和端口进行调整)
- **用途**: 后端可以主动向所有连接的 WebSocket 客户端（即前端页面）推送指令，以实时控制模型的行为。
- **消息格式 (后端 -> 前端)**:

  ```json
  // 示例1: 推送动作指令
  {
    "type": "motion", // 对应 API 中的 command_type
    "data": {         // 对应 API 中的 payload
      "group": "Idle",
      "index": 1
    }
  }

  // 示例2: 推送说话指令
  {
    "type": "speak",
    "data": {
      "audioUrl": "http://localhost:8000/static/audio/greeting.wav"
    }
  }
  ```

  前端的 `Live2D.vue` 组件会监听来自此 WebSocket 的消息，并通过 `executeModelCommand` 方法解析并执行这些指令。

### 3. 口型同步功能详解

本项目的核心亮点之一是实现了 Live2D 模型的实时口型同步。

- **触发方式**: 后端通过 WebSocket 或 API 发送 `speak` 类型的指令，并在 `data` (或 `payload`) 中提供一个 `audioUrl`，该 URL 指向一个前端可访问的音频文件。
- **前端实现流程**:
  1.  **接收指令**: 前端 `Live2D.vue` 组件接收到 `speak` 指令。
  2.  **音频加载与解码**: 使用 `fetch` API 从 `audioUrl` 下载音频数据，并通过 Web Audio API 的 `audioContext.decodeAudioData` 将其解码为可播放的 `AudioBuffer`。
  3.  **音频节点设置**: 创建 `AudioBufferSourceNode` (用于播放解码后的音频) 和 `AnalyserNode` (用于实时分析音频数据)。将它们连接起来：`SourceNode -> AnalyserNode -> audioContext.destination` (扬声器)。
  4.  **同步循环启动**: 音频通过 `SourceNode.start(0)` 开始播放。同时，启动一个名为 `updateMouthLoop` 的函数，该函数通过 `requestAnimationFrame` 实现与浏览器渲染同步的循环。
  5.  **实时分析与更新**: 在 `updateMouthLoop` 的每一帧中：
      - 使用 `AnalyserNode.getByteFrequencyData()` 获取当前音频帧的频率数据。
      - 根据这些频率数据计算出一个近似的当前音量值（例如，取频率数据的平均值）。
      - 将计算出的音量值通过一个映射函数（通常是 `音量 / 敏感度系数`）转换为一个介于 0 (嘴巴完全闭合) 和 1 (嘴巴完全张开) 之间的值。
      - 使用 `currentModelInstance.internalModel.coreModel.setParameterValueById(this.mouthParameterId, mouthOpenValue)` 更新 Live2D 模型中控制嘴巴开合的参数（通常是 `ParamMouthOpenY`）。
  6.  **结束与清理**: 当音频播放完毕时 (`SourceNode.onended` 事件触发)，停止 `updateMouthLoop` 循环，将嘴巴参数设回 0 (闭合)，并断开和清理相关的 Web Audio API 节点。
- **前端可配置参数** (在 `Live2D.vue` 的 `data` 对象中):
  - `mouthParameterId`: (String) Live2D 模型中控制嘴巴上下开合的参数的 ID。默认值为 `"ParamMouthOpenY"`。你需要根据你使用的具体模型的参数名进行调整。
  - `lipSyncSensitivity`: (Number) 口型同步对音量的敏感度。这个值越小，模型嘴巴对较小的声音反应就越灵敏（即更容易张开，或张得更大）。默认值为 `30`。你可以根据音频的整体响度和期望的口型效果来调整此值。

### 4. Hiyori 模型特定内容参考 (示例)

后端 README 中提供了 `hiyori_pro_zh` 模型的可用表情、动作和命中区域列表，这些可以作为你测试 API 和 WebSocket 功能的参考。

- **可选表情 (Expressions)**: 例如 `angry`, `surprise`, `sad`, `happy`, `normal` 等。通过 `name` 字段指定。
- **可选动作 (Motions)**: 通过 `group` (动作组名称) 和 `index` (在该组中的索引) 指定。例如 `Idle` 组有多个待机动作。
- **命中区域 (HitAreas)**: 例如 `Body`。前端用户点击这些区域会触发 `interaction` API 调用。

要了解特定模型支持的所有参数、动作和表情，最准确的方法是查阅该模型的 `.model3.json` 文件。

## 注意事项

- **Live2D Cubism Core SDK**: `frontend/public/live2dcubismcore.min.js` 文件是运行 Live2D 模型的关键。请确保已从 Live2D 官网下载并正确放置到指定目录。如果此文件缺失或加载失败，模型将无法渲染。
- **CORS (跨源资源共享)**: 后端 FastAPI 应用已通过 `CORSMiddleware` 配置为允许所有来源 (`allow_origins=["*"]`) 的跨域请求。这对于本地开发通常足够。在生产环境中，你可能希望将其限制为特定的前端域名。
- **浏览器自动播放策略**: 现代浏览器对音频/视频的自动播放有严格限制。通常，`AudioContext` 的启动或恢复 (通过 `audioContext.resume()`) 以及音频的首次播放，必须由用户的主动交互（如点击页面上的按钮）触发。前端代码中已包含尝试在 `initAudioContext` 中 `resume()` 的逻辑，但确保首次播放与用户手势关联是最佳实践。
- **资源 URL**: 所有传递给前端的 `modelUrl` 和 `audioUrl` 都必须是前端浏览器能够直接访问到的完整、有效的 URL。后端通过 `StaticFiles` 挂载 `static` 目录，使其内容可以通过 HTTP 访问，这是提供这些资源的一种方式。
- **WebSocket 连接**: 确保前端连接的 WebSocket URL (`ws://localhost:8000/ws/live2d`) 与后端 FastAPI 服务实际运行的地址和端口以及定义的 WebSocket 路由匹配。

## 常见问题与故障排除

- **模型加载失败**:

  1.  **检查 `modelUrl`**: 确认前端 `Live2D.vue` 组件接收到的 `modelUrl` prop 是否是一个指向 `.model3.json` 文件的正确且可访问的 URL。
  2.  **后端静态服务**: 确保后端 FastAPI 服务已启动，并且其 `static/` 目录下的模型文件可以通过浏览器直接访问。
  3.  **`live2dcubismcore.min.js`**: 打开浏览器开发者工具（通常按 F12），查看控制台 (Console) 和网络 (Network) 标签页。确认 `live2dcubismcore.min.js` 文件是否成功加载，并且没有相关的 JavaScript 错误。
  4.  **控制台错误**: 仔细阅读浏览器控制台中的任何错误信息，它们通常会给出模型加载失败的具体原因。

- **音频无法播放 / 口型不同步**:

  1.  **用户交互**: 确认用户在尝试播放音频（特别是首次）之前，是否已经与页面进行过至少一次点击等交互操作，以满足浏览器的自动播放策略。
  2.  **`audioUrl`**: 检查后端通过 WebSocket 或 API 发送的 `audioUrl` 是否正确，以及该 URL 指向的音频文件是否在服务器上存在且可以通过浏览器直接访问。
  3.  **Web Audio API 错误**: 查看浏览器控制台是否有与 Web Audio API 相关的错误或警告（例如 `AudioContext was not allowed to start`）。
  4.  **口型参数与敏感度**: 确认 `Live2D.vue` 中的 `mouthParameterId` 与你模型实际的嘴部参数名一致。尝试调整 `lipSyncSensitivity` 的值。

- **WebSocket 连接失败或断开**:
  1.  **后端服务**: 确保后端 FastAPI 服务已正常启动，并且定义的 WebSocket 端点 (`/ws/live2d`) 正在监听。
  2.  **URL 匹配**: 检查前端代码中用于连接 WebSocket 的 URL 是否与后端服务运行的地址、端口以及 WebSocket 路由完全匹配。
  3.  **网络问题**: 检查是否存在网络防火墙、代理或其他网络配置问题可能阻止 WebSocket 连接。
  4.  **控制台与日志**: 查看浏览器控制台和后端服务器的日志，查找有关 WebSocket 连接失败或断开的详细错误信息。前端已包含简单的 5 秒自动重连逻辑。

---

## 附录：Hiyori 模型可选表情与动作

### 可选表情（Expressions）

你可以通过 API 触发以下表情，`name` 字段即为调用参数：

| name     | 文件名             | 说明（可自定义） |
| -------- | ------------------ | ---------------- |
| angry    | angry.exp3.json    | 生气             |
| surprise | surprise.exp3.json | 惊讶             |
| sad      | sad.exp3.json      | 伤心             |
| happy    | ishappy.exp3.json  | 开心             |
| wuyu     | wuyu.exp3.json     | 无语             |
| xianqi   | xianqi.exp3.json   | 嫌弃             |
| yihuo    | yihuo.exp3.json    | 疑惑             |
| shy      | shy.exp3.json      | 害羞             |
| normal   | normal.exp3.json   | 普通/恢复默认    |

**触发表情示例：**

```python
from request_expression import trigger_live2d_motion

trigger_live2d_motion(name="happy")   # 触发“开心”表情
trigger_live2d_motion(name="normal")  # 恢复为普通表情
```

---

### 可选动作（Motions）

动作通过 `group`（动作组）和 `index`（索引）指定。下表为所有可用动作组及其索引：

| group      | index | 文件名                         |
| ---------- | ----- | ------------------------------ |
| Idle       | 0     | motion/hiyori_m01.motion3.json |
| Idle       | 1     | motion/hiyori_m02.motion3.json |
| Idle       | 2     | motion/hiyori_m05.motion3.json |
| Flick      | 0     | motion/hiyori_m03.motion3.json |
| FlickDown  | 0     | motion/hiyori_m04.motion3.json |
| FlickUp    | 0     | motion/hiyori_m06.motion3.json |
| Tap        | 0     | motion/hiyori_m07.motion3.json |
| Tap        | 1     | motion/hiyori_m08.motion3.json |
| Tap@Body   | 0     | motion/hiyori_m09.motion3.json |
| Flick@Body | 0     | motion/hiyori_m10.motion3.json |

**触发动作示例：**

```python
from request_motion import trigger_live2d_motion

# 触发 Tap@Body 动作组的第 0 个动作
trigger_live2d_motion(group_name="Tap@Body", motion_index=0, priority=3)

# 触发 Idle 动作组的第 1 个动作
trigger_live2d_motion(group_name="Idle", motion_index=1, priority=2)
```

---

### 命中区域（HitAreas）

| Id      | Name |
| ------- | ---- |
| HitArea | Body |

前端可通过点击 Body 区域触发相关互动。

---

如需更多细节，请参考 `static/hiyori_pro_zh/runtime/hiyori_pro_t11.model3.json` 文件内容。

## 参考

- [FastAPI 官方文档](https://fastapi.tiangolo.com/zh/)
- [Live2D 官方文档](https://docs.live2d.com/)
- [Vue CLI 配置参考](https://cli.vuejs.org/config/)
- [pixi-live2d-display 文档](https://github.com/guansss/pixi-live2d-display)
