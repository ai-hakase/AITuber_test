# pip install gradio==4.29.0

import gradio as gr
import random
import csv
import os
import json

TALK_CHARACTER = "葉加瀬あい"
TALKING = "話し方"
WAITING = "待機"
EMOTIONS = ['joy、うれしい', 'sadness、悲しい', 'anticipation、期待', 'surprise、驚き', 'anger、怒り', 'fear、恐れ', 'disgust、嫌悪', 'trust、信頼']
DEFAULT_SETTING_FOLDER = "setting"
DEFAULT_SETTING_FILE = DEFAULT_SETTING_FOLDER+"\\default_setting.json"

def generate_video(csv_file, bgm_file, background_video_file, character_name, voice_synthesis_model, emotion_shortcuts, actions, output_folder):
    ...
    # ここに動画生成の処理を記述する
    # CSVファイルからキャラクター・セリフ情報を取得
    # セリフを1つずつ処理（読み上げ音声ファイル生成、感情分析、表情・動作のショートカットキー制御）
    # 解説画像を生成
    # レンダリング（合成音声の再生、表情・動作のショートカットキー入力、BGMと背景動画の合成）
    # 動画ファイルを出力フォルダに保存
    # 生成された動画ファイルのパスを返す
    generated_video_path = os.path.join(output_folder, "generated_video.mp4")
    return generated_video_path

# 設定ファイルを読み込む関数
def load_settings(json_file_path):
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            settings = json.load(f)
            emotion_shortcuts = {emotion: shortcut for emotion, shortcut in settings["emotion_shortcuts"].items()}
            actions = settings["actions"]
            return emotion_shortcuts, actions
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return {emotion: [] for emotion in EMOTIONS}, {}

# 設定ファイルを保存する関数
def save_settings(emotion_shortcuts, actions, json_file_output):
    settings = {
        "emotion_shortcuts": emotion_shortcuts,
        "actions": actions
    }
    with open(os.path.join(DEFAULT_SETTING_FOLDER,json_file_output+".json"), "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


# 感情のショートカットを更新する関数
def update_emotion_shortcut(emotion_shortcuts_input):
    emotion_shortcuts = {row[0]: row[1].split(", ") for row in emotion_shortcuts_input}
    save_settings(emotion_shortcuts, actions_state.value, json_file_output.value)
    return emotion_shortcuts


# アクションのショートカットを更新する関数
def update_action_shortcut(actions_input):
    actions = {}
    for row in actions_input:
        action, shortcut_name, keys = row
        if action not in actions:
            actions[action] = []
        actions[action].append([shortcut_name, keys.split(", ")])
    save_settings(emotion_shortcuts_state.value, actions, json_file_output.value)
    return actions


# アクションのショートカットを平坦化する関数
def flatten_actions(actions):
    flat_actions = []
    for action, shortcuts in actions.items():
        for shortcut in shortcuts:
            flat_actions.append([action, shortcut[0], ", ".join(shortcut[1])])
    return flat_actions


# # アクションのショートカットを更新する関数（平坦化されたデータから）
# def update_action_shortcut(flat_actions):
#     actions = {}
#     for action, shortcut_name, keys in flat_actions:
#         if action not in actions:
#             actions[action] = []
#         actions[action].append([shortcut_name, keys.split(", ")])
#     return actions


# Gradioアプリケーションの構築
with gr.Blocks() as demo:
    gr.Markdown("# AI Tuber 動画編集プログラム")

    with gr.Row():
        with gr.Column():
            csv_file_input = gr.File(label="CSVファイル")
            bgm_file_input = gr.File(label="BGMファイル")
            background_video_file_input = gr.File(label="背景動画ファイル")

        with gr.Column():
            character_name_input = gr.Textbox(label="メインキャラクター名")
            voice_synthesis_model_dropdown = gr.Dropdown(["model1", "model2", "model3"], label="音声合成モデル")

            with gr.Row():
                emotion_shortcuts_input = gr.Dataframe(
                    headers=["Emotion", "Shortcut"],
                    scale=3,
                    col_count=(2, "fixed"),
                    row_count=8,
                    type="array",
                    value=[[emotion, ", ".join(shortcut)] for emotion, shortcut in load_settings(DEFAULT_SETTING_FILE)[0].items()],
                    interactive=False
                )
                update_emotion_shortcuts_button = gr.Button("更新",scale=1)

            with gr.Row():
                actions_input = gr.Dataframe(
                    headers=["Action", "Shortcut Name", "Keys"],
                    scale=3,
                    col_count=(3, "fixed"),
                    row_count=8,
                    type="array",
                    value=flatten_actions(load_settings(DEFAULT_SETTING_FILE)[1])
                )
                update_actions_button = gr.Button("更新",scale=1)

    with gr.Row():
        json_file_input = gr.Textbox(label="設定ファイルパス", value=DEFAULT_SETTING_FILE)
        json_file_output = gr.Textbox(label="設定ファイル名")
    save_settings_button = gr.Button("設定保存")

    output_folder_input = gr.Textbox(label="動画出力フォルダ")
    generate_button = gr.Button("動画生成")
    progress_bar = gr.Progress()

    generated_video_output = gr.File(label="生成された動画")

    emotion_shortcuts_state = gr.State(load_settings(DEFAULT_SETTING_FILE)[0])
    actions_state = gr.State(load_settings(DEFAULT_SETTING_FILE)[1])

    #　ボタンを押したときの挙動 
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

    generate_button.click(
        fn=generate_video,
        inputs=[
            csv_file_input,
            bgm_file_input,
            background_video_file_input,
            character_name_input,
            voice_synthesis_model_dropdown,
            emotion_shortcuts_state,
            actions_state,
            output_folder_input
        ],
        outputs=[generated_video_output],
        show_progress=True
    )

    save_settings_button.click(
        fn=save_settings,
        inputs=[emotion_shortcuts_state, actions_state, json_file_output],
        outputs=[]
    )

demo.launch()
