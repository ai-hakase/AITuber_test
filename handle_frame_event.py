import gradio as gr

import os
from datetime import datetime
import difflib

from utils import save_as_temp_file
from create_subtitle_voice import CreateSubtitleVoice
from create_video import CreateVideo
from render import FrameData
from edit_medias import EditMedia
from handle_gallery_event import HandleGalleryEvent
from katakana_converter import KatakanaConverter
from constants import TALK_CHARACTER



class HandleFrameEvent:
    # def __init__(self):
    def __init__(self, generate_video):
        """
        コンストラクタ
        Args:
            generate_video (GenerateVideo): 動画生成クラス
        """
        self.generate_video = generate_video
        self.create_subtitle_voice = CreateSubtitleVoice()
        self.edit_medias = EditMedia()
        self.handle_gallery_event = HandleGalleryEvent()
        self.katakana_converter = KatakanaConverter()


    def setup_frame_data_list(self):
        """
        フレームデータリストをリセットする関数
        """
        # self.generate_video.frame_data_list = []
        return gr.update(interactive=True), gr.update(interactive=True) #False


    # フレームデータから各要素を抽出してUIに表示する関数
    def update_ui_elements(self, selected_index, frame_data_list: list[FrameData]):
        """
        フレームデータから各要素を抽出してUIに表示する関数

        Args:
            selected_index (int): ギャラリーのインデックス
            frame_data_list (list[FrameData]): フレームデータリスト
        """
        # 各要素を抽出
        frame_data: FrameData = frame_data_list[selected_index]
        character_name = frame_data.character_name
        subtitle_input = frame_data.subtitle_line
        reading_input = frame_data.reading_line
        voice_model_dropdown = frame_data.selected_model[0]
        voice_style_input = frame_data.voice_style
        voice_style_strength_slider = frame_data.voice_style_strength
        pitch_up_strength_slider = frame_data.pitch_up_strength
        reading_speed_slider = frame_data.reading_speed
        test_playback_button = frame_data.audio_file
        emotion_dropdown = frame_data.emotion_shortcut
        motion_dropdown = frame_data.motion_shortcut
        image_video_input = None
        # image_video_input = explanation_path_list[selected_index]
        whiteboard_image = frame_data.whiteboard_image_path
        preview_images = [frame_data.preview_image for frame_data in frame_data_list]

        return (
            character_name, subtitle_input, reading_input, reading_speed_slider, 
            voice_style_input, voice_style_strength_slider, 
            pitch_up_strength_slider,
            voice_model_dropdown,test_playback_button, emotion_dropdown, motion_dropdown, 
            image_video_input, whiteboard_image, preview_images,
            selected_index, frame_data_list
        )


    def compare_subtitle_reading(self, subtitle_line, reading_line):
        """
        subtitle_line, reading_lineを比較して変更がある箇所をカンマ区切りで一行ずつ出力する関数

        Args:
            subtitle_line (str): 字幕のテキスト
            reading_line (str): 読み方のテキスト
        """
        diff = difflib.unified_diff(subtitle_line.splitlines(), reading_line.splitlines(), lineterminator="\n")
        diff_list = list(diff)
        diff_list = [line for line in diff_list if line.startswith("-") or line.startswith("+")]
        diff_list = [line.split(" ") for line in diff_list]
        diff_list = [line[1] for line in diff_list]
        diff_list = [line.strip() for line in diff_list]
        diff_list = [line for line in diff_list if line]
        return "\n".join(diff_list)
    

    def update_subtitle_reading(self,   
                                character_name, subtitle_input, reading_input, update_reading_speed_slider, 
                                voice_style_input, update_voice_style_strength_slider,
                                update_pitch_up_strength_slider,
                                selected_model_tuple_state, emotion_dropdown, motion_dropdown, 
                                image_video_input, whiteboard_image_path, 
                                model_list_state, voice_model_dropdown, 
                                selected_index, frame_data_list_state: list[FrameData]):

        """
        字幕をもとに、読み方を自動変更
        """
        # 読み方を自動変更
        self.katakana_converter.split_words()
        subtitle_line, reading_line = self.create_subtitle_voice.process_line(subtitle_input)
        
        current_frame_data: FrameData = frame_data_list_state[selected_index] #現在のフレームデータを取得

        # フレームデータを更新
        self.update_frame_data(current_frame_data, 
                               character_name, subtitle_line, reading_line, update_reading_speed_slider, 
                               voice_style_input, update_voice_style_strength_slider,
                               update_pitch_up_strength_slider,
                               selected_model_tuple_state, emotion_dropdown, motion_dropdown, 
                               model_list_state, voice_model_dropdown, 
                               image_video_input, whiteboard_image_path)

        # UIコンポーネントを更新
        return self.update_ui_elements(selected_index, frame_data_list_state)


    def handle_update_word_reading_button(self, 
                                          word_input, word_reading_input,
                                          character_name, subtitle_input, reading_input, update_reading_speed_slider, 
                                          voice_style_input, update_voice_style_strength_slider,
                                          update_pitch_up_strength_slider,
                                          selected_model_tuple_state, emotion_dropdown, motion_dropdown, 
                                          image_video_input, whiteboard_image_path, 
                                          model_list_state, voice_model_dropdown, 
                                          selected_index, frame_data_list_state: list[FrameData]):
        """
        単語を辞書に登録->単語を変更->音声ファイルを変更する関数
        """
        # 単語を辞書に登録
        self.katakana_converter.add_word_reading(word_input, word_reading_input)
        self.katakana_converter.split_words()
        new_registered_words_table = self.handle_gallery_event.load_dics()

        # フレームデータリストの各フレームデータを順に処理
        # print(f"frame_data_list_state: {frame_data_list_state}")
        for frame_data in frame_data_list_state:

            # word_inputがフレームデータのsubtitle_lineに含まれている場合
            if word_input in frame_data.subtitle_line:
                # 読み方を自動変更
                reading_line = self.katakana_converter.translate_to_katakana(reading_input)
            
                # 読み方の変更
                frame_data.reading_line = reading_line

                # 音声ファイルの変更
                audio_file_path = self.create_subtitle_voice.generate_audio(
                        frame_data.subtitle_line, reading_line, 
                        frame_data.selected_model, frame_data.reading_speed, 
                        frame_data.voice_style, frame_data.voice_style_strength,
                        frame_data.pitch_up_strength
                        ) 

                # 音声ファイルの変更
                frame_data.audio_file = audio_file_path 

        # UIコンポーネントを更新
        result =  self.update_ui_elements(selected_index, frame_data_list_state)

        # フレームデータを更新
        if result is not None:
            (
                character_name, subtitle_input, reading_input, update_reading_speed_slider, 
                voice_style_input, update_voice_style_strength_slider,
                update_pitch_up_strength_slider,
                voice_model_dropdown, test_playback_button, emotion_dropdown, motion_dropdown, 
                image_video_input, whiteboard_image_path, preview_images, 
                selected_index, frame_data_list_state
            ) = result

        # 動画ファイルパスを返す
        return (
            new_registered_words_table,
            character_name, subtitle_input, reading_input, update_reading_speed_slider, 
            voice_style_input, update_voice_style_strength_slider,
            update_pitch_up_strength_slider,
            voice_model_dropdown, test_playback_button, emotion_dropdown, motion_dropdown, 
            image_video_input, whiteboard_image_path, preview_images, 
            selected_index, frame_data_list_state
        ) 


    def handle_gallery_click(self, evt: gr.SelectData, 
                character_name,subtitle_input, reading_input, update_reading_speed_slider,
                voice_style_input, update_voice_style_strength_slider,
                update_pitch_up_strength_slider,
                selected_model_tuple_state, emotion_dropdown, motion_dropdown, 
                image_video_input, whiteboard_image_path, 
                model_list_state, voice_model_dropdown,
                selected_index, frame_data_list_state: list[FrameData]):
        """
        ギャラリーのインデックスが選択されたときに呼び出される関数
        """
        new_selected_index = evt.index  # ギャラリーのインデックスを取得 -> kwargs のセレクトインデックスを更新
        current_frame_data: FrameData = frame_data_list_state[selected_index] #現在のフレームデータを取得
        
        # フレームデータを更新
        self.update_frame_data(current_frame_data, 
                               character_name, subtitle_input, reading_input, update_reading_speed_slider, 
                               voice_style_input, update_voice_style_strength_slider,
                               update_pitch_up_strength_slider,
                               selected_model_tuple_state, emotion_dropdown, motion_dropdown, 
                               model_list_state, voice_model_dropdown, 
                               image_video_input, whiteboard_image_path)
        
        # UIコンポーネントを更新
        return self.update_ui_elements(new_selected_index, frame_data_list_state)


    def on_update_reading_click(self, 
                    character_name, subtitle_input, reading_input, update_reading_speed_slider, 
                    voice_style_input, update_voice_style_strength_slider,
                    update_pitch_up_strength_slider,
                    selected_model_tuple_state, emotion_dropdown, motion_dropdown, 
                    image_video_input, whiteboard_image_path, 
                    model_list_state, voice_model_dropdown,
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
                               voice_style_input, update_voice_style_strength_slider,
                               update_pitch_up_strength_slider,
                               selected_model_tuple_state, emotion_dropdown, motion_dropdown, 
                               model_list_state, voice_model_dropdown, 
                               image_video_input, whiteboard_image_path)
        # UIコンポーネントを更新
        return self.update_ui_elements(selected_index, frame_data_list_state)


    def update_frame_data(self, current_frame_data: FrameData,
                        character_name, subtitle_input, reading_input, update_reading_speed_slider, 
                        voice_style_input, update_voice_style_strength_slider,
                        update_pitch_up_strength_slider,
                        selected_model_tuple_state, emotion_dropdown, motion_dropdown, 
                        model_list_state, voice_model_dropdown, 
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
        if (
            current_frame_data.reading_line != reading_input
                or current_frame_data.reading_speed != update_reading_speed_slider
                or current_frame_data.selected_model[0] != voice_model_dropdown
                or current_frame_data.pitch_up_strength != update_pitch_up_strength_slider
               ):
            # 変更フラグをTrueにする
            change_flag = True

            # 読み方の変更
            current_frame_data.reading_line = reading_input

            # 読み方の速度の変更
            current_frame_data.reading_speed = update_reading_speed_slider

            # 音声スタイルの変更
            current_frame_data.voice_style = voice_style_input

            # 音声スタイル強度の変更
            current_frame_data.voice_style_strength = update_voice_style_strength_slider

            # ピッチアップ強度の変更
            current_frame_data.pitch_up_strength = update_pitch_up_strength_slider

            # 選択されたモデルの名前を取得
            selected_model_tuple = self.create_subtitle_voice.get_selected_mode_id(voice_model_dropdown, model_list_state)
            current_frame_data.selected_model = selected_model_tuple

            # 音声ファイルの変更
            audio_file_path = self.create_subtitle_voice.generate_audio(
                                                            subtitle_input, reading_input, 
                                                            selected_model_tuple, update_reading_speed_slider, 
                                                            voice_style_input, update_voice_style_strength_slider,
                                                            update_pitch_up_strength_slider
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


    async def create_video(self, output_folder_input,
                            character_name, subtitle_input, reading_input, update_reading_speed_slider, 
                            voice_style_input, update_voice_style_strength_slider,
                            update_pitch_up_strength_slider,
                            selected_model_tuple_state, emotion_dropdown, motion_dropdown, 
                            image_video_input, whiteboard_image_path, 
                            model_list_state, voice_model_dropdown,
                            selected_index, frame_data_list_state: list[FrameData]):
        """
        動画作成ボタンがクリックされたときの処理
        """
        result = None
        result = self.on_update_reading_click(
                                character_name, subtitle_input, reading_input, update_reading_speed_slider, 
                                voice_style_input, update_voice_style_strength_slider,
                                update_pitch_up_strength_slider,
                                selected_model_tuple_state, emotion_dropdown, motion_dropdown, 
                                image_video_input, whiteboard_image_path, 
                                model_list_state, voice_model_dropdown,
                                selected_index, frame_data_list_state
                                )

        # output_folder_inputがなければ作成する
        if not os.path.exists(output_folder_input):
            os.makedirs(output_folder_input)
        output_file_path = os.path.join(output_folder_input, "output-" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + ".mp4")


        # 動画作成クラスを作成
        create_video = CreateVideo(frame_data_list_state, output_file_path)

        # 動画作成
        output_file_path = await create_video.create_video_run()

        # フレームデータを更新
        if result is not None:
            (
                character_name, subtitle_input, reading_input, update_reading_speed_slider, 
                voice_style_input, update_voice_style_strength_slider,
                update_pitch_up_strength_slider,
                voice_model_dropdown, test_playback_button, emotion_dropdown, motion_dropdown, 
                image_video_input, whiteboard_image_path, preview_images, 
                selected_index, frame_data_list_state
            ) = result

        # 動画ファイルパスを返す
        return (
            character_name, subtitle_input, reading_input, update_reading_speed_slider, 
            voice_style_input, update_voice_style_strength_slider,
            update_pitch_up_strength_slider,
            voice_model_dropdown, test_playback_button, emotion_dropdown, motion_dropdown, 
            image_video_input, whiteboard_image_path, preview_images, 
            selected_index, frame_data_list_state, 
            gr.update(value=output_file_path, visible=True) 
        ) 
    