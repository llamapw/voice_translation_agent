import asyncio
import argparse
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time

if os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DASHSCOPE_WEBSOCKET_URL = "wss://dashscope.aliyuncs.com/api-ws/v1/inference"
QINIU_BASE_URL = "https://api.qnaigc.com/v1"


def load_environment():
    try:
        from dotenv import load_dotenv
    except ImportError as exc:
        raise RuntimeError(
            "缺少 python-dotenv。请先安装依赖: pip install -r Test\\reqirments.txt"
        ) from exc

    load_dotenv(PROJECT_ROOT / ".env")


def require_env(name):
    value = os.getenv(name)
    if not value:
        raise EnvironmentError(f"缺少环境变量: {name}，请在项目根目录 .env 中配置")
    return value


def create_openai_client(**kwargs):
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError(
            "缺少 openai。请先安装依赖: pip install -r Test\\reqirments.txt"
        ) from exc

    return OpenAI(**kwargs)


def load_dashscope_asr_classes():
    try:
        import dashscope
        from dashscope.audio.asr import Recognition, RecognitionCallback, RecognitionResult
    except ImportError as exc:
        raise RuntimeError(
            "缺少 dashscope。请先安装依赖: pip install -r Test\\reqirments.txt"
        ) from exc

    dashscope.api_key = require_env("DASHSCOPE_API_KEY")
    dashscope.base_websocket_api_url = DASHSCOPE_WEBSOCKET_URL
    return Recognition, RecognitionCallback, RecognitionResult


def resolve_ffmpeg():
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return ffmpeg_path

    try:
        import imageio_ffmpeg
    except ImportError as exc:
        raise RuntimeError(
            "未找到 ffmpeg。请先安装依赖: pip install -r Test\\reqirments.txt"
        ) from exc

    return imageio_ffmpeg.get_ffmpeg_exe()


def run_ffmpeg(command):
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result


def get_media_duration(ffmpeg_path, media_path):
    result = subprocess.run(
        [ffmpeg_path, "-i", str(media_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", result.stderr)
    if not match:
        return None

    hours = int(match.group(1))
    minutes = int(match.group(2))
    seconds = float(match.group(3))
    return hours * 3600 + minutes * 60 + seconds


def get_audio_sample_rate(ffmpeg_path, audio_path):
    result = subprocess.run(
        [ffmpeg_path, "-i", str(audio_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    match = re.search(r"Audio:.*?(\d+)\s*Hz", result.stderr)
    if not match:
        raise RuntimeError(f"无法读取音频采样率: {audio_path}")
    return int(match.group(1))


def extract_media_to_wav_16k(ffmpeg_path, media_path, output_path):
    command = [
        ffmpeg_path,
        "-y",
        "-i",
        str(media_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-acodec",
        "pcm_s16le",
        str(output_path),
    ]
    run_ffmpeg(command)
    return output_path


def prepare_audio_for_fun_asr(ffmpeg_path, media_path, temp_dir):
    return extract_media_to_wav_16k(ffmpeg_path, media_path, temp_dir / "audio.wav")


def create_srt_callback():
    _, RecognitionCallback, RecognitionResult = load_dashscope_asr_classes()

    class SrtRecognitionCallback(RecognitionCallback):
        def __init__(self):
            self.error_message = None
            self.subtitles = []
            self.last_end_ms = 0

        def on_error(self, result):
            self.error_message = result.message
            print("Recognition task_id: ", result.request_id)
            print("Recognition error: ", result.message)

        def on_event(self, result):
            sentence = result.get_sentence()
            sentences = sentence if isinstance(sentence, list) else [sentence]
            for item in sentences:
                if not item or not RecognitionResult.is_sentence_end(item):
                    continue

                text = item.get("text", "").strip()
                if not text:
                    continue

                begin_ms = item.get("begin_time")
                end_ms = item.get("end_time")
                if end_ms is None:
                    continue
                if begin_ms is None:
                    begin_ms = self.last_end_ms

                self.last_end_ms = end_ms
                self.subtitles.append(
                    {
                        "start": begin_ms / 1000,
                        "end": max(end_ms / 1000, begin_ms / 1000 + 0.5),
                        "text": text,
                    }
                )
                print(f"已识别第 {len(self.subtitles)} 条字幕: {text}")

    return SrtRecognitionCallback()


def recognize_audio_with_fun_asr(audio_path, model):
    Recognition, _, _ = load_dashscope_asr_classes()
    ffmpeg_path = resolve_ffmpeg()
    sample_rate = get_audio_sample_rate(ffmpeg_path, audio_path)
    callback = create_srt_callback()
    recognition = Recognition(
        model=model,
        format=audio_path.suffix.lower().lstrip("."),
        sample_rate=sample_rate,
        callback=callback,
    )

    file_buffer = audio_path.read_bytes()
    if not file_buffer:
        raise RuntimeError(f"音频文件为空: {audio_path}")

    print(f"Fun-ASR audio sample rate: {sample_rate}")
    recognition.start()

    offset = 0
    chunk_size = 3200
    while offset < len(file_buffer) and not callback.error_message:
        current_chunk_size = min(chunk_size, len(file_buffer) - offset)
        audio_data = file_buffer[offset:offset + current_chunk_size]
        try:
            recognition.send_audio_frame(audio_data)
        except Exception as send_error:
            callback.error_message = str(send_error)
            print(f"Send audio frame stopped: {send_error}")
            break
        offset += current_chunk_size
        time.sleep(0.1)

    if callback.error_message:
        raise RuntimeError(callback.error_message)

    recognition.stop()
    return callback.subtitles


def get_llm_api_key():
    return os.getenv("qiniu_ai_api_key") or os.getenv("QINIU_AI_API_KEY")


def get_language_name(language):
    language_map = {
        "zh": "简体中文",
        "zh-cn": "简体中文",
        "en": "英文",
        "ja": "日文",
        "ko": "韩文",
    }
    return language_map.get(language.lower(), language)


def polish_subtitle_text(text, model, translate_to):
    api_key = get_llm_api_key()
    if not api_key:
        raise EnvironmentError("缺少环境变量: qiniu_ai_api_key 或 QINIU_AI_API_KEY")

    client = create_openai_client(base_url=QINIU_BASE_URL, api_key=api_key)
    if translate_to:
        target_language = get_language_name(translate_to)
        system_prompt = (
            "你是字幕翻译和校对助手。请先纠正 ASR 造成的错别字、同音误识别、"
            f"断句和标点问题，然后将字幕完整翻译为{target_language}。"
            f"最终输出必须全部使用{target_language}，不要解释，不要添加编号，不要保留原文。"
        )
    else:
        system_prompt = (
            "你是字幕文本校对助手。请纠正 ASR 或翻译造成的错别字、同音误识别、"
            "标点和断句问题。保持原意和原语种，不扩写，不解释，只输出纠正后的字幕文本。"
        )

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {"role": "user", "content": text},
        ],
        stream=False,
        max_tokens=1024,
        temperature=0,
    )

    content = completion.choices[0].message.content
    return content.strip() if content else text


def format_srt_time(seconds):
    milliseconds = int(round(seconds * 1000))
    hours, milliseconds = divmod(milliseconds, 3600 * 1000)
    minutes, milliseconds = divmod(milliseconds, 60 * 1000)
    secs, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{milliseconds:03}"


def write_srt(items, output_path):
    lines = []
    for index, item in enumerate(items, start=1):
        lines.append(str(index))
        lines.append(
            f"{format_srt_time(item['start'])} --> {format_srt_time(item['end'])}"
        )
        lines.append(item["text"])
        lines.append("")

    pathlib.Path(output_path).write_text("\n".join(lines), encoding="utf-8")


def build_output_path(media_path, output_path):
    if output_path:
        return pathlib.Path(output_path).expanduser().resolve()
    return pathlib.Path(media_path).expanduser().resolve().with_suffix(".srt")


def media_to_srt(
    media_path,
    output_path,
    asr_model,
    correct,
    translate_to,
    llm_model,
):
    media_path = pathlib.Path(media_path).expanduser().resolve()
    if not media_path.exists():
        raise FileNotFoundError(f"媒体文件不存在: {media_path}")

    output_path = build_output_path(media_path, output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    ffmpeg_path = resolve_ffmpeg()

    with tempfile.TemporaryDirectory(prefix="voice_agent_srt_") as temp_dir:
        audio_path = prepare_audio_for_fun_asr(
            ffmpeg_path,
            media_path,
            pathlib.Path(temp_dir),
        )
        subtitles = recognize_audio_with_fun_asr(audio_path, asr_model)

    if not subtitles:
        raise RuntimeError("Fun-ASR 未返回可写入 SRT 的句子时间戳")

    for item in subtitles:
        if item["text"] and (correct or translate_to):
            item["text"] = polish_subtitle_text(item["text"], llm_model, translate_to)

    write_srt(subtitles, output_path)
    return output_path


def parse_args():
    parser = argparse.ArgumentParser(
        description="从视频或音频文件生成带时间戳的 SRT 字幕文件。"
    )
    parser.add_argument("media", help="输入视频或音频文件路径，例如 input.mp4")
    parser.add_argument(
        "-o",
        "--output",
        help="输出 SRT 文件路径，默认与输入文件同目录同名 .srt",
    )
    parser.add_argument(
        "--asr-model",
        help="ASR 模型名称，默认读取 ASR_MODEL 或使用 fun-asr-realtime",
    )
    parser.add_argument(
        "--correct",
        action="store_true",
        help="启用大模型字幕纠错，会额外调用文本大模型",
    )
    parser.add_argument(
        "--translate-to",
        help="将字幕翻译为目标语言，例如 zh、en、ja。不传则不翻译",
    )
    parser.add_argument(
        "--llm-model",
        help="纠错大模型名称，默认读取 LLM_MODEL 或使用 qwen-turbo",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    load_environment()

    asr_model = args.asr_model or os.getenv("ASR_MODEL", "fun-asr-realtime")
    llm_model = args.llm_model or os.getenv("LLM_MODEL", "qwen-turbo")

    output_path = media_to_srt(
        media_path=args.media,
        output_path=args.output,
        asr_model=asr_model,
        correct=args.correct,
        translate_to=args.translate_to,
        llm_model=llm_model,
    )
    print(f"SRT 文件已生成: {output_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"错误信息: {exc}", file=sys.stderr)
        sys.exit(1)
