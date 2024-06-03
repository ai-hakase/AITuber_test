import asyncio

from dataclasses import dataclass
from typing import Tuple


output_file = "output.mp4"

@dataclass
class FrameData:
    subtitle_line: str
    reading_line: str
    audio_file: str
    emotion_shortcut: str
    motion_shortcut: str
    explanation_image_path: str
    whiteboard_image_path: str
    subtitle_image_path: str
    preview_image: str
    selected_model: Tuple[str, str, str]
    audio_duration: float = 0.0,
    frame_clips = None,
    bgm_path: str = None,
    background_video_path: str = None,


# # test用のデフォルトのパス 
# @dataclass
# class TestData:
#     default_bgm = r"C:\Users\okozk\Test\Gradio\test\test_asetts\AI-Hakase_Voice-26S.MP3"#デフォルトのBGM
#     background_video_file_input = r"C:\Users\okozk\Test\Gradio\background_video\default_video.mp4"#デフォルトの背景動画
#     # video_size = (1920, 1080)#動画のサイズ
#     output_folder = "output"#出力フォルダ。なければ作成

#     voice1 = r"C:\Users\okozk\Test\Gradio\test\test_asetts\voice1.wav"#デフォルトの音声ファイル
#     voice2 = r"C:\Users\okozk\Test\Gradio\test\test_asetts\voice2.wav"#デフォルトの音声ファイル
#     kaisetsu1 = r"C:\Users\okozk\Test\Gradio\test\test_asetts\kaisetsu1.png"#デフォルトの解説画像1
#     kaisetsu2 = r"C:\Users\okozk\Test\Gradio\test\test_asetts\kaisetsu2.png"#デフォルトの解説画像2
#     toumei = r"C:\Users\okozk\Test\Gradio\test\test_asetts\toumei.png"#デフォルトのホワイトボード画像
#     jimaku1 = r"C:\Users\okozk\Test\Gradio\test\test_asetts\jimaku1.png"#デフォルトの字幕画像
#     jimaku2 = r"C:\Users\okozk\Test\Gradio\test\test_asetts\jimaku2.png"#デフォルトの字幕画像
#     vtuber_character_path = r"C:\Users\okozk\Test\Gradio\test\test_asetts\v_chara.png"#デフォルトのVTuberキャラクター画像

class Render:
    async def Render(self):
        from create_video import CreateVideo  # インポートを関数内に移動

        # # テスト用のフレームデータを作成
        # frame_data_list = [
        #     FrameData(
        #         "こんにちは、世界！",  # subtitle_line
        #         "コンニチハ、セカイ！",  # reading_line
        #         TestData.voice1,  # audio_file
        #         ["うれしいキラ目","ハート目","うれしい","リボン"],  # emotion_shortcut
        #         ["M1","M2","M3","Defo"],  # motion_shortcut
        #         TestData.kaisetsu1,  # explanation_image_path
        #         TestData.toumei,  # whiteboard_image_path
        #         TestData.jimaku1,  # subtitle_image_path
        #         "test_preview_image_1.png",  # preview_image
        #         ("Model1", "model_id_1", "speaker_id_1")  # selected_model
        #     ),
        #     FrameData(
        #         "おはようございます",  # subtitle_line
        #         "オハヨウゴザイマス",  # reading_line
        #         TestData.voice2,  # audio_file
        #         ["うれしいキラ目","ハート目","うれしい","リボン"],  # emotion_shortcut
        #         ["M1","M2","M3","Defo"],  # motion_shortcut
        #         TestData.kaisetsu2,  # explanation_image_path
        #         TestData.toumei,  # whiteboard_image_path
        #         TestData.jimaku2,  # subtitle_image_path
        #         "test_preview_image_2.png",  # preview_image
        #         ("Model2", "model_id_2", "speaker_id_2")  # selected_model
        #     )
        # ]

        # Name: Defo, File: Motion_Neutral.motion3.json, HotkeyID: 47291e0c66904eefa41605addaf31831
        # Name: M1, File: Motion1.motion3.json, HotkeyID: 27d8e9b7951b4b3c850515f8f63ea848
        # Name: M2, File: Motion2.motion3.json, HotkeyID: 4118e78e607d44c5a3083074ec7f4707
        # Name: M3, File: Motion3.motion3.json, HotkeyID: 2dc644e816b84dd895a7a988c5e9f41c
        # Name: Short Hair, File: expression11.exp3.json, HotkeyID: 5749edd1570d469ea4b9ab50d0419c68
        # Name: 悲しみ, File: expression4.exp3.json, HotkeyID: bd6c977db0cb4c89966cb2964d09fff9
        # Name: リボン, File: expression12.exp3.json, HotkeyID: 31188d773485484c833e2ee827d3d3b5
        # Name: うれしい, File: expression5.exp3.json, HotkeyID: c0d86a1fddc94cbdb7ba142ca2e794fc
        # Name: 怒る, File: expression6.exp3.json, HotkeyID: cd253a31c5c845dda38fd6f504dba3f5
        # Name: ハート目, File: expression8.exp3.json, HotkeyID: fbf8e9e9892746c5b4ba1579ee3bea43
        # Name: うれしいキラ目, File: expression9.exp3.json, HotkeyID: 861e13e4df9046c0bcd1a4690a2b0878
        # Name: バイバイ, File: expression3.exp3.json, HotkeyID: fd95fc980500472682ee9218da303920


        # create_video = CreateVideo(frame_data_list, output_file)
        # await create_video.create_video_run()
        pass
