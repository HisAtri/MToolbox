import os
import hashlib
import json
from tqdm import tqdm
import subprocess

from runtime import VAL

cache = VAL.cache_path


def find_duplicate_audio_files(root_dir):
    audio_files = {}
    duplicate_files = []

    # 尝试读取保存的MD5值字典
    md5_dict = read_md5_dict()

    # 获取音频文件列表
    audio_files_list = get_audio_files_list(root_dir)

    # 遍历文件列表，并显示进度条
    with tqdm(total=len(audio_files_list), desc='Processing') as pbar:
        for file_path in audio_files_list:
            # 检查是否存在对应的MD5值
            if file_path in md5_dict:
                audio_hash = md5_dict[file_path]
            else:
                audio_hash = calculate_md5(file_path)
                # 更新MD5值字典
                md5_dict[file_path] = audio_hash
            if audio_hash in audio_files:
                audio_files[audio_hash].append(file_path)
            else:
                audio_files[audio_hash] = [file_path]
                save_md5_dict(md5_dict)
            pbar.update(1)

    # 找到重复的文件
    for audio_hash, files in audio_files.items():
        if len(files) > 1:
            duplicate_files.append(files)

    # 保存MD5值字典
    save_md5_dict(md5_dict)

    return duplicate_files


def get_audio_files_list(root_dir):
    audio_files_list = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            if is_audio_file(file_path):
                audio_files_list.append(file_path)
    return audio_files_list


def is_audio_file(file_path):
    audio_extensions = ['.mp3', '.flac']
    _, ext = os.path.splitext(file_path)
    return ext.lower() in audio_extensions


def calculate_md5(file_path):
    # 获取拓展名
    extension = os.path.splitext(file_path)[1]
    chunk_size = 4096
    hash_md5 = hashlib.md5()
    # 检查临时文件是否存在，如果有则删除
    temp_file_path = os.path.join(cache, f"cache_file{extension}")
    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)

    # 使用FFmpeg清除所有metadata
    ffmpeg_cmd = ['ffmpeg', '-i', file_path, '-map', '0:a', '-c:a', 'copy', '-map_metadata', '-1', temp_file_path]
    subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # 清除完成后，继续使用临时文件计算MD5
    with open(temp_file_path, 'rb') as f:
        chunk = f.read(chunk_size)
        while chunk:
            hash_md5.update(chunk)
            chunk = f.read(chunk_size)
    # 删除临时文件
    os.remove(temp_file_path)
    # 返回MD5
    return hash_md5.hexdigest()


def read_md5_dict():
    md5_dict = {}
    if os.path.exists('md5_dict.json'):
        with open('md5_dict.json', 'r') as f:
            md5_dict = json.load(f)
    return md5_dict


def save_md5_dict(md5_dict):
    with open('md5_dict.json', 'w') as f:
        json.dump(md5_dict, f)
