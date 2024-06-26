import shutil
import asyncio

from render import FrameData
from create_timeline import Timeline


class CreateVideo:
    """
    動画作成クラス
    """

    def __init__(self, frame_data_list: list[FrameData], output_file_path: str):
        """
        コンストラクタ
        frame_data_list: フレームデータリスト
        output_file_path: 出力ファイルパス
        """
        # タイムラインの作成
        self.timeline = Timeline(frame_data_list, output_file_path)
        # 出力ファイルパス
        self.output_file_path = output_file_path


    async def create_video_run(self):
        """
        動画作成を実行する関数
        """
        obs_video_file_path = await self.timeline.create()

        print(f"動画の作成が完了しました: {obs_video_file_path}")

        await asyncio.sleep(3)

        # output_file_path が指定されていれば、ファイル名を変更して移動
        if hasattr(self, "output_file_path"):

            try:
                # ファイル名を変更して移動
                shutil.move(obs_video_file_path, self.output_file_path)
                print(f"動画を {self.output_file_path} に保存しました。")
        
            except FileNotFoundError:
                print(f"エラー: ファイル {obs_video_file_path} が見つかりません。")

            except PermissionError:
                print(f"エラー: {self.output_file_path} への書き込み権限がありません。")

            except Exception as e:
                print(f"エラー: ファイル移動中にエラーが発生しました: {e}")

        return self.output_file_path
    