// src/services/api.js
/*
 本文件定义了与后端 FastAPI API 进行交互的 axios 客户端实例，并封装了与 Live2D 相关的接口请求方法。
主要用于前端与后端的数据交互，便于维护和调用。
*/
import axios from "axios";

const apiClient = axios.create({
  // （可替换）后端FastAPI API 基础地址
  baseURL: "http://localhost:8000/api/v1/live2d",
  headers: {
    "Content-Type": "application/json",
  },
});

export default {
  postInteraction(data) {
    return apiClient.post("/interaction", data);
  },
};
