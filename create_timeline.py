import threading
import sys
import os
import random
import asyncio
import queue
import librosa
import sounddevice as sd
import pygame
import cv2
import time
import signal


from render import FrameData
from vts_hotkey_trigger import VTubeStudioHotkeyTrigger
from obs_controller import OBSController
from utils import save_as_temp_file
from create_windows import CreateWindows
from PyQt5.QtWidgets import QApplication, QWidget

# 一つ上の階層のパスを取得
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

from vtuber_camera import VTuberCamera
from utils import *


# タイムラインの作成
class Timeline:
    def __init__(self, frame_data_list: list[FrameData], output_file: str, background_video_path: str):
        self.hotkey_trigger = VTubeStudioHotkeyTrigger()
        self.obs_controller = OBSController()
        
        # QApplicationのインスタンスを作成
        self.app = QApplication(sys.argv)

        self.create_windows = CreateWindows(frame_data_list)

        self.audio_file_list = []
        self.explanation_image_list = []
        self.subtitle_image_list = []

        self.frame_data_list = frame_data_list
        self.output_file_path = output_file
        
        self.background_video_path = background_video_path
        self.preview_height, self.preview_width = 1080,1920 # 解像度を取得

        self.hotkeys = []

        self.AUDIO_DEVICE_INDEX = 78 # 78 CABLE-A Input (VB-Audio Cable A , WASAPI (0 in, 2 out) - 48000.0 Hz
        self.device_info = sd.query_devices(self.AUDIO_DEVICE_INDEX, 'output')

        # 既存の初期化コード
        self.previous_emotion_shortcut = None
        self.previous_motion_shortcut = None

        self.output_file = output_file

        self.background_video_start_time = 0# 背景動画の再生時間
        self.explanation_video_start_time = 0# 解説動画の再生時間
        self.previous_video_duration = 0# 前の動画の長さ

    #     # シグナルハンドラの設定
    #     signal.signal(signal.SIGINT, self.handle_exit)

    # async def handle_exit(self, signum, frame):
    #     print("録画停止中...")
    #     self.output_file_path = await self.obs_controller.stop_recording()
    #     print("録画が停止されました。")
    #     sys.exit(0)


    def setup_media_and_shortcut_keys(self):
        total_time = 0
        for frame_data in self.frame_data_list:

            # 各フレームの開始時間と終了時間を設定
            frame_data.start_time = total_time
            data, samplerate = librosa.load(frame_data.audio_file)
            audio_duration = librosa.get_duration(y=data, sr=samplerate)
            frame_data.end_time = total_time + int(audio_duration * 1000)  # ミリ秒に変換
            # total_time = frame_data.end_time

            # ショートカットキーの入力
            # self.hotkeys から Name がemotion_shortcut_key と motion_shortcut_key と一致するhotkeyIDを取得 -> 各リストに複数のキーが入っている
            # frame_data.emotion_shortcut -> ユーザーが選んだショートカットキーの名前
            if frame_data.emotion_shortcut:
                emotion_shortcut_key_ID = [hotkey['hotkeyID'] for hotkey in self.hotkeys if hotkey['name'] in frame_data.emotion_shortcut]
            else:
                emotion_shortcut_key_ID = None
            if frame_data.motion_shortcut:
                motion_shortcut_key_ID = [hotkey['hotkeyID'] for hotkey in self.hotkeys if hotkey['name'] in frame_data.motion_shortcut]
            else:
                motion_shortcut_key_ID = None

            # ショートカットキーのIDをリストに格納
            frame_data.emotion_shortcut = emotion_shortcut_key_ID
            frame_data.motion_shortcut = motion_shortcut_key_ID



    # タイムラインの作成
    async def create(self):

        # OBS Studio に接続
        await self.obs_controller.connect()
        # VTS　API　接続
        await self.hotkey_trigger.connect()

        # ショートカットキーの取得
        self.hotkeys = await self.hotkey_trigger.get_hotkeys()

        # 音声ファイルと画像リストとショートカットキーの準備
        self.setup_media_and_shortcut_keys()

        # 録画開始
        await self.obs_controller.start_recording()

        # 各フレームの処理
        self.create_windows.start()

        # 録画停止
        response = await self.obs_controller.stop_recording()


        if response:  # responseが空でないことを確認
            try:
                # response = json.loads(response)  # ここで文字列を辞書に変換
                print(f"response: {response}")
                print(f"response: {type(response)}")
                # self.output_file_path = response.outputPath
                # self.output_file_path = response['outputPath']
                # print(f"response: {self.output_file_path }")

                # output_path = response.responseData["outputPath"]
                # print(output_path)  # -> 'C:/Users/okozk/Videos/2024-06-11 08-25-13.mp4'

            except json.JSONDecodeError as e:
                print(f"JSONデコードエラー: {e}")
        else:
            print("responseが空です。")

        # self.output_file_path = response['outputPath']

        # VTS　API　切断
        await self.hotkey_trigger.disconnect()
        # OBS Studio 切断
        await self.obs_controller.disconnect()

        return self.output_file_path  # 文字列として返す