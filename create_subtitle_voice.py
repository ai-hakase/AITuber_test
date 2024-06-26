import csv
import requests

from pydub import AudioSegment
from pydub.playback import play
from urllib.request import Request, urlopen
from urllib.parse import urlencode

from utils import save_as_temp_file_audio
from katakana_converter import KatakanaConverter
from constants import TALK_CHARACTER


# サブテキストと読み上げを作成するクラス
class CreateSubtitleVoice:

    def __init__(self):
        self.character_lines = []
        self.katakana_converter = KatakanaConverter()

    # CSVファイルからキャラクター・セリフ情報を取得
    def load_csv_data(self, csv_file_path):
        self.character_lines = []
        try:
            # ファイルを開く
            with open(csv_file_path.name, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    character = row[0]
                    line = row[1]
                    self.character_lines.append((character, line))
        except FileNotFoundError:
            print("CSVファイルが見つかりません。")
        except Exception as e:
            print(f"CSVファイルの読み込み中にエラーが発生しました: {str(e)}")
        return self.character_lines


    # セリフを処理
    def process_line(self, line):
        subtitle_line = line
        # カタカナに変換
        reading_line = self.katakana_converter.translate_to_katakana(line)
        return subtitle_line, reading_line


    # # 辞書機能で英語テキストのカタカナ翻訳を行う関数
    # def translate_to_katakana(self, line, registered_words_table):
    #     for word, reading in registered_words_table:
    #         line = line.replace(word, reading)
    #     return line


    # SBTV2_APIからモデル一覧を取得する関数
    # 例となるデータ
    # model_list = [
    #     ("AI-Hakase-Test2", "0", 0),
    #     ("AI-Hakase-v1", "1", 0)
    def fetch_voice_synthesis_models(self):
        """
        SBTV2_APIからモデル一覧を取得する関数
        """
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



    def get_selected_mode_id(self, voice_synthesis_model_dropdown, model_list_state):
        """
        音声合成モデルドロップダウンの変更イベントに関数をバインド
        
        Args:
            voice_synthesis_model_dropdown (str): 音声合成モデルドロップダウン
            model_list_state (list): モデルリストの状態
        """
        if voice_synthesis_model_dropdown:
            selected_model_tuple = next(
                    (model for model in model_list_state if model[0] == voice_synthesis_model_dropdown), None)
        else:
            print("選択されたモデルが見つかりません。")

        return selected_model_tuple


    def pitch_up_audio(self, file_path, pitch_up_strength):
        sound = AudioSegment.from_file(file_path, format="wav")

        # 半音上げる（1200セント）
        octaves = pitch_up_strength
        new_sample_rate = int(sound.frame_rate * (2.0 ** octaves))
        pitched_sound = sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate})
        pitched_sound = pitched_sound.set_frame_rate(44000)  # 元のサンプリングレートに戻す

        # 上書き保存
        pitched_sound.export(file_path, format="wav")

        return file_path


    # 音声ファイルを生成する関数
    def generate_audio(self, 
                       subtitle_line, reading_line, 
                       selected_model_tuple, reading_speed_slider, voice_style, voice_style_strength,
                       pitch_up_strength):
        """
        音声ファイルを生成する関数
        Args:
            subtitle_line (str): セリフ
            reading_line (str): 読み上げ
            selected_model_tuple (tuple): 選択されたモデルの名前、id、話者id
            reading_speed_slider (int): 読み上げ速度
            voice_style (str): 音声スタイル
        """

        # 選択されたモデルの名前、id、話者idを取得
        model_name, model_id, speaker_id = selected_model_tuple

        # グローバル変数を取得
        # global TALK_CHARACTER
        # print(f"TALK_CHARACTER: {TALK_CHARACTER}")
        
        # リクエストヘッダー
        headers = {
            "accept": "audio/wav"
        }


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
            'length': reading_speed_slider,  # 話速（1が標準）
            'language': 'JP',  # テキストの言語
            'auto_split': 'true',  # 自動でテキストを分割するかどうか
            'split_interval': 0.01,  # 分割した際の無音区間の長さ（秒）
            'assist_text': assist_text,  # 補助テキスト（読み上げと似た声音・感情になりやすい）
            'assist_text_weight': 1.0,  # 補助テキストの影響の強さ
            'style': voice_style,  # 音声のスタイル
            'style_weight': voice_style_strength,  # スタイルの強さ
            # 'reference_audio_path': r"test\AI-Hakase_Voice-26S.MP3",  # 参照オーディオパス（スタイルを音声ファイルで指定）
        }

        # パラメータをURLエンコードして、URLに追加
        url = "http://127.0.0.1:5000/voice" + "?" + urlencode(params)

        # GETリクエストを作成
        req = Request(url, headers=headers, method="GET")

        try:
            # リクエストを送信し、レスポンスを取得
            with urlopen(req) as response:
                temp_file_path = save_as_temp_file_audio(response.read())

                audio_file = self.pitch_up_audio(temp_file_path, pitch_up_strength)

                return audio_file
        except Exception as e:
            print(f"Error occurred: {str(e)}")
            return None
        
