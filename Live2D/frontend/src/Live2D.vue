<script>
// Vue 和 PIXI 相关库的导入
import * as PIXI from "pixi.js"; // 导入 PIXI.js 核心库
import { Live2DModel } from "pixi-live2d-display/cubism4"; // 导入 Live2D Cubism 4 模型的支持库
import api from "@/services/api"; // 导入自定义的 API 服务模块 (用于HTTP交互)

// 将 PIXI 挂载到 window 对象上，这是为了确保 pixi-live2d-display 内部能够正确访问到 PIXI 实例。
// 某些版本的 pixi-live2d-display 可能需要这样做。
window.PIXI = PIXI;

export default {
  // 组件的 props，用于接收父组件传递的数据
  props: {
    // Live2D 模型的 model3.json 文件 URL
    modelUrl: {
      type: String,
      // 默认模型 URL，确保这是一个浏览器可访问的、指向 FastAPI 静态服务或其他可访问服务器的完整 URL
      default:
        "http://localhost:8000/static/hiyori_pro_zh/runtime/hiyori_pro_t11.model3.json",
    },
    // 模型的初始缩放比例
    initialScale: {
      type: Number,
      default: 0.2, // 默认缩放为 0.2
    },
  },
  // 组件的响应式数据对象
  data() {
    return {
      pixiAppInstance: null, // PIXI 应用实例
      currentModelInstance: null, // 当前加载的 Live2D 模型实例
      isLoading: false, // 布尔值，表示模型是否正在加载中
      errorMsg: "", // 字符串，用于存储加载或运行时发生的错误信息
      backendMessage: "", // 字符串，用于显示通过 HTTP 后端交互或 WebSocket 指令返回的消息
      websocket: null, // WebSocket 连接实例

      // --- 口型同步相关数据属性 ---
      audioContext: null, // Web Audio API 的 AudioContext 实例，用于处理音频
      audioSourceNode: null, // 音频源节点 (AudioBufferSourceNode)，用于播放音频数据
      audioAnalyserNode: null, // 音频分析节点 (AnalyserNode)，用于实时分析音频数据以实现口型同步
      isSpeaking: false, // 布尔值，标记当前是否正在播放语音并进行口型同步
      lipSyncRequestId: null, // 存储 requestAnimationFrame 的 ID，用于在不需要时取消动画帧请求
      mouthParameterId: "ParamMouthOpenY", // Live2D 模型中控制嘴巴张开/闭合的参数 ID，通常是 'ParamMouthOpenY'
      lipSyncSensitivity: 30, // 口型同步对音量的敏感度，数值越小越敏感 (嘴巴张得越大)
    };
  },
  // 组件挂载到 DOM 后执行的异步钩子函数
  async mounted() {
    // 初始化 PIXI 应用并加载 Live2D 模型
    await this.initializeAndLoadModel();
    // 连接到 WebSocket 服务器
    this.connectWebSocket();
    // 添加窗口大小变化事件监听器，以便在窗口大小改变时调整模型
    window.addEventListener("resize", this.handleResize);
  },
  // 组件卸载前执行的钩子函数
  beforeUnmount() {
    // 清理工作：移除事件监听器，断开 WebSocket 连接，销毁 PIXI 资源，停止音频等
    window.removeEventListener("resize", this.handleResize);
    this.disconnectWebSocket(); // 断开 WebSocket
    this.cleanupPixi(); // 清理 PIXI 相关的资源
    this.stopSpeaking(); // 停止任何正在进行的语音播放和口型同步

    // 关闭 AudioContext
    if (this.audioContext && this.audioContext.state !== "closed") {
      this.audioContext
        .close()
        .then(() => {
          console.log("AudioContext 已被安全关闭。");
          this.audioContext = null; // 清理引用
        })
        .catch((err) => {
          console.error("关闭 AudioContext 时发生错误:", err);
        });
    }
  },
  // 监听 data 或 props 中属性变化的配置
  watch: {
    // 监听 modelUrl prop 的变化
    modelUrl(newUrl, oldUrl) {
      if (newUrl && newUrl !== oldUrl) {
        // 如果 modelUrl 发生变化，则重新初始化并加载新模型
        this.initializeAndLoadModel();
      }
    },
    // 监听 initialScale prop 的变化
    initialScale() {
      // 如果初始缩放比例发生变化，则调整模型的变换（位置、缩放）
      this.adjustModelTransform();
    }
  },
  // 组件的方法集合
  methods: {
    /**
     * 清理 PIXI.js 相关的资源。
     * 这包括销毁当前加载的 Live2D 模型实例和 PIXI 应用实例，
     * 以释放 WebGL 上下文、纹理等资源，防止内存泄漏。
     */
    cleanupPixi() {
      if (this.currentModelInstance) {
        this.currentModelInstance.destroy(); // 销毁 Live2D 模型
        this.currentModelInstance = null;
      }
      if (this.pixiAppInstance) {
        // 销毁 PIXI 应用实例
        // 第二个参数是一个选项对象，用于指定是否同时销毁子对象、纹理和基础纹理
        this.pixiAppInstance.destroy(true, { // 设置为 true 表示移除 canvas 元素
          children: true,
          texture: true,
          baseTexture: true,
        });
        this.pixiAppInstance = null;
      }
    },

    /**
     * 异步方法：初始化 PIXI 应用并加载 Live2D 模型。
     * 1. 设置加载状态，清空错误消息和后端消息。
     * 2. 清理任何已存在的 PIXI 实例。
     * 3. 检查 canvas 元素是否存在。
     * 4. 创建新的 PIXI.Application 实例，并配置视图、自动启动、自适应窗口大小、背景透明度及分辨率。
     * 5. 使用 Live2DModel.from() 方法异步加载模型。
     * 6. 将加载的模型添加到 PIXI 应用的舞台 (stage) 上。
     * 7. 调整模型的初始变换（位置、缩放、锚点）。
     * 8. 为模型注册 'hit' 事件监听器，用于处理用户点击模型的交互。
     * 9. 处理加载过程中可能发生的错误，并在 finally 块中重置加载状态。
     */
    async initializeAndLoadModel() {
      this.isLoading = true;
      this.errorMsg = "";
      this.backendMessage = "";
      this.cleanupPixi(); // 确保在加载新模型前清理旧实例

      // 检查 canvas 元素是否已在 DOM 中准备好
      if (!this.$refs.liveCanvas) {
        this.errorMsg = "Live2D 的 Canvas 绘图元素未找到。请确保模板中有 <canvas ref='liveCanvas'></canvas>";
        this.isLoading = false;
        console.error(this.errorMsg);
        return;
      }

      try {
        // 创建 PIXI 应用实例
        this.pixiAppInstance = new PIXI.Application({
          view: this.$refs.liveCanvas, // 关联到模板中的 canvas 元素
          autoStart: true, // 自动开始渲染循环
          resizeTo: window, // PIXI 应用的大小将自动调整以适应窗口大小
          backgroundAlpha: 0, // 设置背景为透明
          resolution: window.devicePixelRatio || 1, // 设置分辨率以适应高 DPI 屏幕
        });

        // 异步加载 Live2D 模型
        this.currentModelInstance = await Live2DModel.from(this.modelUrl);
        // 将模型添加到 PIXI 应用的舞台
        this.pixiAppInstance.stage.addChild(this.currentModelInstance);
        // 调整模型的初始位置、缩放等
        this.adjustModelTransform();
        // 为模型注册 'hit' 事件，当用户点击模型的特定区域时触发
        this.currentModelInstance.on("hit", this.handleHit);
      } catch (err) {
        console.error("加载 Live2D 模型时发生严重错误:", err);
        this.errorMsg = `模型加载失败: ${err.message}。请检查控制台日志、模型路径 ('${this.modelUrl}') 是否正确，并确认 Cubism Core SDK (live2dcubismcore.min.js) 已成功加载。`;
      } finally {
        this.isLoading = false; // 无论成功或失败，结束加载状态
      }
    },

    /**
     * 调整 Live2D 模型的变换，包括缩放、位置和锚点。
     * 此方法在模型加载完成后以及窗口大小调整时调用。
     * 1. 检查模型实例和 PIXI 应用实例是否存在。
     * 2. 设置模型的缩放，基于 props 中的 initialScale。
     * 3. 将模型水平居中放置在屏幕上。
     * 4. 将模型垂直放置在屏幕中心偏下 10% 的位置，使其看起来更自然。
     * 5. 设置模型的锚点（旋转和定位的基点）为其自身的中心 (0.5, 0.5)。
     */
    adjustModelTransform() {
      if (!this.currentModelInstance || !this.pixiAppInstance) return; // 防御性编程，确保实例存在

      const model = this.currentModelInstance;
      const app = this.pixiAppInstance;

      model.scale.set(this.initialScale); // 设置模型的缩放

      // 将模型的锚点（通常是其中心）定位到屏幕的中心
      model.x = app.screen.width / 2;
      // 将模型垂直方向上稍微向下偏移一点（屏幕高度的10%），使其看起来更舒适
      model.y = app.screen.height / 2 + app.screen.height * 0.1;

      model.anchor.set(0.5, 0.5); // 将模型的锚点设置在其自身的中心，这样缩放和定位都是相对于模型中心进行的
    },

    /**
     * 处理窗口大小调整事件。
     * 当浏览器窗口大小改变时，此方法被调用，以重新调整模型的位置和可能的缩放，
     * 确保模型在不同窗口大小下保持良好的显示效果。
     */
    handleResize() {
      // 重新计算并应用模型的变换
      this.adjustModelTransform();
    },

    /**
     * 异步方法：处理用户点击 Live2D 模型特定区域（HitArea）的事件。
     * 当用户点击模型上定义的例如头部、身体等区域时，此方法被触发。
     * 1. 检查模型实例是否存在。
     * 2. 记录被点击的区域名称。
     * 3. 从模型 URL 中提取模型 ID (通常是包含模型文件的文件夹名称)。
     * 4. 构建交互负载 (payload)，包含模型 ID、被点击区域、时间戳。
     * 5. 通过 API 服务 (this.api.postInteraction) 将此交互事件发送到后端。
     * 6. 处理来自后端的 HTTP 响应：
     * - 如果响应中包含动作 (action) 指令，则调用 executeModelCommand 执行该动作。
     * - 如果响应中包含来自后端的消息 (message_from_backend)，则显示该消息。
     * 7. 捕获并记录与后端交互时可能发生的错误。
     * * 注意：此方法当前是通过 HTTP API 与后端交互。它也可以被修改为通过 WebSocket 发送点击事件。
     */
    async handleHit(hitAreaNames) {
      if (!this.currentModelInstance) return; // 确保模型已加载

      console.log(`用户点击了模型的以下区域: ${hitAreaNames.join(", ")}`);
      this.backendMessage = ""; // 清空之前的后端消息

      // 从模型 URL 中提取模型 ID，通常是倒数第二个路径部分 (即模型文件夹名)
      const urlParts = this.modelUrl.split("/");
      const modelIdFromUrl =
        urlParts.length > 1
          ? urlParts[urlParts.length - 2] // 取倒数第二个元素，例如 "hiyori_pro_zh"
          : "unknown_model_id"; // 如果 URL 格式不符合预期，则使用默认 ID

      try {
        // 准备要发送到后端的交互数据
        const interactionPayload = {
          model_id: modelIdFromUrl,
          hit_areas: hitAreaNames, // 被点击的区域名称数组
          timestamp: new Date().toISOString(), // 当前时间的 ISO 格式字符串
        };
        // 通过 HTTP POST 请求将交互数据发送到后端 API
        const response = await api.postInteraction(interactionPayload);

        // 如果后端响应了数据
        if (response.data) {
          const backendData = response.data;
          console.log("已将点击事件发送到后端，并收到响应:", backendData);
          // 检查后端响应中是否包含需要模型执行的动作
          if (backendData.action) {
            this.executeModelCommand(
              backendData.action.type, // 动作类型，例如 'motion', 'expression'
              backendData.action // 动作相关的参数
            );
          } else if (backendData.message_from_backend) {
            // 如果后端响应中包含要显示的消息
            this.backendMessage = backendData.message_from_backend;
          }
        }
      } catch (err) {
        console.error("与后端进行 HTTP 交互时发生错误:", err);
        this.errorMsg = "与服务器交互失败，请稍后再试。";
      }
    },

    // --- 语音播放和口型同步相关方法 ---

    /**
     * 初始化 Web Audio API 的 AudioContext。
     * AudioContext 是处理和播放音频的入口点。
     * 1. 检查是否已存在 AudioContext 实例，如果不存在，则创建一个新的实例。
     * 使用 `window.AudioContext || window.webkitAudioContext` 来兼容旧版浏览器 (主要是 Safari)。
     * 2. 检查 AudioContext 的状态。如果由于浏览器自动播放策略而被置于 'suspended' (暂停) 状态，
     * 则尝试调用 `resume()` 方法来激活它。`resume()` 通常需要在用户手势（如点击）后调用才能成功。
     */
    initAudioContext() {
      if (!this.audioContext) {
        try {
          this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
          console.log("AudioContext 已创建。初始状态:", this.audioContext.state);
        } catch (e) {
          console.error("创建 AudioContext 失败:", e);
          this.errorMsg = "浏览器不支持 Web Audio API 或创建失败。";
          return;
        }
      }
      // 如果 AudioContext 已创建但处于暂停状态，尝试恢复它
      // 这通常是为了应对浏览器的自动播放策略限制
      if (this.audioContext && this.audioContext.state === "suspended") {
        this.audioContext.resume().then(() => {
          console.log("AudioContext 已成功恢复。当前状态:", this.audioContext.state);
        }).catch(err => {
          console.warn("恢复 AudioContext 失败 (这可能需要用户手势):", err);
        });
      }
    },

    /**
     * 异步方法：播放指定的音频文件，并启动口型同步。
     * @param {string} audioFileUrl - 要播放的音频文件的 URL。
     *
     * 1. 检查 Live2D 模型是否已加载，以及当前是否已在播放语音。
     * 2. 调用 initAudioContext 确保 AudioContext 已准备就绪。
     * 3. 设置加载状态，清空错误消息。
     * 4. 使用 fetch API 获取音频文件数据，并将其解码为 ArrayBuffer。
     * 5. 使用 AudioContext 的 decodeAudioData 方法将 ArrayBuffer 解码为 AudioBuffer 对象。
     * 6. 创建 AudioBufferSourceNode (音频源节点) 和 AnalyserNode (音频分析节点)。
     * 7. 配置节点连接：音频源 -> 分析器 -> 输出设备 (扬声器)。
     * 8. 为音频源节点设置 onended 事件处理函数，在音频播放完毕时执行清理工作
     * (停止口型同步动画帧, 模型闭嘴, 清理节点引用)。
     * 9. 启动音频播放 (source.start(0))。
     * 10. 设置 isSpeaking 状态为 true，并调用 updateMouthLoop 开始口型同步的动画循环。
     * 11. 捕获过程中可能发生的错误，并在 finally 块中重置加载状态。
     */
    async speak(audioFileUrl) {
      if (!this.currentModelInstance) {
        console.error("Live2D 模型尚未加载，无法播放语音。");
        this.errorMsg = "模型未加载，无法播放语音。";
        return;
      }
      // 如果当前正在播放语音，则先停止当前的播放和口型同步
      if (this.isSpeaking) {
        console.warn("当前已经在播放语音。将停止当前播放并开始新的播放。");
        this.stopSpeaking(); // 调用封装的停止方法
        // 等待一小段时间确保清理操作完成，避免资源冲突
        await new Promise((resolve) => setTimeout(resolve, 100));
      }

      this.initAudioContext(); // 确保 AudioContext 已经初始化并尝试激活

      // 再次检查 AudioContext 状态，如果仍未激活，则提示用户交互
      if (!this.audioContext || this.audioContext.state === 'suspended') {
          console.warn("AudioContext 仍处于暂停状态，可能需要用户与页面交互来激活音频。");
          this.errorMsg = "音频功能未激活。请先与页面进行交互（例如点击一个按钮）。";
          // 通常，如果 speak 是由用户直接点击触发的，initAudioContext 内部的 resume 应该已经成功。
          // 如果是由 WebSocket 自动触发，而用户之前没有交互，这里可能会是 suspended。
          return;
      }


      this.isLoading = true; // 可以用一个专门的 isAudioLoading 状态
      this.errorMsg = "";

      try {
        const response = await fetch(audioFileUrl);
        if (!response.ok) {
          throw new Error(
            `加载音频文件 '${audioFileUrl}' 失败: ${response.status} ${response.statusText}`
          );
        }
        const audioData = await response.arrayBuffer(); // 将响应体读取为 ArrayBuffer
        // 将 ArrayBuffer 数据解码为 AudioBuffer，这是 Web Audio API 可以处理的格式
        const audioBuffer = await this.audioContext.decodeAudioData(audioData);

        // 创建音频源节点和分析节点
        this.audioSourceNode = this.audioContext.createBufferSource();
        this.audioAnalyserNode = this.audioContext.createAnalyser();
        // 你可以根据需要配置 AnalyserNode，例如 fftSize
        // this.audioAnalyserNode.fftSize = 2048; // 默认值

        this.audioSourceNode.buffer = audioBuffer; // 将解码后的音频数据赋值给源节点
        // 连接音频通路：源节点 -> 分析节点 -> 目标输出 (扬声器)
        this.audioSourceNode.connect(this.audioAnalyserNode);
        this.audioAnalyserNode.connect(this.audioContext.destination);

        // 设置音频播放结束时的回调
        this.audioSourceNode.onended = () => {
          this.isSpeaking = false; // 更新说话状态
          if (this.lipSyncRequestId) {
            cancelAnimationFrame(this.lipSyncRequestId); // 取消口型同步的动画帧
            this.lipSyncRequestId = null;
          }
          if (this.currentModelInstance) {
            // 让模型闭上嘴巴
            this.currentModelInstance.internalModel.coreModel.setParameterValueById(
              this.mouthParameterId,
              0 // 嘴巴张开度设为0
            );
          }
          console.log("音频播放完毕，口型同步已停止。");

          // 断开并清理节点，防止内存泄漏
          if (this.audioSourceNode) this.audioSourceNode.disconnect();
          if (this.audioAnalyserNode) this.audioAnalyserNode.disconnect();
          this.audioSourceNode = null;
          this.audioAnalyserNode = null;
        };

        this.audioSourceNode.start(0); // 从头开始播放音频
        this.isSpeaking = true; // 更新说话状态
        this.updateMouthLoop(); // 启动口型同步的动画循环

      } catch (err) {
        console.error("处理音频播放或口型同步时发生错误:", err);
        this.errorMsg = `语音播放失败: ${err.message}`;
        this.isSpeaking = false; // 出错时重置说话状态
        // 出错时也确保模型闭嘴
        if (this.currentModelInstance) {
          this.currentModelInstance.internalModel.coreModel.setParameterValueById(
            this.mouthParameterId,
            0
          );
        }
      } finally {
        this.isLoading = false; // 结束加载状态
      }
    },

    /**
     * 口型同步的动画循环方法。
     * 此方法通过 requestAnimationFrame 被反复调用，以实现平滑的口型动画。
     * 1. 检查是否应该继续更新 (isSpeaking 状态，分析节点和模型实例是否存在)。
     * 2. 从 AnalyserNode 获取当前的音频频率数据 (getByteFrequencyData)。
     * 3. 计算频率数据的平均值，作为当前音量的近似表示。
     * 4. 根据计算出的音量和预设的敏感度 (lipSyncSensitivity)，计算嘴巴的张开程度 (0到1之间)。
     * 使用 Math.min 和 Math.max 确保值在 0-1 范围内。
     * 5. 使用模型的 setParameterValueById 方法，将计算出的张开程度应用到控制嘴巴的参数上。
     * 6. 再次请求下一动画帧，继续循环，直到 isSpeaking 变为 false 或相关节点不存在。
     */
    updateMouthLoop() {
      // 如果不处于说话状态，或者必要的节点/实例不存在，则停止循环
      if (
        !this.isSpeaking ||
        !this.audioAnalyserNode ||
        !this.currentModelInstance
      ) {
        if (this.lipSyncRequestId) {
          cancelAnimationFrame(this.lipSyncRequestId);
          this.lipSyncRequestId = null;
        }
        return; // 退出循环
      }

      // 创建一个 Uint8Array 来存储频率数据
      const dataArray = new Uint8Array(
        this.audioAnalyserNode.frequencyBinCount // frequencyBinCount 是 fftSize 的一半
      );
      // 从分析器获取当前播放音频的频率数据
      this.audioAnalyserNode.getByteFrequencyData(dataArray);

      // 计算音量：简单地取频率数据的平均值
      // 注意：对于更精确的口型同步，可能需要更复杂的算法，例如针对特定频段或使用 getByteTimeDomainData
      let volume = 0;
      if (dataArray.length > 0) {
        // 使用 reduce 计算总和，然后除以长度得到平均值
        volume = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
      }

      // 根据音量和敏感度计算嘴巴张开程度 (0 到 1)
      // volume / this.lipSyncSensitivity 是核心的映射关系
      // Math.max(0, ...) 确保不会出现负值
      // Math.min(1, ...) 确保不会超过最大值 1
      const mouthOpen = Math.min(
        1,
        Math.max(0, volume / this.lipSyncSensitivity)
      );
      
      // 调试日志，可以观察音量和嘴巴开合值的变化
      // console.log("实时音量:", volume.toFixed(2), "嘴巴开合值:", mouthOpen.toFixed(2));

      // 更新 Live2D 模型嘴巴参数
      this.currentModelInstance.internalModel.coreModel.setParameterValueById(
        this.mouthParameterId, // 例如 "ParamMouthOpenY"
        mouthOpen
      );

      // 请求下一帧动画，形成循环
      // 使用箭头函数确保 this.updateMouthLoop 内部的 this 指向 Vue 组件实例
      this.lipSyncRequestId = requestAnimationFrame(() => this.updateMouthLoop());
    },

    /**
     * 停止当前正在播放的语音和口型同步。
     * 1. 如果存在音频源节点 (audioSourceNode)：
     * - 清除其 onended 回调，防止在手动停止后再次执行清理逻辑。
     * - 调用 stop() 方法停止音频播放。
     * - 断开节点连接。
     * - 清理节点引用。
     * 2. 如果存在音频分析节点 (audioAnalyserNode)，断开其连接并清理引用。
     * 3. 如果存在口型同步的动画帧请求 ID (lipSyncRequestId)，取消该动画帧。
     * 4. 如果模型实例存在，将嘴巴参数设置为 0，使模型闭嘴。
     * 5. 更新 isSpeaking 状态为 false。
     */
    stopSpeaking() {
      if (this.audioSourceNode) {
        this.audioSourceNode.onended = null; // 移除回调，因为是手动停止
        try {
          this.audioSourceNode.stop(); // 停止音频播放
        } catch (e) {
          // 如果音频已经停止或从未开始，stop() 可能会抛出错误，可以安全地忽略
          console.warn("尝试停止音频源时发生错误 (可能已停止或未初始化):", e);
        }
        this.audioSourceNode.disconnect(); // 断开连接
        this.audioSourceNode = null; // 清理引用
      }
      if (this.audioAnalyserNode) {
        this.audioAnalyserNode.disconnect(); // 断开连接
        this.audioAnalyserNode = null; // 清理引用
      }
      if (this.lipSyncRequestId) {
        cancelAnimationFrame(this.lipSyncRequestId); // 取消动画帧
        this.lipSyncRequestId = null;
      }
      // 确保模型闭嘴
      if (this.currentModelInstance) {
        this.currentModelInstance.internalModel.coreModel.setParameterValueById(
          this.mouthParameterId,
          0
        );
      }
      this.isSpeaking = false; // 更新状态
      console.log("语音播放已手动停止。");
    },

    // --- WebSocket 相关方法 ---

    /**
     * 连接到 WebSocket 服务器。
     * 1. 获取 WebSocket 服务器的 URL。
     * 2. 检查是否已存在连接或正在连接，如果是，则直接返回。
     * 3. 创建新的 WebSocket 实例。
     * 4. 设置 onopen, onmessage, onerror, onclose 事件处理函数。
     * - onopen: 连接成功时调用，打印日志。
     * - onmessage: 收到服务器消息时调用，解析 JSON 数据，并根据指令类型和数据调用 executeModelCommand。
     * - onerror:发生错误时调用，打印错误日志。
     * - onclose:连接关闭时调用，打印日志，清理 WebSocket 实例，并设置一个延时尝试重连。
     */
    connectWebSocket() {
      const wsUrl = "ws://localhost:8000/ws/live2d"; // WebSocket 端点地址
      // 如果已有连接或正在连接，则不重复创建
      if (
        this.websocket &&
        (this.websocket.readyState === WebSocket.OPEN ||
          this.websocket.readyState === WebSocket.CONNECTING)
      ) {
        console.log("WebSocket 已经连接或正在连接中，无需重复操作。");
        return;
      }

      console.log(`尝试连接到 WebSocket 服务器: ${wsUrl}`);
      this.websocket = new WebSocket(wsUrl);

      this.websocket.onopen = (event) => {
        console.log("成功连接到 WebSocket 服务器:", event);
        // 连接成功后可以发送一条 "客户端准备就绪" 的消息给后端（如果后端需要）
        // this.websocket.send(JSON.stringify({ type: "client_ready", clientId: "some_unique_id" }));
      };

      this.websocket.onmessage = (event) => {
        console.log("从 WebSocket 服务器收到原始消息:", event.data);
        try {
          const command = JSON.parse(event.data); // 解析 JSON 格式的指令
          console.log("解析后的指令:", command);
          // 确保模型实例存在，并且指令包含必要的 type 和 data 字段
          if (this.currentModelInstance && command.type && command.data) {
            this.executeModelCommand(command.type, command.data);
          } else {
            console.warn("收到格式不正确或模型未就绪的 WebSocket 指令:", command);
          }
        } catch (e) {
          console.error("解析或执行来自 WebSocket 的指令时失败:", e);
          this.errorMsg = "处理服务器指令时发生错误。";
        }
      };

      this.websocket.onerror = (error) => {
        console.error("WebSocket 连接发生错误:", error);
        this.errorMsg = "与服务器的实时连接发生错误。";
      };

      this.websocket.onclose = (event) => {
        console.log(
          `WebSocket 连接已关闭。代码: ${event.code}, 原因: "${event.reason}", 是否正常关闭: ${event.wasClean}`
        );
        this.websocket = null; // 清理 WebSocket 实例引用
        // 实现简单的自动重连逻辑
        console.log("5秒后尝试重新连接 WebSocket...");
        setTimeout(() => {
          this.connectWebSocket(); // 尝试重连
        }, 5000); // 5秒后重连
      };
    },

    /**
     * 断开当前的 WebSocket 连接。
     * 如果存在 WebSocket 实例并且其状态不是已关闭或正在关闭，则调用 close() 方法。
     */
    disconnectWebSocket() {
      if (this.websocket) {
        if (this.websocket.readyState === WebSocket.OPEN || this.websocket.readyState === WebSocket.CONNECTING) {
            console.log("正在关闭 WebSocket 连接...");
            this.websocket.close(1000, "组件卸载或手动断开"); // 1000 表示正常关闭
        }
        // onclose 事件处理器中已经将 this.websocket 设置为 null
      }
    },

    /**
     * 根据从后端接收到的指令类型和负载 (payload) 来执行相应的模型操作。
     * 此方法可以由 HTTP 响应或 WebSocket 消息触发。
     * @param {string} commandType - 指令的类型 (例如 'motion', 'expression', 'speak')。
     * @param {object} payload - 与指令相关的参数数据。
     *
     * 1. 检查模型实例是否存在，如果不存在则警告并返回。
     * 2. 使用 switch 语句根据 commandType 执行不同的操作：
     * - 'motion': 播放指定的动作。需要 payload 中包含 group (动作组名称)，
     * 可选 index (动作索引，不提供则随机播放组内动作) 和 priority (优先级)。
     * - 'expression': 设置模型的表情。需要 payload 中包含 name (表情名称)。
     * - 'speak': (对应我们之前定义的 start_lip_sync) 触发语音播放和口型同步。
     * 需要 payload 中包含 audioUrl。可以有选择地从 payload 更新
     * mouthParameterId 和 lipSyncSensitivity。
     * - default: 如果指令类型未知，则打印警告。
     */
    executeModelCommand(commandType, payload) {
      if (!this.currentModelInstance) {
        console.warn(
          `模型实例不存在，无法执行指令: 类型='${commandType}', 负载=`, payload
        );
        return;
      }

      console.log(`准备执行指令: 类型='${commandType}', 负载=`, payload);
      switch (commandType) {
        case "motion": // 处理播放动作的指令
          if (payload.group) {
            this.currentModelInstance.motion(
              payload.group, // 动作组名称
              payload.index, // 动作在组内的索引 (可选, undefined 表示随机)
              payload.priority !== undefined ? payload.priority : 2 // 动作优先级 (可选, 默认为2 - PIXI.Live2DModel.MOTION_PRIORITY_NORMAL)
            );
          } else {
            console.warn("播放动作指令 ('motion') 缺少 'group' 参数。");
          }
          break;
        case "expression": // 处理设置表情的指令
          if (payload.name) {
            this.currentModelInstance.expression(payload.name); // 根据表情名称设置表情
          } else if (payload.index !== undefined) {
            this.currentModelInstance.expression(payload.index); // 或者根据表情索引设置
          } else {
            console.warn("设置表情指令 ('expression') 缺少 'name' 或 'index' 参数。将尝试设置随机表情。");
            this.currentModelInstance.expression(); // 不带参数则随机设置一个表情
          }
          console.log("表情指令已处理:", payload);
          break;
        case "speak": // 处理播放语音并进行口型同步的指令 (之前可能叫 'start_lip_sync')
          if (payload.audioUrl) {
            // 可选：允许后端指令覆盖组件内定义的口型参数和敏感度
            if (payload.mouthParameterId) {
              this.mouthParameterId = payload.mouthParameterId;
            }
            if (payload.lipSyncSensitivity) {
              this.lipSyncSensitivity = Number(payload.lipSyncSensitivity); // 确保是数字
            }
            this.speak(payload.audioUrl); // 调用 speak 方法开始播放和同步
          } else {
            console.warn("语音播放指令 ('speak') 缺少 'audioUrl' 参数。");
            this.errorMsg = "服务器发送的语音指令无效（缺少音频链接）。";
          }
          break;
        default:
          console.warn(`接收到未知的指令类型: '${commandType}'`);
      }
    },
  },
};
</script>

<template>
  <div class="live2d-vue-app">
    <div v-if="isLoading" class="status-overlay loading-message">
      少女祈祷中... (加载中...)
    </div>
    <div v-if="errorMsg" class="status-overlay error-message">
      {{ errorMsg }}
    </div>
    <canvas ref="liveCanvas"></canvas>
    </div>
</template>

<style scoped>
.live2d-vue-app {
  width: 100%; /* 容器宽度占满父元素 */
  height: 100%; /* 容器高度占满父元素 */
  position: relative; /* 用于绝对定位子元素 (如 status-overlay) */
  background-color: transparent; /* 背景透明，以便能看到页面其他内容 */
  overflow: hidden; /* 隐藏超出容器范围的内容 */
}

canvas {
  display: block; /* 消除 canvas 底部可能的空白间隙 */
  width: 100%; /* Canvas 宽度占满其容器 */
  height: 100%; /* Canvas 高度占满其容器 */
}

/* 用于显示加载中或错误信息的覆盖层样式 */
.status-overlay {
  position: absolute; /* 绝对定位，相对于 .live2d-vue-app */
  top: 50%; /* 垂直居中 */
  left: 50%; /* 水平居中 */
  transform: translate(-50%, -50%); /* 精确居中定位 */
  padding: 15px 25px; /* 内边距 */
  border-radius: 8px; /* 圆角边框 */
  color: white; /* 文字颜色 */
  z-index: 100; /*确保在 Canvas 之上显示 */
  text-align: center; /* 文字居中 */
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2); /* 添加阴影增加立体感 */
}

/* 加载中消息的特定背景色 */
.loading-message {
  background-color: rgba(50, 50, 50, 0.85); /* 半透明深灰色背景 */
}

/* 错误消息的特定背景色和最大宽度 */
.error-message {
  background-color: rgba(220, 50, 50, 0.85); /* 半透明红色背景 */
  max-width: 80%; /* 限制最大宽度，防止消息过长 */
}
</style>