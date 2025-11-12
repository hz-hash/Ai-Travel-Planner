# AiTravelPlanner智能旅行助手 🌍✈️

基于AiTravelPlanner框架构建的智能旅行规划助手,集成高德地图MCP服务,提供个性化的旅行计划生成。

## ✨ 功能特点

- 🤖 **AI驱动的旅行规划**: 基于AiTravelPlanner框架的SimpleAgent,智能生成详细的多日旅程
- 🗺️ **高德地图集成**: 通过MCP协议接入高德地图服务,支持景点搜索、路线规划、天气查询
- 🧠 **智能工具调用**: Agent自动调用高德地图MCP工具,获取实时POI、路线和天气信息
- 🎨 **现代化前端**: Vue3 + TypeScript + Vite,响应式设计,流畅的用户体验
- 📱 **完整功能**: 包含住宿、交通、餐饮和景点游览时间推荐

## 🏗️ 技术栈

### 后端
- **框架**: AiTravelPlanner (基于SimpleAgent)
- **API**: FastAPI
- **MCP工具**: amap-mcp-server (高德地图)
- **LLM**: 支持多种LLM提供商(OpenAI, DeepSeek等)

### 前端
- **框架**: Vue 3 + TypeScript
- **构建工具**: Vite
- **UI组件库**: Ant Design Vue
- **地图服务**: 高德地图 JavaScript API
- **HTTP客户端**: Axios

## 📁 项目结构

```
ai-travel-planner/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── agents/            # Agent实现
│   │   │   └── trip_planner_agent.py
│   │   ├── api/               # FastAPI路由
│   │   │   ├── main.py
│   │   │   └── routes/
│   │   │       ├── trip.py
│   │   │       └── map.py
│   │   ├── services/          # 服务层
│   │   │   ├── amap_service.py
│   │   │   └── llm_service.py
│   │   ├── models/            # 数据模型
│   │   │   └── schemas.py
│   │   └── config.py          # 配置管理
│   ├── requirements.txt
│   ├── .env.example
│   └── .gitignore
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── components/        # Vue组件
│   │   ├── services/          # API服务
│   │   ├── types/             # TypeScript类型
│   │   └── views/             # 页面视图
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## 🚀 快速开始

### 前提条件

- Python 3.10+
- Node.js 16+
- 高德地图API密钥 (Web服务API)
- LLM API密钥 (OpenAI/DeepSeek等)

### 后端安装

1. 进入后端目录
```bash
cd backend
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置环境变量
```bash
cp .env.example .env
# 编辑.env文件,填入你的API密钥
```

5. 启动后端服务
```bash
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端安装

1. 进入前端目录
```bash
cd frontend
```

2. 安装依赖
```bash
npm install
```

3. 配置环境变量
```bash
# 创建.env文件,配置高德地图Web API Key
echo "VITE_AMAP_WEB_KEY=your_amap_web_key" > .env
```

4. 启动开发服务器
```bash
npm run dev
```

5. 打开浏览器访问 `http://localhost:5173`

### LLM/语音配置

#### 通用 LLM
后端通过 `ai-travel-planner-core` 读取标准环境变量,推荐在 `backend/.env` 中配置:
```ini
LLM_API_KEY=your_llm_api_key
LLM_BASE_URL=https://api.openai.com/v1   # 或 DeepSeek/其他兼容接口
LLM_MODEL_ID=gpt-4o-mini                 # 根据你的模型替换
LLM_TIMEOUT=260                          # 可选
```
若采用 DeepSeek/自建推理,只需把 `LLM_BASE_URL` 和 `LLM_MODEL_ID` 改成对应值即可。

#### 阿里云百炼语音配置

1. 在[阿里云百炼控制台](https://bailian.console.aliyun.com/)开通语音识别(ASR)能力,获取 DASHScope API Key。北京地域默认 HTTP 接口为 `https://dashscope.aliyuncs.com/api/v1`, 若使用新加坡地域请改为 `https://dashscope-intl.aliyuncs.com/api/v1`。
2. 编辑 `backend/.env`, 增加/确认以下配置:
   ```ini
   BAILIAN_BASE_URL=https://dashscope.aliyuncs.com/api/v1
   BAILIAN_MODEL=xxx
   BAILIAN_API_KEY=your_bailian_api_key
   BAILIAN_WORKSPACE_ID=
   BAILIAN_FORMAT=wav
   BAILIAN_SAMPLE_RATE=16000
   BAILIAN_LANGUAGE=zh
   ```
3. 重新执行 `pip install -r backend/requirements.txt` 确认 `dashscope` 依赖已安装。
4. 前端仍会上传 16k PCM 单声道 WAV 音频,后端会调用 DashScope HTTP API 转写文本并进入自动填表/行程生成流程。

## 🐳 Docker 部署

项目根目录已提供精简多阶段 `Dockerfile`, 会自动：
1. 使用 `node:20-alpine` 构建前端并生成 `frontend/dist`
2. 基于 `python:3.11-slim` 安装后端依赖
3. 将打包后的前端静态文件挂载到 FastAPI, 由同一容器对外提供 Web + API

### 构建镜像
```bash
docker build -t ai-travel-planner .
```

### 运行容器
```bash
docker run --rm \
  -p 8000:8000 \
  --env-file backend/.env \
  ai-travel-planner
```
- 如果你把 `.env` 放到其他位置,只需调整 `--env-file` 路径即可。
- 容器启动后访问 `http://localhost:8000` 即可看到前端; API 仍然在 `/api/*` 路径下,健康检查为 `/health`。

> **提示**: 构建时 `.dockerignore` 已排除 Git、node_modules、录屏等文件,以减小镜像体积。如果还需要挂载本地 MCP/模型资源,可通过 `-v` 额外挂载。

## 📝 使用指南

1. 在首页填写旅行信息:
   - 目的地城市
   - 旅行日期和天数
   - 交通方式偏好
   - 住宿偏好
   - 旅行风格标签

2. 点击"生成旅行计划"按钮

3. 系统将:
   - 调用AiTravelPlanner Agent生成初步计划
   - Agent自动调用高德地图MCP工具搜索景点
   - Agent获取天气信息和路线规划
   - 整合所有信息生成完整行程

4. 查看结果:
   - 每日详细行程
   - 景点信息与地图标记
   - 交通路线规划
   - 天气预报
   - 餐饮推荐

## 🔧 核心实现

### AiTravelPlanner Agent集成

```python
from aitravelplanner_core import SimpleAgent, AiTravelPlannerLLM, MCPTool


# 创建高德地图MCP工具
amap_tool = MCPTool(
    name="amap",
    server_command=["uvx", "amap-mcp-server"],
    env={"AMAP_MAPS_API_KEY": "your_api_key"},
    auto_expand=True
)

# 创建旅行规划Agent
agent = SimpleAgent(
    name="旅行规划助手",
    llm=AiTravelPlannerLLM(),
    system_prompt="你是一个专业的旅行规划助手..."
)

# 添加工具
agent.add_tool(amap_tool)
```

### MCP工具调用

Agent可以自动调用以下高德地图MCP工具:
- `maps_text_search`: 搜索景点POI
- `maps_weather`: 查询天气
- `maps_direction_walking_by_address`: 步行路线规划
- `maps_direction_driving_by_address`: 驾车路线规划
- `maps_direction_transit_integrated_by_address`: 公共交通路线规划

## 📄 API文档

启动后端服务后,访问 `http://localhost:8000/docs` 查看完整的API文档。

主要端点:
- `POST /api/trip/plan` - 生成旅行计划
- `GET /api/map/poi` - 搜索POI
- `GET /api/map/weather` - 查询天气
- `POST /api/map/route` - 规划路线





