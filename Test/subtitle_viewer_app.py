import base64
import html
import json
import mimetypes
import pathlib
import re
import tempfile

import streamlit as st
import streamlit.components.v1 as components

import video_to_srt


LANGUAGE_CODE_BY_LABEL = {
    "中文": "zh",
    "英文": "en",
}


def parse_srt_time(value):
    match = re.match(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})", value.strip())
    if not match:
        raise ValueError(f"无效 SRT 时间: {value}")

    hours, minutes, seconds, milliseconds = [int(part) for part in match.groups()]
    return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000


def parse_srt(text):
    cues = []
    blocks = re.split(r"\n\s*\n", text.replace("\r\n", "\n").strip())
    for block in blocks:
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        if len(lines) < 2:
            continue

        time_line_index = 1 if re.match(r"^\d+$", lines[0]) else 0
        if time_line_index >= len(lines) or "-->" not in lines[time_line_index]:
            continue

        start_raw, end_raw = lines[time_line_index].split("-->", 1)
        text_lines = lines[time_line_index + 1:]
        if not text_lines:
            continue

        cues.append(
            {
                "start": parse_srt_time(start_raw),
                "end": parse_srt_time(end_raw),
                "text": "\n".join(text_lines),
            }
        )
    return cues


def split_bilingual_text(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return "", ""
    if len(lines) == 1:
        return lines[0], ""
    return lines[0], "\n".join(lines[1:])


def build_language_tracks(cues, source_language, target_language, subtitle_mode):
    tracks = {"zh": [], "en": []}
    for cue in cues:
        base = {"start": cue["start"], "end": cue["end"]}
        if subtitle_mode == "bilingual":
            source_text, target_text = split_bilingual_text(cue["text"])
            if source_text:
                tracks.setdefault(source_language, []).append(
                    {**base, "text": source_text}
                )
            if target_text:
                tracks.setdefault(target_language, []).append(
                    {**base, "text": target_text}
                )
            continue

        tracks.setdefault(target_language, []).append({**base, "text": cue["text"]})

    return tracks


def escape_subtitle(text):
    return "<br>".join(html.escape(line) for line in text.splitlines())


def cue_or_none(cues, index):
    if index < len(cues):
        return cues[index]
    return None


def build_display_cues(zh_cues, en_cues, mode):
    if mode == "中文":
        source = zh_cues or en_cues
        return [
            {
                "start": cue["start"],
                "end": cue["end"],
                "html": f"<div class='subtitle-zh'>{escape_subtitle(cue['text'])}</div>",
            }
            for cue in source
        ]

    if mode == "英文":
        source = en_cues or zh_cues
        return [
            {
                "start": cue["start"],
                "end": cue["end"],
                "html": f"<div class='subtitle-en'>{escape_subtitle(cue['text'])}</div>",
            }
            for cue in source
        ]

    display_cues = []
    cue_count = max(len(zh_cues), len(en_cues))
    for index in range(cue_count):
        zh_cue = cue_or_none(zh_cues, index)
        en_cue = cue_or_none(en_cues, index)
        base_cue = zh_cue or en_cue
        if not base_cue:
            continue

        parts = []
        if en_cue:
            parts.append(f"<div class='subtitle-en'>{escape_subtitle(en_cue['text'])}</div>")
        if zh_cue:
            parts.append(f"<div class='subtitle-zh'>{escape_subtitle(zh_cue['text'])}</div>")

        display_cues.append(
            {
                "start": base_cue["start"],
                "end": base_cue["end"],
                "html": "".join(parts),
            }
        )
    return display_cues


def make_video_data_url(video_bytes, filename):
    mime_type = mimetypes.guess_type(filename)[0] or "video/mp4"
    encoded = base64.b64encode(video_bytes).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def render_player(video_data_url, cues):
    payload = json.dumps(cues, ensure_ascii=False)
    components.html(
        f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <style>
    body {{
      margin: 0;
      font-family: Arial, "Microsoft YaHei", sans-serif;
      background: #f7f8fa;
      color: #1f2933;
    }}
    .player {{
      width: 100%;
      background: #101418;
    }}
    video {{
      display: block;
      width: 100%;
      max-height: 520px;
      background: #000;
    }}
    .active-subtitle {{
      min-height: 72px;
      padding: 16px 18px;
      background: #ffffff;
      border-bottom: 1px solid #d9dee7;
      font-size: 20px;
      line-height: 1.55;
    }}
    .subtitle-list {{
      height: 340px;
      overflow-y: auto;
      background: #ffffff;
      border-top: 1px solid #e5e9f0;
    }}
    .cue {{
      width: 100%;
      display: grid;
      grid-template-columns: 112px 1fr;
      gap: 12px;
      border: 0;
      border-bottom: 1px solid #edf0f5;
      background: #ffffff;
      padding: 12px 14px;
      text-align: left;
      cursor: pointer;
      font-size: 15px;
      line-height: 1.45;
    }}
    .cue:hover {{
      background: #f2f6fb;
    }}
    .cue.active {{
      background: #e9f2ff;
      border-left: 4px solid #2563eb;
    }}
    .time {{
      color: #56657a;
      font-variant-numeric: tabular-nums;
      white-space: nowrap;
    }}
    .subtitle-en {{
      color: #293241;
    }}
    .subtitle-zh {{
      color: #0f172a;
      font-weight: 600;
      margin-top: 2px;
    }}
  </style>
</head>
<body>
  <div class="player">
    <video id="video" controls preload="metadata" src="{video_data_url}"></video>
  </div>
  <div id="activeSubtitle" class="active-subtitle"></div>
  <div id="subtitleList" class="subtitle-list"></div>

  <script>
    const cues = {payload};
    const video = document.getElementById("video");
    const activeSubtitle = document.getElementById("activeSubtitle");
    const subtitleList = document.getElementById("subtitleList");

    function formatTime(seconds) {{
      const total = Math.max(0, Math.floor(seconds));
      const h = String(Math.floor(total / 3600)).padStart(2, "0");
      const m = String(Math.floor((total % 3600) / 60)).padStart(2, "0");
      const s = String(total % 60).padStart(2, "0");
      return `${{h}}:${{m}}:${{s}}`;
    }}

    function renderList() {{
      subtitleList.innerHTML = "";
      cues.forEach((cue, index) => {{
        const item = document.createElement("button");
        item.className = "cue";
        item.dataset.index = index;
        item.innerHTML = `<span class="time">${{formatTime(cue.start)}}</span><span>${{cue.html}}</span>`;
        item.addEventListener("click", () => {{
          video.currentTime = cue.start;
          video.play();
          setActive(index);
        }});
        subtitleList.appendChild(item);
      }});
    }}

    function findCueIndex(time) {{
      return cues.findIndex((cue) => time >= cue.start && time <= cue.end);
    }}

    function setActive(index) {{
      const items = subtitleList.querySelectorAll(".cue");
      items.forEach((item) => item.classList.remove("active"));

      if (index < 0 || index >= cues.length) {{
        activeSubtitle.innerHTML = "";
        return;
      }}

      activeSubtitle.innerHTML = cues[index].html;
      const active = subtitleList.querySelector(`[data-index="${{index}}"]`);
      if (active) {{
        active.classList.add("active");
        active.scrollIntoView({{ block: "nearest" }});
      }}
    }}

    video.addEventListener("timeupdate", () => {{
      setActive(findCueIndex(video.currentTime));
    }});

    renderList();
    if (cues.length > 0) {{
      setActive(0);
    }}
  </script>
</body>
</html>
        """,
        height=980,
        scrolling=False,
    )


def generate_srt_from_upload(
    uploaded_video,
    source_language,
    target_language,
    correct,
    asr_model,
    llm_model,
):
    video_bytes = uploaded_video.getvalue()
    video_name = pathlib.Path(uploaded_video.name).name

    video_to_srt.load_environment()
    with tempfile.TemporaryDirectory(prefix="voice_agent_streamlit_") as temp_dir:
        temp_dir_path = pathlib.Path(temp_dir)
        media_path = temp_dir_path / video_name
        output_path = temp_dir_path / "output.srt"
        media_path.write_bytes(video_bytes)

        video_to_srt.media_to_srt(
            media_path=media_path,
            output_path=output_path,
            asr_model=asr_model,
            correct=correct,
            translate_to=target_language,
            llm_model=llm_model,
            subtitle_mode="bilingual",
        )
        srt_text = output_path.read_text(encoding="utf-8-sig")

    return {
        "video_bytes": video_bytes,
        "video_name": video_name,
        "srt_text": srt_text,
        "source_language": source_language,
        "target_language": target_language,
        "subtitle_mode": "bilingual",
    }


def main():
    st.set_page_config(page_title="视频字幕生成预览", layout="wide")
    st.title("视频字幕生成预览")

    with st.sidebar:
        st.header("生成")
        video_upload = st.file_uploader(
            "上传视频",
            type=["mp4", "mov", "mkv", "webm"],
        )
        source_label = st.selectbox("原文语言", ["英文", "中文"], index=0)
        target_label = st.selectbox("翻译目标", ["中文", "英文"], index=0)
        correct = st.checkbox("校对原文", value=False)
        asr_model = st.text_input("ASR 模型", value="fun-asr-realtime")
        llm_model = st.text_input("LLM 模型", value="qwen-turbo")
        generate = st.button("生成字幕", type="primary", use_container_width=True)

        st.header("展示")
        mode = st.radio("字幕语言", ["中文", "英文", "双语"], horizontal=True)

    source_language = LANGUAGE_CODE_BY_LABEL[source_label]
    target_language = LANGUAGE_CODE_BY_LABEL[target_label]

    if generate:
        if video_upload is None:
            st.warning("请先上传一个视频文件。")
        elif source_language == target_language:
            st.warning("原文语言和翻译目标不能相同。")
        else:
            with st.spinner("正在识别语音并生成双语字幕..."):
                try:
                    st.session_state["generated_subtitle"] = generate_srt_from_upload(
                        uploaded_video=video_upload,
                        source_language=source_language,
                        target_language=target_language,
                        correct=correct,
                        asr_model=asr_model,
                        llm_model=llm_model,
                    )
                except Exception as exc:
                    st.error(f"字幕生成失败: {exc}")
                else:
                    st.success("字幕生成完成。")

    generated = st.session_state.get("generated_subtitle")
    if not generated:
        st.info("上传视频后点击“生成字幕”，页面会自动调用 video_to_srt.py 并展示字幕。")
        return

    cues = parse_srt(generated["srt_text"])
    tracks = build_language_tracks(
        cues,
        source_language=generated["source_language"],
        target_language=generated["target_language"],
        subtitle_mode=generated["subtitle_mode"],
    )
    zh_cues = tracks.get("zh", [])
    en_cues = tracks.get("en", [])

    if mode == "中文" and not zh_cues:
        st.warning("生成结果中没有可展示的中文字幕。")
    if mode == "英文" and not en_cues:
        st.warning("生成结果中没有可展示的英文字幕。")

    display_cues = build_display_cues(zh_cues, en_cues, mode)
    if not display_cues:
        st.warning("没有可展示的字幕内容。")
        return

    st.download_button(
        "下载生成的 SRT",
        data=generated["srt_text"].encode("utf-8"),
        file_name=pathlib.Path(generated["video_name"]).with_suffix(".srt").name,
        mime="application/x-subrip",
    )

    video_data_url = make_video_data_url(
        generated["video_bytes"],
        generated["video_name"],
    )
    render_player(video_data_url, display_cues)


if __name__ == "__main__":
    main()
