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

    # Style-Bert-VITS2のAPIが実行中かどうかを確認
    if sbv2_api.check_port():
        print("Style-Bert-VITS2のAPIは既に実行中です。")
    else:
        print("Style-Bert-VITS2のAPIは実行していません。実行されるまで待機します。")
        # 別のターミナルで setup_ai_tuber_tools.py を実行
        subprocess.Popen(["start", "python", "setup_ai_tuber_tools.py"], shell=True)
        time.sleep(30)

        # 別のターミナルで実行されているか確認
        # while is_process_running("python.exe"):
        #     time.sleep(15)
        # プロセスの終了を待つ
        # subprocess.wait()
        # 30秒経ってもプロセスが終了しない場合は、プロセスを終了しないままほかの処理を再開させる
    # if not await wait_for_process_with_timeout("python.exe", "server_fastapi.py"):
    #     print("Style-Bert-VITS2のAPIは実行していません。実行されるまで待機します。")


    # 仮想環境を有効化
    venv_dir = os.path.join(os.path.expanduser("~"), "venv")
    # 仮想環境が存在しない場合に作成
    # if not os.path.exists(venv_dir):
    #     builder = venv.EnvBuilder(with_pip=True)
    #     builder.create(venv_dir)
    # activateスクリプトのパスを取得
    activator = os.path.join(venv_dir, "Scripts", "activate")  # Windowsの場合
    # activateスクリプトを実行
    subprocess.run([activator], shell=True)

    # 実行
    # asyncio.run(ui.create_ui())
    await ui.create_ui()


if __name__ == "__main__":
    asyncio.run(main())
