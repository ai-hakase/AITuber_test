from PIL import Image, ImageDraw, ImageFont
from utils import *
from edit_medias import EditMedia
from create_subtitle_voice import CreateSubtitleVoice
from setup_vtuber_keys import SetupVtuberKeys

class GenerateVideo:

    def __init__(self):

        # インスタンスの生成
        self.edit_medias = EditMedia()
        self.create_subtitle_voice = CreateSubtitleVoice()
        self.setup_vtuber_keys = SetupVtuberKeys()

        # メインキャラクター
        self.main_character = None
        self.subtitle_image_path = None

        # キャラクターごとの最後に入力したモーションショットカットを保持する辞書
        self.last_motion_shortcut = {
            self.main_character: None,
            "other": None
        }

        # プレビューエリアを作成 → 動画の大きさ
        self.preview_width = 1920
        self.preview_height = 1080
        self.preview = Image.new('RGBA', (self.preview_width, self.preview_height))  # RGBAモードで作成


    # プレビュー画像を生成する関数
    def generate_preview_image(self, background_video_file_input, explanation_image_path, whiteboard_image_path, subtitle_image_path, vtuber_character_path):

        # 背景動画の最初のフレームを読み込む
        background = capture_first_frame(background_video_file_input)
        # プレビューエリアのサイズに合わせてリサイズ
        background = self.edit_medias.resize_image_aspect_ratio(background, self.preview_width, self.preview_height+100)#調整

        # 字幕画像を読み込む
        subtitle_img = Image.open(subtitle_image_path).convert("RGBA")

        # Vキャラ画像を読み込む
        vtuber_img = Image.open(vtuber_character_path).convert("RGBA")  # RGBAモードに変換

        # ホワイトボード画像を読み込む
        whiteboard_img = Image.open(whiteboard_image_path).convert("RGBA")  # RGBAモードに変換

        # 解説画像を読み込む
        explanation_img = load_image_or_video(explanation_image_path)

        # 背景画像を合成
        self.preview.paste(background, (0, 0))

        # ホワイトボード画像に解説画像を合成する
        explanation_x = (whiteboard_img.width - explanation_img.width) // 2#解説画像の位置を計算
        explanation_y = (whiteboard_img.height - explanation_img.height) // 2#解説画像の位置を計算
        whiteboard_img.paste(explanation_img, (explanation_x, explanation_y))#ホワイトボード画像に解説画像を合成
        # ホワイトボード画像を合成
        whiteboard_x = 30#ホワイトボード画像の位置を計算
        whiteboard_y = 30#ホワイトボード画像の位置を計算
        self.preview.paste(whiteboard_img, (whiteboard_x, whiteboard_y), mask=whiteboard_img)#ホワイトボード画像を合成

        # Vキャラ画像を合成
        # リサイズ後の位置を計算
        vtuber_x = self.preview_width - vtuber_img.width +10#調整
        vtuber_y = self.preview_height - vtuber_img.height -200#調整
        self.preview.paste(vtuber_img, (vtuber_x, vtuber_y), mask=vtuber_img)

        # 字幕を合成
        subtitle_x = (self.preview_width - subtitle_img.width) // 2
        subtitle_y = self.preview_height - subtitle_img.height
        self.preview.paste(subtitle_img, (subtitle_x, subtitle_y), mask=subtitle_img)

        # プレビュー画像を保存
        preview_image_path = save_as_temp_file(self.preview)

        return preview_image_path


    # 動画生成の主要な処理を行う関数
    def generate_video(self, csv_file_input, bgm_file_input, background_video_file_input, character_name_input, model_list_state, selected_model_tuple_state, reading_speed_slider, registered_words_table, emotion_shortcuts_state, actions_state):
       
        global frame_data_list # グローバル変数にすることで、関数内でもフレームデータのリストにアクセスできるようになる
        frame_data_list.clear() # フレームデータのリストをクリア

        delete_tmp_files() #tmpフォルダーの中身を全て削除する

        print(f"動画準備開始\n")

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


        # プレビュー画像の生成
        bgm_file_input = bgm_file_input
        background_video_file_input = background_video_file_input

        # 字幕画像の生成
        test_subtitle_img = self.edit_medias.generate_subtitle("subtitle_line", self.preview_width, self.preview_height)#字幕画像の生成

        # Vキャラ画像を生成
        test_vtuber_img = self.edit_medias.create_vtuber_image()

        # ホワイトボード画像を生成
        whiteboard_subtitle_height = test_subtitle_img.height // 2 +20#調整
        VTuber_subtitle_height = test_vtuber_img.width -150#調整
        whiteboard_image = self.edit_medias.create_whiteboard(self.preview_width, self.preview_height, VTuber_subtitle_height, whiteboard_subtitle_height)
        whiteboard_image_path = save_as_temp_file(whiteboard_image)

        # 解説画像(初期値：グリーンバック)を生成
        explanation_image_path = r"Asset/Greenbak.png"
        explanation_img = load_image_or_video(explanation_image_path).convert("RGBA")  # RGBAモードに変換
        # 解説画像のアスペクト比を維持しながらホワイトボード画像に合わせてリサイズ
        explanation_img = self.edit_medias.resize_image_aspect_ratio(explanation_img, whiteboard_image.width - 20, whiteboard_image.height - 20)
        # 解説画像の周りにボーダーを追加
        explanation_img = self.edit_medias.add_border(explanation_img, 10)
        explanation_image_path = save_as_temp_file(explanation_img)


        # キャラクター・セリフ情報を処理
        for character, line in character_lines:

            # 元のセリフを字幕用として変数に保持します。
            # 辞書機能で英語テキストのカタカナ翻訳を行ったセリフを読み方用として変数に保持します。
            subtitle_line, reading_line = self.create_subtitle_voice.process_line(line, registered_words_table.values)
            print(f"subtitle_line: {subtitle_line},\n reading_line: {reading_line} \n")

            # Style-Bert-VITS2のAPIを使用して、セリフのテキストの読み上げを作成読み上げ音声ファイルを生成
            audio_file = self.create_subtitle_voice.generate_audio(subtitle_line, reading_line, model_name, model_id, speaker_id)

            # キャラクター事にショートカットキーを選択
            # emotion_shortcut, motion_shortcut = self.setup_vtuber_keys.get_shortcut_key(emotion_shortcuts_state, actions_state, character, subtitle_line)
            emotion_shortcut, motion_shortcut = 'alt+n', 'alt+0'

            # 字幕画像の生成
            subtitle_img = self.edit_medias.generate_subtitle(subtitle_line, self.preview_width, self.preview_height)#字幕画像の生成
            subtitle_image_path = save_as_temp_file(subtitle_img)#テンポラリファイルに保存

            # Vキャラ画像を生成 -> クロマキー処理
            vtuber_img = self.edit_medias.create_vtuber_image()
            vtuber_img_path = save_as_temp_file(vtuber_img)

            # プレビュー画像を生成
            preview_image = self.generate_preview_image(background_video_file_input, explanation_image_path, whiteboard_image_path, subtitle_image_path, vtuber_img_path)

            # フレームデータの生成とリストへの保存
            frame_data = (subtitle_line, reading_line, audio_file, emotion_shortcut, motion_shortcut, explanation_image_path, whiteboard_image_path, subtitle_image_path, preview_image, selected_model)
            frame_data_list.append(frame_data)

        subtitle_line, reading_line, audio_file, emotion_shortcut, motion_shortcut, explanation_image_path, whiteboard_image_path, subtitle_image_path, preview_image, selected_model = frame_data_list[0]
        preview_images = [frame_data[8] for frame_data in frame_data_list]

        print(f"動画準備終了\n")

        # frame_data_listの中身をわかりやすくそれぞれに名前をつけて表示
        print(f"subtitle_line: {subtitle_line},\n reading_line: {reading_line},\n audio_file: {audio_file},\n emotion_shortcut: {emotion_shortcut},\n motion_shortcut: {motion_shortcut},\n explanation_image_path: {explanation_image_path},\n whiteboard_image_path: {whiteboard_image_path},\n subtitle_image_path: {subtitle_image_path},\n preview_images: {preview_images},\n selected_model: {selected_model}")

        return subtitle_line, reading_line, audio_file, emotion_shortcut, motion_shortcut, explanation_image_path, whiteboard_image_path, subtitle_image_path, preview_images, selected_model

# 出力例
#  subtitle_line: 今回は、VTube Studioを使ってAI Tuberを作る方法ということで,
#  reading_line: 今回は、ブイチューブ スタジオを使ってAI Tuberを作る方法ということで,
#  audio_file: C:\Users\okozk\Test\Gradio\tmp\tmpr5k7jr4u.wav,
#  emotion_shortcut: alt+n,
#  motion_shortcut: alt+0,
#  explanation_image_path: C:\Users\okozk\Test\Gradio\tmp\tmp3hrn9cgo.png,
#  whiteboard_image_path: C:\Users\okozk\Test\Gradio\tmp\tmptgciqmxh.png,
#  subtitle_image_path: C:\Users\okozk\Test\Gradio\tmp\tmpvm6adeii.png,
#  preview_images: ['C:\\Users\\okozk\\Test\\Gradio\\tmp\\tmpj7nixtsm.png', 'C:\\Users\\okozk\\Test\\Gradio\\tmp\\tmpabnne5up.png'],
#  selected_model: ['AI-Hakase-v1', '1', 0]
