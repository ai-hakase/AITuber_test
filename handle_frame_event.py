import gradio as gr

from PIL import Image
import os
from datetime import datetime
import asyncio
import difflib

# from constants import *
from generate_video import GenerateVideo
from utils import save_as_temp_file, load_image_or_video
from create_subtitle_voice import CreateSubtitleVoice
from create_video import CreateVideo
from render import FrameData
from edit_medias import EditMedia

# from edit_medias import *


class HandleFrameEvent:
    # def __init__(self):
    def __init__(self, generate_video):
        # self.generate_video = GenerateVideo()
        self.generate_video = generate_video
        self.create_subtitle_voice = CreateSubtitleVoice()
        self.edit_medias = EditMedia()


    # frame_data_list_state をリセットする関数
    def setup_frame_data_list(self):
        # self.generate_video.frame_data_list = []
        return gr.update(interactive=True), gr.update(interactive=True) #False


    # フレームデータから各要素を抽出してUIに表示する関数
    def update_ui_elements(self, selected_index, frame_data_list: list[FrameData]):

        # 各要素を抽出
        frame_data: FrameData = frame_data_list[selected_index]
        character_name = frame_data.character_name
        reading_speed_slider = frame_data.reading_speed
        subtitle_input = frame_data.subtitle_line
        reading_input = frame_data.reading_line
        selected_model_tuple_state = frame_data.selected_model
        test_playback_button = frame_data.audio_file
        emotion_dropdown = frame_data.emotion_shortcut
        motion_dropdown = frame_data.motion_shortcut
        image_video_input = None
        # image_video_input = explanation_path_list[selected_index]
        whiteboard_image = frame_data.whiteboard_image_path
        preview_images = [frame_data.preview_image for frame_data in frame_data_list]

        return (
            character_name, subtitle_input, reading_input, reading_speed_slider, 
            selected_model_tuple_state,test_playback_button, emotion_dropdown, motion_dropdown, 
            image_video_input, whiteboard_image, preview_images,
            selected_index, frame_data_list
        )


    # subtitle_line, reading_lineを比較して変更がある箇所をカンマ区切りで一行ずつ出力する
    def compare_subtitle_reading(self, subtitle_line, reading_line):
        diff = difflib.unified_diff(subtitle_line.splitlines(), reading_line.splitlines(), lineterminator="\n")
        diff_list = list(diff)
        diff_list = [line for line in diff_list if line.startswith("-") or line.startswith("+")]
        diff_list = [line.split(" ") for line in diff_list]
        diff_list = [line[1] for line in diff_list]
        diff_list = [line.strip() for line in diff_list]
        diff_list = [line for line in diff_list if line]
        return "\n".join(diff_list)


    def handle_gallery_click(self, evt: gr.SelectData, 
                character_name,subtitle_input, reading_input, update_reading_speed_slider,
                selected_model_tuple_state, emotion_dropdown, motion_dropdown, 
                image_video_input, whiteboard_image_path, 
                selected_index, frame_data_list_state: list[FrameData]):
        """
        ギャラリーのインデックスが選択されたときに呼び出される関数
        """
        new_selected_index = evt.index  # ギャラリーのインデックスを取得 -> kwargs のセレクトインデックスを更新
        current_frame_data: FrameData = frame_data_list_state[selected_index] #現在のフレームデータを取得
        
        # フレームデータを更新
        self.update_frame_data(current_frame_data, 
                               character_name, subtitle_input, reading_input, update_reading_speed_slider, 
                               selected_model_tuple_state, emotion_dropdown, motion_dropdown, 
                               image_video_input, whiteboard_image_path)
        # UIコンポーネントを更新
        return self.update_ui_elements(new_selected_index, frame_data_list_state)


    def on_update_reading_click(self, 
                    character_name, subtitle_input, reading_input, update_reading_speed_slider, 
                    selected_model_tuple_state, emotion_dropdown, motion_dropdown, 
                    image_video_input, whiteboard_image_path, 
                    selected_index, frame_data_list_state: list[FrameData]):
        """
        読み方変更ボタンがクリックされたときの処理
        フレームデータを更新する関数
        """
        # フレームデータリストがNoneの場合の処理
        if frame_data_list_state is None:
            raise ValueError(f"frame_data_list_state is -> {frame_data_list_state}")
        # ギャラリーのインデックスがNoneの場合の処理
        if selected_index is None:
            raise ValueError(f"selected_index is -> {selected_index}")
            
         #現在のフレームデータを取得
        current_frame_data: FrameData = frame_data_list_state[selected_index]
        # フレームデータを更新
        self.update_frame_data(current_frame_data, 
                               character_name, subtitle_input, reading_input, update_reading_speed_slider, 
                               selected_model_tuple_state, emotion_dropdown, motion_dropdown, 
                               image_video_input, whiteboard_image_path)
        # UIコンポーネントを更新
        return self.update_ui_elements(selected_index, frame_data_list_state)


    def update_frame_data(self, current_frame_data: FrameData,
                        character_name, subtitle_input, reading_input, update_reading_speed_slider, 
                        selected_model_tuple_state, emotion_dropdown, motion_dropdown, 
                        image_video_input, whiteboard_image_path):
        """
        フレームデータを更新する関数
        """
        # 変更フラグ
        change_flag = False

        # 字幕の変更
        if (current_frame_data.subtitle_line != subtitle_input):
            # 変更フラグをTrueにする
            change_flag = True
            # 字幕の変更
            current_frame_data.subtitle_line = subtitle_input 
            # 字幕画像の変更
            subtitle_img = self.edit_medias.generate_subtitle(
                        subtitle_input, 
                        self.generate_video.obs_subtitle_image_path, 
                        self.generate_video.preview_width, 
                        self.generate_video.preview_height
                        )
            subtitle_image_path = save_as_temp_file(subtitle_img)
            current_frame_data.subtitle_image_path=subtitle_image_path

        # 読み方の変更
        if (current_frame_data.reading_line != reading_input
                or current_frame_data.reading_speed != update_reading_speed_slider):
            # 変更フラグをTrueにする
            change_flag = True
            # 読み方の変更
            current_frame_data.reading_line = reading_input
            # 読み方の速度の変更
            current_frame_data.reading_speed = update_reading_speed_slider
            # 音声ファイルの変更
            model_name, model_id, speaker_id = selected_model_tuple_state # モデル情報の取得
            audio_file_path = self.create_subtitle_voice.generate_audio(
                    subtitle_input, reading_input, 
                    model_name, model_id, speaker_id, update_reading_speed_slider
                    ) 
            current_frame_data.audio_file = audio_file_path 

        # 感情の変更
        if (current_frame_data.emotion_shortcut != emotion_dropdown and emotion_dropdown != None):
            # 変更フラグをTrueにする
            change_flag = True
        
        # モーションの変更
        if (current_frame_data.motion_shortcut != motion_dropdown and motion_dropdown != None):
            # 変更フラグをTrueにする
            change_flag = True
        
        # 画像の変更
        if (image_video_input != None):
            # 変更フラグをTrueにする
            change_flag = True
            # 画像の変更
            current_frame_data.explanation_media_path = image_video_input
            # if image_video_input == r"Asset\Greenbak.png": #画像がない場合
            #     image_video_input = None #Noneに変換

        # プレビュー画像の変更
        if (change_flag): 
            preview_image_path = self.generate_video.generate_preview_image(
                current_frame_data.explanation_media_path, current_frame_data.subtitle_image_path, 
                )
            current_frame_data.preview_image = preview_image_path



    # def on_video_creation_complete(self, task, selected_index, frame_data_list):
    #     try:
    #         task.result()  # 例外が発生していないか確認
    #         print("動画の作成が完了しました")
    #         # UIコンポーネントを更新
    #         self.update_ui_elements(selected_index, frame_data_list)
    #     except Exception as e:
    #         print(f"動画の作成中にエラーが発生しました: {e}")


    # 動画作成ボタンがクリックされたときの処理
    def create_video(self, output_folder_input, bgm_file_input, background_video_file_input,
                           character_name, subtitle_input, reading_input, update_reading_speed_slider, 
                           selected_model_tuple_state, emotion_dropdown, motion_dropdown, 
                           image_video_input, whiteboard_image_path, 
                           selected_index, frame_data_list_state: list[FrameData]):
                           
        # result = None
        result = self.on_update_reading_click(
                                character_name, subtitle_input, reading_input, update_reading_speed_slider, 
                                selected_model_tuple_state, emotion_dropdown, motion_dropdown, 
                                image_video_input, whiteboard_image_path,  
                                selected_index, frame_data_list_state
                                )

        # output_folder_inputがなければ作成する
        if not os.path.exists(output_folder_input):
            os.makedirs(output_folder_input)
        output_file_path = os.path.join(output_folder_input, "output-" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + ".mp4")

        # 動画作成
        create_video = CreateVideo(frame_data_list_state, output_file_path, background_video_file_input)
        output_file_path = create_video.create_video_run()

        # 別スレッドで実行
        # task = asyncio.create_task(create_video.create_video_run())
        # task.add_done_callback(lambda t: print("動画の作成が完了しました"))
        # task.add_done_callback(lambda t: self.on_video_creation_complete(t, selected_index, frame_data_list))
        # await create_video.create_video_run()

        # print(f"output_file_path -> {output_file_path}")
        # print(f"result -> {result}")

        # if result is not None:
        #     (
        #         character_name, subtitle_input, reading_input, update_reading_speed_slider, 
        #         selected_model_tuple_state, test_playback_button, emotion_dropdown, motion_dropdown, 
        #         image_video_input, whiteboard_image_path, preview_images, 
        #         selected_index, frame_data_list_state
        #     ) = result

        # # print(f"result -> {result}")
        # # print(f"current_frame_data -> {current_frame_data}")

        # return (
        #     character_name, subtitle_input, reading_input, update_reading_speed_slider, 
        #     selected_model_tuple_state, None, emotion_dropdown, motion_dropdown, 
        #     None, whiteboard_image_path, None, 
        #     selected_index, frame_data_list_state, 
        #     gr.update(value=output_file_path, visible=True) 
        # ) 
    