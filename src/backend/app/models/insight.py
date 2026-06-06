from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


InsightItemType = Literal["key_point", "chapter", "term", "todo", "decision"]


class InsightItem(BaseModel):
    id: str
    type: InsightItemType
    title: str
    content: str
    source_term: Optional[str] = None
    target_term: Optional[str] = None
    start: float = Field(ge=0)
    end: float = Field(ge=0)
    source_cue_indexes: List[int] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_time_range(self) -> "InsightItem":
        if self.end < self.start:
            raise ValueError("Insight item end must be greater than or equal to start.")
        return self


class InsightRead(BaseModel):
    job_id: str
    summary: str
    items: List[InsightItem] = Field(default_factory=list)
    markdown_url: Optional[str] = None
