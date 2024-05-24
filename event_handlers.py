import os
import shutil
from tkinter import filedialog
from constants import *


# BGMファイルの変更時の処理
def on_bgm_file_change(audio_data):
    if audio_data is not None:
        sample_rate, audio_bytes = audio_data
        bgm_file_name = "bgm_audio.wav"
        bgm_file_path = os.path.join(BGM_FOLDER, bgm_file_name)
        
        os.makedirs(BGM_FOLDER, exist_ok=True)
        
        # オーディオデータをWAVファイルとして保存
        with open(bgm_file_path, "wb") as f:
            f.write(audio_bytes)
        
        # BGMファイルのパスを返す代わりに、Noneを返す
        return None
    else:
        return None        
    

# 背景動画ファイルの変更時の処理
def on_background_video_file_change(file):
    if file:
        background_video_file_path = os.path.join(BACKGROUND_VIDEO_FOLDER, os.path.basename(file))
        shutil.copy(file, background_video_file_path)
    else:
        background_video_file_input.value = None


# 動画保存先フォルダの変更時の処理
def on_change_output_folder_click(output_folder_input):
    folder_path = filedialog.askdirectory()
    if folder_path:
        output_folder_input.value = folder_path


# アクションのショートカットを平坦化する関数
def flatten_actions(actions):
    flat_actions = []
    for action, shortcuts in actions.items():
        for shortcut in shortcuts:
            flat_actions.append([action, shortcut[0], ", ".join(shortcut[1])])
    return flat_actions


# 辞書の更新
# def load_and_show_dics():
#     setting_data = load_settings(DEFAULT_SETTING_FILE)
#     dics_data = [[word, reading] for word, reading in setting_data.get("dics", {}).items()]
#     registered_words_table.value = dics_data
#     return gr.Dataframe.update(value=dics_data, visible=True)



