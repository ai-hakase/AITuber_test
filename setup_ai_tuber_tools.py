import os
import subprocess
import time
import pyautogui
import asyncio
import venv
import threading
import time
import socket
import yaml


settings = r"settings.yml"
# 設定ファイルを読み込む
with open(settings, "r", encoding="utf-8") as f:
    settings = yaml.load(f, Loader=yaml.FullLoader)
    SBV2_DIR = settings["SBV2_DIR"]
    SBV2_VENV_DIR = settings["SBV2_VENV_DIR"]
    OBS_SHORTCUT_PATH = settings["OBS_SHORTCUT_PATH"]
    VTUBE_STUDIO_SHORTCUT_PATH = settings["VTUBE_STUDIO_SHORTCUT_PATH"]

hotkey_alt_4 = 'alt', '4'


class StyleBertVITS2API:
    def __init__(self):

        # 仮想環境を有効化
        venv_dir = SBV2_VENV_DIR
        python_exe = os.path.join(venv_dir, "Scripts", "python.exe")
        scripts_dir = os.path.join(venv_dir, "Scripts")
        os.environ["PATH"] = scripts_dir + os.pathsep + os.environ["PATH"]

        self.python_exe = python_exe
        self.is_running = False  # 実行中フラグ

    def check_port(self):
        """ポートが開いたらフラグをTrueにして返す"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(("127.0.0.1", 5000))
                self.is_running = True
                return True
                # return self.is_running
        except ConnectionRefusedError:
            self.is_running = False
            return False
            # return self.is_running

    def run(self):
        """APIを起動する"""
        cd = SBV2_DIR
        os.chdir(cd)
        subprocess.Popen([self.python_exe, "server_fastapi.py"])


def is_process_running(process_name):
    output = subprocess.check_output(['tasklist', '/FI', f'IMAGENAME eq {process_name}'], encoding='cp932')
    return process_name in output


def start_process(process_path):
    subprocess.Popen(process_path, shell=True)


# def run_style_bert_vits2_api(python_exe):
#     cd = r"C:\Users\okozk\Style-Bert-VITS2\Style-Bert-VITS2"
#     os.chdir(cd)
#     # subprocess.call([r"Venv\scripts\activate.bat"])
#     # subprocess.call(["python", "server_fastapi.py"])
#     subprocess.run([python_exe, "server_fastapi.py"])


# async def send_hotkey():
def send_hotkey():
    # await time.sleep(20)
    time.sleep(15)
    pyautogui.hotkey('alt', '4', interval=0.05)


# async def main():
def main(): # async def main():を追加

    # VTube Studioが実行中かどうかを確認
    if is_process_running("VTube Studio.exe"):
        print("VTube Studioは既に実行中です。")
    else:
        print("VTube Studioを起動します。")
        start_process(VTUBE_STUDIO_SHORTCUT_PATH)
        # 起動したら10秒後に「alt＋h」を押す
        # 別タスクでショートカットキー送信処理を実行
        # asyncio.create_task(send_hotkey())
        vst_thread = threading.Thread(target=send_hotkey)
        vst_thread.start()

    # OBSが実行中かどうかを確認
    if is_process_running("obs64.exe"):
        print("OBSは既に実行中です。")
    else:
        print("OBSを起動します。")
        start_process(OBS_SHORTCUT_PATH)
        

    # # Style-Bert-VITS2のAPIが実行中かどうかを確認
    # if is_process_running("python.exe") and "server_fastapi.py" in subprocess.check_output(['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FI', 'WINDOWTITLE eq server_fastapi.py'], encoding='cp932'):
    #     print("Style-Bert-VITS2のAPIは既に実行中です。")
    # else:
    #     print("Style-Bert-VITS2のAPIを起動します。")
    #     # 仮想環境を有効化
    #     venv_dir = "C:\\Users\\okozk\\Style-Bert-VITS2\\Style-Bert-VITS2\\Venv"
    #     python_exe = os.path.join(venv_dir, "Scripts", "python.exe")
    #     scripts_dir = os.path.join(venv_dir, "Scripts")
    #     os.environ["PATH"] = scripts_dir + os.pathsep + os.environ["PATH"]
    #     # 仮想環境の Python インタプリタでスクリプトを実行
    #     # run_style_bert_vits2_api()
    #     run_style_bert_vits2_api(python_exe)
    
    # Style-Bert-VITS2のAPIが実行中かどうかを確認
    api = StyleBertVITS2API()
    if api.check_port():
        print("Style-Bert-VITS2のAPIは既に実行中です。")
    else:
        print("Style-Bert-VITS2のAPIを起動します。")
        api.run()


if __name__ == "__main__":
    # asyncio.run(main()) # asyncio.run(main())で囲む
    main()
