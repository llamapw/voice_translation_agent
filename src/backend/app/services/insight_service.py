import json
from pathlib import Path
from typing import List, Optional

from app.agents.insight_agent import InsightAgent, insight_agent
from app.core.paths import build_job_paths
from app.models.insight import InsightRead
from app.models.subtitle import SubtitleCue
from app.utils.insight_markdown import render_insight_markdown


class InsightSourceNotFoundError(FileNotFoundError):
    pass


class InsightNotFoundError(FileNotFoundError):
    pass


class InsightService:
    def __init__(self, agent: InsightAgent = insight_agent) -> None:
        self._agent = agent

    def read_insight(
        self,
        job_id: str,
        storage_root: Optional[Path] = None,
    ) -> InsightRead:
        paths = build_job_paths(job_id, storage_root=storage_root)
        if not paths.insight_json.exists():
            raise InsightNotFoundError(str(paths.insight_json))

        payload = json.loads(paths.insight_json.read_text(encoding="utf-8"))
        return InsightRead.model_validate(payload)

    def generate_basic_insight(
        self,
        job_id: str,
        storage_root: Optional[Path] = None,
    ) -> InsightRead:
        paths = build_job_paths(job_id, storage_root=storage_root)
        if not paths.subtitles_json.exists():
            raise InsightSourceNotFoundError(str(paths.subtitles_json))

        cues = self._read_subtitles(paths.subtitles_json)
        insight = self._agent.generate(job_id, cues)

        paths.root.mkdir(parents=True, exist_ok=True)
        paths.insight_json.write_text(
            json.dumps(insight.model_dump(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        paths.insight_markdown.write_text(
            render_insight_markdown(insight),
            encoding="utf-8",
        )

        return insight

    def _read_subtitles(self, path: Path) -> List[SubtitleCue]:
        raw_cues = json.loads(path.read_text(encoding="utf-8"))
        return [SubtitleCue.model_validate(raw_cue) for raw_cue in raw_cues]


insight_service = InsightService()
