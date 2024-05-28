import asyncio
import json
import websockets
import base64
import cv2
import numpy as np
from tkinter import *
from PIL import Image, ImageTk

from constants import VTUBE_STUDIO_URI, PLUGIN_NAME, PLUGIN_DEVELOPER

# 認証トークンをリクエストする非同期関数
async def request_token(websocket):
    request = {
        "apiName": "VTubeStudioPublicAPI",
        "apiVersion": "1.0",
        "requestID": "TokenRequestID",
        "messageType": "AuthenticationTokenRequest",
        "data": {
            "pluginName": PLUGIN_NAME,
            "pluginDeveloper": PLUGIN_DEVELOPER
        }
    }
    await websocket.send(json.dumps(request))
    response = await websocket.recv()
    json_response = json.loads(response)
    return json_response["data"].get("authenticationToken")

# 認証を行う非同期関数
async def authenticate(websocket, authentication_token):
    request = {
        "apiName": "VTubeStudioPublicAPI",
        "apiVersion": "1.0",
        "requestID": "AuthenticationRequestID",
        "messageType": "AuthenticationRequest",
        "data": {
            "pluginName": PLUGIN_NAME,
            "pluginDeveloper": PLUGIN_DEVELOPER,
            "authenticationToken": authentication_token
        }
    }
    await websocket.send(json.dumps(request))
    response = await websocket.recv()
    json_response = json.loads(response)
    return json_response["data"].get("authenticated")

# フレームデータを取得してGUIに表示する非同期関数
async def stream_character(uri, label):
    async with websockets.connect(uri) as websocket:
        print("Authentication OK.")
        token = await request_token(websocket)
        if token and await authenticate(websocket, token):
            
            request = {
                "apiName": "VTubeStudioPublicAPI",
                "apiVersion": "1.0",
                "requestID": "APIStateRequestID",
                "messageType": "APIStateRequest"
            }
            await websocket.send(json.dumps(request))
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                if data["messageType"] == "APIStateResponse" and "currentFrame" in data["data"]:
                    frame_data = data["data"]["currentFrame"]
                    frame_base64 = frame_data.split(",")[1]
                    frame_bytes = base64.b64decode(frame_base64)
                    frame_np = np.frombuffer(frame_bytes, dtype=np.uint8)
                    frame = cv2.imdecode(frame_np, cv2.IMREAD_COLOR)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    image = Image.fromarray(frame)
                    photo = ImageTk.PhotoImage(image)
                    label.config(image=photo)
                    label.image = photo  # 参照を保持
        else:
            print("Authentication failed.")


# GUIを作成し、ストリーミングを開始する
def main():
    root = Tk()
    root.title("VTube Studio Stream")
    label = Label(root)
    label.pack()
    root.attributes('-topmost', True)  # ウィンドウを最前面に設定
    root.after(0, lambda: asyncio.run(stream_character(VTUBE_STUDIO_URI, label)))
    root.mainloop()

if __name__ == "__main__":
    main()