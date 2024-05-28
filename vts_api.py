import random
import csv
import os
import json
import asyncio
import json
import websockets
import base64
import cv2
import numpy as np
import gradio as gr
from io import BytesIO
from PIL import Image

from constants import VTUBE_STUDIO_URI, PLUGIN_NAME, PLUGIN_DEVELOPER



# 認証トークンをリクエストする非同期関数
async def request_token(websocket, plugin_name, plugin_developer, plugin_icon=None):
    # 認証トークンリクエストのためのリクエストボディを定義
    request = {
        "apiName": "VTubeStudioPublicAPI",
        "apiVersion": "1.0",
        "requestID": "TokenRequestID",
        "messageType": "AuthenticationTokenRequest",
        "data": {
            "pluginName": plugin_name,
            "pluginDeveloper": plugin_developer,
            "pluginIcon": plugin_icon
        }
    }

    # WebSocket経由でリクエストを送信し、レスポンスを待機
    await websocket.send(json.dumps(request))
    response = await websocket.recv()
    json_response = json.loads(response)

    # 認証トークンが含まれていればそれを返し、そうでなければNoneを返す
    if json_response["messageType"] == "AuthenticationTokenResponse":
        print("接続OK1")
        return json_response["data"]["authenticationToken"]
    else:
        return None

# 認証を行う非同期関数
async def authenticate(websocket, plugin_name, plugin_developer, authentication_token):
    # 認証リクエストのためのリクエストボディを定義
    request = {
        "apiName": "VTubeStudioPublicAPI",
        "apiVersion": "1.0",
        "requestID": "AuthenticationRequestID",
        "messageType": "AuthenticationRequest",
        "data": {
            "pluginName": plugin_name,
            "pluginDeveloper": plugin_developer,
            "authenticationToken": authentication_token
        }
    }

    # WebSocket経由でリクエストを送信し、レスポンスを待機
    await websocket.send(json.dumps(request))
    response = await websocket.recv()
    json_response = json.loads(response)

    # 認証が成功したかどうかを判定
    if json_response["messageType"] == "AuthenticationResponse":
        print("接続OK")
        return json_response["data"]["authenticated"]
    else:
        print("接続NG")
        return False

# フレームデータを取得する非同期関数
async def get_frame_data(websocket):
    while True:
        try:
            message = await websocket.recv()
            data = json.loads(message)
            if data["messageType"] == "APIStateResponse" and "currentFrame" in data["data"]:
                frame_data = data["data"]["currentFrame"]
                frame_base64 = frame_data.split(",")[1]
                frame_bytes = base64.b64decode(frame_base64)
                frame_np = np.frombuffer(frame_bytes, dtype=np.uint8)
                frame = cv2.imdecode(frame_np, cv2.IMREAD_COLOR)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                yield frame
        except Exception as e:
            print(f"Error: {e}")
            break

async def update_frame(frame_generator):
    async for frame in frame_generator:
        _, frame_bytes = cv2.imencode('.jpg', frame)
        frame_base64 = base64.b64encode(frame_bytes).decode('utf-8')
        vtube_studio_character_video = "data:image/jpeg;base64," + frame_base64
        await asyncio.sleep(0.1)  # フレームレートの調整
        print(vtube_studio_character_video)
        print(vtube_studio_character_video.value)
        return vtube_studio_character_video.value

async def capture_frames(uri, plugin_name, plugin_developer):
    async with websockets.connect(uri) as websocket:
        authentication_token = await request_token(websocket, plugin_name, plugin_developer)
        if authentication_token:
            print(f"Token: {authentication_token}")
            is_authenticated = await authenticate(websocket, plugin_name, plugin_developer, authentication_token)
            print(f"Authenticated: {is_authenticated}")
            if is_authenticated:
                request = {
                    "apiName": "VTubeStudioPublicAPI",
                    "apiVersion": "1.0",
                    "requestID": "APIStateRequestID",
                    "messageType": "APIStateRequest"
                }
                await websocket.send(json.dumps(request))
                frame_generator = get_frame_data(websocket)
                update_image = await update_frame(frame_generator)
                return update_image
        else:
            print("Token request failed")


async def set_camera_state(websocket, camera_state):
    request = {
        "apiName": "VTubeStudioPublicAPI",
        "apiVersion": "1.0",
        "requestID": "CameraControlRequestID",
        "messageType": "ChangeVideoSettingsRequest",
        "data": {
            "cameraEnabled": camera_state
        }
    }
    await websocket.send(json.dumps(request))

async def connect_to_vtube_studio(uri, plugin_name, plugin_developer):
    async with websockets.connect(uri) as websocket:
        authentication_token = await request_token(websocket, plugin_name, plugin_developer)
        if authentication_token:
            print(f"Token: {authentication_token}")
            is_authenticated = await authenticate(websocket, plugin_name, plugin_developer, authentication_token)
            print(f"Authenticated: {is_authenticated}")
            if is_authenticated:
                await set_camera_state(websocket, True)  # カメラをONにする
                while True:
                    await asyncio.sleep(1)  # 接続を維持するために待機
        else:
            print("Token request failed")

async def start_vtube_studio_connection():
    await connect_to_vtube_studio(VTUBE_STUDIO_URI, PLUGIN_NAME, PLUGIN_DEVELOPER)


async def connect_to_vtube_studio():
    async with websockets.connect(VTUBE_STUDIO_URI) as websocket:
        # VTube Studioに認証リクエストを送信
        auth_request = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "SomeID",
            "messageType": "AuthenticationRequest",
            "data": {
                "pluginName": PLUGIN_NAME,
                "pluginDeveloper": PLUGIN_DEVELOPER
            }
        }
        await websocket.send(json.dumps(auth_request))
        
        # VTube Studioからの応答を待機
        response = await websocket.recv()
        print(f"Received response: {response}")
        
        # VTube Studioからの映像データを取得するリクエストを送信
        request = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "SomeID",
            "messageType": "CurrentModelRequest"
        }
        await websocket.send(json.dumps(request))
        
        # VTube Studioからの映像データを受信し、HTMLに埋め込む
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            if data["messageType"] == "CurrentModelResponse" and "modelImage" in data["data"]:
                image_data = data["data"]["modelImage"]
                base64_data = image_data.split(",")[1]
                frame_data = base64.b64decode(base64_data)
                with open("current_frame.jpg", "wb") as f:
                    f.write(frame_data)
                break

