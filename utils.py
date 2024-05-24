import os
import json
from moviepy.editor import VideoFileClip
import gradio as gr
from constants import *

# def load_settings(file_path):
#     try:
#         with open(file_path, "r", encoding="utf-8") as f:
#             return json.load(f)
#     except FileNotFoundError:
#         return {}

# 設定ファイルを読み込む関数
def load_settings(json_file_path):
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            settings = json.load(f)
        character_name = settings.get("character_name", "")
        voice_synthesis_model = settings.get("voice_synthesis_model", "model1")
        reading_speed = settings.get("reading_speed", 1.0)
        output_folder = settings.get("output_folder", "outputs")
        bgm_file = settings.get("bgm_file", "")
        background_video_file = settings.get("background_video_file", "")
        emotion_shortcuts = {emotion: shortcut for emotion, shortcut in settings.get("emotion_shortcuts", {}).items()}
        actions = settings.get("actions", {})
        dics = settings.get("dics", {})
        return character_name, voice_synthesis_model, reading_speed, output_folder, bgm_file, background_video_file, emotion_shortcuts, actions, dics
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return "葉加瀬あい", "model1", 1.0, "outputs", "bgm\\default_bgm.wav", "background_video\\default_video.mp4", {emotion: [] for emotion in EMOTIONS}, {}, {}

# 設定ファイルを保存する関数
def save_settings(emotion_shortcuts, actions, json_file_output):
    settings = {
        "emotion_shortcuts": emotion_shortcuts,
        "actions": actions,
        "actions": actions
    }
    with open(os.path.join(DEFAULT_SETTINGS_FOLDER,json_file_output+".json"), "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)



# BGMファイルを変換する関数
def convert_bgm_to_wav(filename):
    # ファイルがMP4, AVI, MOVファイルであるかをチェック
    if filename.endswith((".mp4", ".avi", ".mov")):
        # 元のファイルのフルパス
        video_path = os.path.join(BGM_FOLDER, filename)
        # 変換後のWAVファイルのフルパス
        wav_path = os.path.join(BGM_FOLDER, os.path.splitext(filename)[0] + ".wav")
        
        # 変換後のWAVファイルがすでに存在するかをチェック
        if not os.path.exists(wav_path):
            try:
                # 動画ファイルを読み込む
                video = VideoFileClip(video_path)
                # 音声を抽出し、WAVファイルとして保存
                video.audio.write_audiofile(wav_path)
                print(f"{filename} -> {os.path.basename(wav_path)} に変換されました。")
                
                # VideoFileClipをクローズ
                video.close()
                
                # 元の動画ファイルを削除
                os.remove(video_path)
                print(f"{filename} は削除されました。")
            except Exception as e:
                print(f"ファイル {filename} の変換中にエラーが発生しました: {e}")
        else:
            print(f"{os.path.basename(wav_path)} はすでに存在するため、スキップしました。")
        
        return os.path.splitext(filename)[0] + ".wav"
    else:
        return filename


