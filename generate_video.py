from PIL import Image

from utils import save_as_temp_file, delete_tmp_files
from edit_medias import EditMedia
from vts_hotkey_trigger import VTubeStudioHotkeyTrigger
from create_subtitle_voice import CreateSubtitleVoice
from setup_vtuber_keys import SetupVtuberKeys
from render import FrameData
from katakana_converter import KatakanaConverter
from constants import TALK_CHARACTER


class GenerateVideo:

    def __init__(self):
        self.frame_data_list:list[FrameData] = []

        # インスタンスの生成
        self.edit_medias = EditMedia()
        self.create_subtitle_voice = CreateSubtitleVoice()
        self.setup_vtuber_keys = SetupVtuberKeys()
        self.vts_hotkey_trigger = VTubeStudioHotkeyTrigger()
        self.katakana_converter = KatakanaConverter()
        # self.handle_frame_event = HandleFrameEvent()

        # メインキャラクター
        self.main_character = None


        # キャラクターごとの最後に入力したモーションショットカットを保持する辞書
        self.last_motion_shortcut = {
            self.main_character: None,
            "other": None
        }

        self.default_explanation_media_path = r"Asset/Greenbak.png"

        # OBSの背景・Vキャラ・Vキャラ画像を取得
        self.obs_background_image = None
        self.obs_vtuber_image = None
        self.obs_v_cat_image = None
        self.obs_whiteboard_image = None
        self.obs_subtitle_image = None
        self.obs_whiteboard_image_path = None
        self.obs_subtitle_image_path = None

        # プレビューエリアを作成 → 動画の大きさ
        self.preview_width = 1920
        self.preview_height = 1080
        # self.preview = Image.new('RGBA', (self.preview_width, self.preview_height))  # RGBAモードで作成

        self.preview_green = Image.new('RGB', (self.preview_width, self.preview_height), (0, 255, 0))  # グリーンスクリーン



        self.scene_name = "AI_Tuber_test"
        # self.vtuber_image = None
        # self.v_cat_image = None


    async def request_obs_screenshot_image(self, source_name):
        """
        OBSのスクリーンショットを取得する関数
        """
        return await self.edit_medias.create_obs_screenshot_image(source_name)



    def generate_preview_image(self, explanation_media_path, subtitle_image_path):
        """
        プレビュー画像を生成する関数
        """
        # プレビュー画像を作成
        preview = Image.new('RGBA', (self.preview_width, self.preview_height), (0, 0, 0, 0))  # 透明背景

        # 背景画像を合成
        resized_background_image = self.edit_medias.resize_image_aspect_ratio(self.obs_background_image, self.preview_width, self.preview_height+1)#調整
        preview.paste(resized_background_image, (0, 0))

        # ホワイトボード画像と解説画像を合成
        whiteboard_and_explanation_img = self.edit_medias.generate_composite_media(self.obs_whiteboard_image_path, explanation_media_path)  # 解説画像を合成
        preview.paste(whiteboard_and_explanation_img, (30, 30), mask=whiteboard_and_explanation_img)
        save_as_temp_file(whiteboard_and_explanation_img)

        # Vキャラ画像を合成(vtuber)
        preview.paste(self.obs_vtuber_image, (0, 0), mask=self.obs_vtuber_image)

        # 字幕を合成
        subtitle_image = Image.open(subtitle_image_path).convert("RGBA")#字幕画像を読み込む
        preview.paste(subtitle_image, (0, 0), mask=subtitle_image)

        # Vキャラ画像を合成(v_cat)
        preview.paste(self.obs_v_cat_image, (0, 0), mask=self.obs_v_cat_image)

        # previewを小さくリサイズ
        preview = self.edit_medias.resize_image_aspect_ratio(preview, self.preview_width // 3, self.preview_height // 3)

        # プレビュー画像を保存
        preview_image_path = save_as_temp_file(preview)

        return preview_image_path


    def generate_video_frames(self, 
                                csv_file_input, 
                                character_name_input, reading_speed_slider, voice_synthesis_model_dropdown, 
                                sub_character_name_input, sub_reading_speed_slider, sub_voice_synthesis_model_dropdown,
                                pitch_up_strength_slider, sub_pitch_up_strength_slider,
                                voice_style_dropdown, voice_style_strength_slider, sub_voice_style_dropdown, sub_voice_style_strength_slider,
                                model_list_state, 
                                registered_words_table, emotion_shortcuts_state, actions_state):
        """
        動画生成の主要な処理を行う関数
        """
        from handle_frame_event import HandleFrameEvent
        handle_frame_event = HandleFrameEvent(self)

        self.frame_data_list.clear() # フレームデータのリストをクリア

        delete_tmp_files() #tmpフォルダーの中身を全て削除する

        self.main_character = character_name_input#メインキャラクターを設定

        global TALK_CHARACTER
        TALK_CHARACTER = character_name_input

        # CSVファイルからキャラクター・セリフ情報を取得
        character_lines = self.create_subtitle_voice.load_csv_data(csv_file_input)#キャラクター・セリフ情報を取得

        # # OBSの背景・Vキャラ・Vキャラ画像を取得
        self.obs_background_image = self.edit_medias.create_obs_screenshot_image("background")
        self.obs_vtuber_image = self.edit_medias.create_obs_screenshot_image("VTuber") 
        self.obs_v_cat_image = self.edit_medias.create_obs_screenshot_image("V_cat")

        # ホワイドボード画像の生成
        self.obs_whiteboard_image = self.edit_medias.create_obs_screenshot_image("ホワイドボード") 
        # 字幕画像の生成
        self.obs_subtitle_image = self.edit_medias.create_obs_screenshot_image("字幕_preview")
        # ホワイドボード画像と字幕画像を保存
        self.obs_whiteboard_image_path = save_as_temp_file(self.obs_whiteboard_image)
        self.obs_subtitle_image_path = save_as_temp_file(self.obs_subtitle_image)


        # キャラクター・セリフ情報を処理
        for character, line in character_lines:

            if character == self.main_character:
                voice_synthesis_model = voice_synthesis_model_dropdown
                voice_style = voice_style_dropdown
                voice_style_strength = voice_style_strength_slider
                pitch_up_strength = pitch_up_strength_slider
                reading_speed = reading_speed_slider
                
            elif character == sub_character_name_input:
                voice_synthesis_model = sub_voice_synthesis_model_dropdown
                voice_style = sub_voice_style_dropdown
                voice_style_strength = sub_voice_style_strength_slider
                pitch_up_strength = sub_pitch_up_strength_slider
                reading_speed = sub_reading_speed_slider
            
            # 元のセリフを字幕用として変数に保持します。
            # 辞書機能で英語テキストのカタカナ翻訳を行ったセリフを読み方用として変数に保持します。
            subtitle_line, reading_line = self.create_subtitle_voice.process_line(line)
    
            # 選択された音声合成モデルの名前を取得
            selected_model_tuple = self.create_subtitle_voice.get_selected_mode_id(voice_synthesis_model, model_list_state)

            # Style-Bert-VITS2のAPIを使用して、セリフのテキストの読み上げを作成読み上げ音声ファイルを生成
            audio_file = self.create_subtitle_voice.generate_audio(
                                            subtitle_line, reading_line, 
                                            selected_model_tuple, reading_speed, voice_style, voice_style_strength,
                                            pitch_up_strength)
                
            # キャラクター事にショートカットキーを選択
            emotion_shortcut, motion_shortcut = self.setup_vtuber_keys.get_shortcut_key(emotion_shortcuts_state, actions_state, character, subtitle_line)

            # 画面の文字大きさの字幕画像の生成->グリーンバック＋字幕画像
            subtitle_image = self.edit_medias.generate_subtitle(subtitle_line, self.obs_subtitle_image_path, self.preview_width, self.preview_height)#字幕画像の生成
            subtitle_image_path = save_as_temp_file(subtitle_image)

            # プレビュー画像を生成
            preview_image_path = self.generate_preview_image(self.default_explanation_media_path, subtitle_image_path)

            # フレームデータの生成とリストへの保存
            frame_data = FrameData(
                character_name=character,
                subtitle_line=subtitle_line,
                reading_line=reading_line,
                reading_speed=reading_speed_slider,
                selected_model=selected_model_tuple,
                voice_style=voice_style,
                voice_style_strength=voice_style_strength,
                pitch_up_strength=pitch_up_strength,
                audio_file=audio_file,
                emotion_shortcut=emotion_shortcut,
                motion_shortcut=motion_shortcut,
                explanation_media_path=self.default_explanation_media_path,
                # explanation_image_path=self.default_explanation_image_path,
                whiteboard_image_path=self.obs_whiteboard_image_path,
                subtitle_image_path=subtitle_image_path,
                preview_image=preview_image_path,
            )
            self.frame_data_list.append(frame_data)

        # self.frame_data_list = frame_data_list  # 新しいリストで置き換える
        print(f"動画の準備が完了しました。フレームデータのリストの長さ: {len(self.frame_data_list)}")

        return handle_frame_event.update_ui_elements(selected_index = 0, frame_data_list = self.frame_data_list)
    