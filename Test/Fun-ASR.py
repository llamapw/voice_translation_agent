import asyncio
import os
import re
import shutil
import subprocess
import time

if os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import dashscope
from dashscope.audio.asr import *

import pathlib
from dotenv import load_dotenv
from datetime import datetime

# 加载环境变量
script_dir = pathlib.Path(__file__).resolve().parent
env_path = script_dir.parent / ".env"
load_dotenv(env_path)
audio_path = script_dir / "resources" / "welcome.mp3"

# 新加坡和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
# 若没有配置环境变量，请用百炼API Key将下行替换为：dashscope.api_key = "sk-xxx"
dashscope.api_key = os.environ.get('DASHSCOPE_API_KEY')
if not dashscope.api_key:
    raise EnvironmentError("缺少环境变量 DASHSCOPE_API_KEY，请在项目根目录 .env 中配置")

# 以下为华北2（北京）地域的URL，各地域的URL不同。
dashscope.base_websocket_api_url = 'wss://dashscope.aliyuncs.com/api-ws/v1/inference'

def get_timestamp():
    now = datetime.now()
    formatted_timestamp = now.strftime("[%Y-%m-%d %H:%M:%S.%f]")
    return formatted_timestamp


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


def get_audio_sample_rate(path):
    ffmpeg_path = resolve_ffmpeg()
    result = subprocess.run(
        [ffmpeg_path, "-i", str(path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    match = re.search(r"Audio:.*?(\d+)\s*Hz", result.stderr)
    if not match:
        raise RuntimeError(f"无法读取音频采样率: {path}")
    return int(match.group(1))


class Callback(RecognitionCallback):
    def __init__(self):
        self.error_message = None

    def on_complete(self) -> None:
        print(get_timestamp() + ' Recognition completed')  # recognition complete

    def on_error(self, result: RecognitionResult) -> None:
        self.error_message = result.message
        print('Recognition task_id: ', result.request_id)
        print('Recognition error: ', result.message)

    def on_event(self, result: RecognitionResult) -> None:
        sentence = result.get_sentence()
        if 'text' in sentence:
            print(get_timestamp() + ' RecognitionCallback text: ', sentence['text'])
        if RecognitionResult.is_sentence_end(sentence):
            print(get_timestamp() +
                  'RecognitionCallback sentence end, request_id:%s, usage:%s'
                  % (result.get_request_id(), result.get_usage(sentence)))

callback = Callback()
audio_sample_rate = get_audio_sample_rate(audio_path)

recognition = Recognition(model='fun-asr-realtime',
                          format=audio_path.suffix.lower().lstrip("."),
                          sample_rate=audio_sample_rate,
                          callback=callback)

try:
    audio_data: bytes = None
    if not audio_path.exists():
        raise FileNotFoundError(f"音频文件不存在: {audio_path}")
    if audio_path.stat().st_size:
        # 一次性将文件数据全部读入buffer
        file_buffer = audio_path.read_bytes()
        print(f"Audio sample rate: {audio_sample_rate}")
        print("Start Recognition")
        recognition.start()

        # 从buffer中间隔3200字节发送一次
        buffer_size = len(file_buffer)
        offset = 0
        chunk_size = 3200

        while offset < buffer_size and not callback.error_message:
            # 计算本次要发送的数据块大小
            remaining_bytes = buffer_size - offset
            current_chunk_size = min(chunk_size, remaining_bytes)

            # 从buffer中提取当前数据块
            audio_data = file_buffer[offset:offset + current_chunk_size]

            # 发送音频数据帧
            try:
                recognition.send_audio_frame(audio_data)
            except Exception as send_error:
                callback.error_message = str(send_error)
                print(f"Send audio frame stopped: {send_error}")
                break
            # 更新偏移量
            offset += current_chunk_size

            # 添加延迟模拟实时传输
            time.sleep(0.1)

        if callback.error_message:
            raise RuntimeError(callback.error_message)

        recognition.stop()
    else:
        raise Exception(
            'The supplied file was empty (zero bytes long)')
except Exception as e:
    raise e

print(
    '[Metric] requestId: {}, first package delay ms: {}, last package delay ms: {}'
    .format(
        recognition.get_last_request_id(),
        recognition.get_first_package_delay(),
        recognition.get_last_package_delay(),
    ))
