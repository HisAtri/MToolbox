import os


class Env:
    def __init__(self):
        # 根据操作系统，设置运行时文件路径
        # Windows在 $User\AppData\Local\.musictoolbox 中
        # Linux在 /etc/.musictoolbox 中
        self.runtime_path = self.set_runtime_path()

    @staticmethod
    def set_runtime_path():
        if os.name == 'nt':  # Windows
            runtime_path = os.path.join(os.getenv('APPDATA'), '.musictoolbox')
            os.makedirs(runtime_path, exist_ok=True)
            return runtime_path
        elif os.name == 'posix':  # Linux
            runtime_path = '/etc/.musictoolbox'
            os.makedirs(runtime_path, exist_ok=True)
            return runtime_path
        else:
            raise EnvironmentError("Unsupported operating system")


class G:
    def __init__(self):
        env = Env()
        # 根据Env类生成各种文件路径
        self.cache_path = os.path.join(env.runtime_path, "cache")
        os.makedirs(self.cache_path, exist_ok=True)
        self.config_path = os.path.join(env.runtime_path, "config")
        os.makedirs(self.config_path, exist_ok=True)
        self.tool_path = os.path.join(env.runtime_path, "sw")
        os.makedirs(self.tool_path, exist_ok=True)
        self.source_path = os.path.join(env.runtime_path, "source")
        os.makedirs(self.source_path, exist_ok=True)

        self.ffmpeg = "ffmpeg"


class Color:
    def __init__(self):
        self.red = "\033[31m"
        self.green = "\033[32m"
        self.yellow = "\033[33m"
        self.blue = "\033[34m"
        self.magenta = "\033[35m"
        self.cyan = "\033[36m"
        self.white = "\033[37m"
        self.bg_red = "\033[41m"
        self.bg_green = "\033[42m"
        self.bg_yellow = "\033[43m"
        self.bg_blue = "\033[44m"
        self.bg_magenta = "\033[45m"
        self.bg_cyan = "\033[46m"
        self.bg_white = "\033[47m"
        self.end = "\033[0m"

    @staticmethod
    def clear_screen():
        os.system('cls' if os.name == 'nt' else 'clear')


VAL = G()
COLOR = Color()
