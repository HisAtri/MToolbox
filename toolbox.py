from runtime import COLOR as color
from tools import check_ffmpeg
from tools import sim
from tools import wav2flac

MENU = """
------菜单------
1. 检查FFMpeg安装状态
2. 音乐去重（哈希）
3. 音乐AI去重
4. 将WAV转换为FLAC
------END------
"""

if __name__ == '__main__':
    print(color.cyan, MENU, color.end)
    print("请输入指令对应的编号")
    command = input(">>")

    match command:
        case "1":
            check_ffmpeg.main()
        case "2":
            sim.main()
        case "3":
            print(f"{color.yellow}鉴于依赖项Librosa还没支持Python3.12，")
            print(f"因此我先摸鱼一会儿，此功能暂不可用{color.end}")
        case "4":
            wav2flac.main()
        case _:
            print(f"{color.red}无效的命令{color.end}")
