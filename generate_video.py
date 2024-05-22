import os
import csv
import pyautogui
import pygame
import requests
import random
from transformers import pipeline
import torch
from config import *
from transformers import AutoModelForSequenceClassification, AutoTokenizer, LukeConfig

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using {DEVICE}")

# 感情分析モデルの準備
tokenizer = AutoTokenizer.from_pretrained("Mizuiro-sakura/luke-japanese-large-sentiment-analysis-wrime")
config = LukeConfig.from_pretrained('Mizuiro-sakura/luke-japanese-large-sentiment-analysis-wrime', output_hidden_states=True)
model = AutoModelForSequenceClassification.from_pretrained('Mizuiro-sakura/luke-japanese-large-sentiment-analysis-wrime', config=config)
model.to(DEVICE)


# キャラクターごとの最後に入力したモーションショートカットを保持する辞書
last_motion_shortcut = {
    TALK_CHARACTER: None,
    "other": None
}


# 感情分析を行う関数
def analyze_sentiment(text):
    # テキストの感情分析を行い、感情ラベルを返す
    token = tokenizer(text, truncation=True, max_length=512, padding="max_length")
    input_ids = torch.tensor(token['input_ids']).unsqueeze(0).to(DEVICE)
    attention_mask = torch.tensor(token['attention_mask']).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        output = model(input_ids, attention_mask)
    max_index = torch.argmax(output.logits)
    return EMOTIONS[max_index]


# ランダムにキーを選択する関数
def press_random_key(action_list, last_key):
    """
    同じキーを続けて押さないように、ランダムにキーを選択する関数
    """
    keys = [key for _, key in action_list]
    if len(keys) > 1 and last_key in keys:
        keys.remove(last_key)
    return random.choice(keys) if keys else last_key


# ショートカットキーをランダムに選択する関数
def get_shortcut_key(emotion_shortcuts, actions, character, line):
    """
    ショートカットキーをランダムにキーを選択する関数
    """
    if character == TALK_CHARACTER:
        # 感情分析を行い、表情と動作のショートカットキーを取得
        emotion = analyze_sentiment(line)
        emotion_shortcut = emotion_shortcuts.get(emotion)
        motion_shortcut = press_random_key(actions[TALKING], last_motion_shortcut[TALK_CHARACTER])
        last_motion_shortcut[TALK_CHARACTER] = motion_shortcut
    else:
        emotion_shortcut = emotion_shortcuts.get(emotion, ['alt', 'n'])
        motion_shortcut = press_random_key(actions[WAITING], last_motion_shortcut["other"])
        last_motion_shortcut["other"] = motion_shortcut
    return emotion_shortcut, motion_shortcut


# 動画生成の主要な処理を行う関数
def generate_video(csv_file, bgm_file, background_video_file, character_name, voice_synthesis_model, emotion_shortcuts, actions, output_folder):
    # CSVファイルからキャラクター・セリフ情報を取得
    character_lines = []
    try:
        with open(csv_file.name, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                character = row[0]
                line = row[1]
                character_lines.append((character, line))
    except FileNotFoundError:
        print("CSVファイルが見つかりません。")
        return
    except Exception as e:
        print(f"CSVファイルの読み込み中にエラーが発生しました: {str(e)}")
        return

    # 各セリフを処理
    line_data = []
    for character, line in character_lines:
        # キャラクター事にショートカットキーを選択
        emotion_shortcut, motion_shortcut = get_shortcut_key(emotion_shortcuts, actions, character, line)
        # 読み上げ音声ファイルを生成
        audio_file = generate_audio(line, character, voice_synthesis_model)
        # 解説画像を生成
        explanation_image = generate_explanation_image(line)
        # 音声ファイル、表情・動作のショートカットキー、解説画像をタプルとして保存
        line_data.append((audio_file, emotion_shortcut, motion_shortcut, explanation_image))

    # レンダリング処理
    temp_video_file = os.path.join(output_folder, 'temp_video.mp4')
    final_video_file = os.path.join(output_folder, 'generated_video.mp4')

    # 動画の録画開始
    start_recording(temp_video_file)

    # 各セリフの音声と表情・動作を再生
    for audio_file, emotion_shortcut, motion_shortcut, explanation_image in line_data:
        # 読み上げ音声の再生
        play_audio(audio_file)

        # 表情と動作のショートカットキーを入力
        pyautogui.press(emotion_shortcut)
        pyautogui.press(motion_shortcut)

        # 解説画像を表示
        display_image(explanation_image)

        # 音声の再生が終わるまで待機
        while is_audio_playing():
            pass

    # 動画の録画終了
    stop_recording()

    # 生成された解説動画、BGM、背景動画を組み合わせて最終的な動画ファイルを生成
    combine_videos(temp_video_file, bgm_file.name, background_video_file.name, final_video_file)

    # 一時ファイルやリソースを解放
    cleanup_resources()

    return final_video_file

# 音声ファイルを生成する関数（仮の実装）
def generate_audio(line, character, voice_synthesis_model):
    # Style-Bert-VITS2のAPIを使用して音声ファイルを生成
    # 実際のAPIリクエストの実装は省略
    audio_file = f'temp_audio_{character}.wav'
    return audio_file

# 解説画像を生成する関数（仮の実装）
def generate_explanation_image(line):
    # グリーンバックの画像を読み込み、解説テキストを描画
    # 実際の画像生成処理は省略
    explanation_image = r"Asset/Greenbak.png"
    return explanation_image

# 動画の録画を開始する関数（仮の実装）
def start_recording(output_file):
    # 動画の録画を開始
    # 実際の録画処理は省略
    pass

# 音声を再生する関数（仮の実装）
def play_audio(audio_file):
    # 音声ファイルを再生
    # 実際の音声再生処理は省略
    pass

# 画像を表示する関数（仮の実装）
def display_image(image_file):
    # 画像をフェイドイン・フェイドアウトで表示
    # 実際の画像表示処理は省略
    pass

# 音声の再生が終了したかを確認する関数（仮の実装）
def is_audio_playing():
    # 音声の再生状態を確認
    # 実際の再生状態の確認処理は省略
    return False

# 動画の録画を停止する関数（仮の実装）
def stop_recording():
    # 動画の録画を停止
    # 実際の録画停止処理は省略
    pass

# 動画を結合する関数（仮の実装）
def combine_videos(explanation_video, bgm_file, background_video, output_file):
    # 解説動画、BGM、背景動画を結合して最終的な動画ファイルを生成
    # 実際の動画結合処理は省略
    pass

# 一時ファイルやリソースを解放する関数（仮の実装）
def cleanup_resources():
    # 一時ファイルを削除し、リソースを解放
    # 実際の解放処理は省略
    pass