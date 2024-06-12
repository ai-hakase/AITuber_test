import obswebsocket
import websockets
import json
import asyncio
import threading
import datetime
import yaml
import tempfile
import base64
import os

from PIL import Image
from utils import save_as_temp_file
from obswebsocket import obsws, requests


class OBSController:
    def __init__(self):

        # 設定ファイルを読み込む
        with open('settings.yml', 'r', encoding='utf-8') as file:
            settings = yaml.load(file, Loader=yaml.FullLoader)

        # self.websocket_uri = f"ws://{settings['OBS_IP']}:{settings['OBS_PORT']}"
        self.websocket_uri = settings['OBS_IP']
        self.port = settings['OBS_PORT']
        self.password = settings['OBS_PASSWORD']
        self.websocket = None
        self.target_scene = ""  # 監視対象のシーン名
        self.audio_thread = None
        self.stop_event = threading.Event()
        self.websocket = obswebsocket.obsws(self.websocket_uri, self.port, self.password)
        self.websocket.connect()


    async def connect(self):
        # self.websocket = await websockets.connect(self.websocket_uri)


        self.websocket = obswebsocket.obsws(self.websocket_uri, self.port, self.password)
        self.websocket.connect()

        # if self.password:
        #     await self.websocket.send(json.dumps({"request-type": "Authenticate", "auth": self.password}))
        #     response = await self.websocket.recv()
            # if json.loads(response)["status"] != "ok":
            #     raise ConnectionError("OBS WebSocket authentication failed.")

    async def disconnect(self):
        if self.websocket:
            self.websocket.disconnect()
            self.websocket = None
            
    async def start_recording(self):
        await asyncio.sleep(0.5)
        request = requests.StartRecord()
        response = self.websocket.call(request)

    async def stop_recording(self):
        request = requests.StopRecord()
        output_path = self.websocket.call(request)
        return output_path

    def set_target_scene(self, scene_name):
        self.target_scene = scene_name

    def on_event(self, event):
        if event.get('update-type') == 'RecordingStarted':
            if event.get('stream-timecode'):  # 録画開始イベントかつストリーム時間がある場合
                current_scene = event.get('scene-name')
                if current_scene == self.target_scene:
                    self.stop_event.clear()
                    self.start_time = datetime.datetime.now()
                    self.audio_thread = threading.Thread(target=self.play_audio)  # ここに音声再生関数を指定
                    self.audio_thread.start()

        elif event.get('update-type') == 'RecordingStopped' and self.audio_thread is not None:
            self.stop_event.set()
            self.audio_thread.join(timeout=5)
            self.audio_thread = None








    async def get_current_scene(self):
        """現在のシーン名を取得する"""
        try:
            response = self.ws.call(requests.GetCurrentScene())
            return response.name
        except Exception as e:
            print(f"Error getting current scene: {e}")
            return None


    async def take_screenshot(self, source_name, file_path=r"tmp/screenshot"):
        """スクリーンショットを撮る

        Args:
            scene_name (str, optional): シーン名. Defaults to None.
            source_name (str, optional): ソース名. Defaults to None.

        Returns:
            str: スクリーンショットのファイルパス
        """
        await self.connect()

        # # スクリーンショットのリクエスト
        # request = obswebsocket.requests.GetSourceScreenshot(sourceName=source_name, imageFormat="png")
        # response = self.websocket.call(request)

        # # レスポンスから画像データを抽出
        # image_data_base64 = response.getImageData()

        # # パディングを追加
        # missing_padding = len(image_data_base64) % 4
        # if missing_padding:
        #     image_data_base64 += '=' * (4 - missing_padding)

        # image_data = base64.b64decode(image_data_base64)

        # # 一時ファイルに保存
        # with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
        #     temp_file.write(image_data)
        #     file_path = temp_file.name

        # タイムスタンプを追加
        file_path = f"{file_path}-{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.png"

        # file_pathを絶対パスに変換
        file_path = os.path.abspath(file_path)

        request = requests.SaveSourceScreenshot(sourceName=source_name, imageFormat="png", imageFilePath=file_path)
        response = self.websocket.call(request)

        # print(f"response: {response}")
        # print(f"スクリーンショットを保存しました: {file_path}\n")

        return file_path





    async def run(self):
        await self.connect()
        await self.websocket.send(json.dumps({"request-type": "GetRecordingStatus"}))
        while True:
            event = json.loads(await self.websocket.recv())
            self.on_event(event)

    def play_audio(self):
        # ここに音声再生処理を記述
        pass