from openai import OpenAI
import os
import pathlib
from dotenv import load_dotenv

# 加载环境变量
script_dir = pathlib.Path(__file__).resolve().parent
env_path = script_dir.parent / ".env"
load_dotenv(env_path)

openai_base_url = 'https://api.qnaigc.com/v1'
openai_api_key = os.getenv("qiniu_ai_api_key")

client = OpenAI(
    base_url=openai_base_url,
    api_key=openai_api_key
)

# 发送带有流式输出的请求
content = ""
messages = [
    {"role": "user", "content": "夸一夸七牛云 AI 推理服务"}
]
response = client.chat.completions.create(
    model="qwen-turbo",
    messages=messages,
    stream=True,  # 启用流式输出
    max_tokens=4096
)

# 逐步接收并处理响应
for chunk in response:
    if chunk.choices[0].delta.content:
        content += chunk.choices[0].delta.content

print("第一轮回复:")
print(content)

# Round 2 - 继续对话
messages.append({"role": "assistant", "content": content})
messages.append({'role': 'user', 'content': "继续"})

response = client.chat.completions.create(
    model="qwen-turbo",
    messages=messages,
    stream=True
)

# 重置 content 变量来存储第二轮回复
second_content = ""
for chunk in response:
    if chunk.choices[0].delta.content:
        second_content += chunk.choices[0].delta.content

print("第二轮回复:")
print(second_content)
