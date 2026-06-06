from typing import List

from app.models.insight import InsightItem, InsightRead
from app.models.subtitle import SubtitleCue


class InsightAgent:
    def generate(self, job_id: str, cues: List[SubtitleCue]) -> InsightRead:
        return InsightRead(
            job_id=job_id,
            summary=self._build_summary(cues),
            items=self._build_items(cues),
            markdown_url="/api/jobs/{0}/insights/markdown".format(job_id),
        )

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


insight_agent = InsightAgent()
