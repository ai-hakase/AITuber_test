import asyncio
import os
import subprocess
import yaml

from ui import UI
from vts_hotkey_trigger import VTubeStudioHotkeyTrigger
from setup_ai_tuber_tools import StyleBertVITS2API
from constants import STARTUP_SETTINGS_FILE


# 設定ファイルを読み込む
with open(STARTUP_SETTINGS_FILE, "r", encoding="utf-8") as f:
    settings = yaml.load(f, Loader=yaml.FullLoader)

    OBS_SHORTCUT_PATH = settings["OBS_SHORTCUT_PATH"]
    VTUBE_STUDIO_SHORTCUT_PATH = settings["VTUBE_STUDIO_SHORTCUT_PATH"]


def is_process_running(process_name):
    """プロセスが実行中かどうかを確認する関数"""
    output = subprocess.check_output(['tasklist', '/FI', f'IMAGENAME eq {process_name}'], encoding='cp932')
    return process_name in output


def start_process(process_path):
    """プロセスを起動する関数"""
    subprocess.Popen(process_path, shell=True)


async def start_vts_studio():
    """VTube Studioを起動する関数"""
    start_process(VTUBE_STUDIO_SHORTCUT_PATH)
    await asyncio.sleep(20)#25秒待つ
    vts_hotkey_trigger = VTubeStudioHotkeyTrigger()
    await vts_hotkey_trigger.init_vts_character()


async def main():
    """メイン関数"""

    # OBSが実行中かどうかを確認
    if is_process_running("obs64.exe"):
        print("OBSは既に実行中です。")
    else:
        print("OBSを起動します。")
        start_process(OBS_SHORTCUT_PATH)


    # VTube Studioが実行中かどうかを確認
    if is_process_running("VTube Studio.exe"):
        print("VTube Studioは既に実行中です。")
    else:
        print("VTube Studioを起動します。")
        asyncio.create_task(start_vts_studio())#非同期でVTube Studioを起動


    # Style-Bert-VITS2のAPIが実行中かどうかを確認
    sbv2_api = StyleBertVITS2API()

    if sbv2_api.check_port():
        print("Style-Bert-VITS2のAPIは既に実行中です。")
    else:
        print("Style-Bert-VITS2のAPIは実行していません。実行されるまで待機します。")
        # 別のターミナルで setup_ai_tuber_tools.py を実行
        subprocess.Popen(["start", "python", "setup_ai_tuber_tools.py"], shell=True)
        await asyncio.sleep(25)#25秒待つ


    # 仮想環境を有効化
    venv_dir = os.path.join(os.path.expanduser("~"), "venv")
    activator = os.path.join(venv_dir, "Scripts", "activate")  # Windowsの場合
    # activateスクリプトを実行
    subprocess.run([activator], shell=True)


    # UIを作成
    ui = UI()
    ui.create_ui()


if __name__ == "__main__":
    asyncio.run(main())

