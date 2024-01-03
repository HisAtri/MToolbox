import subprocess

from runtime import COLOR as color


def get_ffmpeg_version():
    try:
        result = subprocess.run(["ffmpeg", '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
                                text=True)
        return result.stdout.splitlines()[0]
    except subprocess.CalledProcessError:
        return False


def is_ffmpeg_available():
    try:
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def main():
    ffmpeg_version = get_ffmpeg_version()

    if is_ffmpeg_available():
        print(f"{color.green}ffmpeg可用{color.end}")
        print(f"{color.blue}ffmpeg版本信息:\n{ffmpeg_version}{color.end}")
    else:
        print(f"{color.red}ffmpeg命令不可用。\n请前往 https://ffmpeg.org 安装FFmpeg{color.end}")
