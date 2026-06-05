import json
from pathlib import Path
from typing import List

from app.models.subtitle import SubtitleCue
from app.utils.srt import cues_to_srt


class SubtitleService:
    def write_subtitles_json(self, cues: List[SubtitleCue], path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                [cue.model_dump() for cue in cues],
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return path

    def write_srt(self, cues: List[SubtitleCue], path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(cues_to_srt(cues), encoding="utf-8")
        return path


subtitle_service = SubtitleService()
