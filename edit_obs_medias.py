import cv2

from utils import save_as_temp_file
from edit_medias import EditMedia
from obs_controller import OBSController


class EditOBSMedias:
    def __init__(self):
        self.edit_medias = EditMedia()
        self.obs_controller = OBSController()

    # ファイルの種類によってトランスフォームを変更
    def get_video_resolution(self, file_path):
        """OpenCVを使って動画の幅と高さを取得する"""

        cap = cv2.VideoCapture(file_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        return width, height

    def calculate_scale(self, source_width, source_height, target_width, target_height):
        """ソースのサイズをターゲットのサイズに合わせるスケールを計算する"""

        width_ratio = target_width / source_width - 0.015#スケールを0.05ずつ小さくする
        height_ratio = target_height / source_height - 0.015

        # アスペクト比を維持するために、小さい方の比率を採用
        scale = min(width_ratio, height_ratio)

        return scale, scale  # scaleX と scaleY は同じ値

    def calculate_position_x(self, source_width, target_width):
        """ソースをターゲットの中央に配置するための position_x を計算する"""
        # print(f"動画の横幅: {source_width}, ホワイトボードの横幅: {target_width}")
        if source_width < target_width:
            return (target_width - source_width) / 2  # 中央に配置
        else:
            return 0  # ソースがターゲットより大きい場合は左端に配置


    async def update_explanation_media(self, file_path, whiteboard_image_path, 
                                       scene_name, source_name, scene_item_id, whiteboard_transform):
        """
        解説メディアの更新
        """
        # シーンアイテムのトランスフォームを取得
        position_x = whiteboard_transform.get("positionX")# シーンアイテムの位置X
        position_y = whiteboard_transform.get("positionY")# シーンアイテムの位置Y
        source_height = whiteboard_transform.get("sourceHeight")# シーンアイテムのソースの高さ
        source_width = whiteboard_transform.get("sourceWidth")# シーンアイテムのソースの幅

        # 動画の場合
        if file_path.lower().endswith(('.mp4', '.avi', '.mov')):
            # 動画の横幅と高さを取得
            width, height = self.get_video_resolution(file_path)
            # ソースのサイズをターゲットのサイズに合わせるスケールを計算
            scale_x, scale_y = self.calculate_scale(width, height, source_width, source_height)
            # スケールを適応した動画の横幅を計算
            video_width = width * scale_x
            # スケールを適応した動画の横幅に合わせる位置を計算
            position_x += self.calculate_position_x(video_width, source_width)-3
            position_y += 5
        else:
            # 画像の場合
            # ホワイトボード画像と解説画像を合成
            whiteboard_and_explanation_img = self.edit_medias.generate_composite_media(
                                                    whiteboard_image_path, file_path)  # 解説画像を合成
            file_path = save_as_temp_file(whiteboard_and_explanation_img)
            scale_x = 1
            scale_y = 1


        # OBSのメディアソースを変更
        input_settings = {"file": file_path, 'local_file': file_path, 'looping': True}
        await self.obs_controller.set_input_settings(source_name, input_settings)

        # シーンアイテムのトランスフォームを変更
        scene_item_transform = {
                                "positionX": position_x, 
                                "positionY": position_y, 
                                "scaleX": scale_x, 
                                "scaleY": scale_y, 
                                }
        await self.obs_controller.set_scene_item_transform(scene_name, scene_item_id, scene_item_transform)

        # シーンアイテムのトランスフォームを取得
        scene_item_transform = await self.obs_controller.get_scene_item_transform(scene_name, scene_item_id)
        # print(f"シーンアイテムのトランスフォームを取得: {scene_item_transform}")

