# AI 同声传译助手

面向英语演讲、技术分享、国际会议和网课场景的 AI 同声传译 Web 应用。项目支持上传视频后自动生成双语字幕，并在播放过程中展示实时字幕、字幕时间轴联动、知识笔记和术语高亮，帮助用户更低成本地获取外语内容信息。

## Demo 演示

- Bilibili: https://www.bilibili.com/video/BV1FeEt68EMV/

## 核心功能

- 视频上传与字幕任务创建：上传本地视频后，后端创建异步处理任务。
- 实时字幕展示：通过 SSE 订阅任务事件，前端可在处理过程中展示逐步返回的字幕。
- 双语字幕与 SRT 下载：生成结构化字幕和 `.srt` 文件，支持下载复用。
- 视频时间轴联动：播放或拖动视频时自动高亮当前字幕，点击字幕可跳转到对应时间。
- 知识笔记 Agent：基于字幕内容生成结构化知识笔记，并支持 Markdown 下载。
- 本视频术语表：从知识洞察中提取术语，在字幕列表和知识笔记中高亮展示。
- 前端工作台体验：提供上传区、视频区、结果边栏、字幕列表和笔记视图，便于长视频查看。

## 技术架构

```text
E:\Code\voice_translation_agent
  src/
    backend/        FastAPI 后端，负责任务接口、媒体处理、ASR、LLM、SSE、知识笔记 Agent
    frontend/       Vue 3 + Vite + TypeScript 前端工作台
    storage/jobs/   本地任务产物目录，保存上传视频、字幕 JSON、SRT、Markdown 等文件
  Test/             早期原型和验证脚本
```

后端主要模块：

- `app/api/`：任务、字幕、事件流、知识笔记接口。
- `app/services/`：任务状态、媒体处理、ASR、LLM、字幕和洞察服务。
- `app/agents/`：知识笔记 Agent 实现。
- `app/workers/`：字幕生成后台流程。

前端主要模块：

- `src/api/`：后端 API 请求封装。
- `src/components/`：上传面板、视频播放器、任务状态、字幕列表、结果面板等组件。
- `src/styles/`：工作台布局与交互样式。

## 环境要求

- Python 3.10+
- Node.js 18+
- npm
- ffmpeg，可使用系统 PATH 中的 `ffmpeg`，也可依赖 `imageio-ffmpeg` 的 fallback
- 可用的 ASR/LLM API Key

## 环境变量

在项目根目录创建 `.env`，按需配置：

```env
APP_NAME=voice_translation_agent
CORS_ORIGINS=http://localhost:5173

USE_REAL_WORKER=true
DEFAULT_SOURCE_LANGUAGE=en
DEFAULT_TARGET_LANGUAGE=zh
FFMPEG_BINARY=ffmpeg

DASHSCOPE_API_KEY=your_dashscope_api_key
ASR_MODEL=fun-asr-realtime

LLM_API_KEY=your_llm_api_key
LLM_BASE_URL=https://api.qnaigc.com/v1
LLM_MODEL=qwen-turbo

USE_LANGCHAIN_INSIGHT_AGENT=true
INSIGHT_AGENT_MODEL=qwen-turbo
INSIGHT_AGENT_TIMEOUT_SECONDS=60
```

说明：

- `USE_REAL_WORKER=true` 时使用真实字幕生成流程；未开启时适合接口联调和前端开发。
- 前端 Vite 代理默认转发到 `http://127.0.0.1:8010`。
- 如果后端端口不是 `8010`，启动前端前设置 `VITE_API_PROXY_TARGET`。

## 安装依赖

后端：

```powershell
cd E:\Code\voice_translation_agent\src\backend
pip install -r requirements.txt
```

前端：

```powershell
cd E:\Code\voice_translation_agent\src\frontend
npm.cmd install
```

## 启动项目

启动后端：

```powershell
cd E:\Code\voice_translation_agent\src\backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

启动前端：

```powershell
cd E:\Code\voice_translation_agent\src\frontend
npm.cmd run dev
```

浏览器打开：

```text
http://127.0.0.1:5173
```

如果后端使用其他端口，例如 `8011`：

```powershell
cd E:\Code\voice_translation_agent\src\frontend
$env:VITE_API_PROXY_TARGET="http://127.0.0.1:8011"
npm.cmd run dev
```

## 常用接口

- `POST /api/jobs`：上传视频并创建字幕任务。
- `GET /api/jobs/{job_id}`：查询任务状态。
- `GET /api/jobs/{job_id}/video`：预览原始视频。
- `GET /api/jobs/{job_id}/events`：订阅任务 SSE 事件。
- `GET /api/jobs/{job_id}/subtitles`：获取结构化字幕。
- `GET /api/jobs/{job_id}/srt`：下载 SRT 字幕。
- `POST /api/jobs/{job_id}/insights`：生成知识洞察。
- `GET /api/jobs/{job_id}/insights`：获取结构化知识洞察。
- `GET /api/jobs/{job_id}/insights/markdown`：下载 Markdown 知识笔记。

## 验证命令

后端测试：

```powershell
cd E:\Code\voice_translation_agent\src\backend
pytest
```

前端测试与构建：

```powershell
cd E:\Code\voice_translation_agent\src\frontend
npm.cmd test
npm.cmd run build
```

## Git 协作

本项目遵循“小功能、小分支、小 PR”的协作方式：

- `master` 保持稳定、可运行、可演示。
- 每个功能从稳定分支切出独立分支。
- 每个 PR 只交付一个清楚、可验证的功能。
- 不提交运行产物、缓存文件、`.env` 或 `文档/` 下的个人规划内容。

更多约定见 `AGENTS.md`。
