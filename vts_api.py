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
from settings import *
from ui import *
from main import *


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
        return json_response["data"]["authenticated"]
    else:
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
        # #00FF00の色を透明にする
        green_color = np.array([0, 255, 0], dtype=np.uint8)
        mask = cv2.inRange(frame, green_color, green_color)
        mask_inv = cv2.bitwise_not(mask)
        fg = cv2.bitwise_and(frame, frame, mask=mask_inv)
        bg = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB)
        bg_inv = cv2.bitwise_not(bg)
        result = cv2.add(fg, bg_inv)

        # 処理後のフレームをPIL画像に変換
        image = Image.fromarray(result)
        # PIL画像をバイト列に変換
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        # 画像データをvtube_studio_outputに設定
        vtube_studio_output.value = img_str
        await asyncio.sleep(0.01)


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
                await update_frame(frame_generator)
        else:
            print("Token request failed")
