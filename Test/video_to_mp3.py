import argparse
import pathlib
import shutil
import subprocess
import sys


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


def build_output_path(video_path, output_path):
    if output_path:
        return pathlib.Path(output_path).expanduser().resolve()
    return video_path.with_suffix(".mp3")


def extract_audio_to_mp3(video_path, output_path, overwrite):
    video_path = pathlib.Path(video_path).expanduser().resolve()
    if not video_path.exists():
        raise FileNotFoundError(f"视频文件不存在: {video_path}")
    if not video_path.is_file():
        raise ValueError(f"输入路径不是文件: {video_path}")

    output_path = build_output_path(video_path, output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists() and not overwrite:
        raise FileExistsError(f"输出文件已存在，如需覆盖请添加 --overwrite: {output_path}")

    ffmpeg_path = resolve_ffmpeg()
    command = [
        ffmpeg_path,
        "-y" if overwrite else "-n",
        "-i",
        str(video_path),
        "-vn",
        "-acodec",
        "libmp3lame",
        "-b:a",
        "192k",
        str(output_path),
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(f"音频提取失败:\n{result.stderr.strip()}")

    return output_path


def parse_args():
    parser = argparse.ArgumentParser(description="从视频文件中提取语音并转为 MP3。")
    parser.add_argument("video", help="输入视频文件路径，例如 input.mp4")
    parser.add_argument(
        "-o",
        "--output",
        help="输出 MP3 文件路径，默认与视频同目录同名 .mp3",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="如果输出文件已存在，则覆盖它",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    output_path = extract_audio_to_mp3(args.video, args.output, args.overwrite)
    print(f"MP3 文件已生成: {output_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"错误信息: {exc}", file=sys.stderr)
        sys.exit(1)
