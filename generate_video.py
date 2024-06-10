import threading
import tkinter as tk
import pygame
import time
import cv2

from PIL import Image, ImageDraw, ImageFont
from utils import process_transparentize_green_back, save_as_temp_file, load_image_or_video, delete_tmp_files, capture_first_frame
from edit_medias import EditMedia
from vts_hotkey_trigger import VTubeStudioHotkeyTrigger
from create_subtitle_voice import CreateSubtitleVoice
from setup_vtuber_keys import SetupVtuberKeys
from render import FrameData


class GenerateVideo:

    def __init__(self):
        self.frame_data_list:list[FrameData] = []

        # インスタンスの生成
        self.edit_medias = EditMedia()
        self.create_subtitle_voice = CreateSubtitleVoice()
        self.setup_vtuber_keys = SetupVtuberKeys()
        self.vts_hotkey_trigger = VTubeStudioHotkeyTrigger()
        # self.handle_frame_event = HandleFrameEvent()

        # メインキャラクター
        self.main_character = None
        self.subtitle_image_path = None

        # キャラクターごとの最後に入力したモーションショットカットを保持する辞書
        self.last_motion_shortcut = {
            self.main_character: None,
            "other": None
        }

        self.default_explanation_image_path = r"Asset/Greenbak.png"

        # プレビューエリアを作成 → 動画の大きさ
        self.preview_width = 1920
        self.preview_height = 1080
        # self.preview = Image.new('RGBA', (self.preview_width, self.preview_height))  # RGBAモードで作成

        self.preview = Image.new('RGBA', (self.preview_width, self.preview_height), (0, 0, 0, 0))  # 透明背景
        self.preview_green = Image.new('RGB', (self.preview_width, self.preview_height), (0, 255, 0))  # グリーンスクリーン



        self.scene_name = "AI_Tuber_test"

    # プレビュー画像を生成する関数
    def generate_preview_image(self, background_video_file_input, explanation_image_path, whiteboard_image_path, subtitle_image_path, vtuber_character_path):

        # 背景動画の最初のフレームを読み込む
        background = capture_first_frame(background_video_file_input)
        # プレビューエリアのサイズに合わせてリサイズ
        background = self.edit_medias.resize_image_aspect_ratio(background, self.preview_width, self.preview_height+1)#調整

        # 字幕画像を読み込む
        subtitle_img = Image.open(subtitle_image_path).convert("RGBA")
        subtitle_img = process_transparentize_green_back(subtitle_img) # グリーンスクリーンを透明にする

        # Vキャラ画像を読み込む
        vtuber_img = Image.open(vtuber_character_path).convert("RGBA")  # RGBAモードに変換

        # ホワイトボード画像を読み込む
        whiteboard_img = Image.open(whiteboard_image_path).convert("RGBA")  # RGBAモードに変換

        # 解説画像を読み込む
        explanation_img = load_image_or_video(explanation_image_path)


        # # 背景画像を合成
        # self.preview.paste(background, (0, 0))

        
        # ホワイトボード画像を合成

        # whiteboard_x = 30#ホワイトボード画像の位置を計算
        # whiteboard_y = 30#ホワイトボード画像の位置を計算
        # self.preview.paste(whiteboard_img, (whiteboard_x, whiteboard_y), mask=whiteboard_img)#ホワイトボード画像を合成

        # # ホワイトボード画像に解説画像を合成する
        # explanation_x = (whiteboard_img.width - explanation_img.width) // 2 + whiteboard_x#解説画像の位置を計算
        # explanation_y = (whiteboard_img.height - explanation_img.height) // 2 + whiteboard_y#解説画像の位置を計算
        # self.preview.paste(explanation_img, (explanation_x, explanation_y))#ホワイトボード画像に解説画像を合成

        # explanation_img = process_transparentize_green_back(explanation_img)
        # self.preview.paste(explanation_img, (30, 30), mask=explanation_img)


        # Vキャラ画像を合成
        # リサイズ後の位置を計算
        # vtuber_x = self.preview_width - vtuber_img.width +10#調整
        # vtuber_y = self.preview_height - vtuber_img.height -200#調整
        # self.preview.paste(vtuber_img, (vtuber_x, vtuber_y), mask=vtuber_img)
        self.preview.paste(vtuber_img, (15, 0), mask=vtuber_img)

        # 解説画像を合成
        self.preview.paste(explanation_img, (30, 30), mask=explanation_img)

        # 字幕を合成
        # subtitle_x = (self.preview_width - subtitle_img.width) // 2
        # subtitle_y = self.preview_height - subtitle_img.height
        # print(f"subtitle_x: {subtitle_x}, subtitle_y: {subtitle_y}")
        # self.preview.paste(subtitle_img, (subtitle_x, subtitle_y), mask=subtitle_img)
        
        # subtitle_imgをクロマキー処理
        self.preview.paste(subtitle_img, (0, 0), mask=subtitle_img)

        # プレビュー画像を保存
        preview_image_path = save_as_temp_file(self.preview)

        return preview_image_path


    # 動画生成の主要な処理を行う関数
    async def generate_video(self, csv_file_input, bgm_file_input, background_video_file_input, 
                    character_name_input, model_list_state, selected_model_tuple_state, 
                    reading_speed_slider, registered_words_table, emotion_shortcuts_state, actions_state):

        from handle_frame_event import HandleFrameEvent
        handle_frame_event = HandleFrameEvent(self)

        # global frame_data_list # グローバル変数にすることで、関数内でもフレームデータのリストにアクセスできるようになる
        # frame_data_list = [] # フレームデータのリストをクリア
        self.frame_data_list.clear() # フレームデータのリストをクリア

        # print(f"frame_data_list: {self.frame_data_list}")

        delete_tmp_files() #tmpフォルダーの中身を全て削除する

        # print(f"動画準備開始\n")

        self.main_character = character_name_input#メインキャラクターを設定

        # CSVファイルからキャラクター・セリフ情報を取得
        character_lines = self.create_subtitle_voice.load_csv_data(csv_file_input)#キャラクター・セリフ情報を取得

        # 選択された音声合成モデルの名前
        if selected_model_tuple_state:#選択されたモデルがある場合
            selected_model = selected_model_tuple_state#選択されたモデルを取得
        else:#選択されたモデルがない場合
            selected_model = model_list_state[1]#選択されたモデルを取得
        model_name, model_id, speaker_id = selected_model#選択されたモデルの情報を取得
        # print(f"選択されたモデル: {model_name}, モデルID: {model_id}, 話者ID: {speaker_id}")


        # キャラクター・セリフ情報を処理
        for character, line in character_lines:          
            # 元のセリフを字幕用として変数に保持します。
            # 辞書機能で英語テキストのカタカナ翻訳を行ったセリフを読み方用として変数に保持します。
            subtitle_line, reading_line = self.create_subtitle_voice.process_line(line, registered_words_table)
            # print(f"subtitle_line: {subtitle_line},\n reading_line: {reading_line} \n")

            # Style-Bert-VITS2のAPIを使用して、セリフのテキストの読み上げを作成読み上げ音声ファイルを生成
            audio_file = self.create_subtitle_voice.generate_audio(subtitle_line, reading_line, model_name, model_id, speaker_id, reading_speed_slider)

            # キャラクター事にショートカットキーを選択
            emotion_shortcut, motion_shortcut = self.setup_vtuber_keys.get_shortcut_key(emotion_shortcuts_state, actions_state, character, subtitle_line)
            # emotion_shortcut, motion_shortcut = 'alt+n', 'alt+0'

            # 字幕画像の生成
            subtitle_img = self.edit_medias.generate_subtitle(subtitle_line, self.preview_width, self.preview_height)#字幕画像の生成
            subtitle_image_path = save_as_temp_file(subtitle_img)#テンポラリファイルに保存

            # Vキャラ画像を生成(　→　背景含む全体) -> クロマキー処理
            vtuber_img = self.edit_medias.create_vtuber_image()
            vtuber_img_path = save_as_temp_file(vtuber_img)

            # ホワイトボード画像を生成
            # VTuber_subtitle_height = self.preview_width -1#調整
            # プレビューウィズの2/3の大きさに調整する   
            # whiteboard_subtitle_width = self.preview_width // 3 * 2
            # whiteboard_subtitle_height = self.preview_height - subtitle_img.height // 2 +20#調整
            # print(f"width,height: {whiteboard_subtitle_width},{whiteboard_subtitle_height}")
            whiteboard_image = self.edit_medias.create_whiteboard(self.preview_width, self.preview_height, subtitle_img)
            whiteboard_image_path = save_as_temp_file(whiteboard_image)

            # 解説画像(初期値：グリーンバック)を生成
            explanation_image_path = self.default_explanation_image_path

            # ホワイトボード画像に解説画像を合成する
            explanation_img = whiteboard_image
            load_explanation_img = load_image_or_video(explanation_image_path).convert("RGBA")  # RGBAモードに変換
            # 解説画像のアスペクト比を維持しながらホワイトボード画像に合わせてリサイズ
            load_explanation_img = self.edit_medias.resize_image_aspect_ratio(load_explanation_img, whiteboard_image.width - 20, whiteboard_image.height - 20)
            # 解説画像の周りにボーダーを追加
            load_explanation_img = self.edit_medias.add_border(load_explanation_img, 5)
            # whiteboard_x = 30#ホワイトボード画像の位置を計算
            # whiteboard_y = 30#ホワイトボード画像の位置を計算
            # explanation_x = (explanation_img.width - load_explanation_img.width) // 2 + whiteboard_x#解説画像の位置を計算
            # explanation_y = (explanation_img.height - load_explanation_img.height) // 2 + whiteboard_y#解説画像の位置を計算
            explanation_x = (explanation_img.width - load_explanation_img.width) // 2 #解説画像の位置を計算
            explanation_y = (explanation_img.height - load_explanation_img.height) // 2 #解説画像の位置を計算
            explanation_img.paste(load_explanation_img, (explanation_x, explanation_y))#ホワイトボード画像に解説画像を合成
            explanation_image_path = save_as_temp_file(explanation_img)

            # # test
            # green_explanation_img = self.preview_green
            # green_explanation_img.paste(explanation_img, (30, 30))
            # explanation_image_path = save_as_temp_file(green_explanation_img)

            # プレビュー画像を生成
            preview_image = self.generate_preview_image(background_video_file_input, explanation_image_path, whiteboard_image_path, subtitle_image_path, vtuber_img_path)

            # フレームデータの生成とリストへの保存
            frame_data = FrameData(
                character_name=character,
                subtitle_line=subtitle_line,
                reading_line=reading_line,
                reading_speed=reading_speed_slider,
                selected_model=selected_model,
                audio_file=audio_file,
                emotion_shortcut=emotion_shortcut,
                motion_shortcut=motion_shortcut,
                explanation_image_path=explanation_image_path,
                # explanation_image_path=self.default_explanation_image_path,
                whiteboard_image_path=whiteboard_image_path,
                subtitle_image_path=subtitle_image_path,
                preview_image=preview_image,
                # background_video_path=background_video_file_input
            )
            self.frame_data_list.append(frame_data)

        # print(f"動画準備終了\n")

        # return の準備
        # first_frame_data = self.frame_data_list[0]
        # # subtitle_line, reading_line, audio_file, emotion_shortcut, motion_shortcut, explanation_image_path, whiteboard_image_path, subtitle_image_path, preview_image, selected_model = self.frame_data_list[0]

        # frame_data_listの中身をわかりやすくそれぞれに名前をつけて表示
        # preview_images = [frame_data.preview_image for frame_data in self.frame_data_list]
        # print(f"[0]subtitle_line: {subtitle_line},\n [1]reading_line: {reading_line},\n [2]audio_file: {audio_file},\n [3]emotion_shortcut: {emotion_shortcut},\n [4]motion_shortcut: {motion_shortcut},\n [5]explanation_image_path: {explanation_image_path},\n [6]whiteboard_image_path: {whiteboard_image_path},\n [7]subtitle_image_path: {subtitle_image_path},\n [8]preview_images: {preview_images},\n [9]selected_model: {selected_model}")

        print(f"動画の準備が完了しました")
        selected_index = 0
        return handle_frame_event.update_ui_elements(selected_index, self.frame_data_list)
        # return first_frame_data.subtitle_line, first_frame_data.reading_line, first_frame_data.audio_file, first_frame_data.emotion_shortcut, first_frame_data.motion_shortcut, None, first_frame_data.whiteboard_image_path, first_frame_data.subtitle_image_path, preview_images, first_frame_data.selected_model, self.frame_data_list, first_frame_data.reading_speed