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
