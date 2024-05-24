import random
import csv
import os
import json
import asyncio
import json
import websockets
import base64
import cv2
import numpy as np
import gradio as gr
import shutil
import pprint

from io import BytesIO
from PIL import Image
from tkinter import filedialog

from constants import *
from vts_api import *
from main import *
from utils import *
from event_handlers import *

import asyncio
import websockets
import json
import numpy as np
import cv2
import base64

import os
from moviepy.editor import VideoFileClip


# 設定ファイルの読み込み
character_name, voice_synthesis_model, reading_speed, output_folder, bgm_file, background_video_file, emotion_shortcuts, actions, dics = load_settings(DEFAULT_SETTING_FILE)



# Gradioアプリケーションの構築
with gr.Blocks() as demo:
    gr.Markdown("# AI Tuber Test Program")

    with gr.Row():
        with gr.Column(scale=1):
            csv_file_input = gr.File(label="CSVファイル")
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
    bgm_file_input.change(on_bgm_file_change, bgm_file_input)
    background_video_file_input.change(on_background_video_file_change, background_video_file_input)
    change_output_folder_button.click(lambda: on_change_output_folder_click(output_folder_input))
    # change_output_folder_button.click(on_change_output_folder_click, None, output_folder_input)
    # show_registered_words_button.click(load_and_show_dics, outputs=[registered_words_table, dics_table])

    emotion_shortcuts_state = gr.State(emotion_shortcuts)
    actions_state = gr.State(actions)


    # 変数をコンソールに書き出す関数
    def print_variables():
        variables = {
            "CSVファイル": csv_file_input.value,
            "BGMファイル": bgm_file_input.value,
            "背景動画ファイル": background_video_file_input.value,
            "キャラクター名": character_name_input.value,
            "音声合成モデル": voice_synthesis_model_dropdown.value,
            "読み上げ速度": reading_speed_slider.value,
            "登録済み単語/文章一覧": registered_words_table.value,
            "感情ショートカット": emotion_shortcuts_input.value,
            "感情ショートカット emotion_shortcuts_state": emotion_shortcuts_state.value,
            "アクション": actions_input.value,
            "アクション actions_state": actions_state.value,
            "動画保存先": output_folder_input.value,
            "設定ファイルパス": settings_file_path_input.value,
        }
        pprint.pprint(variables)
    # 変数をコンソールに表示するボタン
    print_variables_button = gr.Button("変数をコンソールに表示")
    # イベントハンドラの設定
    print_variables_button.click(fn=print_variables)



    analyze_prepare_button = gr.Button("感情分析・動画準備開始（英語テキスト翻訳 + 翻訳後のテキストで音声合成）", elem_classes="font-size: 10px")






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



    async def main():
        uri = "ws://localhost:8001"
        plugin_name = "My Cool Plugin"
        plugin_developer = "My Name"
        asyncio.create_task(capture_frames(uri, plugin_name, plugin_developer))
        demo.launch()



    def on_change_output_folder_click():
        folder_dialog = gr.Interface(lambda x: x, "file", "file", label="動画保存先を選択してください")
        selected_folder = folder_dialog.launch(share=True)
        output_folder_input.value = selected_folder



    # 登録済み単語/文章一覧の表示
    def show_registered_words():
        # 登録済み単語/文章をファイルから読み込む
        registered_words = load_registered_words()
        return registered_words

    # 登録済み単語/文章の追加
    def add_word(registered_words, word, reading):
        # 新しい単語/文章を登録済み単語/文章に追加
        add_registered_word(word, reading)
        return show_registered_words()

    # 登録済み単語/文章の編集
    def edit_word(registered_words, index, word, reading):
        # 指定されたインデックスの単語/文章を編集
        edit_registered_word(index, word, reading)
        return show_registered_words()

    # 登録済み単語/文章の削除
    def delete_word(index):
        # 指定されたインデックスの単語/文章を削除
        delete_registered_word(index)
        return show_registered_words()

    # 設定ファイルの読み込み
    def load_settings_file(settings_file):
        # 選択された設定ファイルを読み込む
        settings = load_settings(settings_file)
        # 設定を反映（emotion_shortcuts_state、actions_stateなどを更新）
        emotion_shortcuts_state.value = settings["emotion_shortcuts"]
        actions_state.value = settings["actions"]
        # その他の設定を反映

    # 新規設定ファイルの保存
    def save_new_settings(new_settings_name):
        # 現在の設定を新規設定ファイルとして保存
        settings = {
            "emotion_shortcuts": emotion_shortcuts_state.value,
            "actions": actions_state.value,
            # その他の設定を追加
        }
        save_settings(settings, new_settings_name)


    def update_reading(subtitle, reading):
        # 読み方変更処理を実装
        pass

    def select_emotion(emotion):
        # 表情選択処理を実装
        pass

    def select_motion(motion):
        # モーション選択処理を実装
        pass

    def upload_image_video(file):
        # 画像/動画アップロード処理を実装
        pass

    def delete_image_video():
        # 画像/動画削除処理を実装
        pass

    def test_playback():
        # テスト再生処理を実装
        pass

    def update_character_position(position):
        # キャラクター位置更新処理を実装
        pass

    def update_character_size(size):
        # キャラクターサイズ更新処理を実装
        pass

    def show_expanded_preview():
        # 拡大表示処理を実装
        video_preview_expanded_output.visible = True

    def hide_expanded_preview():
        # 拡大表示非表示処理を実装
        video_preview_expanded_output.visible = False


    def start_video_generation():
        # 動画生成開始処理を実装
        pass

    def update_rendering_progress(progress):
        # レンダリング進行中の更新処理を実装
        rendering_progress_output.value = f"レンダリング進行中: {progress}%"
        progress_bar.value = progress / 100

    def cancel_video_generation():
        # 動画生成キャンセル処理を実装
        pass

    def show_completion_message(message):
        # 生成完了メッセージ表示処理を実装
        completion_message_output.value = message

    def save_generated_video(video_path):
        # 生成された動画の自動保存処理を実装
        pass

    def preview_generated_video(video_path):
        # 生成された動画のプレビュー表示処理を実装
        generated_video_preview_output.value = video_path

    def update_reading(subtitle, reading):
        # 読み方変更処理を実装
        # subtitleとreadingを使って、読み方を更新する処理を実装します
        # 例えば、subtitleをreadingに変換するAPIを呼び出すなど
        updated_reading = convert_to_reading(subtitle)
        reading_input.value = updated_reading
    def select_emotion(emotion):
        # 表情選択処理を実装
        # 選択されたemotionに基づいて、Vtuberキャラクターの表情を変更する処理を実装します
        # 例えば、Vtuberキャラクターの表情を制御するAPIを呼び出すなど
        set_character_emotion(emotion)
    def select_motion(motion):
        # モーション選択処理を実装
        # 選択されたmotionに基づいて、Vtuberキャラクターのモーションを変更する処理を実装します
        # 例えば、Vtuberキャラクターのモーションを制御するAPIを呼び出すなど
        set_character_motion(motion)
    def upload_image_video(file):
        # 画像/動画アップロード処理を実装
        # アップロードされたfileを処理し、ホワイトボードや説明画像に表示する処理を実装します
        # 例えば、fileを適切なフォルダに保存し、パスを更新するなど
        file_path = save_file(file)
        whiteboard_output.value = file_path
        explanation_image_output.value = file_path
    def delete_image_video():
        # 画像/動画削除処理を実装
        # ホワイトボードや説明画像から画像/動画を削除する処理を実装します
        # 例えば、表示中の画像/動画のパスを削除するなど
        whiteboard_output.value = None
        explanation_image_output.value = None
    def test_playback():
        # テスト再生処理を実装
        # 現在の設定で動画をテスト再生する処理を実装します
        # 例えば、字幕、Vtuberキャラクター、説明画像などを組み合わせて動画を生成し、プレビューに表示するなど
        video_path = generate_test_video()
        video_preview_output.value = video_path
    def update_character_position(position):
        # キャラクター位置更新処理を実装
        # キャラクターの位置を更新する処理を実装します
        # 例えば、Vtuberキャラクターの位置を制御するAPIを呼び出すなど
        set_character_position(position)
    def update_character_size(size):
        # キャラクターサイズ更新処理を実装
        # キャラクターのサイズを更新する処理を実装します
        # 例えば、Vtuberキャラクターのサイズを制御するAPIを呼び出すなど
        set_character_size(size)
    def show_expanded_preview():
        # 拡大表示処理を実装
        video_preview_expanded_output.visible = True
    def hide_expanded_preview():
        # 拡大表示非表示処理を実装
        video_preview_expanded_output.visible = False
    def start_video_generation():
        # 動画生成開始処理を実装
        # 動画生成のプロセスを開始する処理を実装します
        # 例えば、バックエンドで動画生成を行うAPIを呼び出すなど
        start_backend_video_generation()
    def update_rendering_progress(progress):
        # レンダリング進行中の更新処理を実装
        rendering_progress_output.value = f"レンダリング進行中: {progress}%"
        progress_bar.value = progress / 100
    def cancel_video_generation():
        # 動画生成キャンセル処理を実装
        # 動画生成のプロセスをキャンセルする処理を実装します
        # 例えば、バックエンドで動画生成をキャンセルするAPIを呼び出すなど
        cancel_backend_video_generation()
    def show_completion_message(message):
        # 生成完了メッセージ表示処理を実装
        completion_message_output.value = message
    def save_generated_video(video_path):
        # 生成された動画の自動保存処理を実装
        # 生成された動画を指定のフォルダに自動保存する処理を実装します
        # 例えば、video_pathの動画をoutput_folderに保存するなど
        save_video_to_folder(video_path, output_folder)
    def preview_generated_video(video_path):
        # 生成された動画のプレビュー表示処理を実装
        generated_video_preview_output.value = video_path




    # # ボタンを押したときの挙動 


    # change_output_folder_button.click(on_change_output_folder_click)

    # generate_video_button.click(start_video_generation, None, [rendering_progress_output, progress_bar])
    # cancel_button.click(cancel_video_generation, None, [rendering_progress_output, progress_bar])

    # update_reading_button.click(update_reading, [subtitle_input, reading_input], None)
    # emotion_dropdown.change(select_emotion, emotion_dropdown, None)
    # motion_dropdown.change(select_motion, motion_dropdown, None)
    # image_video_input.upload(upload_image_video, image_video_input, [whiteboard_output, vtuber_character_output])
    # delete_image_video_button.click(delete_image_video, None, [whiteboard_output, vtuber_character_output])
    # test_playback_button.click(test_playback, None, [video_preview_output, subtitle_output, explanation_image_output])
    # character_position_slider.change(update_character_position, character_position_slider, vtuber_character_output)
    # character_size_slider.change(update_character_size, character_size_slider, vtuber_character_output)
    # video_preview_output.click(show_expanded_preview, None, video_preview_expanded_output)
    # video_preview_expanded_output.click(hide_expanded_preview, None, video_preview_expanded_output)


    # # ボタンのクリックイベントを設定
    # show_registered_words_button.click(show_registered_words, None, registered_words_table)
    # add_word_button.click(add_word, [registered_words_table, word_input, reading_input], registered_words_table)
    # edit_word_button.click(edit_word, [registered_words_table, index_input, word_edit_input, reading_edit_input], registered_words_table)
    # delete_word_button.click(delete_word, [registered_words_table, "インデックス"], registered_words_table)
    # load_settings_button.click(load_settings_file, settings_file_dropdown, None)
    # save_new_settings_button.click(save_new_settings, new_settings_name_input, None)

    # # 感情分析・動画準備開始ボタンのクリックイベントを設定
    # analyze_prepare_button.click(analyze_and_prepare, csv_file_input, None)


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

    # generate_button.click(
    #     fn=generate_video,
    #     inputs=[
    #         csv_file_input,
    #         bgm_file_input,
    #         background_video_file_input,
    #         character_name_input,
    #         voice_synthesis_model_dropdown,
    #         emotion_shortcuts_state,
    #         actions_state,
    #         output_folder_input
    #     ],
    #     outputs=[generated_video_output],
    #     show_progress=True
    # )

    # save_settings_button.click(
    #     fn=save_settings,
    #     inputs=[emotion_shortcuts_state, actions_state, json_file_output],
    #     outputs=[]
    # )

# アプリケーションの起動
demo.launch()
