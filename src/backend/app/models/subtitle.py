from typing import Optional

from pydantic import BaseModel, model_validator


class SubtitleCue(BaseModel):
    index: int
    start: float
    end: float
    source_text: str
    target_text: str
    display_text: Optional[str] = None

    @model_validator(mode="after")
    def build_display_text(self) -> "SubtitleCue":
        if self.display_text is None:
            self.display_text = "{0}\n{1}".format(self.source_text, self.target_text)
        return self
