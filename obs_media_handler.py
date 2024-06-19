import os
import re
import threading
import asyncio
import librosa
import sounddevice as sd
import time

from obs_controller import OBSController
from edit_obs_medias import EditOBSMedias
from vts_hotkey_trigger import VTubeStudioHotkeyTrigger
from render import FrameData
from constants import TALK_CHARACTER


class OBSMediaHandler:
    def __init__(self, frame_data_list: list[FrameData]):
        self.obs_controller = OBSController()
        self.edit_obs_medias = EditOBSMedias()
        self.vts_hotkey_trigger = VTubeStudioHotkeyTrigger()
        self.frame_data_list = frame_data_list
        self.before_media_path = None
        # 絶対パスに変換する
        self.default_subtitle_image_path = os.path.abspath('Asset\subtitle.png')
        self.default_explanation_media_path = os.path.abspath('Asset\解説用メディアソース.png')


    # オーディオファイルの再生
    def play_audio(self, audio_file, AUDIO_DEVICE_INDEX):
        device_info = sd.query_devices(AUDIO_DEVICE_INDEX, 'output')
        data, samplerate = librosa.load(audio_file, sr=device_info['default_samplerate'])
        sd.play(data, samplerate=samplerate, device=AUDIO_DEVICE_INDEX)
        sd.wait()


    async def handle_obs_sources(self):
        await self.obs_controller.connect()

        # VTS　API　接続
        await self.vts_hotkey_trigger.connect()

        # シーンアイテム
        scene_name = "AI_Tuber_test"

        # シーンアイテムのトランスフォームを取得
        source_name = "ホワイドボード"
        scene_item_id = await self.obs_controller.get_scene_item_id(scene_name, source_name)
        whiteboard_transform = await self.obs_controller.get_scene_item_transform(scene_name, scene_item_id)

        # インプットの設定を変更
        source_name = "解説用メディアソース"
        # シーンアイテムのIDを取得
        scene_item_id = await self.obs_controller.get_scene_item_id(scene_name, source_name)

        # 撮影用_字幕のシーンアイテム
        subtitle_source_name = "撮影用_字幕"



        # 最初のフレームデータを取得 -> OBSのメディアソースとシーンアイテムのトランスフォームを更新
        first_frame_data = self.frame_data_list[0]

        # subtitle_source_nameのインプットの設定を変更
        subtitle_input_settings = {"file": first_frame_data.subtitle_image_path, 
                                    'local_file': first_frame_data.subtitle_image_path, 
                                    'looping': True}
        await self.obs_controller.set_input_settings(subtitle_source_name, subtitle_input_settings)

        # シーンアイテムのトランスフォームを更新
        await self.edit_obs_medias.update_explanation_media(
                                    first_frame_data.explanation_media_path, first_frame_data.whiteboard_image_path, 
                                    scene_name, source_name, scene_item_id, whiteboard_transform)
        # メディアファイルのパスを更新
        # self.before_media_path = first_frame_data.explanation_media_path





        # 🌟録画開始 -> 後で削除する
        await self.obs_controller.start_recording()


        # フレームデータを順に処理
        for frame_data in self.frame_data_list:

            if frame_data.character_name == TALK_CHARACTER:
                AUDIO_DEVICE_INDEX = 78
            else:
                AUDIO_DEVICE_INDEX = 65

            # VTSのホットキーを発火
            if frame_data.emotion_shortcut is not None:
                await self.vts_hotkey_trigger.trigger_hotkey(frame_data.emotion_shortcut)
            if frame_data.motion_shortcut is not None:
                await self.vts_hotkey_trigger.trigger_hotkey(frame_data.motion_shortcut)

            # # 音声を再生
            # audio_thread = threading.Thread(target=self.play_audio, args=(frame_data.audio_file, AUDIO_DEVICE_INDEX))
            # audio_thread.start()


            # 前のメディアファイルと同じ場合は処理しない
            if self.before_media_path == frame_data.explanation_media_path:
                pass
            else:
                # シーンアイテムの無効を設定
                await self.obs_controller.set_scene_item_enabled(scene_name, scene_item_id, False)
                # シーンアイテムのトランスフォームを更新
                await self.edit_obs_medias.update_explanation_media(
                                            frame_data.explanation_media_path, frame_data.whiteboard_image_path, 
                                            scene_name, source_name, scene_item_id, whiteboard_transform)
                # シーンアイテムの有効を設定
                await self.obs_controller.set_scene_item_enabled(scene_name, scene_item_id, True)
                # メディアファイルのパスを更新
                self.before_media_path = frame_data.explanation_media_path

                # インプットの設定を取得
                # input_settings = await self.obs_controller.get_input_settings(source_name)
                # print(f"インプットの設定を取得: {input_settings}")
                # print()


            # Subtitleのメディアソースを変更
            subtitle_input_settings = {"file": frame_data.subtitle_image_path, 
                                       'local_file': frame_data.subtitle_image_path, 
                                       'looping': True}
            await self.obs_controller.set_input_settings(subtitle_source_name, subtitle_input_settings)


            # 音声の再生が終了するまで待機
            self.play_audio(frame_data.audio_file, AUDIO_DEVICE_INDEX)
            # await asyncio.sleep(frame_data.audio_duration)
            # audio_thread.join()

        await asyncio.sleep(1)


        # 🌟録画停止 -> 後で削除する
        response = await self.obs_controller.stop_recording()
        response_data = response.data
        print(f"response_data: {response_data}")

        # 終了後の処理 -> subtitle_source_nameのインプットの設定を変更
        subtitle_input_settings = {"file": self.default_subtitle_image_path, 
                                    'local_file': self.default_subtitle_image_path, 
                                    'looping': True}
        await self.obs_controller.set_input_settings(subtitle_source_name, subtitle_input_settings)

        # シーンアイテムのトランスフォームを更新
        await self.edit_obs_medias.update_explanation_media(
                                    self.default_explanation_media_path, first_frame_data.whiteboard_image_path, 
                                    scene_name, source_name, scene_item_id, whiteboard_transform)


        # VTS　API　切断
        await self.vts_hotkey_trigger.disconnect()
        # OBS Studio 切断
        await self.obs_controller.disconnect()

        if response:  # responseが空でないことを確認
            # 正規表現でパスを抽出
            response = str(response)
            match = re.search(r"'outputPath':\s*'([^']+)'", response)
            if match:
                obs_output_path = match.group(1)
                print(f"obs_output_path: {obs_output_path}")
                
                return obs_output_path

        return None
    