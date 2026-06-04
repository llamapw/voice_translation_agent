import argparse
import base64
import os
import pathlib

from dotenv import load_dotenv
from openai import OpenAI


SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DEFAULT_AUDIO_PATH = SCRIPT_DIR / "resources" / "welcome.mp3"
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
QINIU_BASE_URL = "https://api.qnaigc.com/v1"


def load_environment():
    env_path = PROJECT_ROOT / ".env"
    load_dotenv(env_path)


def require_env(name):
    value = os.getenv(name)
    if not value:
        raise EnvironmentError(f"缺少环境变量: {name}，请在项目根目录 .env 中配置")
    return value


def audio_to_data_uri(audio_path):
    audio_path = pathlib.Path(audio_path).expanduser().resolve()
    if not audio_path.exists():
        raise FileNotFoundError(f"音频文件不存在: {audio_path}")
    if audio_path.suffix.lower() != ".mp3":
        raise ValueError(f"当前脚本只处理 MP3 文件: {audio_path}")

    base64_str = base64.b64encode(audio_path.read_bytes()).decode()
    return f"data:audio/mpeg;base64,{base64_str}"


def transcribe_mp3(audio_path, model):
    client = OpenAI(
        api_key=require_env("DASHSCOPE_API_KEY"),
        base_url=DASHSCOPE_BASE_URL,
    )

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": audio_to_data_uri(audio_path),
                        },
                    }
                ],
            }
        ],
        stream=False,
        extra_body={
            "asr_options": {
                "enable_itn": False,
            }
        },
    )

    content = completion.choices[0].message.content
    if not content:
        raise RuntimeError("ASR 未返回识别文本")
    return content.strip()


def get_llm_api_key():
    return os.getenv("qiniu_ai_api_key") or os.getenv("QINIU_AI_API_KEY")


def correct_text(text, model):
    api_key = get_llm_api_key()
    if not api_key:
        raise EnvironmentError("缺少环境变量: qiniu_ai_api_key 或 QINIU_AI_API_KEY")

    client = OpenAI(
        base_url=QINIU_BASE_URL,
        api_key=api_key,
    )

    messages = [
        {
            "role": "system",
            "content": (
                "你是语音识别和翻译文本的后处理专家。"
                "请自动纠正文本中的识别错误、同音误识别、错别字、标点断句错误和明显翻译不顺。"
                "必须保持原意和原语种，不要扩写，不要解释，只输出纠正后的文本。"
            ),
        },
        {
            "role": "user",
            "content": f"请纠正以下文本:\n{text}",
        },
    ]

    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=False,
        max_tokens=4096,
    )

    content = completion.choices[0].message.content
    if not content:
        raise RuntimeError("大模型未返回纠错文本")
    return content.strip()


def parse_args():
    parser = argparse.ArgumentParser(
        description="将 MP3 先通过 ASR 转成文字，再交给大模型自动纠错。"
    )
    parser.add_argument(
        "audio",
        nargs="?",
        default=str(DEFAULT_AUDIO_PATH),
        help=f"输入 MP3 文件路径，默认: {DEFAULT_AUDIO_PATH}",
    )
    parser.add_argument(
        "--asr-model",
        default=os.getenv("ASR_MODEL", "qwen3-asr-flash"),
        help="ASR 模型名称，默认读取 ASR_MODEL 或使用 qwen3-asr-flash",
    )
    parser.add_argument(
        "--llm-model",
        default=os.getenv("LLM_MODEL", "qwen-turbo"),
        help="纠错大模型名称，默认读取 LLM_MODEL 或使用 qwen-turbo",
    )
    return parser.parse_args()


def main():
    load_environment()
    args = parse_args()

    raw_text = transcribe_mp3(args.audio, args.asr_model)
    corrected_text = correct_text(raw_text, args.llm_model)

    print("ASR 原始识别文本:")
    print(raw_text)
    print()
    print("大模型纠错后文本:")
    print(corrected_text)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"错误信息: {exc}")
