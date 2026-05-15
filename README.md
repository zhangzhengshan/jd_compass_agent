# 1.名称：简历分析多Agent助手

介绍：JD Compass Agent 是一个面向“求职场景”的轻量级多 Agent 项目。

# 2.项目任务：输入求职信息后，自动完成简历匹配度报告

# 3.项目流程

```text
用户输入
→ 需求解析 Agent
→ 路由 Agent
→（可选）研究 Agent
→ 输出 Agent
→ 前端展示
```

# 4.项目设计思路

**采用固定流程+单点路由**

# 5.技术栈

## 后端
- **Python 3.11**
- **FastAPI**：提供 HTTP 接口和流式输出
- **Uvicorn**：ASGI 服务启动
- **LangGraph**：负责 Agent 工作流编排
- **LangChain**：负责模型调用封装
- **Pydantic**：请求体与流式事件结构定义
- **python-dotenv**：加载 `.env`
- **httpx**：用于本地测试和接口验证

## 模型与搜索
- **DeepSeek / OpenAI-compatible Chat API**
- **DuckDuckGoSearchAPIWrapper**

## 前端
- **React**
- **Vite**
- **原生 CSS**
- 轻量化组件化设计：输入区、流程区、结果区

# 6.项目开发日志

点开上面的项目日志文件，即可查看

# 7.效果图

点击执行：

<img width="1636" height="1258" alt="屏幕截图 2026-05-15 223104" src="https://github.com/user-attachments/assets/f8b5f44e-a209-499f-8d77-a464a65930b8" />

执行研究路线的展示：

<img width="1633" height="1258" alt="屏幕截图 2026-05-15 223125" src="https://github.com/user-attachments/assets/bb703151-0667-4614-8040-b8ba97076f87" />

执行研究路线的输出展示：

<img width="1605" height="1318" alt="屏幕截图 2026-05-15 223142" src="https://github.com/user-attachments/assets/b8ea6840-5d4d-4750-9b69-15cfa4256fc2" />

执行直接路线的输出展示：

<img width="1629" height="1329" alt="屏幕截图 2026-05-15 223503" src="https://github.com/user-attachments/assets/f7b211ee-a439-4226-933c-99104171fa9d" />









