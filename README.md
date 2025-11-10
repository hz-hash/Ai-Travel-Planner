# AiTravelPlanner智能旅行助手 🌍✈️

基于AiTravelPlanner框架构建的智能旅行规划助手,集成高德地图MCP服务,提供个性化的旅行计划生成。

## ✨ 功能特点

- 🤖 **AI驱动的旅行规划**: 基于AiTravelPlanner框架的SimpleAgent,智能生成详细的多日旅程
- 🗺️ **高德地图集成**: 通过MCP协议接入高德地图服务,支持景点搜索、路线规划、天气查询
- 🧠 **智能工具调用**: Agent自动调用高德地图MCP工具,获取实时POI、路线和天气信息
- 🎨 **现代化前端**: Vue3 + TypeScript + Vite,响应式设计,流畅的用户体验
- 📱 **完整功能**: 包含住宿、交通、餐饮和景点游览时间推荐
- 🎙️ **语音输入**: 集成科大讯飞语音听写,一键录音即可自动填表或直接生成行程

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
- 科大讯飞开放平台语音听写 AppID / API Key / API Secret

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

5. 打开浏览器访问 `http://localhost:5173/auth` 体验登录/注册,成功后会跳转到主系统

### 科大讯飞语音配置

1. 在[科大讯飞开放平台](https://www.xfyun.cn/)启用“语音听写 WebAPI (v2)”能力,获取 `AppID / APIKey / APISecret`。
2. 编辑 `backend/.env`, 增加以下配置:
   ```ini
   IFLYTEK_APP_ID=your_app_id
   IFLYTEK_API_KEY=your_api_key
   IFLYTEK_API_SECRET=your_api_secret
   IFLYTEK_LANGUAGE=zh_cn
   IFLYTEK_DOMAIN=iat
   IFLYTEK_ACCENT=mandarin
   ```
3. 重新执行 `pip install -r backend/requirements.txt`, 确认新引入的 `websockets` 等依赖安装完成。
4. 前端已内置 Web Audio 录音与 16k PCM 转码逻辑,直接使用首页的“语音快速输入”按钮即可触发识别与自动填表。

## 📝 使用指南

### 登录 / 注册

1. 默认体验账号: `demo@aitrip.com / demo123`
2. 或在登录页切换到“注册”,填写昵称+邮箱+密码即可生成本地账号(数据暂存于浏览器 localStorage)
3. 登录成功后自动跳转至主控台,即可像以往一样填写行程信息

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

### 🎙️ 语音输入玩法

1. 点击首页的“语音快速输入”按钮,授予浏览器麦克风权限并描述: 目的地、出行日期/天数、预算、同行人数、旅行偏好等内容。
2. 松开录音后,系统会调用科大讯飞语音听写接口获取文本,并利用 LLM 抽取表单字段,自动标注缺失项。
3. 可选择“使用语音填充表单”快速带入识别结果,也可以直接点击“语音直接生成行程”一步到位。
4. 所有语音表单都会保存原文本,便于用户二次编辑或加入额外需求。

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
- `POST /api/voice/transcribe` - 上传语音并返回识别文本+表单建议
- `POST /api/voice/plan` - 上传语音并直接生成完整旅行计划

## 🤝 贡献指南

欢迎提交Pull Request或Issue!

## 📜 开源协议

CC BY-NC-SA 4.0

## 🙏 致谢

- [AiTravelPlanner](https://github.com/datawhalechina/Hello-Agents) - 智能体教程
- [AiTravelPlanner框架](https://github.com/jjyaoao/AiTravelPlanner) - 智能体框架
- [高德地图开放平台](https://lbs.amap.com/) - 地图服务
- [amap-mcp-server](https://github.com/sugarforever/amap-mcp-server) - 高德地图MCP服务器

---

**AiTravelPlanner智能旅行助手** - 让旅行计划变得简单而智能 🌈

