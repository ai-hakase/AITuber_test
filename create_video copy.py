import os
import subprocess
import asyncio

from render import FrameData
from create_timeline import Timeline
from moviepy.config import change_settings


class CreateVideo:

    def __init__(self, frame_data_list: list[FrameData], output_file: str):
        # タイムラインの作成
        self.timeline = Timeline(frame_data_list, output_file)


    async def create_video_run(self):

        output_file = await self.timeline.create()

        print(f"動画の作成が完了しました: {output_file}")

        # output_file = os.path.abspath(output_file)

        return output_file
