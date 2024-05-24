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

from io import BytesIO
from PIL import Image
from settings import *
from vts_api import *
from main import *


# Gradioアプリケーションの構築
with gr.Blocks() as demo:
    gr.Markdown("# AI Tuber Test Program")

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


    # VTube Studioのキャプチャ画面を表示するコンポーネント
    vtube_studio_output = gr.Image(label="VTube Studio Output")

    async def main():
        uri = "ws://localhost:8001"
        plugin_name = "My Cool Plugin"
        plugin_developer = "My Name"
        asyncio.create_task(capture_frames(uri, plugin_name, plugin_developer))
        demo.launch()

    # ボタンを押したときの挙動 
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
