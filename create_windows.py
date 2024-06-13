import asyncio
import os
import sys
import subprocess
import cv2
import time

from PIL import Image
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import  QWidget
from PyQt5.QtCore import Qt,QUrl , QEventLoop, QThread, pyqtSignal, QTimer
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QAudioOutput, QAudioDeviceInfo, QAudio
from PyQt5.QtMultimediaWidgets import QGraphicsVideoItem, QVideoWidget
from PyQt5.QtGui import QPixmap, QImage

from vts_hotkey_trigger import VTubeStudioHotkeyTrigger
from render import FrameData


class CreateWindows(QWidget):
    # trigger_hotkey_signal = pyqtSignal()


    def __init__(self, frame_data_list: list[FrameData]):
        super().__init__()
        # self.trigger_hotkey_signal.connect(self.trigger_hotkey_handler)

        self.default_subtitle_image_path = r'Asset\tb00018_03_pink.png'
        self.default_explanation_image_path = r'Asset\tmpq9fc1jl_.png'
        self.default_whiteboard_image_path = r'Asset\white_boad.png'
        self.default_video_path = r'Asset\sample_video.mp4'

        self.frame_data_list = frame_data_list
        self._audio_started = False  # 音声再生開始フラグ（インスタンス変数）
        self.app = QtWidgets.QApplication(sys.argv)
        self.windows = {}  # ウィンドウを格納する辞書
        self.current_frame_data = frame_data_list[0]
        self.video_capture = None  # ビデオキャプチャ用変数を追加
        self.fps = None



        self.video_shown = False  # 動画が最初に表示されたかどうかを管理するフラグ
        self.last_video_path = None  # 最後に表示した動画のパスを記憶する変数

        self.current_frame_index = 0



        self.vts_hotkey_trigger = VTubeStudioHotkeyTrigger()

        # 利用可能なオーディオデバイスの一覧を取得
        devices = QAudioDeviceInfo.availableDevices(QAudio.AudioOutput)
        selected_device = None
        for device in devices:
            if device.deviceName() == "CABLE-A Input (VB-Audio Cable A)":
                selected_device = device
                break

        if selected_device is None:
            raise ValueError("指定されたオーディオデバイスが見つかりません")

        # QAudioOutputを作成し、指定されたオーディオデバイスを設定
        self.audio_output = QAudioOutput(selected_device)

        # QMediaPlayerにQAudioOutputを設定
        self.media_player = QMediaPlayer(self)
        # self.media_player.setAudioOutput(audio_output)
        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(frame_data_list[0].audio_file)))
        self.media_player.positionChanged.connect(self.update_images)

        self.media_player.stateChanged.connect(self.handle_state_changed)  # 状態遷移を監視

        # QMediaPlayerのaudioOutputプロパティにQAudioOutputを設定
        # self.media_player.audioOutput = self.audio_output

        self.create()
        self.load_media(0)  # 最初の音声ファイルをロード
        self.show_image("subtitle", self.default_subtitle_image_path, is_subtitle=True)  # 初期画像を表示
        self.show_image("explanation", self.default_explanation_image_path)

        # self.show_image("subtitle", frame_data_list[0].subtitle_image_path, is_subtitle=True)  # 初期画像を表示
        # explanation_image_path = frame_data_list[0].explanation_image_path

        # if explanation_image_path.endswith(('.mp4', '.avi', '.mov')):  # 動画ファイルの拡張子をチェック
        #     self.show_video("explanation", explanation_image_path)
        # else:
        #     self.show_image("explanation", explanation_image_path)


        # 利用可能なオーディオデバイスの一覧を表示
        # self.list_audio_devices()



    def list_audio_devices(self):
        devices = QAudioDeviceInfo.availableDevices(QAudio.AudioOutput)
        print("Available audio output devices:")
        for device in devices:
            print(f"- {device.deviceName()}")


# - DELL S2721QS (NVIDIA High Definition Audio)
# - Voicemeeter In 5 (VB-Audio Voicemeeter VAIO)
# - CABLE-B Input (VB-Audio Cable B)
# - Voicemeeter AUX Input (VB-Audio Voicemeeter VAIO)
# - Voicemeeter VAIO3 Input (VB-Audio Voicemeeter VAIO)
# - CABLE Input (VB-Audio Virtual Cable)
# - Voicemeeter In 4 (VB-Audio Voicemeeter VAIO)
# - HP LE2202x (NVIDIA High Definition Audio)
# - Voicemeeter In 2 (VB-Audio Voicemeeter VAIO)
# - Voicemeeter In 3 (VB-Audio Voicemeeter VAIO)
# - Voicemeeter Input (VB-Audio Voicemeeter VAIO)
# - Speakers (NVIDIA Broadcast)
# - スピーカー (3- JBL Quantum Stream*)
# - Voicemeeter In 1 (VB-Audio Voicemeeter VAIO)
# - CABLE-A Input (VB-Audio Cable A)
# - Voicemeeter VAIO3 Input (VB-Audio Voicemeeter VAIO)
# - Speakers (NVIDIA Broadcast)
# - Voicemeeter In 5 (VB-Audio Voicemeeter VAIO)
# - CABLE-A Input (VB-Audio Cable A)
# - Voicemeeter In 4 (VB-Audio Voicemeeter VAIO)
# - CABLE Input (VB-Audio Virtual Cable)
# - Voicemeeter Input (VB-Audio Voicemeeter VAIO)
# - Voicemeeter In 3 (VB-Audio Voicemeeter VAIO)
# - CABLE-B Input (VB-Audio Cable B)
# - DELL S2721QS (NVIDIA High Definition Audio)
# - スピーカー (3- JBL Quantum Stream*)
# - Voicemeeter AUX Input (VB-Audio Voicemeeter VAIO)
# - HP LE2202x (NVIDIA High Definition Audio)
# - Voicemeeter In 2 (VB-Audio Voicemeeter VAIO)
# - Voicemeeter In 1 (VB-Audio Voicemeeter VAIO)



    def load_media(self, index):
        # if index < len(self.frame_data_list):
        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(self.frame_data_list[index].audio_file)))
        self.current_frame_index = index
        # else:
        #     self.app.quit()  # 最後の音声ファイル再生後に終了


    def start(self):
        self.media_player.play()
        self.app.exec()
        print(f"🌟 end")


    # def handle_state_changed(self, state):
    def handle_state_changed(self, state):
        # 音声ファイルの再生が開始した瞬間
        # フラグが False である、つまりまだ一度も音声再生が開始されていないことを示します。
        if state == QMediaPlayer.PlayingState and not self._audio_started:
            print(f"🌟 音声再生開始: {self._audio_started}")
            self._audio_started = True  # 音声再生開始フラグを True に設定
            self.update_images()  # 最初の再生開始時のみ画像を更新

        # 音声ファイルの再生が終了した瞬間
        if state == QMediaPlayer.StoppedState and self.media_player.mediaStatus() == QMediaPlayer.EndOfMedia:
            print(f"🌟 音声再生終了: {self._audio_started}")
            # self.update_images()  # 初期画像を表示

            if self.current_frame_index + 1 < len(self.frame_data_list):
                self.load_media(self.current_frame_index + 1)  # 次の音声ファイルをロード
                self._audio_started = False  # 次の音声ファイル再生前にフラグをリセット
                self.media_player.play()
            else:
                self.app.quit()  # 最後の音声ファイル再生後に終了
                # sys.exit(timeline.app.exec_())


    def trigger_hotkey_handler(self):
        loop = QEventLoop()
        asyncio.ensure_future(self.trigger_hotkey(loop))
        loop.exec_()

        self.update_images()

        if self.current_frame_index + 1 < len(self.frame_data_list):
            self.load_media(self.current_frame_index + 1)
            self.media_player.play()
        else:
            self.app.quit()



    async def trigger_hotkey(self, loop):
        # emotion_shortcut と motion_shortcut を引数のショートカットキーを渡してAPIでトリガーする処理
        frame_data = self.frame_data_list[self.current_frame_index]

        if frame_data.emotion_shortcut is not None:
            await self.vts_hotkey_trigger.trigger_hotkey(frame_data.emotion_shortcut)
            print("感情ショートカット", frame_data.emotion_shortcut)
        if frame_data.motion_shortcut is not None:
            await self.vts_hotkey_trigger.trigger_hotkey(frame_data.motion_shortcut)
            print("動作ショートカット", frame_data.motion_shortcut)
        loop.quit()


    def update_images(self, position=None):
        frame_data = self.frame_data_list[self.current_frame_index]

        if frame_data.explanation_image_path.endswith(('.mp4', '.avi', '.mov')):  # 動画ファイルの拡張子をチェック
            self.show_image("subtitle", frame_data.subtitle_image_path, is_subtitle=True)
            self.show_video("explanation", frame_data.explanation_image_path)
            print(f"🌟 画像表示: {frame_data.subtitle_image_path}\n")
        else:
            self.show_image("subtitle", frame_data.subtitle_image_path, is_subtitle=True)
            self.show_image("explanation", frame_data.explanation_image_path)
            print(f"🌟 画像表示: {frame_data.subtitle_image_path}\n")


    def show_image(self, window_name: str, image_path: str, is_subtitle: bool = False):
        # 現在の動画再生を停止
        if self.video_shown and not is_subtitle:
            self.timer.stop()
            self.video_capture.release()
            self.video_shown = False
            self.last_video_path = None
            print("現在の動画再生を停止しました。")

        # print(f"windows: {self.windows}")
        # try:
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
        # except Exception as e:
        #     print(f"🌟 Error loading image: {e}")


    def show_video(self, window_name: str, video_path: str):

        if self.video_shown and self.last_video_path == video_path:
            print("動画は既に表示されています。")
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
        # self.timer.start(30)  # 約 30fps でフレーム更新

        self.video_shown = True  # フラグをTrueに設定
        self.last_video_path = video_path  # 最後に表示した動画のパスを記憶


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
                qImg = QImage(frame.data, width, height, bytesPerLine, QImage.Format_RGB888)
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

            end_time = time.time()  # フレーム処理終了時間を記録
            elapsed_time = end_time - start_time  # 処理時間を計算
            wait_time = max(0, (1 / self.fps) - elapsed_time)  # 待機時間を計算
            time.sleep(wait_time)  # 待機

            
    def create(self):
        # ウィンドウの作成と初期画像の表示
        for i, window_name in enumerate(["subtitle", "explanation"]):
            # ウィンドウ作成時に画像を表示
            if window_name == "subtitle":
                # image_path = self.default_subtitle_image_path  # 対応する画像パスを取得
                image_path = self.frame_data_list[1].subtitle_image_path  # 対応する画像パスを取得
                image_width, image_height = Image.open(image_path).size
                image_width, image_height = image_width + 10, image_height + 10
            elif window_name == "explanation":
                # image_path = self.frame_data_list[1].explanation_image_path  # 対応する画像パスを取得
                # print(f"🌟 画像表示: {image_path}=========\n")
                image_path = self.default_explanation_image_path  # 対応する画像パスを取得
                image_width, image_height = Image.open(image_path).size
                image_width, image_height = image_width + 10, image_height + 10

            graphics_view = QtWidgets.QGraphicsView()
            scene = QtWidgets.QGraphicsScene()
            graphics_view.setScene(scene)
            # ウィンドウタイトルを削除
            graphics_view.setWindowTitle(window_name)  # ウィンドウタイトルを設定
            # graphics_view.setWindowFlags(Qt.FramelessWindowHint)  # タイトルバーを削除
            # ウィンドウのサイズを画像のサイズに調整し、余白を考慮して少し大きく設定
            graphics_view.resize(image_width, image_height) # 余白を追加
            graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 水平スクロールバーを非表示に設定
            graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 垂直スクロールバーを非表示に設定
            scene.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(0, 255, 0)))  # 背景をグリーンバックの色に設定
            # QGraphicsViewを辞書に保存
            self.windows[window_name] = graphics_view 
            # self.show_image(window_name, image_path) #画像を表示