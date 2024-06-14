import asyncio
import time
import cv2
import sounddevice as sd
import sys

from PIL import Image
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QUrl, QTimer, QThread, pyqtSignal
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput, QMediaDevices
from PyQt6.QtGui import QPixmap, QImage, QGuiApplication

from vts_hotkey_trigger import VTubeStudioHotkeyTrigger
from render import FrameData



class AsyncioThread(QThread):
    trigger_hotkey_signal = pyqtSignal(FrameData)  # シグナルの定義

    def __init__(self):
        super().__init__()
        self.vts_hotkey_trigger = VTubeStudioHotkeyTrigger()

    def run(self):
        self.loop = asyncio.new_event_loop()  # loop をインスタンス変数に
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()  # イベントループを継続的に実行

    def handle_signal(self, frame_data: FrameData):
        # シグナルを受信したら、非同期処理をスケジュール
        asyncio.run_coroutine_threadsafe(self.trigger_hotkey(frame_data), self.loop)

    # スロットの定義
    async def trigger_hotkey(self, frame_data:FrameData):

        # VTS　API　接続
        await self.vts_hotkey_trigger.connect()
        # print("感情ショートカット", frame_data.emotion_shortcut)
        # print("動作ショートカット", frame_data.motion_shortcut)

        # emotion_shortcut と motion_shortcut を引数のショートカットキーを渡してAPIでトリガーする処理
        if frame_data.emotion_shortcut is not None:
            await self.vts_hotkey_trigger.trigger_hotkey(frame_data.emotion_shortcut)
        if frame_data.motion_shortcut is not None:
            await self.vts_hotkey_trigger.trigger_hotkey(frame_data.motion_shortcut)



class CreateWindows(QWidget):
    def __init__(self, frame_data_list: list[FrameData]):
        super().__init__()
        
        self.asyncio_thread = AsyncioThread()
        self.asyncio_thread.trigger_hotkey_signal.connect(self.asyncio_thread.trigger_hotkey)  # シグナルとスロットの接続
        self.asyncio_thread.start()

        self.default_subtitle_image_path = r'Asset\tmpc_kh5x20.png'
        self.default_explanation_image_path = r'Asset\tmpq9fc1jl_.png'
        self.default_whiteboard_image_path = r'Asset\white_boad.png'
        self.default_video_path = r'Asset\sample_video.mp4'

        self.frame_data_list = frame_data_list

        self.desktop = QGuiApplication.screens()
        self.screen_index = 0
        self._audio_started = False  # 音声再生開始フラグ（インスタンス変数）
        self.app = QtWidgets.QApplication(sys.argv)
        self.windows = {}  # ウィンドウを格納する辞書
        self.current_frame_data = frame_data_list[0]
        self.video_capture = None  # ビデオキャプチャ用変数を追加
        self.fps = None

        # 既存の初期化コード
        self.video_shown = False  # 動画が最初に表示されたかどうかを管理するフラグ
        self.last_video_path = None  # 最後に表示した動画のパスを記憶する変数

        # 現在のフレームインデックス
        self.current_frame_index = 0

        # 利用可能なオーディオデバイスの一覧を取得
        self.character_audio_outputs = []  # キャラクター名とオーディオデバイスの対応を保持する辞書
        self.character1 = "葉加瀬あい"
        self.character2 = "らむ"
        self.select_audio_device()
        
        # QMediaPlayerにQAudioOutputを設定
        self.media_player = QMediaPlayer()
        self.set_current_audio_output(self.current_frame_index)

        # 再生させるオーディオファイルをメディアプレイヤーにセット
        audio_file_url = QUrl.fromLocalFile(frame_data_list[0].audio_file)
        self.media_player.setSource(audio_file_url)

        self.media_player.mediaStatusChanged.connect(self.handle_state_changed)  # 状態遷移を監視

        self.create()
        self.load_media(0)  # 最初の音声ファイルをロード
        # self.update_images()
        self.show_image("subtitle", self.default_subtitle_image_path, is_subtitle=True)  # 初期画像を表示
        self.show_image("explanation", self.default_explanation_image_path)



    def select_audio_device(self):
        # 利用可能なオーディオデバイスの一覧を取得
        devices = QMediaDevices.audioOutputs()

        for frame_data in self.frame_data_list:
            character_name = frame_data.character_name

            # キャラクター名に応じて target_device_name を設定
            if character_name == self.character1:
                target_device_name = "CABLE-A Input (VB-Audio Cable A)"
            elif character_name == self.character2:
                target_device_name = "CABLE-B Input (VB-Audio Cable B)"
            else:
                print(f"Unknown character name: {character_name}")  # エラーログ出力
                continue  # 次のキャラクターへ

            # デバイス一覧から検索
            selected_device = None
            for device in devices:
                if device.description() == target_device_name:
                    selected_device = device
                    print(f"🌟 オーディオデバイスを選択: {selected_device.description()}")
                    break
            if selected_device is None:
                raise ValueError("指定されたオーディオデバイスが見つかりません")
    
            # QAudioOutputを作成し、選択したオーディオデバイスを設定
            audio_output = QAudioOutput(selected_device)
            # 音量を設定
            audio_output.setVolume(0.5)  # 0.0から1.0の範囲で設定

            self.character_audio_outputs.append(audio_output)


    def set_current_audio_output(self, index):
        audio_output = self.character_audio_outputs[index]
        self.media_player.setAudioOutput(audio_output)



    def start(self):
        self.media_player.play()
        self.app.exec()
        print(f"🌟 end")


    def load_media(self, index):
        audio_file_url = QUrl.fromLocalFile(self.frame_data_list[index].audio_file)
        self.media_player.setSource(audio_file_url)        


    def handle_state_changed(self, status):
        # 音声ファイルの再生が開始した瞬間
        if status == QMediaPlayer.MediaStatus.LoadedMedia and not self._audio_started:
            self._audio_started = True  # 音声再生開始フラグを True に設定

            # 最初の再生開始時のみ画像を更新
            self.update_images()

            # シグナルを送信して、AsyncioThreadに処理を依頼
            frame_data = self.frame_data_list[self.current_frame_index]
            asyncio.run_coroutine_threadsafe(self.asyncio_thread.trigger_hotkey(frame_data), self.asyncio_thread.loop)

        # 音声ファイルの再生が終了した瞬間
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.current_frame_index += 1
            self._audio_started = False  # 音声再生開始フラグを False に設定

            # 次のフレームの情報を取得
            if self.current_frame_index < len(self.frame_data_list):
                self.set_current_audio_output(self.current_frame_index)
                self.load_media(self.current_frame_index)  # 次の音声ファイルをロード
                self.media_player.play()
            else:
                self.app.quit()  # 最後の音声ファイル再生後に終了


    def update_images(self, position=None):
        frame_data = self.frame_data_list[self.current_frame_index]

        if frame_data.explanation_image_path.endswith(('.mp4', '.avi', '.mov')):  # 動画ファイルの拡張子をチェック
            self.show_image("subtitle", frame_data.subtitle_image_path, is_subtitle=True)
            self.show_video("explanation", frame_data.explanation_image_path)
        else:
            self.show_image("subtitle", frame_data.subtitle_image_path, is_subtitle=True)
            self.show_image("explanation", frame_data.explanation_image_path)


    def show_image(self, window_name: str, image_path: str, is_subtitle: bool = False):
        # 現在の動画再生を停止
        if self.video_shown and not is_subtitle:
            self.timer.stop()
            self.video_capture.release()
            self.video_shown = False
            self.last_video_path = None

        image = QtGui.QImage(image_path)
        pixmap = QtGui.QPixmap.fromImage(image)
        if not pixmap.isNull():
            scene = self.windows[window_name].scene()
            scene.clear()  # 現在のウィンドウの画像を全てまっさらにする
            scene.addPixmap(pixmap)
                
            # 画像を中央に配置
            view_width = self.windows[window_name].width()
            view_height = self.windows[window_name].height()
            pixmap_item = scene.items()[0]
            pixmap_item.setOffset((view_width - pixmap.width()) / 2, (view_height - pixmap.height()) / 2)

            self.windows[window_name].show()
            print(f"Image shown in {window_name}: {image_path}")
        else:
            print(f"Error loading image: {image_path}")


    def show_video(self, window_name: str, video_path: str):

        if self.last_video_path == video_path:
            # print("動画は既に表示されています。")
            return

        # ホワイトボード画像の読み込みとサイズ取得
        whiteboard_image = QtGui.QImage(self.default_whiteboard_image_path)
        whiteboard_pixmap = QtGui.QPixmap.fromImage(whiteboard_image)
        whiteboard_width = whiteboard_pixmap.width()
        whiteboard_height = whiteboard_pixmap.height()
    
        self.video_capture = cv2.VideoCapture(video_path)  # OpenCV で動画ファイルを開く
        self.fps = self.video_capture.get(cv2.CAP_PROP_FPS)  # フレームレートを取得
        interval = int(1000 / self.fps)  # ミリ秒単位のインターバルを計算

        self.timer = QTimer(self)
        self.timer.timeout.connect(lambda: self.update_video_frame(window_name, whiteboard_pixmap.copy(), whiteboard_width, whiteboard_height))  # copy() を追加
        self.timer.start(interval)  # フレームレートに基づいてインターバルを設定

        self.video_shown = True  # フラグをTrueに設定
        self.last_video_path = video_path  # 最後に表示した動画のパスを記憶
        print(f"move shown in {window_name}: {video_path}")


    def update_video_frame(self, window_name, whiteboard_pixmap, whiteboard_width, whiteboard_height):
        if self.video_capture.isOpened():
            start_time = time.time()  # フレーム処理開始時間を記録
            ret, frame = self.video_capture.read()
            if ret:
                # 動画フレームのサイズ調整（ホワイトボード画像のサイズを超えないように）
                video_height, video_width, _ = frame.shape
                aspect_ratio = video_width / video_height
                new_video_width = min(whiteboard_height * aspect_ratio, whiteboard_width)  # 幅がホワイトボードを超えないように調整
                new_video_height = min(whiteboard_height, new_video_width / aspect_ratio)  # 高さがホワイトボードを超えないように調整
                frame = cv2.resize(frame, (int(new_video_width), int(new_video_height)))

                # OpenCV の BGR 形式を PyQt の RGB 形式に変換
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                height, width, channel = frame.shape
                bytesPerLine = 3 * width
                qImg = QImage(frame.data, width, height, bytesPerLine, QImage.Format.Format_RGB888)
                video_pixmap = QPixmap.fromImage(qImg)

                # ホワイトボード画像に動画を合成
                painter = QtGui.QPainter(whiteboard_pixmap)
                # 整数除算を使用して座標を整数型に変換
                x = int((whiteboard_width - new_video_width) // 2)
                y = int((whiteboard_height - new_video_height) // 2)
                painter.drawPixmap(x, y, video_pixmap)  # 中央に配置
                painter.end()

                scene = self.windows[window_name].scene()
                scene.clear()
                scene.addPixmap(whiteboard_pixmap)
            else:
                # 動画の最後まで到達したら、再度読み込み開始
                self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)  # 最初のフレームに戻る

            end_time = time.time()  # フレーム処理終了時間を記録
            elapsed_time = end_time - start_time  # 処理時間を計算
            wait_time = max(0, (1 / self.fps) - elapsed_time)  # 待機時間を計算
            time.sleep(wait_time)  # 待機


    def create(self):
        # ウィンドウの作成と初期画像の表示
        for i, window_name in enumerate(["subtitle", "explanation"]):

            # ウィンドウ作成時に画像を表示
            if window_name == "subtitle":
                image_path = self.default_subtitle_image_path  # 対応する画像パスを取得
                image_width, image_height = Image.open(image_path).size
                image_width, image_height = image_width + 10, image_height + 10
            elif window_name == "explanation":
                image_path = self.default_whiteboard_image_path  # 対応する画像パスを取得
                image_width, image_height = Image.open(image_path).size
                image_width, image_height = image_width + 10, image_height + 10

            # ウィンドウの作成
            graphics_view = QtWidgets.QGraphicsView()
            scene = QtWidgets.QGraphicsScene()
            graphics_view.setScene(scene)
            graphics_view.setWindowTitle(window_name)  # ウィンドウタイトルを設定

            # ウィンドウのサイズを画像のサイズに調整し、余白を考慮して少し大きく設定
            graphics_view.resize(image_width, image_height) # 余白を追加
            graphics_view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # 水平スクロールバーを非表示に設定
            graphics_view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # 垂直スクロールバーを非表示に設定
            scene.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(0, 255, 0)))  # 背景をグリーンバックの色に設定

            # 画面のジオメトリを取得する部分を修正
            screen_geometry = self.desktop[self.screen_index].geometry()  # 指定された画面のジオメトリを取得
            graphics_view.move(screen_geometry.left(), screen_geometry.top())  # ウィンドウを画面の左上隅に移動

            # QGraphicsViewを辞書に保存
            self.windows[window_name] = graphics_view
            time.sleep(3)
