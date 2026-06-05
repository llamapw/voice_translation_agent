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
