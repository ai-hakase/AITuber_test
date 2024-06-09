from PIL import Image
from moviepy.editor import VideoFileClip
from utils import *
from vtuber_camera import VTuberCamera

import textwrap
from PIL import ImageDraw, ImageFont


class EditMedia:

    def __init__(self):
        self.vtuber_camera = VTuberCamera()
        # 字幕画像のパスを準備
        self.subtitle_image_path = "Asset/tb00018_03_pink.png"
        self.font_path = "Asset/NotoSansJP-VariableFont_wght.ttf"

    # 画像のアスペクト比を維持しながらリサイズ
    def resize_image_aspect_ratio(self, image, target_width, target_height):
        # RGBAモードに変換
        image = image.convert("RGBA")
        
        width, height = image.size
        aspect_ratio = width / height
        
        if target_width is not None and target_height is not None:
            target_aspect_ratio = target_width / target_height
            if aspect_ratio > target_aspect_ratio:
                new_width = target_width
                new_height = int(new_width / aspect_ratio)
            else:
                new_height = target_height
                new_width = int(new_height * aspect_ratio)
        elif target_width is not None:
            new_width = target_width
            new_height = int(new_width / aspect_ratio)
        elif target_height is not None:
            new_height = target_height
            new_width = int(new_height * aspect_ratio)
        else:
            return image
        
        resized_image = image.resize((new_width, new_height), Image.LANCZOS).convert("RGBA")
        return resized_image


    # アスペクト比を維持しながら、指定した横幅または高さに基づいてリサイズ後の寸法を計算
    def resize_aspect_ratio(self, current_width, current_height, target_width, target_height):
        aspect_ratio = current_width / current_height
        
        if target_width is not None and target_height is not None:
            target_aspect_ratio = target_width / target_height
            if aspect_ratio > target_aspect_ratio:
                new_width = target_width
                new_height = int(new_width / aspect_ratio)
            else:
                new_height = target_height
                new_width = int(new_height * aspect_ratio)
        elif target_width is not None:
            new_width = target_width
            new_height = int(new_width / aspect_ratio)
        elif target_height is not None:
            new_height = target_height
            new_width = int(new_height * aspect_ratio)
        else:
            new_width = current_width
            new_height = current_height
        
        return new_width, new_height


    # 動画のアスペクト比を維持しながらリサイズ 
    def resize_video_aspect_ratio(self, input_path, output_path, target_width=None, target_height=None):
        # 動画クリップを読み込む
        video = VideoFileClip(input_path)
        
        # 元の動画のサイズ
        width, height = video.size
        aspect_ratio = width / height

        # 新しいサイズを計算
        if target_width is not None and target_height is not None:
            target_aspect_ratio = target_width / target_height
            if aspect_ratio > target_aspect_ratio:
                new_width = target_width
                new_height = int(new_width / aspect_ratio)
            else:
                new_height = target_height
                new_width = int(new_height * aspect_ratio)
        elif target_width is not None:
            new_width = target_width
            new_height = int(new_width / aspect_ratio)
        elif target_height is not None:
            new_height = target_height
            new_width = int(new_height * aspect_ratio)
        else:
            new_width, new_height = width, height

        # 動画クリップをリサイズ
        resized_video = video.resize(newsize=(new_width, new_height))

        return resized_video
        # # 出力ファイルとして保存
        # resized_video.write_videofile(output_path, codec='libx264', audio_codec='aac')


    # 画像の周りにボーダーラインを引く
    def add_border(self, image, border_width):
        width, height = image.size
        new_width = width + border_width * 2
        new_height = height + border_width * 2
        bordered_image = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 255))
        bordered_image.paste(image, (border_width, border_width))
        return bordered_image


    # PILを使用してグリーンバック画像を生成
    def generate_explanation_image(self):
        img = Image.new('RGB', (1280, 720), (0, 255, 0))
        return save_as_temp_file(img)


    # 字幕画像の生成   
    def generate_subtitle(self, subtitle_line, preview_width, preview_height):

        # 字幕用の画像を読み込む
        img = Image.open(self.subtitle_image_path)
        d = ImageDraw.Draw(img)
        font = ImageFont.truetype(self.font_path, 48)

        # 画像のサイズを取得
        img_width, img_height = img.size

        # テキストを指定された幅で改行する
        wrapped_text = textwrap.fill(subtitle_line, width=((img_width - 50) // font.getbbox("あ")[2]))

        # 改行後のテキストを2行以内に制限する
        lines = wrapped_text.split("\n")
        if len(lines) > 2:
            lines = lines[:2]
        wrapped_text = "\n".join(lines)

        # テキストのサイズを取得
        text_width, text_height = d.multiline_textbbox((0, 0), wrapped_text, font=font)[2:]

        # 文字を中央揃えにするための位置を計算
        text_x = (img_width - text_width) / 2
        text_y = (img_height - text_height) / 2

        # 一行の場合は文字の位置を上げる
        if len(lines) == 1:
            text_y -= 30  # 上に5ピクセル移動

        # 文字の描画位置を計算
        draw_x = text_x
        draw_y = text_y - text_height / 2 +140#調整

        # 計算された位置にテキストを描画
        d.multiline_text((draw_x, draw_y), wrapped_text, fill=(0, 0, 0), font=font, align='center', spacing=20)

        subtitle_img = self.resize_image_aspect_ratio(img, preview_width, preview_height)#リサイズ


        # グリーンバック画像を生成
        subtitle_with_green_background = Image.new('RGB', (preview_width, preview_height), (0, 255, 0))

        # 字幕画像のサイズを取得
        subtitle_width, subtitle_height = subtitle_img.size

        # 字幕画像を下部中央に配置するための座標を計算
        x = (subtitle_with_green_background.width - subtitle_width) // 2  # 横方向の中央
        y = subtitle_with_green_background.height - subtitle_height       # 下部に配置

        # グリーンバック画像に字幕画像を貼り付け
        subtitle_with_green_background.paste(subtitle_img, (x, y), mask=subtitle_img)

        return subtitle_with_green_background
    

    def create_preview_area(self):
        # プレビューエリアを作成
        preview_width = 1920
        preview_height = 1080
        preview = Image.new('RGBA', (preview_width, preview_height))  # RGBAモードで作成
        return preview


    # PILを使用してホワイトボード画像を生成
    def create_whiteboard(self, preview_width, preview_height, subtitle_img):
        
        # ホワイトボードのサイズを計算
        left_margin = 30
        right_margin = 30
        top_margin = 30
        bottom_margin = 30

        # ホワイトボードのサイズを計算
        whiteboard_width = preview_width // 4 * 3 -50#調整
        whiteboard_height = preview_height - subtitle_img.height // 2 -30#調整

        # ホワイトボードのサイズを計算
        whiteboard_width = whiteboard_width - left_margin - right_margin
        whiteboard_height = whiteboard_height - top_margin - bottom_margin

        print(f"width,height: {whiteboard_width},{whiteboard_height}")
        # ホワイトボード画像を作成
        # img = Image.new('RGBA', (whiteboard_width, whiteboard_height), (255, 255, 255, 0))
        img = Image.new('RGBA', (whiteboard_width, whiteboard_height), (255, 255, 255, 150))

        #一時ファイルに保存してパスを返す
        return img


    def create_vtuber_image(self):

        # Camera -> Vキャラ画像をキャプチャ
        vtuber_img = self.vtuber_camera.capture_image().convert("RGBA")  # RGBAモードに変換

        # クロマキー処理
        vtuber_img = process_transparentize_green_back(vtuber_img)

        # # イメージの横幅を取得してそれの1/4を左と右のそれぞれから切り取る
        # vtuber_width, vtuber_height = vtuber_img.size
        # # left = (vtuber_width - 600) // 2
        # # right = left + 600
        # left = vtuber_width // 4 -30#調整
        # right = vtuber_width - left
        # top = 0
        # bottom = vtuber_height
        # vtuber_img = vtuber_img.crop((left, top, right, bottom))

        # # リサイズ
        # vtuber_img = self.resize_image_aspect_ratio(vtuber_img, None, 720).convert("RGBA")  # RGBAモードに変換

        return vtuber_img

