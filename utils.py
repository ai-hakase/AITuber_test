import os
import tempfile
import json
import cv2
import numpy as np
import shutil

from PIL import Image
from moviepy.editor import VideoFileClip

from constants import *


# def load_settings(file_path):
#     try:
#         with open(file_path, "r", encoding="utf-8") as f:
#             return json.load(f)
#     except FileNotFoundError:
#         return {}

#ディレクトリを作成
def create_directory(desired_directory):
    if desired_directory is None:
        desired_directory = os.path.abspath(os.path.dirname(__file__))  # デフォルトディレクトリ

    #ディレクトリを作成
    if not os.path.exists(desired_directory):
        os.makedirs(desired_directory)


#一時ファイルとして保存しパスを返す関数
def save_as_temp_file(img, suffix=".png", desired_directory="tmp"):
    create_directory(desired_directory)
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=desired_directory) as tmp:
        img.save(tmp.name)
        return tmp.name


#一時ファイルとして保存しパスを返す関数
def save_as_temp_file_audio(audio_data, suffix=".wav", desired_directory="tmp"):
    # 一時ファイルを作成して音声データを保存
    create_directory(desired_directory)
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=desired_directory) as temp_file:
        temp_file.write(audio_data)
        temp_file_path = temp_file.name
        return temp_file_path


# 動画を一時ファイルとして保存しパスを返す関数  
def save_as_temp_video(video_data, suffix=".mp4", desired_directory="tmp"):
    create_directory(desired_directory)
    temp_video_path = os.path.join(desired_directory, f"temp_video{suffix}")
    
    # 動画データを一時ファイルに書き出す
    with open(temp_video_path, 'wb') as f:
        f.write(video_data)
    
    # 動画を読み込む
    video = cv2.VideoCapture(temp_video_path)
    
    # 動画の元のサイズとFPSを取得
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = video.get(cv2.CAP_PROP_FPS)
    
    # 動画の出力先を設定
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_video_path, fourcc, fps, (width, height))
    
    # 動画をフレームごとに読み込み、書き出す
    while True:
        ret, frame = video.read()
        if not ret:
            break
        
        out.write(frame)
    
    # リソースを解放
    video.release()
    out.release()
    
    return temp_video_path



# tmpフォルダーの中身を全て削除する関数 
def delete_tmp_files():
    # tmp フォルダーの中身を全て削除する
    tmp_directory = 'tmp'
    for filename in os.listdir(tmp_directory):
        file_path = os.path.join(tmp_directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'ファイル {file_path} の削除中にエラーが発生しました。エラー: {e}')



# 動画の最初の部分をキャプチャーして画像として返す
def capture_first_frame(video_path):
    # 動画ファイルを開く
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("動画ファイルを開けません")
        return None

    # 最初のフレームを読み込む
    ret, frame = cap.read()
    if not ret:
        print("フレームのキャプチャに失敗しました")
        return None

    # OpenCVの画像データをPIL形式に変換
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(frame)

    # キャプチャを解放
    cap.release()
    return img


# 解説画像が動画ファイルの場合、最初のフレームを抽出して使用
def load_image_or_video(path):
    if path.lower().endswith(('.mp4', '.avi', '.mov')):
        img = capture_first_frame(path)
        if img is None:
            raise ValueError("動画からフレームを抽出できませんでした。")
    else:
        img = Image.open(path).convert("RGBA")
    return img


# グリーンバックの色(00FF00)を透明に変換
def process_transparentize_green_back(img):

    # PILイメージの場合
    if isinstance(img, Image.Image):
        # PILイメージをNumPy配列に変換
        img_array = np.array(img)
    # NumPy配列の場合
    else:
        img_array = img

    # RGB色空間からBGR色空間に変換
    img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

    # BGR色空間からHSV色空間に変換
    hsv = cv2.cvtColor(img_array, cv2.COLOR_BGR2HSV)

    # グリーンバックの色範囲を定義
    lower_green = np.array([40, 50, 50])
    upper_green = np.array([80, 255, 255])

    # グリーンバックのマスクを作成
    mask = cv2.inRange(hsv, lower_green, upper_green)

    # BGR色空間からRGBA色空間に変換
    img_array = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGBA)

    # 透明にする値の配列を作成
    transparent_color = np.zeros_like(img_array, dtype=np.uint8)
    transparent_color[:, :, 3] = 0  # アルファチャンネルを0（透明）に設定

    # マスクを4次元に拡張
    mask_4d = np.repeat(mask[:, :, np.newaxis], 4, axis=2)

    # マスクを使用して透明にする
    img_array[mask_4d > 0] = transparent_color[mask_4d > 0]

    # PILイメージの場合
    if isinstance(img, Image.Image):
        # NumPy配列をPILイメージに変換
        img = Image.fromarray(img_array)
    # NumPy配列の場合
    else:
        img = img_array

    return img


# 設定ファイルを読み込む関数
def load_settings(json_file_path):
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            settings = json.load(f)
        character_name = settings.get("character_name", "")
        voice_synthesis_model = settings.get("voice_synthesis_model", "model1")
        reading_speed = settings.get("reading_speed", 1.0)
        output_folder = settings.get("output_folder", "outputs")
        bgm_file = settings.get("bgm_file", "")
        background_video_file = settings.get("background_video_file", "")
        emotion_shortcuts = {emotion: shortcut for emotion, shortcut in settings.get("emotion_shortcuts", {}).items()}
        actions = settings.get("actions", {})
        dics = settings.get("dics", {})
        return character_name, voice_synthesis_model, reading_speed, output_folder, bgm_file, background_video_file, emotion_shortcuts, actions, dics
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return "葉加瀬あい", "model1", 1.0, "outputs", "bgm\\default_bgm.wav", "background_video\\default_video.mp4", {emotion: [] for emotion in EMOTIONS}, {}, {}


# 設定ファイルを保存する関数
def save_settings(emotion_shortcuts, actions, json_file_output):
    settings = {
        "emotion_shortcuts": emotion_shortcuts,
        "actions": actions,
        "actions": actions
    }
    with open(os.path.join(DEFAULT_SETTINGS_FOLDER,json_file_output+".json"), "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)



# BGMファイルを変換する関数
def convert_bgm_to_wav(filename):
    # ファイルがMP4, AVI, MOVファイルであるかをチェック
    if filename.endswith((".mp4", ".avi", ".mov")):
        # 元のファイルのフルパス
        video_path = os.path.join(BGM_FOLDER, filename)
        # 変換後のWAVファイルのフルパス
        wav_path = os.path.join(BGM_FOLDER, os.path.splitext(filename)[0] + ".wav")
        
        # 変換後のWAVファイルがすでに存在するかをチェック
        if not os.path.exists(wav_path):
            try:
                # 動画ファイルを読み込む
                video = VideoFileClip(video_path)
                # 音声を抽出し、WAVファイルとして保存
                video.audio.write_audiofile(wav_path)
                print(f"{filename} -> {os.path.basename(wav_path)} に変換されました。")
                
                # VideoFileClipをクローズ
                video.close()
                
                # 元の動画ファイルを削除
                os.remove(video_path)
                print(f"{filename} は削除されました。")
            except Exception as e:
                print(f"ファイル {filename} の変換中にエラーが発生しました: {e}")
        else:
            print(f"{os.path.basename(wav_path)} はすでに存在するため、スキップしました。")
        
        return os.path.splitext(filename)[0] + ".wav"
    else:
        return filename


# メディアをリサイズする関数
def resize_media(media_path, target_width, target_height):
    # メディアのタイプを判定
    media_type = 'video' if media_path.endswith(('.mp4', '.avi', '.mov')) else 'image'

    if media_type == 'image':
        # 画像の読み込み
        image = Image.open(media_path)
        
        # RGBAモードに変換
        image = image.convert("RGBA")
        
        # 画像をリサイズ
        resized_image = image.resize((target_width, target_height), Image.LANCZOS).convert("RGBA")
                
        return resized_image
    
    elif media_type == 'video':
        # 動画の読み込み
        video = cv2.VideoCapture(media_path)
        
        # 動画の元のサイズを取得
        width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # 動画の元のFPSとフレーム数を取得
        fps = video.get(cv2.CAP_PROP_FPS)
        frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        
        
        # 動画の出力先を設定
        resized_video_path = 'resized_' + os.path.basename(media_path)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(resized_video_path, fourcc, fps, (target_width, target_height))
        
        # 動画をフレームごとに読み込み、リサイズして書き出す
        while True:
            ret, frame = video.read()
            if not ret:
                break
            
            resized_frame = cv2.resize(frame, (target_width, target_height))
            out.write(resized_frame)
        
        # リソースを解放
        video.release()
        out.release()
        
        return video
    

    # 動画のアスペクト比を維持しながらリサイズ 
def resize_video_aspect_ratio(input_path, output_path, target_width=None, target_height=None):
    # 動画クリップを読み込む
    video = VideoFileClip(input_path)
    
    # 元の動画のサイズ
    width, height = video.size
    aspect_ratio = width / height

    # 新しいサイズを計算
    if target_width is not None and target_height is not None:
        target_aspect_ratio = target_width / target_height
        if aspect_ratio > target_aspect_ratio:
            new_width = target_width
            new_height = int(new_width / aspect_ratio)
        else:
            new_height = target_height
            new_width = int(new_height * aspect_ratio)
    elif target_width is not None:
        new_width = target_width
        new_height = int(new_width / aspect_ratio)
    elif target_height is not None:
        new_height = target_height
        new_width = int(new_height * aspect_ratio)
    else:
        new_width, new_height = width, height

    # 動画クリップをリサイズ
    resized_video = video.resize(newsize=(new_width, new_height))

    return resized_video



# アスペクト比を維持しながら、指定した横幅または高さに基づいてリサイズ後の寸法を計算
def resize_aspect_ratio(current_width, current_height, target_width, target_height):
    aspect_ratio = current_width / current_height
    
    if target_width is not None and target_height is not None:
        target_aspect_ratio = target_width / target_height
        if aspect_ratio > target_aspect_ratio:
            new_width = target_width
            new_height = int(new_width / aspect_ratio)
        else:
            new_height = target_height
            new_width = int(new_height * aspect_ratio)
    elif target_width is not None:
        new_width = target_width
        new_height = int(new_width / aspect_ratio)
    elif target_height is not None:
        new_height = target_height
        new_width = int(new_height * aspect_ratio)
    else:
        new_width = current_width
        new_height = current_height
    
    return new_width, new_height
