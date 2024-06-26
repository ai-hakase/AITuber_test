import os
import subprocess
import socket
import yaml
from constants import STARTUP_SETTINGS_FILE


# 設定ファイルを読み込む
with open(STARTUP_SETTINGS_FILE, "r", encoding="utf-8") as f:
    settings = yaml.load(f, Loader=yaml.FullLoader)

    SBV2_DIR = settings["SBV2_DIR"]
    SBV2_VENV_DIR = settings["SBV2_VENV_DIR"]


class StyleBertVITS2API:
    def __init__(self):

        # 仮想環境を有効化
        python_exe = os.path.join(SBV2_VENV_DIR, "Scripts", "python.exe")
        scripts_dir = os.path.join(SBV2_VENV_DIR, "Scripts")
        os.environ["PATH"] = scripts_dir + os.pathsep + os.environ["PATH"]

        # 仮想環境のPython実行ファイルのパス
        self.python_exe = python_exe
        # 実行中フラグ
        self.is_running = False  


    def run(self):
        """APIを起動する"""
        cd = SBV2_DIR
        os.chdir(cd)
        print(f"cd: {cd}")
        print(f"python_exe: {self.python_exe}")
        subprocess.Popen([self.python_exe, "server_fastapi.py"])


    def check_port(self):
        """ポートが開いたらフラグをTrueにして返す"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(("127.0.0.1", 5000))
                self.is_running = True
                return True

        except ConnectionRefusedError:
            self.is_running = False
            return False


def main():
    sbv2_api = StyleBertVITS2API()
    sbv2_api.run()


if __name__ == "__main__":
    main()
