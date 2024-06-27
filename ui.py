import signal
import gradio as gr
import json

from vtuber_camera import VTuberCamera

from utils import DEFAULT_SETTINGS_FOLDER, DEFAULT_SETTING_FILE
from generate_video import GenerateVideo
from create_subtitle_voice import CreateSubtitleVoice
from handle_gallery_event import HandleGalleryEvent
from handle_frame_event import HandleFrameEvent
from vts_hotkey_trigger import VTubeStudioHotkeyTrigger

class UI:
    def __init__(self):        
        self.vtuber_camera = VTuberCamera()
        self.generate_video = GenerateVideo()
        # self.edit_medias = EditMedia()
        self.create_subtitle_voice = CreateSubtitleVoice()
        # self.vts_hotkey_trigger = VTubeStudioHotkeyTrigger()
        self.handle_gallery_event = HandleGalleryEvent()
        # self.handle_frame_event = HandleFrameEvent()  # インスタンスを渡す
        self.handle_frame_event = HandleFrameEvent(self.generate_video)  # インスタンスを渡す

        # 設定ファイルの読み込み
        with open(DEFAULT_SETTING_FILE, "r", encoding="utf-8") as f:
            settings = json.load(f)
        
        self.character_name = settings["character_name"]
        self.voice_synthesis_model = settings["voice_synthesis_model"]
        self.voice_style = settings["voice_style"]
        self.voice_style_strength = settings["voice_style_strength"]
        self.pitch_up_strength = settings["pitch_up_strength"]
        self.reading_speed = settings["reading_speed"]

        self.sub_character_name = settings["sub_character_name"]
        self.sub_voice_synthesis_model = settings["sub_voice_synthesis_model"]
        self.sub_voice_style = settings["sub_voice_style"]
        self.sub_voice_style_strength = settings["sub_voice_style_strength"]
        self.sub_pitch_up_strength = settings["sub_pitch_up_strength"]
        self.sub_reading_speed = settings["sub_reading_speed"]

        self.output_folder = settings["output_folder"]
        self.bgm_file = settings["bgm_file"]
        self.background_video_file = settings["background_video_file"]
        self.emotion_shortcuts = settings["emotion_shortcuts"]
        self.actions = settings["actions"]
        self.dics = settings["dics"]

        # プレビュー画像の幅と高さ
        self.preview_width, self.preview_height = 1920, 1080
        # self.hotkeys_data = None
        
        signal.signal(signal.SIGINT, self.vtuber_camera.stop) # ターミナルでの Ctrl+C で終了するための処理


    # Gradioアプリケーションの構築
    def create_ui(self):
        with gr.Blocks(theme=gr.themes.Soft()) as demo:

            gr.Markdown("# AI Tuber Test Program")# タイトル

            # 一時的な出力を受け取るための隠しコンポーネント
            selected_model_tuple_state = gr.State()# 選択されたモデルのタプルを保持するための変数
            sub_selected_model_tuple_state = gr.State()# 選択されたモデルのタプルを保持するための変数
            emotion_shortcuts_state = gr.State(self.emotion_shortcuts)
            actions_state = gr.State(self.actions)
            selected_index = gr.State(0)
            whiteboard_image_path = gr.File(label="", visible=False)
            subtitle_image_path = gr.File(label="", visible=False)
            # hidden_output = gr.JSON(visible=False)
            frame_data_list_state = gr.State()
            # frame_data_list_state = gr.State(self.generate_video.frame_data_list)

            with gr.Row():

                with gr.Column(scale=1):
                    csv_file_input = gr.File(label="CSVファイル", file_types=['text'], value="test\\AItuber_test.csv")
                    # bgm_file_input = gr.Audio(label="BGMファイル", value=self.bgm_file, interactive=True)
                    # background_video_file_input = gr.Video(label="背景動画ファイル", value=self.background_video_file, interactive=True)

                    with gr.Row():
                        with gr.Column(scale=3):
                            generate_video_button = gr.Button("感情分析・動画準備開始\n（英語テキスト翻訳 + 翻訳後のテキストで音声合成）", size="lg", interactive=True)
                        # create_video_button = gr.Button("動画生成開始", size="lg", interactive=False)

                    # 動画準備
                    # 変数をコンソールに表示するボタン
                    # print_variables_button = gr.Button("変数をコンソールに表示")

                with gr.Column(scale=2):
                    with gr.Tab("読み上げ設定"):
                        with gr.Row():
                            model_list, model_names = self.create_subtitle_voice.fetch_voice_synthesis_models()
                            model_list_state = gr.State(model_list)  # モデル情報のタプルを保持
                            with gr.Column(scale=1):
                                # mainキャラ
                                character_name_input = gr.Textbox(label="メインキャラクター名", value=self.character_name, interactive=True)
                                voice_synthesis_model_dropdown = gr.Dropdown(model_names, label="音声合成モデル", value=self.voice_synthesis_model)
                                voice_style_dropdown = gr.Textbox(label="音声スタイル", value=self.voice_style)
                                voice_style_strength_slider = gr.Slider(0, 10, value=self.voice_style_strength, step=0.1, label="音声スタイル強度", interactive=True)
                                pitch_up_strength_slider = gr.Slider(-1.0, 1.0 , value=self.pitch_up_strength, step=0.1, label="ピッチ調整", interactive=True)
                                reading_speed_slider = gr.Slider(0.5, 2.0, value=self.reading_speed, step=0.01, label="読み上げ速度", interactive=True)
                            with gr.Column(scale=1):
                                # subキャラ
                                sub_character_name_input = gr.Textbox(label="サブキャラクター名", value=self.sub_character_name, interactive=True)
                                sub_voice_synthesis_model_dropdown = gr.Dropdown(model_names, label="音声合成モデル", value=self.sub_voice_synthesis_model, interactive=True)
                                sub_voice_style_dropdown = gr.Textbox(label="音声スタイル", value=self.sub_voice_style)
                                sub_voice_style_strength_slider = gr.Slider(0, 10, value=self.sub_voice_style_strength, step=0.1, label="音声スタイル強度", interactive=True)
                                sub_pitch_up_strength_slider = gr.Slider(-1.0, 1.0 , value=self.sub_pitch_up_strength, step=0.1, label="ピッチ調整", interactive=True)
                                sub_reading_speed_slider = gr.Slider(0.5, 2.0, value=self.sub_reading_speed, step=0.01, label="読み上げ速度", interactive=True)


                    with gr.Tab("読み方一覧"):
                        with gr.Row():
                            registered_words_table = gr.Dataframe(
                                headers=["単語/文章", "読み方"],
                                datatype=["str", "str"],
                                col_count=(2, "fixed"),
                                row_count=20,
                                scale=4,
                                type="array",  # ここを確認
                                # value=[[word, reading] for word, reading in self.dics.items()]
                            )
                            update_dics_button = gr.Button("更新", scale=1)

                        # 読み方を登録するボタンを追加
                        with gr.Accordion("読み方を一括登録", open=False):
                            with gr.Row():
                                with gr.Column(scale=3):
                                    register_reading_input = gr.Textbox(label="読み方を一括登録（カンマ、スペース、コロン、ピリオド などで区切る）", lines=12, max_lines=12, interactive=True, scale=3)
                                register_reading_button = gr.Button("一括登録", scale=1)

                    # hotkeys = await self.handle_gallery_event.load_hotkeys()
                    # hotkeys_data = [[hotkey['name'], hotkey['file'], hotkey['hotkeyID']] for hotkey in hotkeys]

                    with gr.Tab("VTSホットキー一覧"):
                        
                        hotkeys_data = gr.Dataframe(
                            headers=["ホットキー名", "ファイルパス","hotkeyID"],
                            scale=1,
                            col_count=(3, "fixed"),
                            type="array",
                            # value= [[hotkey['name'], hotkey['file'], hotkey['hotkeyID']] for hotkey in hotkeys],
                            # value=self.hotkeys_data,
                            interactive=False
                        )

                    # ショートカット設定
                    with gr.Tab("ショートカット設定"):

                        with gr.Row():
                            with gr.Column(scale=4):
                                emotion_shortcuts_input = gr.Dataframe(
                                    headers=["Emotion", "Shortcut"],
                                    col_count=(2, "fixed"),
                                    row_count=8,
                                    type="array",
                                    # value=[[emotion, shortcut] for emotion, shortcut in self.emotion_shortcuts.items()],
                                    interactive=True
                                )
                                actions_input = gr.Dataframe(
                                    headers=["Action", "Shortcut"],
                                    datatype=["str", "str"],
                                    col_count=(2, "fixed"),
                                    row_count=4,
                                    type="array",
                                    interactive=True
                                )
                            update_shortcuts_button = gr.Button("更新", scale=1)

                    # タプルを表示する
                    with gr.Tab("再生用オーディオデバイス"):
                        audio_devices = gr.Dataframe(
                            headers=["デバイス番号", "デバイス名"],
                            scale=1,
                            col_count=(2, "fixed"),
                            type="array",
                            value=[],
                            interactive=False
                        )

                    with gr.Tab("保存先・設定ファイル"):
                        # 動画保存先
                        output_folder_input = gr.Textbox(label="動画保存先", value=self.output_folder)
                        change_output_folder_button = gr.Button("保存先変更")
                        # 設定ファイル読み込み
                        settings_folder_display = gr.Textbox(label="設定フォルダ", value=DEFAULT_SETTINGS_FOLDER, interactive=True)
                        settings_file_path_input = gr.Textbox(label="読み込み対象の設定ファイルパス", value=DEFAULT_SETTING_FILE, interactive=True)
                        load_settings_button = gr.Button("設定ファイル読み込み")
                        with gr.Row():
                            new_settings_name_input = gr.Textbox(label="新規設定ファイル名")
                            save_new_settings_button = gr.Button("新規設定ファイル保存")

            # generate_video_button = gr.Button("感情分析・動画準備開始\n（英語テキスト翻訳 + 翻訳後のテキストで音声合成）", size="lg", interactive=True)

            with gr.Row():
                    
                with gr.Column():
                    with gr.Tab("テキスト・画像・動画編集"):
                        with gr.Row():
                            # 音声合成、セリフ、字幕・読み方を一括変更＋辞書登録の設定
                            with gr.Column(scale=3):

                                # 音声合成の設定
                                with gr.Accordion("音声合成の設定", open=False):
                                    with gr.Row():
                                        character_name = gr.Textbox(label="キャラクター名", interactive=True)
                                        voice_model_dropdown = gr.Dropdown(model_names, label="音声合成モデル")
                                    voice_style_input = gr.Textbox(label="音声スタイル")
                                    update_voice_style_strength_slider = gr.Slider(0, 10, step=0.1, label="音声スタイル強度", interactive=True)
                                    update_pitch_up_strength_slider = gr.Slider(-1.0, 1.0, step=0.1, label="ピッチ調整", interactive=True)
                                    update_reading_speed_slider = gr.Slider(0.5, 2.0, step=0.01, label="読み上げ速度")

                                # セリフの設定
                                with gr.Accordion("セリフの設定", open=False):
                                    subtitle_input = gr.Textbox(label="セリフ（字幕用）", lines=2)
                                    reading_input = gr.Textbox(label="セリフ（読み方）", lines=2)
                                    update_subtitle_reading_button = gr.Button("字幕をもとに、読み方を自動変更",scale=1)

                                # 字幕・読み方を一括変更＋辞書登録
                                with gr.Accordion("字幕・読み方を一括変更＋辞書登録", open=False):
                                    word_input = gr.Textbox(label="単語/文章", lines=1)
                                    word_reading_input = gr.Textbox(label="読み方", lines=1)
                                    update_word_reading_button = gr.Button("一括変更",scale=1)

                            with gr.Row():
                                update_reading_button = gr.Button("変更",scale=1)
                        with gr.Accordion("画像/動画選択", open=True):
                            image_video_input = gr.File(label="画像/動画選択", file_types=["image", "video"], interactive=True, height=400)
                            with gr.Row():
                                preview_image_output = gr.Image(
                                    label="画像プレビュー", 
                                    elem_id="image_preview_output", 
                                    interactive=True, 
                                    visible=False, 
                                    scale=3, 
                                    height=400
                                    )
                                # preview_image_output = gr.ImageEditor(label="画像プレビュー", elem_id="image_preview_output", interactive=True, visible=False, scale=3, height=400)
                                preview_video_output = gr.Video(
                                    label="動画プレビュー", 
                                    elem_id="video_preview_output", 
                                    interactive=True, 
                                    visible=False, 
                                    scale=3, 
                                    height=400
                                    )
                                # delete_image_video_button = gr.Button("削除", visible=False, scale=1)
                                
                    with gr.Tab("Vキャラ・モーション設定"):
                    # with gr.Tab("Vキャラ・モーション設定"):

                        # character_position_slider = gr.Slider(minimum=0, maximum=100, step=1, label="キャラクター位置")
                        # character_size_slider = gr.Slider(minimum=50, maximum=200, step=1, label="キャラクターサイズ")
                        emotion_dropdown = gr.Dropdown(label="表情選択")#, choices=["neutral", "happy", "sad", "angry"])
                        motion_dropdown = gr.Dropdown(label="モーション選択")#, choices=["idle", "nod", "shake", "point"])

                with gr.Column(scale=1):
                    test_playback_button = gr.Audio(type="filepath", label="テスト再生")
                    preview_images = gr.Gallery(label="画像/動画フレーム一覧", elem_id="frame_gallery")

                    # with gr.Tab("画像・動画編集"):
                    #     with gr.Row():
                    #         update_image_video_button = gr.Button("変更", scale=2)
                        # preview_image_output = gr.Image(label="画像プレビュー", elem_id="image_preview_output", interactive=True)
                        # preview_video_output = gr.Video(label="動画プレビュー", elem_id="video_preview_output", interactive=True)


                    # with gr.Accordion("字幕・読み方を一括変更＋辞書登録", open=False):
                    #     word_input = gr.Textbox(label="単語/文章", lines=1)
                    #     word_reading_input = gr.Textbox(label="読み方", lines=1)
                    #     update_word_reading_button = gr.Button("一括変更",scale=1)
                        # with gr.Row():
                        #     with gr.Column(scale=3):
                        #         vtuber_character_output = gr.Interface(
                        #         fn=self.vtuber_camera.get_frame,
                        #         inputs=[],
                        #         outputs=gr.Image(type="numpy", label="VTuber Camera"),
                        #         live=True,
                        #         submit_btn="",  # Submitボタンを非表示にする
                        #         clear_btn=None,   # Clearボタンを非表示にする
                        #         allow_flagging="never",  # Flagボタンを非表示にする
                        #     )
                        #     vtuber_character_update_button = gr.Button("変更", scale=1)
            with gr.Row():
                with gr.Column(scale=4):
                    video_preview_output = gr.Video(label="生成された動画のプレビュー", visible=False)
                    progress_bar = gr.Progress()


            create_video_button = gr.Button("動画生成開始", size="lg", interactive=False)

                # with gr.Column():
                #     create_video_button = gr.Button("動画生成開始", scale=1, visible=False)
                #     cancel_button = gr.Button("キャンセル", scale=1, visible=False)

            # completion_message_output = gr.Textbox(label="生成完了メッセージ", interactive=False) #visible=False
            # progress_bar = gr.Progress()
            # # rendering_progress_output = gr.Textbox(label="レンダリング進行中", interactive=False)
            # generated_video_preview_output = gr.Video(label="生成された動画のプレビュー")


            # イベントハンドラの設定

            # モデル選択ドロップダウンの変更イベント
            voice_synthesis_model_dropdown.change(
                fn=self.handle_gallery_event.on_model_change,
                inputs=[voice_synthesis_model_dropdown, model_list_state],
                outputs=selected_model_tuple_state
            )

            # モデル選択ドロップダウンの変更イベント
            sub_voice_synthesis_model_dropdown.change(
                fn=self.handle_gallery_event.on_model_change,
                inputs=[sub_voice_synthesis_model_dropdown, model_list_state],
                outputs=sub_selected_model_tuple_state
            )

            # 読み方登録ボタンのクリックイベント
            register_reading_button.click(
                # self.dics　を引数で渡す
                fn=self.handle_gallery_event.update_dics,
                inputs=register_reading_input,
                outputs=registered_words_table,  # 更新後のテーブルを表示
            )

            # 読み方登録ボタンのクリックイベント
            update_dics_button.click(
                # self.dics　を引数で渡す
                fn=self.handle_gallery_event.update_dics_from_table,
                inputs=registered_words_table,
                outputs=registered_words_table,  # 更新後のテーブルを表示
            )

            # 画像/動画変更時にプレビューを更新
            image_video_input.change(
                fn=self.handle_gallery_event.update_preview,
                inputs=image_video_input,
                outputs=[preview_image_output, preview_video_output]
            )


            # UIコンポーネントの設定
            # ギャラリーの選択イベントに関数をバインド
            preview_images.select(
                fn=self.handle_frame_event.handle_gallery_click,    
                inputs=[
                    character_name, subtitle_input, reading_input, update_reading_speed_slider, 
                    voice_style_input, update_voice_style_strength_slider, 
                    update_pitch_up_strength_slider,
                    selected_model_tuple_state, emotion_dropdown, motion_dropdown, 
                    image_video_input, whiteboard_image_path, 
                    model_list_state, voice_model_dropdown,
                    selected_index, frame_data_list_state
                    ],
                outputs=[
                    character_name, subtitle_input, reading_input, update_reading_speed_slider, 
                    voice_style_input, update_voice_style_strength_slider,
                    update_pitch_up_strength_slider,
                    voice_model_dropdown, test_playback_button, emotion_dropdown, motion_dropdown, 
                    image_video_input, whiteboard_image_path, preview_images, 
                    selected_index, frame_data_list_state
                    ],
                show_progress=True,
            )
            
            # 読み方更新ボタンのクリックイベント設定
            update_reading_button.click(
                fn=self.handle_frame_event.on_update_reading_click,
                inputs=[
                    character_name, subtitle_input, reading_input, update_reading_speed_slider, 
                    voice_style_input, update_voice_style_strength_slider,
                    update_pitch_up_strength_slider,
                    selected_model_tuple_state, emotion_dropdown, motion_dropdown, 
                    image_video_input, whiteboard_image_path, 
                    model_list_state, voice_model_dropdown,
                    selected_index, frame_data_list_state
                    ],
                outputs=[
                    character_name, subtitle_input, reading_input, update_reading_speed_slider, 
                    voice_style_input, update_voice_style_strength_slider,
                    update_pitch_up_strength_slider,
                    voice_model_dropdown, test_playback_button, emotion_dropdown, motion_dropdown, 
                    image_video_input, whiteboard_image_path, preview_images, 
                    selected_index, frame_data_list_state
                    ],
                show_progress=True,
            )

            # 字幕・読み方を同時変更
            update_subtitle_reading_button.click(
                fn=self.handle_frame_event.update_subtitle_reading,
                inputs=[
                    character_name, subtitle_input, reading_input, update_reading_speed_slider, 
                    voice_style_input, update_voice_style_strength_slider,
                    update_pitch_up_strength_slider,
                    selected_model_tuple_state, emotion_dropdown, motion_dropdown, 
                    image_video_input, whiteboard_image_path, 
                    model_list_state, voice_model_dropdown, 
                    selected_index, frame_data_list_state
                    ],
                outputs=[
                    character_name, subtitle_input, reading_input, update_reading_speed_slider, 
                    voice_style_input, update_voice_style_strength_slider,
                    update_pitch_up_strength_slider,
                    voice_model_dropdown, test_playback_button, emotion_dropdown, motion_dropdown, 
                    image_video_input, whiteboard_image_path, preview_images, 
                    selected_index, frame_data_list_state
                    ],
            )


            # 字幕・読み方を一括変更＋辞書登録
            update_word_reading_button.click(
                fn=self.handle_frame_event.handle_update_word_reading_button,
                inputs=[
                    word_input, word_reading_input,
                    character_name, subtitle_input, reading_input, update_reading_speed_slider, 
                    voice_style_input, update_voice_style_strength_slider,
                    update_pitch_up_strength_slider,
                    selected_model_tuple_state, emotion_dropdown, motion_dropdown, 
                    image_video_input, whiteboard_image_path, 
                    model_list_state, voice_model_dropdown,
                    selected_index, frame_data_list_state
                    ],
                outputs=[
                    registered_words_table,
                    character_name, subtitle_input, reading_input, update_reading_speed_slider, 
                    voice_style_input, update_voice_style_strength_slider,
                    update_pitch_up_strength_slider,
                    voice_model_dropdown, test_playback_button, emotion_dropdown, motion_dropdown, 
                    image_video_input, whiteboard_image_path, preview_images, 
                    selected_index, frame_data_list_state
                    ],
            )



            # # Vtuberキャラクター更新ボタンのクリックイベント設定    
            # vtuber_character_update_button.click(
            #     fn=self.handle_frame_event.on_update_reading_click,
            #     inputs=[
            #         character_name, subtitle_input, reading_input, update_reading_speed_slider, 
            #         selected_model_tuple_state, emotion_dropdown, motion_dropdown, 
            #         image_video_input, whiteboard_image_path, 
            #         selected_index, frame_data_list_state
            #         ],
            #     outputs=[
            #         character_name, subtitle_input, reading_input, update_reading_speed_slider, 
            #         selected_model_tuple_state, test_playback_button, emotion_dropdown, motion_dropdown, 
            #         image_video_input, whiteboard_image_path, preview_images, 
            #         selected_index, frame_data_list_state
            #         ],
            #     show_progress=True,
            # )

            # 動画準備開始ボタンのクリックイベント設定
            generate_video_button.click(
                fn=self.generate_video.generate_video_frames,
                inputs=[
                    csv_file_input, 
                    character_name_input, reading_speed_slider, voice_synthesis_model_dropdown, 
                    sub_character_name_input, sub_reading_speed_slider, sub_voice_synthesis_model_dropdown,
                    pitch_up_strength_slider, sub_pitch_up_strength_slider,
                    voice_style_dropdown, voice_style_strength_slider, sub_voice_style_dropdown, sub_voice_style_strength_slider,
                    model_list_state, 
                    registered_words_table, emotion_shortcuts_state, actions_state,
                    ],
                outputs=[
                    character_name, subtitle_input, reading_input, update_reading_speed_slider, 
                    voice_style_input, update_voice_style_strength_slider, 
                    update_pitch_up_strength_slider,
                    voice_model_dropdown, test_playback_button, emotion_dropdown, motion_dropdown, 
                    image_video_input, whiteboard_image_path, preview_images, 
                    selected_index, frame_data_list_state
                    ],
                show_progress=True,
            ).then(
                fn=self.handle_frame_event.setup_frame_data_list,
                inputs=[],
                outputs=[generate_video_button, create_video_button]
            )


            # 動画生成開始ボタンのクリックイベント設定
            create_video_button.click(
                fn=self.handle_frame_event.create_video,
                inputs=[
                    output_folder_input, 
                    character_name, subtitle_input, reading_input, update_reading_speed_slider, 
                    voice_style_input, update_voice_style_strength_slider,
                    update_pitch_up_strength_slider,
                    selected_model_tuple_state, emotion_dropdown, motion_dropdown, 
                    image_video_input, whiteboard_image_path, 
                    model_list_state, voice_model_dropdown,
                    selected_index, frame_data_list_state
                    ],
                outputs=[
                    character_name, subtitle_input, reading_input, update_reading_speed_slider, 
                    voice_style_input, update_voice_style_strength_slider,
                    update_pitch_up_strength_slider,
                    voice_model_dropdown, test_playback_button, emotion_dropdown, motion_dropdown, 
                    image_video_input, whiteboard_image_path, preview_images, 
                    selected_index, frame_data_list_state, 
                    video_preview_output
                    ],
                show_progress=True,
            )

            demo.load(fn=self.handle_gallery_event.load_emotion_shortcuts, inputs=[], outputs=emotion_shortcuts_input)
            demo.load(fn=self.handle_gallery_event.load_actions, inputs=[], outputs=actions_input)
            demo.load(fn=self.handle_gallery_event.load_dics, inputs=[], outputs=registered_words_table)
            demo.load(fn=self.handle_gallery_event.load_hotkeys, inputs=[], outputs=hotkeys_data)
            demo.load(fn=self.handle_gallery_event.load_audio_devices, inputs=[], outputs=audio_devices)
        demo.launch()
