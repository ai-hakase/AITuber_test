import os

from render import FrameData
from create_timeline import Timeline
import subprocess

from moviepy.config import change_settings

change_settings({"FFMPEG_BINARY": "ffmpeg"})  # FFmpeg のパスを指定 (必要に応じて変更)


class CreateVideo:

    def __init__(self, frame_data_list: list[FrameData], output_file: str, background_video_path: str):
        self.frame_data_list = frame_data_list
        self.output_file = output_file
        self.background_video_path = background_video_path

        # GPUアクセラレーションオプションを指定
        self.ffmpeg_params = ["-hwaccel", "cuda"]  # NVIDIAのGPUを使用する場合

    async def create_video_run(self):

        # タイムラインの作成
        timeline = Timeline(self.frame_data_list, self.output_file, self.background_video_path)
        await timeline.create()


        # 出力ファイルが既に存在する場合は削除
        if os.path.exists(self.output_file):
            os.remove(self.output_file)


        # 最初の2秒間を切り取る
        final_clip = timeline.final_clip
        final_clip = final_clip.subclip(0, 2)


        # # FFmpeg コマンドを生成
        # command = (
        #     [
        #         "ffmpeg",
        #         "-hwaccel", "cuda",
        #         "-i", self.background_video_path,
        #         "-i", final_clip.filename,  # MoviePy が一時的に生成した動画ファイルのパス
        #         "-map", "0:v",  # 背景動画のビデオストリームを選択
        #         "-map", "1:a",  # final_clip のオーディオストリームを選択
        #         "-c:v", "h264_nvenc",
        #         "-preset", "fast",
        #         "-b:v", "2M",
        #         "-c:a", "aac",
        #         "-b:a", "128k",
        #         self.output_file
        #     ]
        #     # + self.ffmpeg_params  # 追加の FFmpeg パラメータ
        # )
        # # FFmpeg コマンドを実行し、結果をチェックする関数
        # # command = "ffmpeg -hwaccel cuda -i input.mp4 -c:v h264_nvenc -preset fast -b:v 2M -c:a aac -b:a 128k output.mp4"
        # subprocess.run(command, check=True)


        # # 動画をプレビュー再生
        # # オーディオクリップのフレームレートを設定
        # if final_clip.audio:
        #     final_clip.audio = final_clip.audio.set_fps(48000)  # 44100は一般的なオーディオのフレームレートです
        # final_clip.preview()


        # 動画を書き出し
        final_clip.write_videofile(
            self.output_file, 
            threads=5,
            # bitrate="2000k",
            audio_codec='aac', 
            codec='h264_nvenc', 
            # codec='libx264', 
            fps=24, 
            # progress_bar = False,
            # ffmpeg_params=["-hwaccel", "cuda", "-i", self.background_video_path] + self.ffmpeg_params,
        )




