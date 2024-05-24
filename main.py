import random
import csv
import os
import json
import asyncio
import json
import websockets
import base64
import cv2
import numpy as np
import gradio as gr

from io import BytesIO
from PIL import Image

from constants import *
from ui import *
from vts_api import *


def generate_video(csv_file, bgm_file, background_video_file, character_name, voice_synthesis_model, emotion_shortcuts, actions, output_folder):
    ...
    # ここに動画生成の処理を記述する
    # CSVファイルからキャラクター・セリフ情報を取得
    # セリフを1つずつ処理（読み上げ音声ファイル生成、感情分析、表情・動作のショートカットキー制御）
    # 解説画像を生成
    # レンダリング（合成音声の再生、表情・動作のショートカットキー入力、BGMと背景動画の合成）
    # 動画ファイルを出力フォルダに保存
    # 生成された動画ファイルのパスを返す
    generated_video_path = os.path.join(output_folder, "generated_video.mp4")
    return generated_video_path


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


gr.themes.Soft()

if __name__ == "__main__":
    asyncio.run(main())