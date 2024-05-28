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
        # outputs=[generated_video_output],
        show_progress=True
    )



    with gr.Row():
        with gr.Column():
            frame_list_output = gr.Gallery(label="画像/動画フレーム一覧", elem_id="frame_gallery")
            selected_frame_preview_output = gr.Image(label="選択された画像/動画のプレビュー", )#value=gr.Image.update(value=frame_list_output, every=1)

        with gr.Column():
            with gr.Tab("テキスト・モーション編集"):
                subtitle_input = gr.Textbox(label="セリフ（字幕用）")
                reading_input = gr.Textbox(label="セリフ（読み方）")
                with gr.Row():
                    update_reading_button = gr.Button("読み方変更")
                    test_playback_button = gr.Button("テスト再生")
                emotion_dropdown = gr.Dropdown(label="表情選択", choices=["neutral", "happy", "sad", "angry"])
                motion_dropdown = gr.Dropdown(label="モーション選択", choices=["idle", "nod", "shake", "point"])

            with gr.Tab("画像・動画編集"):
                image_video_input = gr.File(label="画像/動画選択", file_types=["image", "video"])
                delete_image_video_button = gr.Button("画像/動画削除")
                # whiteboard_output = gr.Image(label="ホワイトボード")

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
            generate_video_button = gr.Button("動画生成開始", scale=1, elem_classes="font-size: 10px")
            cancel_button = gr.Button("キャンセル", scale=1, elem_classes="font-size: 10px")

    completion_message_output = gr.Textbox(label="生成完了メッセージ", interactive=False) #visible=False
    progress_bar = gr.Progress()
    # rendering_progress_output = gr.Textbox(label="レンダリング進行中", interactive=False)
    generated_video_preview_output = gr.Video(label="生成された動画のプレビュー")



    update_emotion_shortcuts_button.click(
        fn=update_emotion_shortcut,
        inputs=[emotion_shortcuts_input],
        outputs=[emotion_shortcuts_state]
    )

    update_actions_button.click(
        fn=update_action_shortcut,
        inputs=[actions_input],
        outputs=[actions_state]
    )


    # save_settings_button.click(
    #     fn=save_settings,
    #     inputs=[emotion_shortcuts_state, actions_state, json_file_output],
    #     outputs=[]
    # )

async def main():
    asyncio.create_task(capture_frames(VTUBE_STUDIO_URI, PLUGIN_NAME, PLUGIN_DEVELOPER))

if __name__ == "__main__":
    asyncio.run(main())
