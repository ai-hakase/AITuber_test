import asyncio
import numpy as np
import gradio as gr
import pprint
import asyncio
import numpy as np
import requests
import signal

from tkinter import filedialog
from moviepy.editor import VideoFileClip

from vtuber_camera import VTuberCamera
from edit_medias import EditMedia
from constants import *
from vts_api import *
from main import *
from utils import *
from generate_video import *
from create_subtitle_voice import CreateSubtitleVoice
from event_handlers import *

vtuber_camera = VTuberCamera()
generate_video = GenerateVideo()
edit_medias = EditMedia()
create_subtitle_voice = CreateSubtitleVoice()

signal.signal(signal.SIGINT, vtuber_camera.stop) # ターミナルでの Ctrl+C で終了するための処理

# 設定ファイルの読み込み
character_name, voice_synthesis_model, reading_speed, output_folder, bgm_file, background_video_file, emotion_shortcuts, actions, dics = load_settings(DEFAULT_SETTING_FILE)

# プレビュー画像の幅と高さ
preview_width, preview_height = 1920, 1080


# 変数をコンソールに書き出す関数
def print_variables():
    variables = {
        "CSVファイル": csv_file_input.value['path'],
        "BGMファイル": bgm_file_input.value['path'],
        "背景動画ファイル": background_video_file_input.value['video']['path'],
        "subtitle_line": subtitle_input.value,
        "reading_line": reading_input.value,
        "image_video_input": image_video_input,
        "image_video_input.value": image_video_input.value,
        "キャラクター名.value": character_name_input.value,
        "キャラクター名": character_name_input,
        "音声合成モデル": voice_synthesis_model_dropdown.value,
        "読み上げ速度": reading_speed_slider.value,
        "登録済み単語/文章一覧": registered_words_table.value['data'],
        "感情ショートカット emotion_shortcuts_state": emotion_shortcuts_state.value,
        "アクション actions_state": actions_state.value,
        "動画保存先": output_folder_input.value,
        "設定ファイルパス": settings_file_path_input.value,
    }
    pprint.pprint(variables)


# アップロードされたファイルの種類に応じてプレビューを更新する関数
def update_preview(file):
    if file is None:
        return gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)
    
    if isinstance(file, dict):
        file_type = file["type"]
        file_name = file["name"]
    else:
        import mimetypes
        file_type, _ = mimetypes.guess_type(file)
        file_name = file

    if file_type.startswith("image"):
        return gr.update(value=file_name, visible=True), gr.update(visible=False), gr.update(visible=True)
    elif file_type.startswith("video"):
        return gr.update(visible=False), gr.update(value=file_name, visible=True), gr.update(visible=True)
    return gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)


def on_delete_image_video_click():
    return gr.update(label="画像/動画選択", value=None, file_types=["image", "video"], interactive=True), gr.update(value=None, visible=False), gr.update(value=None, visible=False), gr.update(visible=False)


# フレームデータから各要素を抽出してUIに表示する関数
def update_ui_elements(selected_index):
    global frame_data_list

    # 各要素を抽出
    try:
        preview_images = [frame_data[8] for frame_data in frame_data_list]
        subtitle_input_list = [frame_data[0] for frame_data in frame_data_list]
        reading_input_list = [frame_data[1] for frame_data in frame_data_list]
        audio_file_list = [frame_data[2] for frame_data in frame_data_list]
        emotion_dropdown_list = [frame_data[3] for frame_data in frame_data_list]
        motion_dropdown_list = [frame_data[4] for frame_data in frame_data_list]
        image_video_input_list = [frame_data[6] for frame_data in frame_data_list]
    except IndexError as e:
        print(f"IndexError: {e}")
        return None, None, None, None, None, None

    subtitle_input.value = subtitle_input_list[selected_index]
    reading_input.value = reading_input_list[selected_index]
    test_playback_button.value = audio_file_list[selected_index]
    emotion_dropdown = emotion_dropdown_list[selected_index]
    motion_dropdown = motion_dropdown_list[selected_index]
    image_video_input.value = image_video_input_list[selected_index]

    # 戻り値として各要素のリストを返す
    return preview_images, subtitle_input.value, reading_input.value, test_playback_button.value, emotion_dropdown, motion_dropdown, image_video_input.value

    
#　グローバル変数にリストを格納 → 最初に更新
def update_frame_data_list(frame_data):
    global frame_data_list
    if frame_data_list is None:
        frame_data_list = frame_data
        # print("frame_data_list:", frame_data_list)  # デバッグ用にデータを出力
        return update_ui_elements(0)
    else:
        print("No data:", frame_data_list)  # デバッグ用にデータを出力
        return None, None, None, None, None, None

# 読み方変更ボタンがクリックされたときの処理
def on_update_reading_click(subtitle_line, reading_line, image_video_input, selected_index, selected_model_tuple_state, whiteboard_image_path):
    global frame_data_list

    if frame_data_list is None:
        # selected_index = 0
        raise ValueError(f"frame_data_list is -> {frame_data_list}")
    
    if selected_index is None:
        # selected_index = 0
        raise ValueError(f"selected_index is -> {selected_index}")
    

    print(f"\n selected_index is -> {selected_index} !!!")

    
    # 字幕画像の生成
    subtitle_img = edit_medias.generate_subtitle(subtitle_line, preview_width, preview_height)#字幕画像の生成
    subtitle_image_path = save_as_temp_file(subtitle_img)#テンポラリファイルに保存

    # Vキャラ画像を生成 -> クロマキー処理
    vtuber_img = edit_medias.create_vtuber_image()
    vtuber_character_path = save_as_temp_file(vtuber_img)

    # image_video_input が None の場合の処理
    if image_video_input is None:
        image_video_input = r"Asset\Greenbak.png"

    # 解説画像の生成
    explanation_img = load_image_or_video(image_video_input).convert("RGBA")  # RGBAモードに変換
    whiteboard_image = Image.open(whiteboard_image_path).convert("RGBA")  # RGBAモードに変換
    # 解説画像のアスペクト比を維持しながらホワイトボード画像に合わせてリサイズ
    explanation_img = edit_medias.resize_image_aspect_ratio(explanation_img, whiteboard_image.width - 20, whiteboard_image.height - 20)
    # 解説画像の周りにボーダーを追加
    explanation_img = edit_medias.add_border(explanation_img, 10)
    explanation_image_path = save_as_temp_file(explanation_img)

    # プレビュー画像の生成  
    preview_image_path = generate_video.generate_preview_image(background_video_file, explanation_image_path, whiteboard_image_path, subtitle_image_path, vtuber_character_path)

    # 現在のフレームデータを更新
    frame_data = list(frame_data_list[selected_index])

    if image_video_input == r"Asset\Greenbak.png": #画像がない場合
        image_video_input = None #Noneに変換

    #読み方が変わっていれば音声変換してパスを取得
    if reading_line != frame_data[1] :
        model_name, model_id, speaker_id = selected_model_tuple_state #モデル情報を取得
        audio_file_path = create_subtitle_voice.generate_audio(subtitle_line, reading_line, model_name, model_id, speaker_id) #音声変換
        frame_data[2] = audio_file_path #フレームデータに音声パスを追加

    frame_data[0] = subtitle_line #字幕
    frame_data[1] = reading_line #読み方
    frame_data[6] = image_video_input #画像
    frame_data[8] = preview_image_path #プレビュー画像

    # 更新されたフレームデータをリストに戻す
    frame_data_list[selected_index] = tuple(frame_data)

    # UIコンポーネントを更新
    return update_ui_elements(selected_index)


# 読み方用のテキストエリアでEnterキーが押されたときの処理
def on_reading_input_submit(evt, subtitle_line, reading_line, image_video_input):
    if evt.key == "Enter":
        return on_update_reading_click(subtitle_line, reading_line, image_video_input)
    return gr.update()


# ギャラリーのインデックスが選択されたときに呼び出される関数
def handle_gallery_click(evt: gr.SelectData, subtitle_input, reading_input, image_video_input, selected_index, selected_model_tuple_state):
    global frame_data_list
    
    new_selected_index = evt.index#ギャラリーのインデックスを取得

    current_frame_data = frame_data_list[selected_index]#現在のフレームデータを取得

    # 現在のデータと新しいデータを比較
    if (current_frame_data[0] != subtitle_input or current_frame_data[1] != reading_input or current_frame_data[6] != image_video_input): 
        whiteboard_image_path = current_frame_data[6]
        # データが異なる場合のみ更新
        on_update_reading_click(subtitle_input, reading_input, image_video_input, selected_index, selected_model_tuple_state, whiteboard_image_path)

    # 次に表示するUI要素を更新
    preview_images, subtitle_input, reading_input, test_playback_button, emotion_dropdown, motion_dropdown, image_video_input = update_ui_elements(new_selected_index)

    return preview_images, subtitle_input, reading_input, test_playback_button, emotion_dropdown, motion_dropdown, image_video_input, new_selected_index


# Gradioアプリケーションの構築
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# AI Tuber Test Program")

    with gr.Row():
        with gr.Column(scale=1):
            csv_file_input = gr.File(label="CSVファイル", file_types=['text'], value="test\\AItuber_test.csv")
            bgm_file_input = gr.Audio(label="BGMファイル", value=bgm_file, interactive=True)
            background_video_file_input = gr.Video(label="背景動画ファイル", value=background_video_file, interactive=True)



        with gr.Column(scale=2):
            with gr.Tab("読み上げ設定"):
                # キャラ
                character_name_input = gr.Textbox(label="メインキャラクター名", value=character_name)
                model_list, model_names = create_subtitle_voice.fetch_voice_synthesis_models()
                model_list_state = gr.State(model_list)  # モデル情報のタプルを保持
                voice_synthesis_model_dropdown = gr.Dropdown(model_names, label="音声合成モデル", value=voice_synthesis_model)
                reading_speed_slider = gr.Slider(0.5, 2.0, value=reading_speed, step=0.1, label="読み上げ速度")

                # 選択されたモデルのタプルを保持するための変数
                selected_model_tuple_state = gr.State()

                # ドロップダウンの変更イベントに関数をバインド
                def on_model_change(voice_synthesis_model_dropdown, model_list_state):
                    if voice_synthesis_model_dropdown:
                        selected_model_tuple = next((model for model in model_list_state if model[0] == voice_synthesis_model_dropdown), None)
                    else:
                        print("選択されたモデルが見つかりません。")
                    return selected_model_tuple

                voice_synthesis_model_dropdown.change(
                    fn=on_model_change,
                    inputs=[voice_synthesis_model_dropdown, model_list_state],
                    outputs=selected_model_tuple_state
                )

                # 辞書
                registered_words_table = gr.Dataframe(
                    headers=["単語/文章", "読み方"],
                    datatype=["str", "str"],
                    col_count=(2, "fixed"),
                    row_count=8,
                    label="登録済み単語/文章一覧",
                    value=[[word, reading] for word, reading in dics.items()]
                )
                # show_registered_words_button = gr.Button("登録済み単語/文章一覧表示")#→全体画面表示する。
                # with gr.Row():
                    # ここにJsonファイルの場所を表示
                    # add_word_button = gr.Button("追加") #一番上に行を追加
                    # edit_word_button = gr.Button("編集") # 
                    # delete_word_button = gr.Button("削除")

            with gr.Tab("ショートカット設定"):
                emotion_shortcuts_input = gr.Dataframe(
                    headers=["Emotion", "Shortcut"],
                    scale=1,
                    col_count=(2, "fixed"),
                    row_count=8,
                    type="array",
                    value=[[emotion, ", ".join(shortcut)] for emotion, shortcut in emotion_shortcuts.items()],
                    interactive=False
                )
                update_emotion_shortcuts_button = gr.Button("更新", scale=1)
                actions_input = gr.Dataframe(
                    headers=["Action", "Shortcut Name", "Keys"],
                    scale=1,
                    col_count=(3, "fixed"),
                    row_count=6,
                    type="array",
                    value=flatten_actions(actions)
                )
                update_actions_button = gr.Button("更新", scale=1)

            with gr.Tab("保存先・設定ファイル"):
                # 動画保存先
                output_folder_input = gr.Textbox(label="動画保存先", value=output_folder)
                change_output_folder_button = gr.Button("保存先変更")
                # 設定ファイル読み込み
                settings_folder_display = gr.Textbox(label="設定フォルダ", value=DEFAULT_SETTINGS_FOLDER, interactive=False)
                settings_file_path_input = gr.Textbox(label="読み込み対象の設定ファイルパス", value=DEFAULT_SETTING_FILE)
                load_settings_button = gr.Button("設定ファイル読み込み")
                with gr.Row():
                    new_settings_name_input = gr.Textbox(label="新規設定ファイル名")
                    save_new_settings_button = gr.Button("新規設定ファイル保存")


    # 動画準備
    generate_video_button = gr.Button("感情分析・動画準備開始（英語テキスト翻訳 + 翻訳後のテキストで音声合成）", elem_classes="font-size: 10px",scale=1)
    # 変数をコンソールに表示するボタン
    print_variables_button = gr.Button("変数をコンソールに表示")





    with gr.Row():
        # 一時的な出力を受け取るための隠しコンポーネント
        selected_index = gr.State(0)
        whiteboard_image_path = gr.File(label="", visible=False)
        subtitle_image_path = gr.File(label="", visible=False)
        hidden_output = gr.JSON(visible=False)

        with gr.Column():
            test_playback_button = gr.Audio(value=r"bgm\default_bgm.wav ", type="filepath", label="テスト再生", scale=1)
            preview_images = gr.Gallery(label="画像/動画フレーム一覧", elem_id="frame_gallery", scale=2)
            
        with gr.Column():
            with gr.Tab("テキスト・画像・動画編集"):
                with gr.Row():
                    with gr.Column(scale=3):
                        subtitle_input = gr.Textbox(label="セリフ（字幕用）",scale=3)
                        reading_input = gr.Textbox(label="セリフ（読み方）",scale=3)
                    with gr.Row():
                        update_reading_button = gr.Button("変更",scale=1)
                with gr.Column(scale=1):
                    image_video_input = gr.File(label="画像/動画選択", file_types=["image", "video"], interactive=True, height=400)
                    with gr.Row():
                        preview_image_output = gr.ImageEditor(label="画像プレビュー", elem_id="image_preview_output", interactive=True, visible=False, scale=3, height=400)
                        preview_video_output = gr.Video(label="動画プレビュー", elem_id="video_preview_output", interactive=True, visible=False, scale=3, height=400)
                        delete_image_video_button = gr.Button("削除", visible=False, scale=1)

            # with gr.Tab("画像・動画編集"):
            #     with gr.Row():
            #         update_image_video_button = gr.Button("変更", scale=2)
                # preview_image_output = gr.Image(label="画像プレビュー", elem_id="image_preview_output", interactive=True)
                # preview_video_output = gr.Video(label="動画プレビュー", elem_id="video_preview_output", interactive=True)

            with gr.Tab("Vキャラ・モーション設定"):
                # character_position_slider = gr.Slider(minimum=0, maximum=100, step=1, label="キャラクター位置")
                # character_size_slider = gr.Slider(minimum=50, maximum=200, step=1, label="キャラクターサイズ")
                emotion_dropdown = gr.Dropdown(label="表情選択")#, choices=["neutral", "happy", "sad", "angry"])
                motion_dropdown = gr.Dropdown(label="モーション選択")#, choices=["idle", "nod", "shake", "point"])
                with gr.Row():
                    with gr.Column(scale=3):
                        vtuber_character_output = gr.Interface(
                        fn=vtuber_camera.get_frame,
                        inputs=[],
                        outputs=gr.Image(type="numpy", label="VTuber Camera"),
                        live=True,
                        submit_btn="",  # Submitボタンを非表示にする
                        clear_btn=None,   # Clearボタンを非表示にする
                        allow_flagging="never",  # Flagボタンを非表示にする
                        )
                    vtuber_character_update_button = gr.Button("変更", scale=1)


    with gr.Row():
        with gr.Column(scale=4):
            video_preview_output = gr.Video(label="現在のフレームをプレビュー")
        with gr.Column():
            generate_video_button2 = gr.Button("動画生成開始", scale=1, elem_classes="font-size: 10px")
            cancel_button = gr.Button("キャンセル", scale=1, elem_classes="font-size: 10px")

    completion_message_output = gr.Textbox(label="生成完了メッセージ", interactive=False) #visible=False
    progress_bar = gr.Progress()
    # rendering_progress_output = gr.Textbox(label="レンダリング進行中", interactive=False)
    generated_video_preview_output = gr.Video(label="生成された動画のプレビュー")





    # UIコンポーネントの設定
    # ギャラリーの選択イベントに関数をバインド
    preview_images.select(
        fn=handle_gallery_click,    
        inputs=[subtitle_input, reading_input, image_video_input, selected_index, selected_model_tuple_state],
        outputs=[preview_images, subtitle_input, reading_input, test_playback_button, emotion_dropdown, motion_dropdown, image_video_input, selected_index]
    )
    
    # 読み方更新ボタンのクリックイベント設定
    update_reading_button.click(
        fn=on_update_reading_click,
        inputs=[subtitle_input, reading_input, image_video_input, selected_index, selected_model_tuple_state, whiteboard_image_path],
        outputs=[preview_images, subtitle_input, reading_input, test_playback_button, emotion_dropdown, motion_dropdown, image_video_input]
    )

    # Vtuberキャラクター更新ボタンのクリックイベント設定    
    vtuber_character_update_button.click(
        fn=on_update_reading_click,
        inputs=[subtitle_input, reading_input, image_video_input, selected_index, selected_model_tuple_state, whiteboard_image_path],
        outputs=[preview_images, subtitle_input, reading_input, test_playback_button, emotion_dropdown, motion_dropdown, image_video_input]
    )

    # 画像/動画削除ボタンのクリックイベント設定
    delete_image_video_button.click(
        fn=on_delete_image_video_click,
        inputs=[],
        outputs=[image_video_input, preview_image_output, preview_video_output, delete_image_video_button]
    )

    # 画像/動画変更時にプレビューを更新
    image_video_input.change(
        fn=update_preview,
        inputs=image_video_input,
        outputs=[preview_image_output, preview_video_output, delete_image_video_button]
    )


    # イベントハンドラの設定
    csv_file_input.change(on_csv_file_change, csv_file_input)
    bgm_file_input.change(on_bgm_file_change, bgm_file_input)
    background_video_file_input.change(on_background_video_file_change, background_video_file_input)
    change_output_folder_button.click(lambda: on_change_output_folder_click(output_folder_input))
    # change_output_folder_button.click(on_change_output_folder_click, None, output_folder_input)
    # show_registered_words_button.click(load_and_show_dics, outputs=[registered_words_table, dics_table])
    emotion_shortcuts_state = gr.State(emotion_shortcuts)
    actions_state = gr.State(actions)
    # イベントハンドラの設定
    print_variables_button.click(fn=print_variables)


    # 動画準備開始ボタンのクリックイベント設定
    generate_video_button.click(
    fn=generate_video.generate_video,
    inputs=[
        csv_file_input,
        bgm_file_input,
        background_video_file_input,
        character_name_input,
        model_list_state,
        selected_model_tuple_state,
        reading_speed_slider,
        registered_words_table,
        emotion_shortcuts_state,
        actions_state
    ],
    outputs=[subtitle_input, reading_input, test_playback_button, emotion_dropdown, motion_dropdown, image_video_input, whiteboard_image_path, subtitle_image_path, preview_images, selected_model_tuple_state],
    show_progress=True
    )

    # # 読み方入力フィールドのサブミットイベント設定
    # reading_input.submit(
    #     fn=on_reading_input_submit,
    #     inputs=[reading_input, subtitle_input, image_video_input],
    #     outputs=[preview_images, subtitle_input, reading_input, emotion_dropdown, motion_dropdown, image_video_input]
    # )

    # hidden_outputの値が変更されたときにupdate_ui_elementsを呼び出す
    # hidden_output.change(
    #     fn=update_frame_data_list,
    #     inputs=[hidden_output],
    #     outputs=[preview_images, subtitle_input, reading_input, emotion_dropdown, motion_dropdown, image_video_input]
    # )

    # update_emotion_shortcuts_button.click(
    #     fn=update_emotion_shortcut,
    #     inputs=[emotion_shortcuts_input],
    #     outputs=[emotion_shortcuts_state]
    # )

    # update_actions_button.click(
    #     fn=update_action_shortcut,
    #     inputs=[actions_input],
    #     outputs=[actions_state]
    # )


    # save_settings_button.click(
    #     fn=save_settings,
    #     inputs=[emotion_shortcuts_state, actions_state, json_file_output],
    #     outputs=[]
    # )

async def main():
    asyncio.create_task(capture_frames(VTUBE_STUDIO_URI, PLUGIN_NAME, PLUGIN_DEVELOPER))

if __name__ == "__main__":
    asyncio.run(main())
