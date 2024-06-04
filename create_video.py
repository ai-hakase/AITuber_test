import os

from render import FrameData
from create_timeline import Timeline


class CreateVideo:

    def __init__(self, frame_data_list: list[FrameData], output_file: str, background_video_path: str):
        self.frame_data_list = frame_data_list
        self.output_file = output_file
        self.background_video_path = background_video_path

    async def create_video_run(self):

        # タイムラインの作成
        timeline = Timeline(self.frame_data_list, self.output_file, self.background_video_path)
        await timeline.create()


        # 出力ファイルが既に存在する場合は削除
        if os.path.exists(self.output_file):
            os.remove(self.output_file)

        # GPUアクセラレーションオプションを指定
        ffmpeg_params = ["-hwaccel", "cuda"]  # NVIDIAのGPUを使用する場合


        # 最初の2秒間を切り取る
        final_clip = timeline.final_clip
        # final_clip = final_clip.subclip(0, 1)

        # final_video.write_videofile(self.output_file, codec='libx264', audio_codec='aac', fps=24, ffmpeg_params=ffmpeg_params)
        # 動画を書き出し
        final_clip.write_videofile(self.output_file, codec='libx264', audio_codec='aac', fps=24)
        # final_video.write_videofile(self.output_file, codec='libx264', audio_codec='aac', fps=24, ffmpeg_params=ffmpeg_params)

