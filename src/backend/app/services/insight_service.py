import json
from pathlib import Path
from typing import List, Optional

from app.core.paths import build_job_paths
from app.models.insight import InsightItem, InsightRead
from app.models.subtitle import SubtitleCue
from app.utils.insight_markdown import render_insight_markdown


class InsightSourceNotFoundError(FileNotFoundError):
    pass


class InsightNotFoundError(FileNotFoundError):
    pass


class InsightService:
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
        insight = InsightRead(
            job_id=job_id,
            summary=self._build_summary(cues),
            items=self._build_items(cues),
            markdown_url="/api/jobs/{0}/insights/markdown".format(job_id),
        )

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

    def _build_summary(self, cues: List[SubtitleCue]) -> str:
        summary_parts = [cue.target_text.strip() for cue in cues[:3] if cue.target_text.strip()]
        return " ".join(summary_parts)

    def _build_items(self, cues: List[SubtitleCue]) -> List[InsightItem]:
        return [
            InsightItem(
                id="key_point_{0}".format(cue.index),
                type="key_point",
                title="片段 {0}".format(cue.index),
                content=cue.target_text,
                start=cue.start,
                end=cue.end,
                source_cue_indexes=[cue.index],
            )
            for cue in cues
        ]


insight_service = InsightService()
