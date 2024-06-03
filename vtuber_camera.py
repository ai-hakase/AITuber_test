import cv2
import pyvirtualcam
import sys
import numpy as np

from PIL import Image

# VTuberCameraクラス
class VTuberCamera:

    def __init__(self):
        self.cap = cv2.VideoCapture(1)  # 数字は環境によって異なります
        # self.width = 1920
        # self.height = 1080
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # カメラからフレームをキャプチャし、仮想カメラに送信する関数
    def get_frame(self):
        for frame in self.capture_camera_frame():
            yield frame


    # カメラからフレームをキャプチャする関数
    def capture_camera_frame(self):
        cam = pyvirtualcam.Camera(width=self.width, height=self.height, fps=24)
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            # OpenCV の BGR 形式から RGB 形式に変換
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # 仮想カメラにフレームを送信
            cam.send(frame)
            cam.sleep_until_next_frame()
            yield cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # yield frame    

    # カメラを開始する関数
    def start(self):
        self.running = True
        self.get_frame()


    # ターミナルでの Ctrl+C で終了するための処理
    def stop(self, sig, frame):
        self.running = False
        # リソースを解放
        if hasattr(self, 'cap'):
            self.cap.release()
        if hasattr(self, 'cam'):
            self.cam.close()
        sys.exit(0)


    # 画像をキャプチャする関数
    def capture_image(self):
        ret, frame = self.cap.read()
        if not ret:
            return None
        
        # OpenCV の BGR 形式から RGB 形式に変換
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # numpy.ndarrayをPillowのImageオブジェクトに変換
        capture_image = Image.fromarray(frame)

        return capture_image