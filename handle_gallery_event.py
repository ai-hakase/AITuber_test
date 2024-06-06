import os
import csv
import pprint
import shutil
import sounddevice as sd

from tkinter import filedialog
from ui import *
from constants import *
from vts_hotkey_trigger import VTubeStudioHotkeyTrigger


class HandleGalleryEvent:
    def __init__(self):
        self.vts_hotkey_trigger = VTubeStudioHotkeyTrigger()


    # アップロードされたファイルの種類に応じてプレビューを更新する関数
    def update_preview(self, file):
        if file is None:
            return gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)
        
        if isinstance(file, dict):
            file_type = file["type"]
            file_name = file["name"]
        else:
            import mimetypes
            file_type, _ = mimetypes.guess_type(file)
            file_name = file

        if file_type.startswith("image"):
            return gr.update(value=file_name, visible=True), gr.update(visible=False), gr.update(visible=True)
        elif file_type.startswith("video"):
            return gr.update(visible=False), gr.update(value=file_name, visible=True), gr.update(visible=True)
        return gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)



    # #　グローバル変数にリストを格納 → 最初に更新
    # def update_frame_data_list(self, frame_data):
    #     global frame_data_list
    #     if frame_data_list is None:
    #         frame_data_list = frame_data
    #         # print("frame_data_list:", frame_data_list)  # デバッグ用にデータを出力
    #         return self.update_ui_elements(0)
    #     else:
    #         print("No data:", frame_data_list)  # デバッグ用にデータを出力
    #         return None, None, None, None, None, None


    # # 読み方用のテキストエリアでEnterキーが押されたときの処理
    # def on_reading_input_submit(self, evt, subtitle_line, reading_line, image_video_input):
    #     if evt.key == "Enter":
    #         return on_update_reading_click(subtitle_line, reading_line, image_video_input)
    #     return gr.update()




    # 画像/動画選択ボタンがクリックされたときの処理
    def on_delete_image_video_click(self):
        return gr.update(label="画像/動画選択", value=None, file_types=["image", "video"], interactive=True), gr.update(value=None, visible=False), gr.update(value=None, visible=False), gr.update(visible=False)




    # # 変数をコンソールに書き出す関数
    # def print_variables(self):
    #     variables = {
    #         "CSVファイル": csv_file_input.value['path'],
    #         "BGMファイル": bgm_file_input.value['path'],
    #         "背景動画ファイル": background_video_file_input.value['video']['path'],
    #         "subtitle_line": subtitle_input.value,
    #         "reading_line": reading_input.value,
    #         "image_video_input": image_video_input,
    #         "image_video_input.value": image_video_input.value,
    #         "キャラクター名.value": character_name_input.value,
    #         "キャラクター名": character_name_input,
    #         "音声合成モデル": voice_synthesis_model_dropdown.value,
    #         "読み上げ速度": reading_speed_slider.value,
    #         "登録済み単語/文章一覧": registered_words_table.value['data'],
    #         "感情ショートカット emotion_shortcuts_state": emotion_shortcuts_state.value,
    #         "アクション actions_state": actions_state.value,
    #         "動画保存先": output_folder_input.value,
    #         "設定ファイルパス": settings_file_path_input.value,
    #     }
    #     pprint.pprint(variables)


    # ドロップダウンの変更イベントに関数をバインド
    def on_model_change(self, voice_synthesis_model_dropdown, model_list_state):
        if voice_synthesis_model_dropdown:
            selected_model_tuple = next((model for model in model_list_state if model[0] == voice_synthesis_model_dropdown), None)
        else:
            print("選択されたモデルが見つかりません。")
        return selected_model_tuple

    
    # アクションのショートカットを平坦化する関数
    def flatten_actions(self, actions):
        flat_actions = []
        for action, shortcuts in actions.items():
            for shortcut in shortcuts:
                flat_actions.append([action, shortcut[0], shortcut[1]])
        return flat_actions
    

    # ホットキーを読み込む
    async def load_hotkeys(self):
        await self.vts_hotkey_trigger.connect()
        hotkeys = await self.vts_hotkey_trigger.get_hotkeys()
        await self.vts_hotkey_trigger.disconnect()
        return [[hotkey['name'], hotkey['file']] for hotkey in hotkeys]


    # オーディオデバイスを読み込む
    async def load_audio_devices(self):
        #オーディオデバイスの一覧を取得する
        devices = sd.query_devices()

        cable_devices = []

        for device in devices:

            if "CABLE" in device["name"] and device["max_output_channels"] >= 2:  # デバイス名で判定
                device_number = device["index"]  # デバイス番号を取得
                device_name = device["name"].replace(")", "")  # デバイス名を取得
                hostapi = device["hostapi"] # ホストアピを取得
                max_input_channels = device["max_input_channels"] # 入力チャネル数を取得
                max_output_channels = device["max_output_channels"] # 出力チャネル数を取得
                default_samplerate = device["default_samplerate"] # サンプルレートを取得

                # # ホストアピからデバイスの種類を推測
                device_type = "不明"
                if hostapi == 0:
                    device_type = "MME"
                elif hostapi == 1:
                    device_type = "DirectSound"
                elif hostapi == 2:
                    device_type = "ASIO"
                elif hostapi == 3:
                    device_type = "WASAPI"
                elif hostapi == 4:
                    device_type = "WDM-KS"

                device_name = f"{device_name} , {device_type} ({max_input_channels} in, {max_output_channels} out) - {default_samplerate} Hz"
                # タプルを作成してリストに追加
                cable_devices.append((device_number, device_name))

        return [[device_number, device_name] for device_number, device_name in cable_devices]


#     # csvファイルの変更時の処理
#     def on_csv_file_change(file):
#         global csv_data
#         if file:
#             csv_data = []
#             with open(file.name, 'r', encoding='utf-8') as f:
#                 reader = csv.reader(f)
#                 for row in reader:
#                     csv_data.append(row)
#         else:
#             csv_data = []


#     # BGMファイルの変更時の処理
#     def on_bgm_file_change(audio_data):
#         if audio_data is not None:
#             sample_rate, audio_bytes = audio_data
#             bgm_file_name = "bgm_audio.wav"
#             bgm_file_path = os.path.join(BGM_FOLDER, bgm_file_name)
            
#             os.makedirs(BGM_FOLDER, exist_ok=True)
            
#             # オーディオデータをWAVファイルとして保存
#             with open(bgm_file_path, "wb") as f:
#                 f.write(audio_bytes)
            
#             # BGMファイルのパスを返す代わりに、Noneを返す
#             return None
#         else:
#             return None        
    

# # 背景動画ファイルの変更時の処理
# def on_background_video_file_change(file):
#     if file:
#         background_video_file_path = os.path.join(BACKGROUND_VIDEO_FOLDER, os.path.basename(file))
#         shutil.copy(file, background_video_file_path)
#     else:
#         background_video_file_input.value = None


# # 動画保存先フォルダの変更時の処理
# def on_change_output_folder_click(output_folder_input):
#     folder_path = filedialog.askdirectory()
#     if folder_path:
#         output_folder_input.value = folder_path



# # 感情のショートカットを更新する関数
# def update_emotion_shortcut(emotion_shortcuts_input):
#     emotion_shortcuts = {row[0]: row[1] for row in emotion_shortcuts_input}
#     save_settings(emotion_shortcuts, actions_state.value, json_file_output.value)
#     return emotion_shortcuts


# # アクションのショートカットを更新する関数
# def update_action_shortcut(actions_input):
#     actions = {}
#     for row in actions_input:
#         action, shortcut_name, keys = row
#         if action not in actions:
#             actions[action] = []
#         actions[action].append([shortcut_name, keys.split(", ")])
#     save_settings(emotion_shortcuts_state.value, actions, json_file_output.value)
#     return actions


# # # アクションのショートカットを更新する関数（平坦化されたデータから）
# # def update_action_shortcut(flat_actions):
# #     actions = {}
# #     for action, shortcut_name, keys in flat_actions:
# #         if action not in actions:
# #             actions[action] = []
# #         actions[action].append([shortcut_name, keys.split(", ")])
# #     return actions


# # 辞書の更新
# # def load_and_show_dics():
# #     setting_data = load_settings(DEFAULT_SETTING_FILE)
# #     dics_data = [[word, reading] for word, reading in setting_data.get("dics", {}).items()]
# #     registered_words_table.value = dics_data
# #     return gr.Dataframe.update(value=dics_data, visible=True)


# def on_change_output_folder_click():
#     folder_dialog = gr.Interface(lambda x: x, "file", "file", label="動画保存先を選択してください")
#     selected_folder = folder_dialog.launch(share=True)
#     output_folder_input.value = selected_folder


