# voice_translation_agent src 重构目录

`src/` 是本项目从 `Test/` 原型脚本重构为前后端分离 Web 工程的正式开发目录。

当前目录只用于承载重构后的项目结构。`Test/` 目录继续保留为原型参考，不在本目录中直接修改或复制原型脚本。

## 目录结构

```text
src/
  backend/
    app/
      main.py
      core/
        config.py
        paths.py
      api/
        routes_jobs.py
        routes_subtitles.py
      models/
        job.py
        subtitle.py
      services/
        job_service.py
        media_service.py
        asr_service.py
        llm_service.py
        subtitle_service.py
      workers/
        subtitle_worker.py
      utils/
        ffmpeg.py
        srt.py
    requirements.txt
  frontend/
    src/
      App.vue
      main.ts
      api/
        jobs.ts
        subtitles.ts
      components/
        UploadPanel.vue
        JobStatus.vue
        VideoPlayer.vue
        SubtitlePanel.vue
        SubtitleList.vue
      types/
        job.ts
        subtitle.ts
      styles/
        app.css
    package.json
    vite.config.ts
    tsconfig.json
    index.html
  storage/
    jobs/
```

## 目录职责

- `backend/`：FastAPI 后端服务目录，负责视频上传、任务状态管理、字幕生成流程调度和文件下载。
- `backend/app/core/`：配置读取、路径管理等基础能力。
- `backend/app/api/`：HTTP API 路由。
- `backend/app/models/`：任务、字幕等数据结构。
- `backend/app/services/`：媒体处理、ASR、LLM、字幕生成等业务服务。
- `backend/app/workers/`：后台任务执行流程。
- `backend/app/utils/`：ffmpeg、SRT 等通用工具。
- `frontend/`：Vue 3 + Vite + TypeScript 前端目录。
- `frontend/src/api/`：前端请求后端接口的封装。
- `frontend/src/components/`：单页面展示组件。
- `frontend/src/types/`：前端 TypeScript 类型定义。
- `frontend/src/styles/`：前端样式。
- `storage/jobs/`：本地任务文件目录，用于保存上传视频、处理中间文件和字幕输出。

## 当前状态

除本 README 外，`src/` 下其他文件当前均为空文件，只作为目录结构占位。

后续开发应按单一功能逐步填充文件内容，并在每一步完成后运行对应验证，避免一次性提交大量未验证代码。

## 建议实施顺序

1. 填写后端依赖与 FastAPI 最小启动入口。
2. 定义任务状态模型和字幕数据模型。
3. 实现上传视频和查询任务状态接口。
4. 实现模拟后台任务流程，先验证前后端通信链路。
5. 搭建前端单页面上传、状态展示和轮询逻辑。
6. 从 `Test/video_to_srt.py` 逐步迁移真实 ffmpeg、ASR、LLM 和 SRT 生成能力。
7. 从 `Test/subtitle_viewer_app.py` 迁移字幕展示、当前字幕联动和字幕列表交互思路。

每个阶段应保持一个清晰、可验证的提交目标。

## 分步文件职责

### 1. `backend/requirements.txt`

记录后端运行所需的 Python 依赖。

第一阶段只放 FastAPI 最小后端需要的依赖，包括 Web 框架、ASGI 服务、表单上传支持和配置读取支持。真实 ASR、LLM、ffmpeg 相关依赖后续迁移到对应功能时再添加。

### 2. `backend/app/main.py`

FastAPI 后端应用入口。

后续会在这里创建 FastAPI 应用实例，注册 CORS、挂载 API 路由，并提供最小健康检查或启动验证能力。

### 3. `backend/app/core/config.py`

统一管理运行配置。

后续会负责读取 `.env`、模型名称、API Key、默认语言、CORS 来源、运行环境等配置，避免业务代码直接读取环境变量。

### 4. `backend/app/core/paths.py`

统一管理本地文件路径。

后续会负责生成上传视频、临时音频、字幕 JSON、SRT 输出等路径，保证所有任务文件都落在 `storage/jobs/{job_id}/` 之下。

### 5. `backend/app/models/job.py`

定义字幕生成任务的数据结构。

后续会包含任务 ID、任务状态、进度、提示信息、错误信息、源语言、目标语言、视频地址、字幕地址和 SRT 下载地址。

### 6. `backend/app/models/subtitle.py`

定义字幕条目的数据结构。

后续会包含字幕序号、开始时间、结束时间、原文、译文和前端展示文本。

### 7. 任务接口和服务层

任务接口主要包含：

- `backend/app/api/routes_jobs.py`：上传视频、创建任务、查询任务状态、预览视频。
- `backend/app/api/routes_subtitles.py`：获取结构化字幕、下载 SRT 文件。

服务层主要包含：

- `backend/app/services/job_service.py`：维护内存任务表，创建任务，更新状态和错误。
- `backend/app/services/media_service.py`：处理视频到音频的转换。
- `backend/app/services/asr_service.py`：封装 ASR 识别。
- `backend/app/services/llm_service.py`：封装字幕校对和翻译。
- `backend/app/services/subtitle_service.py`：生成字幕 JSON、SRT 或其他字幕格式。
- `backend/app/workers/subtitle_worker.py`：串联完整后台处理流程。
- `backend/app/utils/ffmpeg.py`：封装 ffmpeg 路径解析和命令执行。
- `backend/app/utils/srt.py`：封装 SRT 时间格式、解析和写入工具。
