# vts_hotkey_trigger.py
import sys
import os
import random
import asyncio
import websockets
import json
import pprint
import yaml

from render import FrameData




vts_settings_path = "vts_settings.yml"
with open(vts_settings_path, "r", encoding="utf-8") as f:
    settings = yaml.load(f, Loader=yaml.FullLoader)
    AUTHENTICATION_TOKEN = settings["AUTHENTICATION_TOKEN"]
    VTUBE_STUDIO_URI = settings["VTUBE_STUDIO_URI"]
    PLUGIN_NAME = settings["PLUGIN_NAME"]
    PLUGIN_DEVELOPER = settings["PLUGIN_DEVELOPER"]



# VTUBE_STUDIO_URI = VTUBE_STUDIO_URI
# PLUGIN_NAME = PLUGIN_NAME
# PLUGIN_DEVELOPER = PLUGIN_DEVELOPER
# AUTHENTICATION_TOKEN = AUTHENTICATION_TOKEN

class VTubeStudioHotkeyTrigger:
    def __init__(self):
        # vts_settings.ymlの読み込み
        # with open('vts_settings.yml', 'r', encoding='utf-8') as file:
        #     for line in file:
        #         if line.startswith('VTUBE_STUDIO_URI'):
        #             self.websocket_uri = line.split(':')[1].strip()
        #         elif line.startswith('PLUGIN_NAME'):
        #             self.plugin_name = line.split(':')[1].strip()
        #         elif line.startswith('PLUGIN_DEVELOPER'):
        #             self.plugin_developer = line.split(':')[1].strip()
        #         elif line.startswith('AUTHENTICATION_TOKEN'):
        #             self.authentication_token = line.split(':')[1].strip()

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
                "data": {}
            }
            # request = {
            #     "apiName": "VTubeStudioPublicAPI",
            #     "apiVersion": "1.0",
            #     "requestID": "GetHotkeysRequest",
            #     "messageType": "HotkeysInCurrentModelRequest"
            # }

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
            with open('vts_settings.yml', 'w') as f:
                # AUTHENTICATION_TOKEN: ""の行のみを書き換える
                f.write(f"AUTHENTICATION_TOKEN: {self.authentication_token} \n VTUBE_STUDIO_URI: {self.websocket_uri} \n PLUGIN_NAME: {self.plugin_name} \n PLUGIN_DEVELOPER: {self.plugin_developer} \n ")
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


    async def trigger_hotkey(self, hotkey_id):
        request = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "UniqueRequestIDForTriggering",
            "messageType": "HotkeyTriggerRequest",
            "data": {
                "hotkeyID": hotkey_id
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
