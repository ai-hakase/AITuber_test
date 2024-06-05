
import os
import subprocess
import time
import pyautogui

def is_process_running(process_name):
    output = subprocess.check_output(['tasklist', '/FI', f'IMAGENAME eq {process_name}'], encoding='cp932')
    return process_name in output

def start_process(process_path):
    subprocess.Popen(process_path, shell=True)

def run_style_bert_vits2_api():
    cd = r"C:\Users\okozk\Style-Bert-VITS2\Style-Bert-VITS2"
    os.chdir(cd)
    subprocess.call([r"Venv\scripts\activate.bat"])
    subprocess.call(["python", "server_fastapi.py"])

# VTube Studioが実行中かどうかを確認
if is_process_running("VTube Studio.exe"):
    print("VTube Studioは既に実行中です。")
else:
    print("VTube Studioを起動します。")
    start_process(r"C:\Users\okozk\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Steam\VTube Studio.url")
    # 起動したら60秒後に「alt＋h」を押す
    time.sleep(60)
    pyautogui.hotkey('alt', 'h')

# OBSが実行中かどうかを確認
if is_process_running("obs64.exe"):
    print("OBSは既に実行中です。")
else:
    print("OBSを起動します。")
    start_process(r"C:\Users\Public\Desktop\OBS Studio.lnk")

# Style-Bert-VITS2のAPIが実行中かどうかを確認
if is_process_running("python.exe") and "server_fastapi.py" in subprocess.check_output(['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FI', 'WINDOWTITLE eq server_fastapi.py'], encoding='cp932'):
    print("Style-Bert-VITS2のAPIは既に実行中です。")
else:
    print("Style-Bert-VITS2のAPIを起動します。")
    run_style_bert_vits2_api()