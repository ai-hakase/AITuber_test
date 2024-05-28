import os
import csv
import pprint
import shutil
from tkinter import filedialog

from ui import *
from constants import *


# csvファイルの変更時の処理
def on_csv_file_change(file):
    global csv_data
    if file:
        csv_data = []
        with open(file.name, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                csv_data.append(row)
    else:
        csv_data = []


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


# 感情のショートカットを更新する関数
def update_emotion_shortcut(emotion_shortcuts_input):
    emotion_shortcuts = {row[0]: row[1].split(", ") for row in emotion_shortcuts_input}
    save_settings(emotion_shortcuts, actions_state.value, json_file_output.value)
    return emotion_shortcuts


# アクションのショートカットを更新する関数
def update_action_shortcut(actions_input):
    actions = {}
    for row in actions_input:
        action, shortcut_name, keys = row
        if action not in actions:
            actions[action] = []
        actions[action].append([shortcut_name, keys.split(", ")])
    save_settings(emotion_shortcuts_state.value, actions, json_file_output.value)
    return actions


# # アクションのショートカットを更新する関数（平坦化されたデータから）
# def update_action_shortcut(flat_actions):
#     actions = {}
#     for action, shortcut_name, keys in flat_actions:
#         if action not in actions:
#             actions[action] = []
#         actions[action].append([shortcut_name, keys.split(", ")])
#     return actions


# 辞書の更新
# def load_and_show_dics():
#     setting_data = load_settings(DEFAULT_SETTING_FILE)
#     dics_data = [[word, reading] for word, reading in setting_data.get("dics", {}).items()]
#     registered_words_table.value = dics_data
#     return gr.Dataframe.update(value=dics_data, visible=True)


def on_change_output_folder_click():
    folder_dialog = gr.Interface(lambda x: x, "file", "file", label="動画保存先を選択してください")
    selected_folder = folder_dialog.launch(share=True)
    output_folder_input.value = selected_folder
