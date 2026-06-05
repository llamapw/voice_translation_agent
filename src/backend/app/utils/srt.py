from typing import List

from app.models.subtitle import SubtitleCue


def format_srt_time(seconds: float) -> str:
    milliseconds = int(round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return "{0:02}:{1:02}:{2:02},{3:03}".format(hours, minutes, secs, millis)


def cues_to_srt(cues: List[SubtitleCue]) -> str:
    blocks = []
    for cue in cues:
        blocks.append(
            "\n".join(
                [
                    str(cue.index),
                    "{0} --> {1}".format(
                        format_srt_time(cue.start),
                        format_srt_time(cue.end),
                    ),
                    cue.display_text or "",
                ]
            )
        )
    return "\n\n".join(blocks) + "\n"
