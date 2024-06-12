import asyncio
import os
import sys
import subprocess

from PIL import Image
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import  QWidget
from PyQt5.QtCore import Qt,QUrl , QEventLoop, QThread, pyqtSignal
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QAudioOutput, QAudioDeviceInfo, QAudio
from PyQt5.QtMultimediaWidgets import QGraphicsVideoItem, QVideoWidget
from vts_hotkey_trigger import VTubeStudioHotkeyTrigger
from render import FrameData


class CreateWindows(QWidget):
    # trigger_hotkey_signal = pyqtSignal()


    def __init__(self, frame_data_list: list[FrameData]):
        super().__init__()
        # self.trigger_hotkey_signal.connect(self.trigger_hotkey_handler)

        self.frame_data_list = frame_data_list
        self._audio_started = False  # 音声再生開始フラグ（インスタンス変数）
        self.app = QtWidgets.QApplication(sys.argv)
        self.windows = {}  # ウィンドウを格納する辞書
        self.current_frame_data = frame_data_list[0]
        self.vts_hotkey_trigger = VTubeStudioHotkeyTrigger()

        self.current_frame_index = 0

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
        self.media_player.audioOutput = self.audio_output

        self.create()
        self.load_media(0)  # 最初の音声ファイルをロード
        self.show_media("subtitle", self.frame_data_list[0].subtitle_image_path)  # 初期画像を表示
        self.show_media("explanation", self.frame_data_list[0].explanation_image_path)

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

        # timeline.create()
        # timeline.show()
        self.media_player.play()
        # 終了処理
        self.app.exec()

        print(f"🌟 end")
# sys.exit(timeline.app.exec_())




    # def handle_state_changed(self, state):
    def handle_state_changed(self, state):
        if state == QMediaPlayer.StoppedState and self.media_player.mediaStatus() == QMediaPlayer.EndOfMedia:
            # self.trigger_hotkey_signal.emit()
            self.update_images()

            if self.current_frame_index + 1 < len(self.frame_data_list):
                self.load_media(self.current_frame_index + 1)
                self.media_player.play()
            else:
                self.app.quit()




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
        self.show_media("subtitle", frame_data.subtitle_image_path)
        self.show_media("explanation", frame_data.explanation_image_path)


    def show_media(self, window_name: str, media_path: str):
        """
        メディアを表示するメソッド
        """
        if media_path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            self.show_image(window_name, media_path)
        elif media_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            self.show_video(window_name, media_path)
        else:
            print(f"Unsupported media type: {media_path}")


    def show_image(self, window_name: str, image_path: str):
        """
        画像を表示するメソッド
        """
        image = QtGui.QImage(image_path)
        pixmap = QtGui.QPixmap.fromImage(image)
        if not pixmap.isNull():
            scene = self.windows[window_name].scene()
            scene.clear()
            scene.addPixmap(pixmap)
            view_width = self.windows[window_name].width()
            view_height = self.windows[window_name].height()
            pixmap_item = scene.items()[0]
            pixmap_item.setOffset((view_width - pixmap.width()) / 2, (view_height - pixmap.height()) / 2)
            self.windows[window_name].show()
            print(f"Image shown in {window_name}: {image_path}")
        else:
            print(f"Error loading image: {image_path}")


    # def show_images(self, window_name: str, image_path: str):
    def show_image(self, window_name: str, image_path: str):
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
        """
        動画を表示するメソッド
        ホワイトボード画像[Asset\white_boad.png] を表示してからその上に動画を表示
        """
        scene = self.windows[window_name].scene()
        scene.clear()

        # # --- ホワイトボード画像の表示 ---
        # image_path = r"Asset\white_boad.png"
        # image = QtGui.QImage(image_path)
        # pixmap = QtGui.QPixmap.fromImage(image)
        # if not pixmap.isNull():
        #     scene = self.windows[window_name].scene()
        #     scene.clear()
        #     scene.addPixmap(pixmap)
        #     view_width = self.windows[window_name].width()
        #     view_height = self.windows[window_name].height()
        #     pixmap_item = scene.items()[0]
        #     pixmap_item.setOffset((view_width - pixmap.width()) / 2, (view_height - pixmap.height()) / 2)
        #     self.windows[window_name].show()
        #     print(f"Image shown in {window_name}: {image_path}")
        # else:
        #     print(f"Error loading image: {image_path}")


        # --- 動画の表示 ---
        # QGraphicsVideoItemを作成

        # h264_video_path = self.convert_to_h264(video_path)

        video_item = QGraphicsVideoItem()
        # シーンに動画アイテムを追加
        scene.addItem(video_item)
        # QMediaPlayerを作成し、動画を設定
        media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)

        # media_player.setMedia(QMediaContent(QUrl.fromLocalFile(h264_video_path)))
        media_player.setMedia(QMediaContent(QUrl.fromLocalFile(video_path)))
        media_player.setVideoOutput(video_item)  # 動画の出力をvideo_itemに設定
        print(f"video output set to video_item: {video_item}")  # video_item が設定されたか確認



        # ウィンドウのサイズを取得してvideo_itemのサイズを設定
        view_width = self.windows[window_name].width()
        view_height = self.windows[window_name].height()
        video_item.setSize(QtCore.QSizeF(view_width, view_height))
        video_item.setPos(0, 0) 
        print(f"video_item size set to: {view_width}x{view_height}")  # video_item のサイズを確認


        # デバッグ用のシグナル接続
        media_player.error.connect(lambda: print(f"Media player error: {media_player.errorString()}"))
        media_player.stateChanged.connect(lambda state: print(f"Media player state changed: {state}"))
        media_player.mediaStatusChanged.connect(lambda status: print(f"Media player status changed: {status}"))



        media_player.play()  # 動画再生
        print(f"media_player play status: {media_player.state()}")  # 再生状態を確認 (QMediaPlayer.PlayingState のはず)


        # ウィンドウを表示
        self.windows[window_name].show()
        print(f"Video shown in {window_name}: {video_path}")  # 動画表示のログ出力




    def handle_error(self, error):
        print(f"Media player error: {self.media_player.errorString()}")






            
    def create(self):
        # ウィンドウの作成と初期画像の表示
        for i, window_name in enumerate(["subtitle", "explanation"]):
            # ウィンドウ作成時に画像を表示
            if window_name == "subtitle":
                image_path = self.frame_data_list[1].subtitle_image_path  # 対応する画像パスを取得
                image_width, image_height = Image.open(image_path).size
                image_width, image_height = image_width + 10, image_height + 10
            elif window_name == "explanation":
                # image_path = self.frame_data_list[1].explanation_image_path  # 対応する画像パスを取得
                image_path = r"Asset\tmpq9fc1jl_.png"  # 対応する画像パスを取得
                image_width, image_height = Image.open(image_path).size
                image_width, image_height = image_width + 10, image_height + 10

            graphics_view = QtWidgets.QGraphicsView()
            graphics_view.setViewportUpdateMode(QtWidgets.QGraphicsView.FullViewportUpdate)  # ビューポート更新モードを設定

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

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    # create_windows = CreateWindows()
    # create_windows.create()
    # sys.exit(app.exec_())


