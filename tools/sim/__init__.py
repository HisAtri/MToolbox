import os
from mutagen import File
from itertools import islice
from flask import Flask, request

from runtime import COLOR as color
from . import md5 as hash_
from .. import check_ffmpeg

html = r"""
<!DOCTYPE html>
<html>
<head>
    <title>文件管理-WebUI</title>
    <style>
        .textshow{
            padding: 10px;
            margin: 5px;
        }
    </style>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css" integrity="sha384-xOolHFLEh07PJGoPkLv1IbcEPTNtaed2xpHsD9ESMhqIYd0nLMwNLD69Npy4HI+N" crossorigin="anonymous">
    <script>
        function handleClick(event) {
            var div = event.currentTarget;
            var path = div.querySelector('.path').textContent;
            var confirmDialog = confirm('确定要删除文件' + path + '吗？');

            if (confirmDialog) {
                fetch('/api', {
                    method: 'POST',
                    body: path
                })
                    .then(function (response) {
                        if (response.status === 200) {
                            div.style.display = 'none';
                        } else {
                            alert('请求失败');
                        }
                    })
                    .catch(function (error) {
                        alert('请求失败: ' + error);
                    });
            }
        }
    </script>
</head>
<body>
<div class="container">
<h1>MD5重复文件</h1>
"""


def format_file_size(file_size):
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    while file_size >= 1024 and unit_index < len(units) - 1:
        file_size /= 1024
        unit_index += 1
    return f"{file_size:.2f}{units[unit_index]}"


def get_audio_info(musicPath):
    result = []
    file_size = os.path.getsize(musicPath)
    file_size_str = f"{file_size / (1024 * 1024):.2f}MB"
    result.append(f"文件大小：{file_size_str}")
    try:
        audio = File(musicPath)
    except Exception as e:
        print(musicPath + str(e))
        return f"文件大小：{file_size_str}"
    # 获取标签信息
    if audio and audio.tags:
        tags = audio.tags
        # 获取音乐标题
        title = tags.get("title")
        if title:
            result.append(f"标题：{title[0]}")
        # 获取艺人
        artist = tags.get("artist")
        if artist:
            result.append(f"艺人：{artist[0]}")
        # 获取专辑
        album = tags.get("album")
        if album:
            result.append(f"专辑：{album[0]}")
        # 获取时长
        duration = audio.info.length
        duration_str = f"{int(duration // 60):02d}:{int(duration % 60):02d}"
        result.append(f"时长：{duration_str}")
        # 获取码率
        bitrate = audio.info.bitrate // 1000 if audio.info.bitrate else None
        if bitrate:
            result.append(f"码率：{bitrate}kbps")
    return "；".join(result)


# 列出cluster下的每一个文件构建HTML
def divCluster(cluster):
    ClusterHTML = ""
    for musicPath in cluster:
        ClusterHTML += f"<div class=\"textshow card\" onclick=\"handleClick(event)\"><p class=\"path\">{musicPath}</p><p>{get_audio_info(musicPath)}</p><p>点击删除此文件</p></div>\n"
    return ClusterHTML


def main():
    _path = input("请输入音乐根文件夹：")
    if not os.path.isdir(_path) or not _path:
        print(f"{color.red}定义的路径不存在{color.end}")
    if not check_ffmpeg.is_ffmpeg_available():
        print(f"{color.red}ffmpeg命令不可用。\n请前往 https://ffmpeg.org 安装FFmpeg{color.end}")
        return
    duplicateList = hash_.find_duplicate_audio_files(_path)
    htmlbody = ""
    # 限制单次最多调用50个
    limititems = 50
    limited_duplicateList = islice(duplicateList, limititems)
    for cluster in limited_duplicateList:
        # 构建每个cluster的外层的DIV
        htmlbody += "<div class=\"clustershow alert alert-dark shadow p-3 mb-5 rounded \" role=\"alert\"><p>Cluster</p>"
        htmlbody += divCluster(cluster)
        htmlbody += "</div>"
    htmlbody += "</div></body></html>"

    fullHTML = html + htmlbody
    print("即将启动Flask服务器，默认访问地址为http://127.0.0.1:5000\n可通过 Ctrl+C 结束服务器")

    app = Flask(__name__)

    @app.route('/')
    def hello():
        return fullHTML

    @app.route('/api', methods=['POST'])
    def delete_file():
        file_path = request.get_data(as_text=True)  # 获取请求中的文本内容
        try:
            os.remove(file_path)  # 尝试删除文件
            return '', 200  # 返回状态码 200 表示删除成功
        except Exception as e:
            return str(e), 500  # 返回状态码 500 表示删除失败，并返回错误信息

    app.run()
