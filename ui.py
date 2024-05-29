import csv
import asyncio
import numpy as np
import gradio as gr
import pprint
import asyncio
import numpy as np
import requests

from tkinter import filedialog
from moviepy.editor import VideoFileClip

from constants import *
from vts_api import *
from main import *
from utils import *
from generate_video import *
from event_handlers import *


# 設定ファイルの読み込み
character_name, voice_synthesis_model, reading_speed, output_folder, bgm_file, background_video_file, emotion_shortcuts, actions, dics = load_settings(DEFAULT_SETTING_FILE)
# csv_data = []

# selected_index = 0


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
    # print(f"frame_data_list: {frame_data_list}")
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

    # 初期状態または特定のフレームが選択された場合の処理
    # if selected_index is None:
    #     selected_index = 0

    # 各要素を選択されたインデックスに基づいて設定
    # subtitle_input = subtitle_input_list[selected_index]
    # reading_input = reading_input_list[selected_index]
    subtitle_input.value = subtitle_input_list[selected_index]
    reading_input.value = reading_input_list[selected_index]
    test_playback_button.value = audio_file_list[selected_index]

    emotion_dropdown = emotion_dropdown_list[selected_index]
    motion_dropdown = motion_dropdown_list[selected_index]
    # image_video_input = image_video_input_list[selected_index]
    # image_video_input.value = r"Asset\Greenbak.png"
    image_video_input.value = image_video_input_list[selected_index]

    # print(f"ー＞\nimage_video_input: {image_video_input}")
    # print(f"image_video_input.value: {image_video_input.value}")
    # if image_video_input.value == r"Asset\Greenbak.png":
    #     image_video_input.value = None

    # print(f"image_video_input: {image_video_input}")
    # print(f"image_video_input.value: {image_video_input.value}")
    # image_video_input: <gradio.components.file.File object at 0x0000025A6FA01030>
    # image_video_input.value: C:\Users\okozk\Test\Gradio\tmp\tmpfn30of0o.png

    # 戻り値として各要素のリストを返す
    return preview_images, subtitle_input.value, reading_input.value, test_playback_button.value, emotion_dropdown, motion_dropdown, image_video_input.value

    
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

# 読み方変更ボタンがクリックされたときの処理
def on_update_reading_click(subtitle_line, reading_line, image_video_input, selected_index, selected_model_tuple_state):
    global frame_data_list
    # global selected_index

    if frame_data_list is None:
        # selected_index = 0
        raise ValueError(f"frame_data_list is -> {frame_data_list}")
    
    if selected_index is None:
        # selected_index = 0
        raise ValueError(f"selected_index is -> {selected_index}")
    

    print(f"\n selected_index is -> {selected_index} !!!")
    # print(f"{background_video_file_input, subtitle_line, reading_line, image_video_input}")
    
    whiteboard_image_path = ""
    vtuber_character_path = capture_and_process_image()


    # image_video_input が None の場合の処理
    if image_video_input is None:
        preview_image_path = generate_preview_image(r'background_video\default_video.mp4', r"Asset\Greenbak.png", whiteboard_image_path, subtitle_line, vtuber_character_path)
    else:
        preview_image_path = generate_preview_image(r'background_video\default_video.mp4', image_video_input, whiteboard_image_path, subtitle_line, vtuber_character_path)

    if image_video_input == r"Asset\Greenbak.png":
        image_video_input = None

    # 現在のフレームデータを更新
    frame_data = list(frame_data_list[selected_index])

    #読み方が変わっていれば音声変換してパスを取得
    if reading_line != frame_data[1] :
        model_name, model_id, speaker_id = selected_model_tuple_state
        audio_file_path = generate_audio(subtitle_line, reading_line, model_name, model_id, speaker_id)
        frame_data[2] = audio_file_path


    frame_data[0] = subtitle_line
    frame_data[1] = reading_line
    frame_data[6] = image_video_input
    frame_data[8] = preview_image_path

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
    
    new_selected_index = evt.index

    # # デバッグ用にselected_indexの値を確認
    # if selected_index is None:
    #     print("Error: selected_index is None", frame_data_list)
    # else:
    #     print(f"selected_index is set to: {selected_index}", frame_data_list)

    # 現在のフレームデータを取得
    current_frame_data = frame_data_list[selected_index]

    # 現在のデータと新しいデータを比較
    if (current_frame_data[0] != subtitle_input or current_frame_data[1] != reading_input or current_frame_data[6] != image_video_input):            
        # データが異なる場合のみ更新
        if image_video_input is None:
            on_update_reading_click(subtitle_input, reading_input, r"Asset\Greenbak.png", selected_index, selected_model_tuple_state)
        else:
            on_update_reading_click(subtitle_input, reading_input, image_video_input, selected_index, selected_model_tuple_state)

    # 次に表示するUI要素を更新
    preview_images, subtitle_input, reading_input, test_playback_button, emotion_dropdown, motion_dropdown, image_video_input = update_ui_elements(new_selected_index)

    # # print(f"image_video_input: {image_video_input}")
    # if image_video_input == r"Asset\Greenbak.png":
    #     image_video_input = None

    return preview_images, subtitle_input, reading_input, test_playback_button, emotion_dropdown, motion_dropdown, image_video_input, new_selected_index



# SBTV2_APIからモデル一覧を取得する関数
# 例となるデータ
# model_list = [
#     ("AI-Hakase-Test2", "0", 0),
#     ("AI-Hakase-v1", "1", 0)
def fetch_voice_synthesis_models():
    response = requests.get("http://127.0.0.1:5000/models/info")  # 適切なAPIエンドポイントに置き換えてください
    if response.status_code == 200:
        models = response.json()
        model_list = []
        model_names = []
        for model_id, model_info in models.items():
            speaker_name = list(model_info["id2spk"].values())[0]
            speaker_id = list(model_info["spk2id"].values())[0]
            model_list.append((speaker_name, model_id, speaker_id))
            model_names.append(speaker_name)
        return model_list, model_names
    else:
        print("モデル一覧の取得に失敗しました。")
        return [], []




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
                model_list, model_names = fetch_voice_synthesis_models()
                model_list_state = gr.State(model_list)  # モデル情報のタプルを保持
                voice_synthesis_model_dropdown = gr.Dropdown(model_names, label="音声合成モデル", value=voice_synthesis_model)
                # voice_synthesis_model_dropdown = gr.Dropdown(["model1", "model2", "model3"], label="音声合成モデル", value=voice_synthesis_model)
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
            preview_images = gr.Gallery(label="画像/動画フレーム一覧", elem_id="frame_gallery",scale=2)
            
        with gr.Column():
            with gr.Tab("テキスト・画像・動画編集"):
                with gr.Row():
                    with gr.Column(scale=3):
                        subtitle_input = gr.Textbox(label="セリフ（字幕用）",scale=3)
                        reading_input = gr.Textbox(label="セリフ（読み方）",scale=3)
                    with gr.Row():
                        update_reading_button = gr.Button("変更",scale=1)
                with gr.Column(scale=1):
                    image_video_input = gr.File(label="画像/動画選択", file_types=["image", "video"], interactive=True)
                    with gr.Row():
                        preview_image_output = gr.Image(label="画像プレビュー", elem_id="image_preview_output", visible=False, scale=3)
                        preview_video_output = gr.Video(label="動画プレビュー", elem_id="video_preview_output", visible=False, scale=3)
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
                    vtuber_character_output = gr.Video(sources=["webcam"], label="Vtuberキャラクター", scale=3)
                    vtuber_character_update_button = gr.Button("変更", scale=1)

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
        inputs=[subtitle_input, reading_input, image_video_input, selected_index, selected_model_tuple_state],
        outputs=[preview_images, subtitle_input, reading_input, test_playback_button, emotion_dropdown, motion_dropdown, image_video_input]
    )

    # Vtuberキャラクター更新ボタンのクリックイベント設定    
    vtuber_character_update_button.click(
        fn=on_update_reading_click,
        inputs=[subtitle_input, reading_input, image_video_input, selected_index, selected_model_tuple_state],
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
    
    generate_video_button.click(
    fn=generate_video,
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
