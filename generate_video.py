import os
import csv
import pyautogui
import random
import torch

from transformers import pipeline
from PIL import Image, ImageDraw, ImageFont
from constants import *
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
    reading_line = translate_to_katakana(line, registered_words_table)
    return subtitle_line, reading_line

# 辞書機能で英語テキストのカタカナ翻訳を行う関数
def translate_to_katakana(line, registered_words_table):
    for word, reading in registered_words_table:
        line = line.replace(word, reading)
    return line


# 音声ファイルを生成する関数（仮の実装）
def generate_audio(line, character, voice_synthesis_model):
    # # Style-Bert-VITS2のAPIを使用して音声ファイルを生成
    # # キャラクター名で処理を分岐
    # if character == "葉加瀬あい":
    #     audio_file = generate_audio(reading_line, character, voice_synthesis_model_dropdown)
    # else:
    #     audio_file = generate_audio(line, character, voice_synthesis_model_dropdown)
    # audio_file = f'temp_audio_{character}.wav'
    # return audio_file
    pass

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
        emotion_shortcut = emotion_shortcuts.get(emotion, ['alt', 'n'])
        motion_shortcut = press_random_key(actions[WAITING], last_motion_shortcut["other"])
        last_motion_shortcut["other"] = motion_shortcut
    return emotion_shortcut, motion_shortcut


# PILを使用してホワイトボード画像を生成
def create_whiteboard():
    # 1280x720の透明な画像を作成
    img = Image.new('RGBA', (1280, 720), (255, 255, 255, 0))
    whiteboard = 'whiteboard.png'
    # img.save(whiteboard)
    return whiteboard


# PILを使用してグリーンバック画像を生成
def generate_explanation_image():
    img = Image.new('RGB', (1280, 720), (0, 255, 0))
    explanation_image = f'explanation.png'
    # img.save(explanation_image)
    return explanation_image


def generate_subtitle(): # subtitle_line
    # 字幕用の画像を読み込む
    img = Image.open("Asset/tb00018_03_pink.png")
    # d = ImageDraw.Draw(img)
    # font = ImageFont.truetype("arial.ttf", 64)
    # # テキストのサイズを取得
    # text_width, text_height = d.textbbox((0, 0), subtitle_line, font=font)[2:]
    # # 画像のサイズを取得
    # img_width, img_height = img.size
    # # テキストを中央揃えで描画する位置を計算
    # x = (img_width - text_width) / 2
    # y = (img_height - text_height) / 2

    # # 計算された位置にテキストを描画
    # d.text((x, y), subtitle_line, fill=(255, 255, 255), font=font)
    # 画像そのものを返す
    return img


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

    # グリーンバックを透明にする処理
    # img = img.convert("RGBA")
    datas = img.getdata()

    newData = []
    for item in datas:
        # グリーンバックの色(00FF00)を透明に変換
        if item[0] == 0 and item[1] == 255 and item[2] == 0:
            newData.append((255, 255, 255, 0))
        else:
            newData.append(item)

    img.putdata(newData)
    # img.save("output.png")  # 透明化した画像を保存

    return img  # PIL Imageオブジェクトを返す

# 関数を呼び出して画像を処理
# processed_image = capture_and_process_image()
# if processed_image:
#     processed_image.show()  # 処理後の画像を表示


# プレビュー画像を生成する関数
def generate_preview_image(frame_data, vtuber_character):
    # 各フレームデータから情報を取得
    subtitle_line, reading_line, audio_file, emotion_shortcut, motion_shortcut, explanation_image, whiteboard_image, subtitleImg = frame_data

    # 背景画像を読み込む
    background = Image.open("background_video/default_video.mp4")  # 最初のフレームを画像として読み込む
    background = background.resize((400, 300))  # プレビュー画像のサイズに合わせる

    # 解説画像を読み込む
    explanation = Image.open(explanation_image)
    explanation = explanation.resize((400, 300))  # プレビュー画像のサイズに合わせる

    # Vキャラ画像を読み込む
    vtuber_img = Image.open(vtuber_character)
    vtuber_img = vtuber_img.resize((100, 150))  # Vキャラのサイズを調整

    # ホワイトボード（透明な画像）を作成
    whiteboard = Image.new('RGBA', (1280, 720), (255, 255, 255, 0))

    # プレビュー画像を作成
    preview = Image.new('RGBA', (400, 300))

    # レイヤーを合成
    preview.paste(background, (0, 0))  # 背景画像
    preview.paste(explanation, (0, 0), explanation)  # 解説画像
    preview.paste(vtuber_img, (300, 150), vtuber_img)  # Vキャラ画像

    # 字幕を追加
    draw = ImageDraw.Draw(preview)
    font = ImageFont.truetype("arial.ttf", 52)
    text_width, text_height = draw.textsize(subtitle_line, font=font)
    text_x = (400 - text_width) / 2
    text_y = 300 - text_height  # 下部に配置
    draw.text((text_x, text_y), subtitle_line, font=font, fill=(255, 255, 255))

    # プレビュー画像を保存
    preview_image_path = f'preview_image.png'
    # preview_image_path = f'preview_{frame_data}.png'
    preview.save(preview_image_path)

    return preview_image_path


# generate_preview_image()  # 処理後の画像を表示


# プレビュー画像を表示する関数（仮の実装）
def display_preview_images(preview_images):
    pass


# 動画生成の主要な処理を行う関数
def generate_video(csv_file_input, bgm_file_input, background_video_file_input, character_name_input, voice_synthesis_model_dropdown, reading_speed_slider, registered_words_table, emotion_shortcuts_state, actions_state):
   

    sample_rate, audio_data = bgm_file_input
    bgm_file = (sample_rate, audio_data.tolist())  # NumPy arrayをリストに変換

    main_character = character_name_input

    # CSVファイルからキャラクター・セリフ情報を取得
    character_lines = load_csv_data(csv_file_input)

    # 各セリフ,キャラクター事に処理
    # line_data = []

    # フレームデータのリスト
    frame_data_list = []

    # 字幕画像の生成
    subtitleImg = generate_subtitle()
    # subtitle = generate_subtitle(subtitle_line)

    # ホワイドボード画像を生成
    whiteboard_image = create_whiteboard()

    # 解説画像(グリーンバック)を生成
    explanation_image = generate_explanation_image()


    for character, line in character_lines:

        # セリフを処理
        # 元のセリフを字幕用として変数に保持します。
        # 辞書機能で英語テキストのカタカナ翻訳を行ったセリフを読み方用として変数に保持します。
        subtitle_line, reading_line = process_line(line, registered_words_table.values)
        print(subtitle_line, reading_line)

    #     # Style-Bert-VITS2のAPIを使用して、セリフのテキストの読み上げを作成読み上げ音声ファイルを生成
    #     # audio_file = generate_audio(reading_line, character, voice_synthesis_model_dropdown)
        audio_file = "test/test.mp3"

        # キャラクター事にショートカットキーを選択
        emotion_shortcut, motion_shortcut = get_shortcut_key(emotion_shortcuts_state, actions_state, character, subtitle_line)

    #     # 音声ファイル、表情・動作のショートカットキー、解説画像をタプルとして保存
    #     # line_data.append((audio_file, emotion_shortcut, motion_shortcut, explanation_image))

        # フレームデータの生成とリストへの保存
        frame_data = (subtitle_line, reading_line, audio_file, emotion_shortcut, motion_shortcut, explanation_image, whiteboard_image, subtitleImg)
        frame_data_list.append(frame_data)

    # # プレビュー画像の生成と表示
    # preview_images = []
    # for frame_data in frame_data_list:
    #     subtitle_line, reading_line, audio_file, emotion_shortcut, motion_shortcut, explanation_image, whiteboard_image, subtitleImg = frame_data
    #     vtuber_character = capture_and_process_image()
    #     preview_image = generate_preview_image(frame_data, vtuber_character)
    #     preview_images.append(preview_image)

    # # プレビュー画像を横並びで表示
    # display_preview_images(preview_images)

    # return frame_data_list






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


