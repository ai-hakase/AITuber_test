import os
import sys
import librosa
import sounddevice as sd
import json
import subprocess
import re

from datetime import datetime
from PIL import Image
from PyQt6.QtWidgets import QApplication, QWidget
from moviepy.editor import ImageClip, VideoFileClip, CompositeVideoClip, ColorClip

from render import FrameData
from vts_hotkey_trigger import VTubeStudioHotkeyTrigger
from obs_controller import OBSController
from utils import resize_aspect_ratio, save_as_temp_file, save_as_temp_video
from edit_medias import EditMedia
from create_windows import CreateWindows


# タイムラインの作成
class Timeline:
    def __init__(self, frame_data_list: list[FrameData], output_file: str, background_video_path: str):
        self.hotkey_trigger = VTubeStudioHotkeyTrigger()
        self.obs_controller = OBSController()
        self.edit_medias = EditMedia()
        
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


    # タイムラインの作成
    async def create(self):

        # OBS Studio に接続
        await self.obs_controller.connect()

        # Vショートカットキーの取得
        await self.hotkey_trigger.connect()
        self.hotkeys = await self.hotkey_trigger.get_hotkeys()
        await self.hotkey_trigger.disconnect()

        # 音声ファイルと画像リストとショートカットキーの準備
        self.setup_media_and_shortcut_keys()

        # 録画開始
        await self.obs_controller.start_recording()

        # 各フレームの処理
        self.create_windows.start()

        # 録画停止
        response = await self.obs_controller.stop_recording()


        if response:  # responseが空でないことを確認

            # 正規表現でパスを抽出
            response = str(response)
            match = re.search(r"'outputPath':\s*'([^']+)'", response)

            if match:
                obs_output_path = match.group(1)
                self.output_file_path = obs_output_path

                # print(f"output_path {obs_output_path}")  # C:/Users/okozk/Videos/2024-06-13 08-41-40.mp4

                # トリミングの実行
                # self.trim_video(obs_output_path, self.output_file_path, start_time = 0.05)

            else:
                print("パスが見つかりませんでした。")

        else:
            print("responseが空です。")


        # VTS　API　切断
        await self.hotkey_trigger.disconnect()
        # OBS Studio 切断
        await self.obs_controller.disconnect()

        return self.output_file_path  # 文字列として返す

    def setup_media_and_shortcut_keys(self):
        total_time = 0
        for frame_data in self.frame_data_list:

            # 各フレームの開始時間と終了時間を設定
            frame_data.start_time = total_time
            data, samplerate = librosa.load(frame_data.audio_file)
            audio_duration = librosa.get_duration(y=data, sr=samplerate)
            audio_duration = int(audio_duration * 1000)
            frame_data.audio_duration = audio_duration
            frame_data.end_time = total_time + audio_duration  # ミリ秒に変換
            # total_time = frame_data.end_time

            # ショートカットキーの入力
            # self.hotkeys から Name がemotion_shortcut_key と motion_shortcut_key と一致するhotkeyIDを取得 -> 各リストに複数のキーが入っている
            # frame_data.emotion_shortcut -> ユーザーが選んだショートカットキーの名前
            if frame_data.emotion_shortcut:
                emotion_shortcut_key_ID = [hotkey['hotkeyID'] for hotkey in self.hotkeys if hotkey['name'] in frame_data.emotion_shortcut]
                emotion_shortcut_key_ID = emotion_shortcut_key_ID[0]
                print("感情ショートカット", emotion_shortcut_key_ID)
            else:
                emotion_shortcut_key_ID = None
            if frame_data.motion_shortcut:
                motion_shortcut_key_ID = [hotkey['hotkeyID'] for hotkey in self.hotkeys if hotkey['name'] in frame_data.motion_shortcut]
                motion_shortcut_key_ID = motion_shortcut_key_ID[0]
                print("動作ショートカット", motion_shortcut_key_ID)
            else:
                motion_shortcut_key_ID = None

            # ショートカットキーのIDをリストに格納
            frame_data.emotion_shortcut = emotion_shortcut_key_ID
            frame_data.motion_shortcut = motion_shortcut_key_ID



    

    def trim_video(self, input_path, output_path, start_time):
        """
        ffmpeg を使用して動画を指定された開始時間と長さでトリミングする関数
        """
        # 絶対パスに変換する
        input_path = os.path.abspath(input_path)
        output_path = os.path.abspath(output_path)

        # ffmpeg の形式に変換する
        input_path = input_path.replace("\\", "/")
        output_path = output_path.replace("\\", "/")

        print(f"input_path: {input_path}\n")
        print(f"output_file_path: {output_path}\n")


        # input_path: C:/Users/okozk/Videos/2024-06-13 09-00-05.mp4
        # output_file_path: C:\Users\okozk\Test\Gradio\outputs\output-2024-06-13-09-47-44.mp4

        # output_path-------: C:/Users/okozk/Videos/2024-06-13 09-47-06.mp4
        # output_file_path: C:/Users/okozk/Test/Gradio/outputs/output-2024-06-13-09-47-04.mp4


        # 動画の長さを取得
        result = subprocess.run(["ffmpeg", "-i", input_path], stderr=subprocess.PIPE, text=True)
        duration_match = re.search(r"Duration:\s*(\d{2}):(\d{2}):(\d{2})\.(\d{2})", result.stderr)
        if duration_match:
            hours, minutes, seconds, milliseconds = map(int, duration_match.groups())
            total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 100
        # else:
        #     raise ValueError("動画の長さを取得できませんでした")

        # トリミングの実行 (最初の0.1秒から先をすべて保存)
        duration = total_seconds - start_time

        command = [
            "ffmpeg",
            "-i", input_path,
            "-ss", str(start_time),  # 開始時間
            "-t", str(duration),      # トリミングの長さ
            "-c:v", "libx264",        # ビデオコーデック（必要に応じて変更）
            "-c:a", "aac",            # オーディオコーデック（必要に応じて変更）
            "-y", output_path         # 上書き保存
        ]

        subprocess.run(command)
