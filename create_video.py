import os
import shutil
import asyncio

from render import FrameData
from create_timeline import Timeline
from constants import DEFAULT_OUTPUTS_FOLDER


class CreateVideo:

    def __init__(self, frame_data_list: list[FrameData], output_file: str):
        # タイムラインの作成
        self.timeline = Timeline(frame_data_list, output_file)


    async def create_video_run(self):

        output_file = await self.timeline.create()

        print(f"動画の作成が完了しました: {output_file}")

        await asyncio.sleep(3)

        # output_fileをoutputsディレクトリに移動
        new_file_path = os.path.join(DEFAULT_OUTPUTS_FOLDER, os.path.basename(output_file))
        try:
            shutil.move(output_file, new_file_path)
            print(f"動画を {new_file_path} に移動しました。")
        except FileNotFoundError:
            print(f"エラー: ファイル {output_file} が見つかりません。")
        except PermissionError:
            print(f"エラー: {new_file_path} への書き込み権限がありません。")
        except Exception as e:
            print(f"エラー: ファイル移動中にエラーが発生しました: {e}")

        return new_file_path

        # return output_file
