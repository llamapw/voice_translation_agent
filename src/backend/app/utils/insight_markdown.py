from app.models.insight import InsightRead


ITEM_TYPE_TITLES = {
    "chapter": "章节",
    "key_point": "关键要点",
    "term": "术语",
    "todo": "待办",
    "decision": "关键决策",
}

ITEM_TYPE_ORDER = ["chapter", "key_point", "term", "todo", "decision"]


def format_markdown_time(seconds: float) -> str:
    milliseconds = int(round(seconds * 1000))
    minutes, remainder = divmod(milliseconds, 60_000)
    secs, millis = divmod(remainder, 1000)
    return "{0:02}:{1:02}.{2:03}".format(minutes, secs, millis)


def render_insight_markdown(insight: InsightRead) -> str:
    lines = [
        "# 视频知识笔记",
        "",
        "任务 ID: `{0}`".format(insight.job_id),
        "",
        "## 摘要",
        "",
        insight.summary,
    ]

    for item_type in ITEM_TYPE_ORDER:
        items = [item for item in insight.items if item.type == item_type]
        if not items:
            continue

        lines.extend(["", "## {0}".format(ITEM_TYPE_TITLES[item_type]), ""])
        for item in items:
            lines.append(
                "- [{0}] **{1}**".format(format_markdown_time(item.start), item.title)
            )
            lines.append("  {0}".format(item.content))
            if item.source_cue_indexes:
                cue_indexes = ", ".join(str(index) for index in item.source_cue_indexes)
                lines.append("  来源字幕: {0}".format(cue_indexes))

    return "\n".join(lines) + "\n"
