import asyncio
import os
import venv
import subprocess
import time
import sounddevice as sd

from ui import UI
from setup_ai_tuber_tools import StyleBertVITS2API


# async def wait_for_process_with_timeout(process_name, window_title, timeout=20):
#     """プロセスが終了するのを待つ関数 (タイムアウト付き)"""
#     start_time = time.time()
#     while time.time() - start_time < timeout:
#         if not is_process_running("python.exe") and "server_fastapi.py" not in subprocess.check_output(['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FI', 'WINDOWTITLE eq server_fastapi.py'], encoding='cp932'):
#         # if not is_process_running(process_name, window_title):
#             return True  # プロセスが終了
#         await asyncio.sleep(1)  # 1秒待機
#     return False  # タイムアウト



async def main():
    ui = UI()
    sbv2_api = StyleBertVITS2API()

    loop = asyncio.get_event_loop()

    # Style-Bert-VITS2のAPIが実行中かどうかを確認
    if sbv2_api.check_port():
        print("Style-Bert-VITS2のAPIは既に実行中です。")
    else:
        print("Style-Bert-VITS2のAPIは実行していません。実行されるまで待機します。")
        # 別のターミナルで setup_ai_tuber_tools.py を実行
        subprocess.Popen(["start", "python", "setup_ai_tuber_tools.py"], shell=True)
        time.sleep(30)

    # 仮想環境を有効化
    venv_dir = os.path.join(os.path.expanduser("~"), "venv")
    activator = os.path.join(venv_dir, "Scripts", "activate")  # Windowsの場合
    # activateスクリプトを実行
    subprocess.run([activator], shell=True)


    try:
        # loop.run_until_complete(ui.create_ui())
        loop.run_until_complete(await ui.create_ui())
        
    except ConnectionResetError as e:
        # 無視して処理を続ける
        pass

    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()


if __name__ == "__main__":
    asyncio.run(main())
