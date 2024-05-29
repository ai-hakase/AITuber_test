import os
import tempfile
import csv
import pyautogui
import random
import torch
import requests
import textwrap
from urllib.request import Request, urlopen
from urllib.parse import urlencode

from transformers import pipeline
from PIL import Image, ImageDraw, ImageFont
from constants import *
from utils import *
from vts_api import *
from transformers import AutoModelForSequenceClassification, AutoTokenizer, LukeConfig

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using {DEVICE}")

# 感情分析モデルの準備
tokenizer = AutoTokenizer.from_pretrained("Mizuiro-sakura/luke-japanese-large-sentiment-analysis-wrime")
config = LukeConfig.from_pretrained('Mizuiro-sakura/luke-japanese-large-sentiment-analysis-wrime', output_hidden_states=True)
model = AutoModelForSequenceClassification.from_pretrained('Mizuiro-sakura/luke-japanese-large-sentiment-analysis-wrime', config=config)
model.to(DEVICE)


# メインキャラクター
main_character = None
subtitle_image_path = None

# キャラクターごとの最後に入力したモーションショートカットを保持する辞書
last_motion_shortcut = {
    main_character: None,
    "other": None
}

# CSVファイルからキャラクター・セリフ情報を取得
def load_csv_data(csv_file_path):
    character_lines = []
    try:
        with open(csv_file_path.name, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                character = row[0]
                line = row[1]
                character_lines.append((character, line))
    except FileNotFoundError:
        print("CSVファイルが見つかりません。")
    except Exception as e:
        print(f"CSVファイルの読み込み中にエラーが発生しました: {str(e)}")
    return character_lines


# セリフを処理
def process_line(line, registered_words_table):
    subtitle_line = line
    # カタカナに変換→時間かかるので検討中
    reading_line = translate_to_katakana(line, registered_words_table)
    return subtitle_line, reading_line
    # return subtitle_line, line#reading_line

# 辞書機能で英語テキストのカタカナ翻訳を行う関数
def translate_to_katakana(line, registered_words_table):
    for word, reading in registered_words_table:
        line = line.replace(word, reading)
    return line


# 音声ファイルを生成する関数
def generate_audio(subtitle_line, reading_line, model_name, model_id, speaker_id):
    # リクエストヘッダー
    headers = {
        "accept": "audio/wav"
    }

    print(subtitle_line, reading_line, model_name, model_id, speaker_id)

    text = reading_line
    # assist_text = None
    assist_text = subtitle_line
    # speaker_name = None
    speaker_name = model_name

    # リクエストパラメータ
    params = {
        "text": text,  # 前後の空白を削除し、改行を取り除く
        # "text": text.strip().replace("\n", ""),  # 前後の空白を削除し、改行を取り除く
        "encoding": "utf-8", # "utf-8"
        'model_id': model_id,  # 使用するモデルのID
        # 'speaker_name': speaker_name,  # 話者の名前（speaker_idより優先される）
        'speaker_id': speaker_id,  # 話者のID
        'sdp_ratio': 0.2,  # SDP（Stochastic Duration Predictor）とDP（Duration Predictor）の混合比率
        'noise': 0.6,  # サンプルノイズの割合（ランダム性を増加させる）
        'noisew': 0.8,  # SDPノイズの割合（発音の間隔のばらつきを増加させる）
        'length': 0.9,  # 話速（1が標準）
        'language': 'JP',  # テキストの言語
        'auto_split': 'true',  # 自動でテキストを分割するかどうか
        'split_interval': 1,  # 分割した際の無音区間の長さ（秒）
        'assist_text': assist_text,  # 補助テキスト（読み上げと似た声音・感情になりやすい）
        'assist_text_weight': 1.0,  # 補助テキストの影響の強さ
        'style': 'Neutral',  # 音声のスタイル
        'style_weight': 5.0,  # スタイルの強さ
        # 'reference_audio_path': r"test\AI-Hakase_Voice-26S.MP3",  # 参照オーディオパス（スタイルを音声ファイルで指定）
    }

    # パラメータをURLエンコードして、URLに追加
    url = "http://127.0.0.1:5000/voice" + "?" + urlencode(params)

    # GETリクエストを作成
    req = Request(url, headers=headers, method="GET")

    # print(url)

    try:
        # リクエストを送信し、レスポンスを取得
        with urlopen(req) as response:
            temp_file_path = save_as_temp_file_audio(response.read())
            return temp_file_path
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return None
    
    
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


# 感情分析を行い、表情と動作のショートカットキーを取得。ショートカットキーをランダムに選択する関数
def get_shortcut_key(emotion_shortcuts, actions, character, line):
    """
    ショートカットキーをランダムにキーを選択する関数
    """
    if character == main_character:
        emotion = analyze_sentiment(line)
        emotion_shortcut = emotion_shortcuts.get(emotion)
        motion_shortcut = press_random_key(actions[TALKING], last_motion_shortcut[main_character])
        last_motion_shortcut[main_character] = motion_shortcut
    else:
        emotion_shortcut = emotion_shortcuts.get('anticipation、期待')
        motion_shortcut = press_random_key(actions[WAITING], last_motion_shortcut["other"])
        last_motion_shortcut["other"] = motion_shortcut
    return emotion_shortcut, motion_shortcut


# # PILを使用してホワイトボード画像を生成
# def create_whiteboard():
#     # 1280x720の透明な画像を作成
#     img = Image.new('RGBA', (1280, 720), (255, 255, 255, 80))
#     return save_as_temp_file(img)


# PILを使用してグリーンバック画像を生成
def generate_explanation_image():
    img = Image.new('RGB', (1280, 720), (0, 255, 0))
    return save_as_temp_file(img)


def generate_subtitle(subtitle_line):
    # 字幕用の画像を読み込む
    img = Image.open("Asset/tb00018_03_pink.png")
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype("Asset/NotoSansJP-VariableFont_wght.ttf", 48)

    # 画像のサイズを取得
    img_width, img_height = img.size

    # テキストを指定された幅で改行する
    wrapped_text = textwrap.fill(subtitle_line, width=((img_width - 50) // font.getbbox("あ")[2]))

    # 改行後のテキストを2行以内に制限する
    lines = wrapped_text.split("\n")
    if len(lines) > 2:
        lines = lines[:2]
    wrapped_text = "\n".join(lines)

    # テキストのサイズを取得
    text_width, text_height = d.multiline_textbbox((0, 0), wrapped_text, font=font)[2:]

    # 文字を中央揃えにするための位置を計算
    text_x = (img_width - text_width) / 2
    text_y = (img_height - text_height) / 2

    # 一行の場合は文字の位置を上げる
    if len(lines) == 1:
        text_y -= 30  # 上に5ピクセル移動

    # 文字の描画位置を計算
    draw_x = text_x
    draw_y = text_y - text_height / 2 +140#調整

    # 計算された位置にテキストを描画
    d.multiline_text((draw_x, draw_y), wrapped_text, fill=(0, 0, 0), font=font, align='center', spacing=20)

    return save_as_temp_file(img)


def capture_and_process_image():
    # # ライブカメラからのキャプチャを開始
    # cap = cv2.VideoCapture(0)  # 0はデフォルトのカメラを指します

    # # カメラが開けたか確認
    # if not cap.isOpened():
    #     print("カメラが開けません")
    #     return None

    # # 画像を1フレームキャプチャ
    # ret, frame = cap.read()
    # if not ret:
    #     print("フレームのキャプチャに失敗しました")
    #     return None

    # # キャプチャした画像をファイルに保存
    # cv2.imwrite('capture.png', frame)

    # # カメラを解放
    # cap.release()

    # 画像をPillowで開く
    img = Image.open('test\capture.png')
    img = process_transparentize_green_back(img)
    # img.save("output.png")  # 透明化した画像を保存
    return save_as_temp_file(img)  # PIL Imageオブジェクトを返す

# 関数を呼び出して画像を処理
# processed_image = capture_and_process_image()
# if processed_image:
#     processed_image.show()  # 処理後の画像を表示


# イメージ画像をリサイズする
def resize_image_aspect_ratio(image, target_width, target_height):
    width, height = image.size
    aspect_ratio = width / height
    
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
        return image
    
    resized_image = image.resize((new_width, new_height))
    return resized_image


# 画像の周りにボーダーラインを引く
def add_border(image, border_width):
    width, height = image.size
    new_width = width + border_width * 2
    new_height = height + border_width * 2
    bordered_image = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 255))
    bordered_image.paste(image, (border_width, border_width))
    return bordered_image




# PILを使用してホワイトボード画像を生成
def create_whiteboard(preview_width, preview_height, vtuber_img_width, subtitle_img_height):
    # ホワイトボードのサイズを計算
    left_margin = 30
    right_margin = 30 + vtuber_img_width
    top_margin = 30
    bottom_margin = 30 + subtitle_img_height

    whiteboard_width = preview_width - left_margin - right_margin
    whiteboard_height = preview_height - top_margin - bottom_margin

    # ホワイトボード画像を作成
    img = Image.new('RGBA', (whiteboard_width, whiteboard_height), (255, 255, 255, 0))
    # img = Image.new('RGBA', (whiteboard_width, whiteboard_height), (255, 255, 255, 80))

    #一時ファイルに保存してパスを返す
    return save_as_temp_file(img)



# プレビュー画像を生成する関数
def generate_preview_image(background_video_file_input, explanation_image_path, whiteboard_image_path, subtitle_line, vtuber_character_path):
    
    # プレビューエリアを作成
    preview_width = 1980
    preview_height = 1080
    preview = Image.new('RGBA', (preview_width, preview_height))
    
    # 背景動画の最初のフレームを読み込む
    background = capture_first_frame(background_video_file_input)
    # if background:
    background = resize_image_aspect_ratio(background, preview_width, preview_height+100)#調整


    #画像の生成とリサイズ
    # 字幕画像を作成
    subtitle_image_path = generate_subtitle(subtitle_line)
    subtitle_img = Image.open(subtitle_image_path)
    subtitle_img = resize_image_aspect_ratio(subtitle_img, preview_width, preview_height)

    # Vキャラ画像を読み込む
    vtuber_img = Image.open(vtuber_character_path)
    # クロマキー処理
    vtuber_img = process_transparentize_green_back(vtuber_img)
    # 中央から左右の800ピクセルを切り取る
    vtuber_width, vtuber_height = vtuber_img.size
    left = (vtuber_width - 600) // 2
    top = 0
    right = left + 600
    bottom = vtuber_height
    vtuber_img = vtuber_img.crop((left, top, right, bottom))
    # リサイズ
    vtuber_img = resize_image_aspect_ratio(vtuber_img, None, 720)
    vtuber_x = preview_width - vtuber_img.width +10#調整
    vtuber_y = preview_height - vtuber_img.height -200#調整


    # ホワイトボード画像を生成
    whiteboard_subtitle_height = subtitle_img.height // 2 + 20  # 調整
    VTuber_subtitle_height = vtuber_img.width - 40  # 調整
    whiteboard_image_path = create_whiteboard(preview_width, preview_height, VTuber_subtitle_height, whiteboard_subtitle_height)
    whiteboard_img = Image.open(whiteboard_image_path)

    # 解説画像を読み込む
    explanation_img = Image.open(explanation_image_path)

    # 解説画像のアスペクト比を維持しながらホワイトボード画像に合わせてリサイズ
    explanation_img = resize_image_aspect_ratio(explanation_img, whiteboard_img.width - 40, whiteboard_img.height - 20)

    # 解説画像の周りにボーダーを追加
    explanation_img = add_border(explanation_img, 10)

    # 解説画像をホワイトボード画像の中央に配置
    explanation_x = (whiteboard_img.width - explanation_img.width) // 2
    explanation_y = (whiteboard_img.height - explanation_img.height) // 2

    # ホワイトボード画像に解説画像を合成する
    whiteboard_img.paste(explanation_img, (explanation_x, explanation_y))


    # 背景画像を合成
    preview.paste(background, (0, 0))
    # ホワイトボード画像を合成  
    whiteboard_x = 30
    whiteboard_y = 30
    preview.paste(whiteboard_img, (whiteboard_x, whiteboard_y))

    # Vキャラ画像を合成
    preview.paste(vtuber_img, (vtuber_x, vtuber_y))
    # 字幕を合成
    subtitle_x = (preview_width - subtitle_img.width) // 2
    subtitle_y = preview_height - subtitle_img.height
    preview.paste(subtitle_img, (subtitle_x, subtitle_y), mask=subtitle_img)

    # プレビュー画像を保存
    preview_image_path = save_as_temp_file(preview)

    return preview_image_path



# プレビュー画像を表示する関数（仮の実装）
def display_preview_images(preview_images):
    pass


# 動画生成の主要な処理を行う関数
def generate_video(csv_file_input, bgm_file_input, background_video_file_input, character_name_input, model_list_state, selected_model_tuple_state, reading_speed_slider, registered_words_table, emotion_shortcuts_state, actions_state):
    print(f"動画準備開始\n")

    
    # フレームデータのリスト
    global frame_data_list
    frame_data_list.clear()

    main_character = character_name_input

    # 選択された音声合成モデルの名前
    if selected_model_tuple_state:
        selected_model = selected_model_tuple_state
    else:
        selected_model = model_list_state[1]
    # 選択されたモデルの情報を取得  
    model_name, model_id, speaker_id = selected_model
    print(f"選択されたモデル: {model_name}, モデルID: {model_id}, 話者ID: {speaker_id}")

    # 字幕画像の生成
    subtitle_image_path = "Asset/tb00018_03_pink.png"

    # CSVファイルからキャラクター・セリフ情報を取得
    character_lines = load_csv_data(csv_file_input)

    # PILを使用してホワイトボード画像を生成
    # 1280x720の透明な画像を作成
    img = Image.new('RGBA', (1280, 720), (255, 255, 255, 80))
    whiteboard_image_path = save_as_temp_file(img)


    # 解説画像(グリーンバック)を生成
    explanation_image_path = r"Asset/Greenbak.png"
    # explanation_image_path = generate_explanation_image()
    # print(f"一時ファイルのパス: {explanation_image_path}")

    for character, line in character_lines:

        # セリフを処理
        # 元のセリフを字幕用として変数に保持します。
        # 辞書機能で英語テキストのカタカナ翻訳を行ったセリフを読み方用として変数に保持します。
        # subtitle_line, reading_line = line, line
        subtitle_line, reading_line = process_line(line, registered_words_table.values)
        print(f"subtitle_line: {subtitle_line},\n reading_line: {reading_line} \n")

        # Style-Bert-VITS2のAPIを使用して、セリフのテキストの読み上げを作成読み上げ音声ファイルを生成
        audio_file = generate_audio(subtitle_line, reading_line, model_name, model_id, speaker_id)
        # audio_file = "test/test.mp3"

        # キャラクター事にショートカットキーを選択
        # emotion_shortcut, motion_shortcut = get_shortcut_key(emotion_shortcuts_state, actions_state, character, subtitle_line)
        emotion_shortcut, motion_shortcut = 'alt+n', 'alt+0'

    #     # 音声ファイル、表情・動作のショートカットキー、解説画像をタプルとして保存
    #     # line_data.append((audio_file, emotion_shortcut, motion_shortcut, explanation_image))

        vtuber_character = capture_and_process_image()
        preview_image = generate_preview_image(background_video_file_input, explanation_image_path, whiteboard_image_path, subtitle_line, vtuber_character)
        # preview_image, resized_preview = generate_preview_image(background_video_file_input, explanation_image_path, whiteboard_image_path, subtitle_line, vtuber_character)
        # preview_images.append(preview_image)
        # resized_previews.append(resized_preview)

        # フレームデータの生成とリストへの保存
        # frame_data = (subtitle_line, reading_line, audio_file, emotion_shortcut, motion_shortcut, None, whiteboard_image_path, subtitle_image_path, preview_image)
        frame_data = (subtitle_line, reading_line, audio_file, emotion_shortcut, motion_shortcut, explanation_image_path, whiteboard_image_path, subtitle_image_path, preview_image, selected_model)
        frame_data_list.append(frame_data)
    # preview_images[0].show()

    # # プレビュー画像を横並びで表示
    # display_preview_images(preview_images)
    print(f"動画準備終了\n")
    subtitle_line, reading_line, audio_file, emotion_shortcut, motion_shortcut, explanation_image_path, whiteboard_image_path, subtitle_image_path, preview_image, selected_model = frame_data_list[0]
    preview_images = [frame_data[8] for frame_data in frame_data_list]

    # explanation_image_path   
    return subtitle_line, reading_line, audio_file, emotion_shortcut, motion_shortcut, None, whiteboard_image_path, subtitle_image_path, preview_images, selected_model






# # 解説画像を生成する関数（仮の実装）
# def generate_explanation_image(line):
#     # グリーンバックの画像を読み込み、解説テキストを描画
#     # 実際の画像生成処理は省略
#     explanation_image = r"Asset/Greenbak.png"
#     return explanation_image

# 音声を再生する関数（仮の実装）
def play_audio(audio_file):
    # 音声ファイルを再生
    # 実際の音声再生処理は省略
    pass

# 音声の再生が終了したかを確認する関数（仮の実装）
def is_audio_playing():
    # 音声の再生状態を確認
    # 実際の再生状態の確認処理は省略
    return False


# 画像を表示する関数（仮の実装）
def display_image(image_file):
    # 画像をフェイドイン・フェイドアウトで表示
    # 実際の画像表示処理は省略
    pass


# 動画を結合する関数（仮の実装）
def combine_videos(explanation_video, bgm_file, background_video, output_file):
    # 解説動画、BGM、背景動画を結合して最終的な動画ファイルを生成
    # 実際の動画結合処理は省略
    pass









    # # レンダリング処理
    # temp_video_file = os.path.join(output_folder, 'temp_video.mp4')
    # final_video_file = os.path.join(output_folder, 'generated_video.mp4')

    # # 動画の録画開始
    # start_recording(temp_video_file)

    # # 各セリフの音声と表情・動作を再生
    # for audio_file, emotion_shortcut, motion_shortcut, explanation_image in line_data:
    #     # 読み上げ音声の再生
    #     play_audio(audio_file)

    #     # 表情と動作のショートカットキーを入力
    #     pyautogui.press(emotion_shortcut)
    #     pyautogui.press(motion_shortcut)

    #     # 解説画像を表示
    #     display_image(explanation_image)

    #     # 音声の再生が終わるまで待機
    #     while is_audio_playing():
    #         pass

    # # 動画の録画終了
    # stop_recording()

    # # 生成された解説動画、BGM、背景動画を組み合わせて最終的な動画ファイルを生成
    # combine_videos(temp_video_file, bgm_file.name, background_video_file.name, final_video_file)

    # # 一時ファイルやリソースを解放
    # cleanup_resources()

    # return final_video_file


