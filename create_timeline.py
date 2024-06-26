import os
import sys
import librosa
import sounddevice as sd
import json
import subprocess
import re

from render import FrameData
from vts_hotkey_trigger import VTubeStudioHotkeyTrigger
from obs_controller import OBSController
from edit_medias import EditMedia
from obs_media_handler import OBSMediaHandler


# タイムラインの作成
class Timeline:
    def __init__(self, frame_data_list: list[FrameData], output_file: str):
        self.hotkey_trigger = VTubeStudioHotkeyTrigger()
        self.obs_controller = OBSController()
        self.edit_medias = EditMedia()

        self.obs_media_handler = OBSMediaHandler(frame_data_list)

        self.frame_data_list = frame_data_list
        self.output_file = output_file

        self.hotkeys = []


    async def create(self):
        """
        タイムラインの作成
        """
        # Vショートカットキーの取得
        await self.hotkey_trigger.connect()
        self.hotkeys = await self.hotkey_trigger.get_hotkeys()
        await self.hotkey_trigger.disconnect()

        # 音声ファイルと画像リストとショートカットキーの準備
        self.setup_media_and_shortcut_keys()

        output_file_path = await self.obs_media_handler.handle_obs_sources()

        return output_file_path  # 文字列として返す


    def setup_media_and_shortcut_keys(self):
        """
        音声ファイルと画像リストとショートカットキーの準備
        """
        for frame_data in self.frame_data_list:

            data, samplerate = librosa.load(frame_data.audio_file)
            audio_duration = librosa.get_duration(y=data, sr=samplerate)
            audio_duration = float(audio_duration * 1000)
            frame_data.audio_duration = audio_duration


            # 感情ショートカットキーの入力
            if frame_data.emotion_shortcut:
                emotion_shortcut_key_ID = [hotkey['hotkeyID'] for hotkey in self.hotkeys if hotkey['name'] in frame_data.emotion_shortcut]
                if len(emotion_shortcut_key_ID) > 0:
                    frame_data.emotion_shortcut = emotion_shortcut_key_ID[0]
            else:
                frame_data.emotion_shortcut = None

            # 動作ショートカットキーの入力
            if frame_data.motion_shortcut:
                motion_shortcut_key_ID = [hotkey['hotkeyID'] for hotkey in self.hotkeys if hotkey['name'] in frame_data.motion_shortcut]
                if len(motion_shortcut_key_ID) > 0:
                    frame_data.motion_shortcut = motion_shortcut_key_ID[0]
            else:
                frame_data.motion_shortcut = None

            print("感情ショートカット:", frame_data.emotion_shortcut)
            print("動作ショートカット:", frame_data.motion_shortcut)
