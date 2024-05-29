import csv
import asyncio
import numpy as np
import gradio as gr
import pprint
import asyncio
import numpy as np

from tkinter import filedialog
from moviepy.editor import VideoFileClip

from constants import *
from vts_api import *
from main import *
from utils import *
from event_handlers import *
from generate_video import generate_video


# 設定ファイルの読み込み
character_name, voice_synthesis_model, reading_speed, output_folder, bgm_file, background_video_file, emotion_shortcuts, actions, dics = load_settings(DEFAULT_SETTING_FILE)
# csv_data = []

# グローバル変数でフレームデータリストを保持
frame_data_list = None



# 変数をコンソールに書き出す関数
def print_variables():
    variables = {
        "CSVファイル": csv_file_input.value['path'],
        "BGMファイル": bgm_file_input.value['path'],
        "背景動画ファイル": background_video_file_input.value['video']['path'],
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
        return gr.update(visible=False), gr.update(visible=False)
    
    if isinstance(file, dict):
        file_type = file["type"]
        file_name = file["name"]
    else:
        import mimetypes
        file_type, _ = mimetypes.guess_type(file)
        file_name = file

    if file_type.startswith("image"):
        return gr.update(value=file_name, visible=True), gr.update(visible=False)
    elif file_type.startswith("video"):
        return gr.update(visible=False), gr.update(value=file_name, visible=True)
    return gr.update(visible=False), gr.update(visible=False)



# フレームデータから各要素を抽出してUIに表示する関数
def update_ui_elements(selected_index):

    # print(f"frame_data_list: {frame_data_list}")
    # 各要素を抽出
    try:
        preview_images = [frame_data[8] for frame_data in frame_data_list]
        subtitle_input_list = [frame_data[0] for frame_data in frame_data_list]
        reading_input_list = [frame_data[1] for frame_data in frame_data_list]
        emotion_dropdown_list = [frame_data[3] for frame_data in frame_data_list]
        motion_dropdown_list = [frame_data[4] for frame_data in frame_data_list]
        image_video_input_list = [frame_data[6] for frame_data in frame_data_list]
    except IndexError as e:
        print(f"IndexError: {e}")
        return None, None, None, None, None, None

    # 初期状態または特定のフレームが選択された場合の処理
    if selected_index is None:
        selected_index = 0

    # 各要素を選択されたインデックスに基づいて設定
    # preview_image = preview_images[selected_index]
    subtitle_input = subtitle_input_list[selected_index]
    reading_input = reading_input_list[selected_index]
    emotion_dropdown = emotion_dropdown_list[selected_index]
    motion_dropdown = motion_dropdown_list[selected_index]
    image_video_input = image_video_input_list[selected_index]

    # 戻り値として各要素のリストを返す
    return preview_images, subtitle_input, reading_input, emotion_dropdown, motion_dropdown, image_video_input

    
# ギャラリーのインデックスが選択されたときに呼び出される関数
def handle_gallery_click(evt: gr.SelectData):
    selected_index = evt.index
    print(f"Selected index: {selected_index}")
    return update_ui_elements(selected_index)


#　グローバル変数にリストを格納 → 最初に更新
# hidden_outputの値が変更されたときにframe_data_listを更新
def update_frame_data_list(frame_data):
    global frame_data_list
    if frame_data_list is None:
        frame_data_list = frame_data
        # print("frame_data_list:", frame_data_list)  # デバッグ用にデータを出力
        return update_ui_elements(0)
    else:
        print("No data:", frame_data_list)  # デバッグ用にデータを出力
        return None, None, None, None, None, None






# Gradioアプリケーションの構築
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# AI Tuber Test Program")

    with gr.Row():
        with gr.Column(scale=1):
            csv_file_input = gr.File(label="CSVファイル", file_types=['text'], value="test\\AItuber_test.csv")
            bgm_file_input = gr.Audio(label="BGMファイル", value=bgm_file, interactive=True)
            background_video_file_input = gr.Video(label="背景動画ファイル", value=background_video_file, interactive=True)

        with gr.Column():
            with gr.Tab("読み上げ設定"):
                # キャラ
                character_name_input = gr.Textbox(label="メインキャラクター名", value=character_name)
                voice_synthesis_model_dropdown = gr.Dropdown(["model1", "model2", "model3"], label="音声合成モデル", value=voice_synthesis_model)
                reading_speed_slider = gr.Slider(0.5, 2.0, value=reading_speed, step=0.1, label="読み上げ速度")

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

    # イベントハンドラの設定
    csv_file_input.change(on_csv_file_change, csv_file_input)
    bgm_file_input.change(on_bgm_file_change, bgm_file_input)
    background_video_file_input.change(on_background_video_file_change, background_video_file_input)
    change_output_folder_button.click(lambda: on_change_output_folder_click(output_folder_input))
    # change_output_folder_button.click(on_change_output_folder_click, None, output_folder_input)
    # show_registered_words_button.click(load_and_show_dics, outputs=[registered_words_table, dics_table])
    emotion_shortcuts_state = gr.State(emotion_shortcuts)
    actions_state = gr.State(actions)

    # 変数をコンソールに表示するボタン
    print_variables_button = gr.Button("変数をコンソールに表示")
    # イベントハンドラの設定
    print_variables_button.click(fn=print_variables)

    # 動画準備
    generate_video_button = gr.Button("感情分析・動画準備開始（英語テキスト翻訳 + 翻訳後のテキストで音声合成）", elem_classes="font-size: 10px")







    with gr.Row():
        with gr.Column():
            # selected_frame_preview_output = gr.Image(label="選択された画像/動画のプレビュー", )#value=gr.Image.update(value=frame_list_output, every=1)


            preview_images = gr.Gallery(label="画像/動画フレーム一覧", elem_id="frame_gallery")
            # 一時的な出力を受け取るための隠しコンポーネント
            hidden_output = gr.JSON(visible=False)


        with gr.Column():
            with gr.Tab("テキスト・モーション編集"):
                subtitle_input = gr.Textbox(label="セリフ（字幕用）")
                reading_input = gr.Textbox(label="セリフ（読み方）")
                with gr.Row():
                    update_reading_button = gr.Button("読み方変更")
                    test_playback_button = gr.Button("テスト再生")
                emotion_dropdown = gr.Dropdown(label="表情選択")#, choices=["neutral", "happy", "sad", "angry"])
                motion_dropdown = gr.Dropdown(label="モーション選択")#, choices=["idle", "nod", "shake", "point"])

            with gr.Tab("画像・動画編集"):
                image_video_input = gr.File(label="画像/動画選択", file_types=["image", "video"])
                preview_image_output = gr.Image(label="画像プレビュー", elem_id="image_preview_output", visible=False)
                preview_video_output = gr.Video(label="動画プレビュー", elem_id="video_preview_output", visible=False)

            with gr.Tab("Vキャラ設定"):
                character_position_slider = gr.Slider(minimum=0, maximum=100, step=1, label="キャラクター位置")
                character_size_slider = gr.Slider(minimum=50, maximum=200, step=1, label="キャラクターサイズ")
                vtuber_character_output = gr.Video(sources=["webcam"], label="Vtuberキャラクター")
                # vtuber_character_output =gr.Interface(fn=custom_html, inputs=[], outputs=gr.HTML())
                # video_preview_output = gr.HTML(value=custom_html())
                # video_output = gr.HTML(video_feed)
                # demo = gr.Interface(lambda: "", inputs=[], outputs=video_output, allow_flagging="never")



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


    generate_video_button.click(
        fn=generate_video,
        inputs=[
            csv_file_input,
            bgm_file_input,
            background_video_file_input,
            character_name_input,
            voice_synthesis_model_dropdown,
            reading_speed_slider,
            registered_words_table,
            emotion_shortcuts_state,
            actions_state
        ],
        outputs=[hidden_output],
        show_progress=True
    )

    # ファイルがアップロードされたときにプレビューを更新
    image_video_input.change(
        fn=update_preview,
        inputs=image_video_input,
        outputs=[preview_image_output, preview_video_output]
    )



    # ギャラリーの選択イベントに関数をバインド
    # preview_images.select(handle_gallery_click)    

    # ギャラリーの選択イベントに関数をバインド
    preview_images.select(
        fn=handle_gallery_click,
        inputs=None,
        outputs=[preview_images, subtitle_input, reading_input, emotion_dropdown, motion_dropdown, image_video_input]
    )

    # hidden_outputの値が変更されたときにupdate_ui_elementsを呼び出す
    hidden_output.change(
        fn=update_frame_data_list,
        inputs=[hidden_output],
        outputs=[preview_images, subtitle_input, reading_input, emotion_dropdown, motion_dropdown, image_video_input]
    )



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
