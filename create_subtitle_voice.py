import csv
import requests
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from utils import save_as_temp_file_audio


# サブテキストと読み上げを作成するクラス
class CreateSubtitleVoice:

    def __init__(self):
        self.character_lines = []

    # CSVファイルからキャラクター・セリフ情報を取得
    def load_csv_data(self, csv_file_path):
        try:
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
    def process_line(self, line, registered_words_table):
        subtitle_line = line
        # カタカナに変換　→　🌟時間かかるので検討中
        reading_line = self.translate_to_katakana(line, registered_words_table)
        return subtitle_line, reading_line


    # 辞書機能で英語テキストのカタカナ翻訳を行う関数
    def translate_to_katakana(self, line, registered_words_table):
        for word, reading in registered_words_table:
            line = line.replace(word, reading)
        return line


    # SBTV2_APIからモデル一覧を取得する関数
    # 例となるデータ
    # model_list = [
    #     ("AI-Hakase-Test2", "0", 0),
    #     ("AI-Hakase-v1", "1", 0)
    def fetch_voice_synthesis_models(self):
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


    # 音声ファイルを生成する関数
    def generate_audio(self, 
                       subtitle_line, reading_line, 
                       model_name, model_id, speaker_id, reading_speed_slider):
        # リクエストヘッダー
        headers = {
            "accept": "audio/wav"
        }

        # print(subtitle_line, reading_line, model_name, model_id, speaker_id)

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
            # 'length': 1,  # 話速（1が標準）
            'length': reading_speed_slider,  # 話速（1が標準）
            'language': 'JP',  # テキストの言語
            'auto_split': 'true',  # 自動でテキストを分割するかどうか
            'split_interval': 0.01,  # 分割した際の無音区間の長さ（秒）
            'assist_text': assist_text,  # 補助テキスト（読み上げと似た声音・感情になりやすい）
            'assist_text_weight': 1.0,  # 補助テキストの影響の強さ
            # 'style': 'Neutral',  # 音声のスタイル
            'style': 'NeutralamazinGood(onmygod)',  # 音声のスタイル
            'style_weight': 2.5,  # スタイルの強さ
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
                return temp_file_path
        except Exception as e:
            print(f"Error occurred: {str(e)}")
            return None
        
