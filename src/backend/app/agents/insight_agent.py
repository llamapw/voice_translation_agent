import json
from typing import Any, List, Optional

from app.core.config import settings
from app.models.insight import InsightItem, InsightRead
from app.models.subtitle import SubtitleCue


class InsightAgentError(RuntimeError):
    pass


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


class LangChainInsightAgent(InsightAgent):
    def __init__(
        self,
        chat_model: Optional[Any] = None,
        model: str = settings.insight_agent_model,
        base_url: str = settings.llm_base_url,
        api_key: Optional[str] = settings.llm_api_key,
        timeout: int = settings.insight_agent_timeout_seconds,
    ) -> None:
        self._chat_model = chat_model or self._create_chat_model(
            model=model,
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
        )

    def generate(self, job_id: str, cues: List[SubtitleCue]) -> InsightRead:
        response = self._chat_model.invoke(
            [
                {
                    "role": "system",
                    "content": self._build_system_prompt(),
                },
                {
                    "role": "user",
                    "content": self._build_user_prompt(cues),
                },
            ]
        )
        payload = self._parse_response_content(self._extract_response_content(response))
        return InsightRead(
            job_id=job_id,
            summary=payload.get("summary", ""),
            items=payload.get("items", []),
            markdown_url="/api/jobs/{0}/insights/markdown".format(job_id),
        )

    def _create_chat_model(
        self,
        model: str,
        base_url: str,
        api_key: Optional[str],
        timeout: int,
    ) -> Any:
        if not api_key:
            raise InsightAgentError("Missing LLM_API_KEY for LangChain Insight Agent.")

        try:
            from langchain_openai import ChatOpenAI
        except ImportError as error:
            raise InsightAgentError("Missing langchain-openai dependency.") from error

        return ChatOpenAI(
            model=model,
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            temperature=0,
        )

    def _build_system_prompt(self) -> str:
        return (
            "你是视频知识理解助手。请根据字幕生成结构化知识笔记，"
            "只输出 JSON，不要输出解释。"
        )

    def _build_user_prompt(self, cues: List[SubtitleCue]) -> str:
        cue_lines = [
            "[{index}] {start:.3f}-{end:.3f}\n原文: {source}\n译文: {target}".format(
                index=cue.index,
                start=cue.start,
                end=cue.end,
                source=cue.source_text,
                target=cue.target_text,
            )
            for cue in cues
        ]
        return (
            "请输出以下 JSON 结构:\n"
            "{{\n"
            '  "summary": "视频摘要",\n'
            '  "items": [\n'
            "    {{\n"
            '      "id": "key_point_1",\n'
            '      "type": "key_point",\n'
            '      "title": "要点标题",\n'
            '      "content": "要点内容",\n'
            '      "start": 0.0,\n'
            '      "end": 1.0,\n'
            '      "source_cue_indexes": [1]\n'
            "    }}\n"
            "  ]\n"
            "}}\n\n"
            "可用 type: chapter, key_point, term, todo, decision。\n"
            "字幕:\n{0}".format("\n\n".join(cue_lines))
        )

    def _extract_response_content(self, response: Any) -> str:
        if isinstance(response, str):
            return response

        content = getattr(response, "content", None)
        if isinstance(content, str):
            return content

        raise InsightAgentError("LangChain Insight Agent returned empty content.")

    def _parse_response_content(self, content: str) -> dict:
        text = content.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].strip().startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            text = "\n".join(line.strip() for line in lines).strip()

        try:
            payload = json.loads(text)
        except json.JSONDecodeError as error:
            raise InsightAgentError("LangChain Insight Agent returned invalid JSON.") from error

        if not isinstance(payload, dict):
            raise InsightAgentError("LangChain Insight Agent JSON must be an object.")

        return payload


insight_agent = InsightAgent()
