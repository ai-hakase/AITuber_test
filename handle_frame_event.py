import gradio as gr

from PIL import Image
import os
from datetime import datetime
import asyncio

# from constants import *
from generate_video import GenerateVideo
from utils import save_as_temp_file, load_image_or_video
from create_subtitle_voice import CreateSubtitleVoice
from create_video import CreateVideo
from render import FrameData

# from edit_medias import *


class HandleFrameEvent:
    def __init__(self, generate_video):
        self.generate_video = generate_video
        self.create_subtitle_voice = CreateSubtitleVoice()

    # frame_data_list_state をリセットする関数
    def reset_frame_data_list(self):
        self.generate_video.frame_data_list = []
        return []

    # フレームデータから各要素を抽出してUIに表示する関数
    def update_ui_elements(self, selected_index, frame_data_list: list[FrameData]):

        # 各要素を抽出
        try:
            preview_images = [frame_data.preview_image for frame_data in frame_data_list]
            subtitle_input_list = [frame_data.subtitle_line for frame_data in frame_data_list]
            reading_input_list = [frame_data.reading_line for frame_data in frame_data_list]
            audio_file_list = [frame_data.audio_file for frame_data in frame_data_list]
            emotion_dropdown_list = [frame_data.emotion_shortcut for frame_data in frame_data_list]
            motion_dropdown_list = [frame_data.motion_shortcut for frame_data in frame_data_list]
            explanation_path_list = [frame_data.explanation_image_path for frame_data in frame_data_list]
        except IndexError as e:
            print(f"IndexError: {e}")
            return None, None, None, None, None, None

        subtitle_input = subtitle_input_list[selected_index]
        reading_input = reading_input_list[selected_index]
        test_playback_button = audio_file_list[selected_index]
        emotion_dropdown = emotion_dropdown_list[selected_index]
        motion_dropdown = motion_dropdown_list[selected_index]
        # image_video_input = explanation_path_list[selected_index]
        image_video_input = None

        # 戻り値として各要素のリストを返す
        return preview_images, subtitle_input, reading_input, test_playback_button, emotion_dropdown, motion_dropdown, image_video_input


    # 読み方変更ボタンがクリックされたときの処理
    def on_update_reading_click(self, subtitle_line, reading_line, image_video_input, selected_index, selected_model_tuple_state, whiteboard_image_path, frame_data_list: list[FrameData]):

        # フレームデータリストがNoneの場合の処理
        if frame_data_list is None:
            raise ValueError(f"frame_data_list is -> {frame_data_list}")
        # ギャラリーのインデックスがNoneの場合の処理
        if selected_index is None:
            raise ValueError(f"selected_index is -> {selected_index}")
            
        print(f"\n selected_index is -> {selected_index} !!!")

        # image_video_input が None の場合の処理
        if image_video_input is None:
            image_video_input = r"Asset\Greenbak.png"

        # 字幕画像の生成
        subtitle_img = self.generate_video.edit_medias.generate_subtitle(subtitle_line, self.generate_video.preview_width, self.generate_video.preview_height)#字幕画像の生成
        subtitle_image_path = save_as_temp_file(subtitle_img)#テンポラリファイルに保存

        # Vキャラ画像を生成 -> クロマキー処理
        vtuber_img = self.generate_video.edit_medias.create_vtuber_image()
        vtuber_character_path = save_as_temp_file(vtuber_img)

        # 解説画像の生成
        explanation_img = load_image_or_video(image_video_input).convert("RGBA")  # RGBAモードに変換
        whiteboard_image = Image.open(whiteboard_image_path).convert("RGBA")  # RGBAモードに変換
        # 解説画像のアスペクト比を維持しながらホワイトボード画像に合わせてリサイズ
        explanation_img = self.generate_video.edit_medias.resize_image_aspect_ratio(explanation_img, whiteboard_image.width - 20, whiteboard_image.height - 20)
        # 解説画像の周りにボーダーを追加
        explanation_img = self.generate_video.edit_medias.add_border(explanation_img, 10)
        explanation_image_path = save_as_temp_file(explanation_img)
        background_video_file = "background_video\default_video.mp4"
        # プレビュー画像の生成  
        preview_image_path = self.generate_video.generate_preview_image(background_video_file, explanation_image_path, whiteboard_image_path, subtitle_image_path, vtuber_character_path)

        # 現在のフレームデータを更新
        frame_data : FrameData = frame_data_list[selected_index]

        # if image_video_input == r"Asset\Greenbak.png": #画像がない場合
        #     image_video_input = None #Noneに変換

        #読み方が変わっていれば音声変換してパスを取得
        if reading_line != frame_data.reading_line :
            model_name, model_id, speaker_id = selected_model_tuple_state #モデル情報を取得
            audio_file_path = self.create_subtitle_voice.generate_audio(subtitle_line, reading_line, model_name, model_id, speaker_id) #音声変換
            frame_data.audio_file = audio_file_path #フレームデータに音声パスを追加

        frame_data.subtitle_line = subtitle_line #字幕
        frame_data.reading_line = reading_line #読み方
        frame_data.explanation_image_path = image_video_input #画像
        frame_data.preview_image = preview_image_path #プレビュー画像

        # 更新されたフレームデータをリストに戻す
        frame_data_list[selected_index] = frame_data

        # UIコンポーネントを更新
        return self.update_ui_elements(selected_index, frame_data_list)


    # ギャラリーのインデックスが選択されたときに呼び出される関数
    def handle_gallery_click(self, evt: gr.SelectData, subtitle_input, reading_input, image_video_input, selected_index, selected_model_tuple_state, frame_data_list: list[FrameData]):
        # global frame_data_list
        
        new_selected_index = evt.index#ギャラリーのインデックスを取得
        # print(f"new_selected_index: {new_selected_index}")
        # print(f"selected_index: {selected_index}")

        current_frame_data: FrameData = frame_data_list[selected_index]#現在のフレームデータを取得


        # 現在のデータと新しいデータを比較
        if (current_frame_data.subtitle_line != subtitle_input or current_frame_data.reading_line != reading_input or current_frame_data.explanation_image_path != image_video_input): 

            # データが異なる場合のみ更新
            if image_video_input != None: #画像がある場合
                whiteboard_image_path = current_frame_data.whiteboard_image_path
                self.on_update_reading_click(subtitle_input, reading_input, image_video_input, selected_index, selected_model_tuple_state, whiteboard_image_path, frame_data_list)
                # image_video_input = r"Asset\Greenbak.png" #Noneに変換

        # 次に表示するUI要素を更新
        preview_images, subtitle_input, reading_input, test_playback_button, emotion_dropdown, motion_dropdown, image_video_input = self.update_ui_elements(new_selected_index, frame_data_list)

        # if image_video_input == r"Asset\Greenbak.png": #画像がない場合
        #     image_video_input = None #Noneに変換
            
        return preview_images, subtitle_input, reading_input, test_playback_button, emotion_dropdown, motion_dropdown, None, new_selected_index



    # def on_video_creation_complete(self, task, selected_index, frame_data_list):
    #     try:
    #         task.result()  # 例外が発生していないか確認
    #         print("動画の作成が完了しました")
    #         # UIコンポーネントを更新
    #         self.update_ui_elements(selected_index, frame_data_list)
    #     except Exception as e:
    #         print(f"動画の作成中にエラーが発生しました: {e}")


    # 動画作成ボタンがクリックされたときの処理
    async def create_video(self, output_folder_input, bgm_file_input, subtitle_input, reading_input, image_video_input, selected_index, selected_model_tuple_state, whiteboard_image_path, frame_data_list: list[FrameData]):
        # global frame_data_list
    

        print(f"image_video_input: {image_video_input}")
        if image_video_input == None:
            image_video_input = frame_data_list[selected_index].explanation_image_path

        preview_images, subtitle_input, reading_input, test_playback_button, emotion_dropdown, motion_dropdown, image_video_input = self.on_update_reading_click(subtitle_input, reading_input, image_video_input, selected_index, selected_model_tuple_state, whiteboard_image_path, frame_data_list)
    
        # final_frame_data_list = []
        # for frame in frame_data_list:
        #     frame_data = FrameData(*frame)
        #     frame_data.bgm_path = bgm_file_input
        #     final_frame_data_list.append(frame_data)
        #     print(f"frame_data.background_video_path: {frame_data.background_video_path}")
        # output_folder_input.value　+　output　+　タイムスタンプ　.mp4　がファイルパス

        background_video_path = "background_video\default_video.mp4"
        output_file_path = os.path.join(output_folder_input, "output-" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + ".mp4")
        # print(f"output_file_path: {output_file_path}")

        create_video = CreateVideo(frame_data_list, output_file_path, background_video_path)
        # create_video = CreateVideo(final_frame_data_list, output_file_path)
        await create_video.create_video_run()

        # 別スレッドで実行
        # task = asyncio.create_task(create_video.create_video_run())
        # task.add_done_callback(lambda t: print("動画の作成が完了しました"))
        # task.add_done_callback(lambda t: self.on_video_creation_complete(t, selected_index, frame_data_list))
        # await create_video.create_video_run()

        return preview_images, subtitle_input, reading_input, test_playback_button, emotion_dropdown, motion_dropdown, None, output_file_path 
