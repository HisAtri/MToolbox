import os
import re

import subprocess

from runtime import COLOR as color
from runtime import VAL as val
from .. import check_ffmpeg


def main():
    color.clear_screen()
    extensions = (".wav", ".wmv", ".aac")
    if not check_ffmpeg.is_ffmpeg_available():
        print(f"{color.red}ffmpeg命令不可用。\n请前往 https://ffmpeg.org 安装FFmpeg{color.end}")
        return
    print(
        "此功能需要ffmpeg\n- 程序会自动遍历子目录下的所有WAV文件\n- 转换为FLAC后，新路径中保留目录结构\n- 输出目录留空，代表在原地转码")
    print(f"此功能支持自动识别并转换{"/".join(extensions)}文件")
    input_dir = input(f"{color.magenta}要转换的音乐文件目录：{color.end}")
    output_dir = input(f"{color.magenta}FLAC文件输出目录（留空代表与原始文件相同）：{color.end}")
    if not output_dir:
        output_dir = input_dir
    # 检查input_dir是否为合法路径
    if not os.path.isdir(input_dir):
        print(f"{color.red}定义的WAV文件路径不存在{color.end}")
        return

    # 遍历input_dir下的所有wav文件
    wav_files = []
    succeed_list = []
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(extensions):
                input_file = os.path.join(root, file)
                output_file = os.path.join(output_dir,
                                           os.path.relpath(os.path.join(root, file), input_dir))
                real_output_file = re.sub(r'\.wav$', '.flac', output_file, flags=re.IGNORECASE)
                wav_files.append([input_file, real_output_file])

    if len(wav_files) == 0:
        print(f"{color.red}指定目录下未找到WAV文件{color.end}")
        return

    print(f"{color.green}已获取{len(wav_files)}个WAV文件，开始转换{color.end}")

    for obj in wav_files:
        command = [val.ffmpeg, "-i", obj[0], "-c:a", "flac", "-compression_level", "8", "-write_id3v2", "1", "-y", obj[1]]
        print(command)
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            print(f"{color.bg_green}File {obj[1]} transcode successfully{color.end}")
            succeed_list.append(obj[0])
        else:
            print(f"{color.red}{obj[0]}Error! ffmpeg abort with code {result.returncode}{color.end}")

    del_det = input("是否删除成功转换的文件(Y/N :N)")
    if del_det and del_det in "Yy":
        for file in succeed_list:
            os.remove(file)
