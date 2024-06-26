import obswebsocket
import json
import threading
import datetime
import yaml
import os

from obswebsocket import requests
from constants import STARTUP_SETTINGS_FILE


# 設定ファイルを読み込む
with open(STARTUP_SETTINGS_FILE, 'r', encoding='utf-8') as file:
    settings = yaml.load(file, Loader=yaml.FullLoader)


class OBSController:
    def __init__(self):
        self.websocket_uri = settings['OBS_IP']#OBSのIPアドレス
        self.port = settings['OBS_PORT']#OBSのポート
        self.password = settings['OBS_PASSWORD']#OBSのパスワード
        self.websocket = None
        self.target_scene = ""  # 監視対象のシーン名
        self.audio_thread = None
        self.stop_event = threading.Event()#ストリーム停止イベント
        self.websocket = obswebsocket.obsws(self.websocket_uri, self.port, self.password)#OBS WebSocketクライアント
        self.websocket.connect()#OBS WebSocket接続

        # # イベントを購読
        # self.websocket.register(self.on_event2)


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
        # await asyncio.sleep(0.5)
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

        # タイムスタンプを追加
        file_path = f"{file_path}-{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.png"

        # file_pathを絶対パスに変換
        file_path = os.path.abspath(file_path)

        request = requests.SaveSourceScreenshot(sourceName=source_name, imageFormat="png", imageFilePath=file_path)
        response = self.websocket.call(request)

        # print(f"response: {response}")
        # print(f"スクリーンショットを保存しました: {file_path}\n")

        return file_path


    async def get_current_program_scene(self):
        """現在のプログラムシーンを取得する

        Returns:
            str: 現在のプログラムシーン
        """
        request = requests.GetCurrentProgramScene()
        response = self.websocket.call(request)
        return response



    async def get_input_list(self):
        """インプットのリストを取得する

        Returns:
            list: インプットリスト
        """
        request = requests.GetInputList()
        response = self.websocket.call(request)
        response_data = response.datain
        input_list = []

        for input_data in response_data.get("inputs"):
            inputName = input_data.get('inputName')
            inputKind = input_data.get('inputKind')
            inputUuid = input_data.get('inputUuid')
            input_list.append((inputName, inputKind, inputUuid))  # タプルとしてリストに追加

        return input_list



    async def get_input_settings(self, inputName):
        """インプットの設定を取得する

        Args:
            inputName (str): インプット名

        Returns:
            str: インプット設定
        """
        request = requests.GetInputSettings(inputName=inputName)
        response = self.websocket.call(request)
        return response


    async def set_input_settings(self, inputName, inputSettings):
        """インプットの設定を変更する

        Args:
            inputName (str): インプット名
            inputSettings (dict): インプット設定

        Returns:
            str: インプットUUID
        """
        request = requests.SetInputSettings(
            inputName=inputName, 
            inputSettings=inputSettings, 
            overlay=True
            )
        response = self.websocket.call(request)
        # print(f"インプットの設定を変更しました: {response}")
        # return response


    async def set_scene_item_enabled(self, scene_name, scene_item_id, sceneItemEnabled):
        """シーンアイテムの有効/無効を設定する

        Args:
            scene_name (str): シーン名
            scene_item_id (int): シーンアイテムID
            enabled (bool): 有効かどうか
        """
        request = requests.SetSceneItemEnabled(sceneName=scene_name, sceneItemId=scene_item_id, sceneItemEnabled=sceneItemEnabled)
        response = self.websocket.call(request)
        return response


    async def create_input(self, scene_name, input_name, input_kind):
        """シーンにインプットを作成する

        Args:
            scene_name (str): シーン名
            input_name (str): インプット名
            input_kind (str): インプットタイプ

        Returns:
            str: インプットUUID
            int: シーンアイテムID
        """
        request = requests.CreateInput(sceneName=scene_name, inputName=input_name, inputKind=input_kind)
        response = self.websocket.call(request)
        response_data = response.datain
        input_uuid = response_data.get('inputUuid')
        scene_item_id = response_data.get('sceneItemId')
        return input_uuid, scene_item_id


    async def get_scene_item_list(self, scene_name):
        """シーンアイテムのリストを取得する

        Args:
            scene_name (str): シーン名

        Returns:
            list: シーンアイテムリスト
        """
        request = requests.GetSceneItemList(sceneName=scene_name)
        response = self.websocket.call(request)
        return response


    async def get_scene_item_id(self, scene_name, sourceName):
        """シーンアイテムのIDを取得する

        Args:
            scene_name (str): シーン名
            sourceName (str): ソース名

        Returns:
            int: シーンアイテムID
        """
        request = requests.GetSceneItemId(sceneName=scene_name, sourceName=sourceName)
        response = self.websocket.call(request)
        response_data = response.datain
        scene_item_id = response_data.get('sceneItemId')
        return scene_item_id


    async def get_scene_item_transform(self, scene_name, scene_item_id):
        """シーンアイテムのトランスフォームを取得する

        Args:
            scene_name (str): シーン名
            scene_item_id (int): シーンアイテムID

        Returns:
            dict: シーンアイテムトランスフォーム
        """
        request = requests.GetSceneItemTransform(sceneName=scene_name, sceneItemId=scene_item_id)
        response = self.websocket.call(request)
        response_data = response.datain
        scene_item_transform = response_data.get('sceneItemTransform')
        return scene_item_transform


    async def set_scene_item_transform(self, scene_name, scene_item_id, scene_item_transform):
        """シーンアイテムのトランスフォームを変更する

        Args:
            scene_name (str): シーン名
            scene_item_id (int): シーンアイテムID
            scene_item_transform (dict): シーンアイテムトランスフォーム
        """
        request = requests.SetSceneItemTransform(sceneName=scene_name, sceneItemId=scene_item_id, sceneItemTransform=scene_item_transform)
        response = self.websocket.call(request)
        return response


    # def on_event2(self, event):
    #     if event.name == "MediaInputPlaybackStarted":
    #         # input_name = event.inputName
    #         # input_uuid = event.inputUuid
    #         print(f"Media input '{event}' started playing.")
    #         # print(f"Media input '{input_name}' ({input_uuid}) started playing.")


    async def run(self):
        await self.connect()
        await self.websocket.send(json.dumps({"request-type": "GetRecordingStatus"}))
        while True:
            event = json.loads(await self.websocket.recv())
            self.on_event(event)

    def play_audio(self):
        # ここに音声再生処理を記述
        pass