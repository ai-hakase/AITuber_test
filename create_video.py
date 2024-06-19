import os
import subprocess
import asyncio

from render import FrameData
from create_timeline import Timeline
from moviepy.config import change_settings


class CreateVideo:

    def __init__(self, frame_data_list: list[FrameData], output_file: str, background_video_path: str):
        self.frame_data_list = frame_data_list
        self.output_file = output_file
        self.background_video_path = background_video_path

        # GPUアクセラレーションオプションを指定
        self.ffmpeg_params = ["-hwaccel", "cuda"]  # NVIDIAのGPUを使用する場合


    async def create_video(self, timeline):
        await timeline.create()


    def create_video_run(self):

        # タイムラインの作成
        timeline = Timeline(self.frame_data_list, self.output_file, self.background_video_path)
        output_file = asyncio.run(self.create_video(timeline))

        # self.output_file = await timeline.output_file
        print(f"動画の作成が完了しました: {output_file}")

        # output_file = os.path.abspath(output_file)

        # await timeline.create()

        return output_file
