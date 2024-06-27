import websockets
import json
import yaml
import asyncio


vts_settings_path = "vts_settings.yml"
with open(vts_settings_path, "r", encoding="utf-8") as f:
    settings = yaml.load(f, Loader=yaml.FullLoader)
    AUTHENTICATION_TOKEN = settings["AUTHENTICATION_TOKEN"]
    VTUBE_STUDIO_URI = settings["VTUBE_STUDIO_URI"]
    PLUGIN_NAME = settings["PLUGIN_NAME"]
    PLUGIN_DEVELOPER = settings["PLUGIN_DEVELOPER"]


class VTubeStudioHotkeyTrigger:
    def __init__(self):
        self.websocket_uri = VTUBE_STUDIO_URI
        self.plugin_name = PLUGIN_NAME
        self.plugin_developer = PLUGIN_DEVELOPER
        self.authentication_token = AUTHENTICATION_TOKEN
        self.websocket = None
        self.is_authenticated = False


    # 認証トークンをリクエストする非同期関数
    async def request_token(self, plugin_icon=None):
        # 認証トークンリクエストのためのリクエストボディを定義
        request = {
            "apiName": "VTubeStudioPublicAPI",  # 使用するAPIの名前
            "apiVersion": "1.0",  # APIのバージョン
            "requestID": "TokenRequestID",  # リクエストの一意識別子
            "messageType": "AuthenticationTokenRequest",  # メッセージタイプ
            "data": {  # リクエストに必要なデータ
                "pluginName": self.plugin_name,  # プラグイン名
                "pluginDeveloper": self.plugin_developer,  # 開発者名
                "pluginIcon": plugin_icon  # プラグインのアイコン（オプション）
            }
        }

        # WebSocket経由でリクエストを送信し、レスポンスを待機
        await self.websocket.send(json.dumps(request))
        response = await self.websocket.recv()
        json_response = json.loads(response)  # レスポンスをJSON形式で解析

        # 認証トークンが含まれていればそれを返し、そうでなければNoneを返す
        if json_response["messageType"] == "AuthenticationTokenResponse":
            return json_response["data"]["authenticationToken"]
        else:
            return None


    # 認証を行う非同期関数
    async def authenticate(self):
        # 認証リクエストのためのリクエストボディを定義
        request = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "AuthenticationRequestID",
            "messageType": "AuthenticationRequest",
            "data": {
                "pluginName": self.plugin_name,
                "pluginDeveloper": self.plugin_developer,
                "authenticationToken": self.authentication_token
            }
        }

        # WebSocket経由でリクエストを送信し、レスポンスを待機
        await self.websocket.send(json.dumps(request))
        response = await self.websocket.recv()
        json_response = json.loads(response)  # レスポンスをJSON形式で解析

        # 認証が成功したかどうかを判定
        if json_response["messageType"] == "AuthenticationResponse":
            return json_response["data"]["authenticated"]
        else:
            return False


    async def get_hotkeys(self, model_id=None, live2d_item_filename=None):
        if self.is_authenticated:
            request = {
                "apiName": "VTubeStudioPublicAPI",
                "apiVersion": "1.0",
                "requestID": "UniqueRequestIDLessThan64Characters",
                "messageType": "HotkeysInCurrentModelRequest",
                "data": {
                    "modelID": model_id,
                    "live2DItemFileName": live2d_item_filename
                }
            }

            if model_id is not None:
                request["data"]["modelID"] = model_id
            if live2d_item_filename is not None:
                request["data"]["live2DItemFileName"] = live2d_item_filename

            await self.websocket.send(json.dumps(request))
            response = await self.websocket.recv()
            # print(f"Received: {response}")
            # {"name":"ハート目",  "file":"expression8.exp3.json","hotkeyID":"fbf8e9e9892746c5b4ba1579ee3bea43"}のみを取得
            # pprint.pprint(response)
            response_json = json.loads(response)  # ここで JSON 形式に変換
            hotkeys = []
            if "data" in response_json and "availableHotkeys" in response_json["data"]:
                for hotkey in response_json["data"]["availableHotkeys"]:
                    hotkeys.append({"name": hotkey['name'], "file": hotkey['file'], "hotkeyID": hotkey['hotkeyID']})
                    # print(f"Name: {hotkey['name']}, File: {hotkey['file']}, HotkeyID: {hotkey['hotkeyID']}")
            return hotkeys


    async def connect(self):
        # コネクションを確立し、認証トークンをリクエスト
        self.websocket = await websockets.connect(self.websocket_uri)

        # async with self.websocket:
        # 認証トークンをリクエスト
        if self.authentication_token == "":
            self.authentication_token = await self.request_token()
            # ここでトークンをファイルに保存
            with open('vts_settings.yml', 'w', encoding='utf-8') as f:
                settings_data = {
                    "AUTHENTICATION_TOKEN": self.authentication_token,
                    "VTUBE_STUDIO_URI": self.websocket_uri,
                    "PLUGIN_NAME": self.plugin_name,
                    "PLUGIN_DEVELOPER": self.plugin_developer
                }
                yaml.dump(settings_data, f, default_flow_style=False)  # YAML形式で保存

        # 認証トークンが取得できた場合、認証処理を行う
        if self.authentication_token:
            # print(f"Token: {self.authentication_token}")
            self.is_authenticated = await self.authenticate()
            # print(f"Authenticated: {self.is_authenticated}")
        else:
            print("Token request failed")  # 認証トークンの取得に失敗した場合


    async def disconnect(self):
        await self.websocket.close()


    # ホットキーのリクエスト
    async def request_hotkeys(self):
        request = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "UniqueRequestIDForHotkeys",
            "messageType": "HotkeysInCurrentModelRequest",
            "data": {}
        }
        await self.websocket.send(json.dumps(request))
        response = await self.websocket.recv()
        response_json = json.loads(response)
        if "data" in response_json and "availableHotkeys" in response_json["data"]:
            return response_json["data"]["availableHotkeys"]
        return []


    async def trigger_hotkey(self, hotkey_id, itemInstanceID=None):
        request = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "UniqueRequestIDForTriggering",
            "messageType": "HotkeyTriggerRequest",
            "data": {
                "hotkeyID": hotkey_id,
                "itemInstanceID": itemInstanceID
            }
        }

        # print("hotkey_id", hotkey_id)

        try:
            await self.websocket.send(json.dumps(request))
            response = await self.websocket.recv()
        except websockets.exceptions.ConnectionClosedError as e:
            print("WebSocket connection closed. Attempting to reconnect...")
            await self.connect()  # 再接続を試みる
            await self.trigger_hotkey(hotkey_id)
        # print(f"Triggered Hotkey Response: {response}")

    
    async def take_screenshot(self, save_to_gallery=False, save_to_custom_path=False, custom_file_path="", transparent=False, crop_to_model=False, photo_width=1920, photo_height=1080, photo_format="png"):
        """VTube Studio のスクリーンショットを撮る関数

        Args:
            save_to_gallery (bool, optional): ギャラリーに保存するかどうか. Defaults to True.
            save_to_custom_path (bool, optional): カスタムパスに保存するかどうか. Defaults to False.
            custom_file_path (str, optional): カスタムファイルパス. Defaults to "".
            transparent (bool, optional): 透過背景にするかどうか. Defaults to False.
            crop_to_model (bool, optional): モデルの領域にクロップするかどうか. Defaults to False.
            photo_width (int, optional): 画像の幅. Defaults to 1920.
            photo_height (int, optional): 画像の高さ. Defaults to 1080.
            photo_format (str, optional): 画像の形式 ("png" or "jpg"). Defaults to "png".
        """

        if not self.is_authenticated:
            print("VTube Studio に認証されていません。")
            return

        request = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "TakeScreenshotRequest",
            "messageType": "TakeScreenshotRequest",
            "data": {
                "saveToGallery": save_to_gallery,
                "saveToCustomPath": save_to_custom_path,
                "customFilePath": custom_file_path,
                "transparent": transparent,
                "cropToModel": crop_to_model,
                "photoWidth": photo_width,
                "photoHeight": photo_height,
                "photoFormat": photo_format
            }
        }

        await self.websocket.send(json.dumps(request))

        response = await self.websocket.recv()
        print(f"Received: {response}\n")
        response_data = json.loads(response)
        if "data" in response_data and "filePath" in response_data["data"]:
            print(f"Screenshot saved to: {response_data['data']['filePath']}")
        else:
            print("Failed to take screenshot or retrieve the file path")



    async def get_available_models(self):
        if self.is_authenticated:
            request = {
                "apiName": "VTubeStudioPublicAPI",
                "apiVersion": "1.0",
                "requestID": "SomeID",
                "messageType": "AvailableModelsRequest"
            }

            await self.websocket.send(json.dumps(request))
            response = await self.websocket.recv()

            response_json = json.loads(response)  # ここで JSON 形式に変換
            print(response_json)


    async def get_current_model_id(self):
        if self.is_authenticated:
            request = {
                "apiName": "VTubeStudioPublicAPI",
                "apiVersion": "1.0",
                "requestID": "SomeID",
                "messageType": "CurrentModelRequest"
            }

            await self.websocket.send(json.dumps(request))
            response = await self.websocket.recv()

            response_json = json.loads(response)  # ここで JSON 形式に変換
            print(response_json)


    async def load_model(self, model_id):
        if self.is_authenticated:
            request = {
                "apiName": "VTubeStudioPublicAPI",
                "apiVersion": "1.0",
                "requestID": "SomeID",
                "messageType": "ModelLoadRequest",
                "data": {
                    "modelID": model_id
                }
            }

            await self.websocket.send(json.dumps(request))
            response = await self.websocket.recv()

            response_json = json.loads(response)  # ここで JSON 形式に変換
            print(response_json)


#  'numberOfTextures': 3, 'textureResolution': 4096, 'modelPosition': {'positionX': 0.025965213775634766, 'positionY': 0.4059581756591797, 'rotation': 360.0, 'size': -86.47582244873047}}}
    async def move_model(self, positionX, positionY, rotation, size):
        if self.is_authenticated:
            request = {
                "apiName": "VTubeStudioPublicAPI",
                "apiVersion": "1.0",
                "requestID": "SomeID",
                "messageType": "MoveModelRequest",
                "data": {
                    "timeInSeconds": 0,
                    "valuesAreRelativeToModel": False,
                    "positionX": positionX,
                    "positionY": positionY,
                    "rotation": rotation,
                    "size": size
                }
            }

            await self.websocket.send(json.dumps(request))
            response = await self.websocket.recv()

            response_json = json.loads(response)  # ここで JSON 形式に変換
            print(response_json)


    async def init_vts_character(self):
        """VTube Studio のキャラクターを初期化する関数"""

        await self.connect()#VTube Studio に接続

        # modelName': 'customidol', 'modelID': '2c057619e3a54268b49f1c2036f44a14
        await self.load_model("2c057619e3a54268b49f1c2036f44a14")#モデルを読み込む
        await asyncio.sleep(1)#1秒待つ

        await self.move_model(positionX=0.026, positionY=0.406, rotation=360.0, size=-86.5)#モデルを移動する
        await asyncio.sleep(1)#1秒待つ

        # {'name': 'ハカセモード1', 'file': 'AI-Hakase-v4.exp3.json', 'hotkeyID': 'f747535def7d43b29aa749290e8bd3f1'}, 
        await self.trigger_hotkey(hotkey_id="f747535def7d43b29aa749290e8bd3f1")#ハカセモードを起動する

