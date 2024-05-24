# import asyncio
# import json
# import websockets
# import base64
# import cv2
# import numpy as np
# import tkinter as tk
# from PIL import Image, ImageTk

# # 認証トークンをリクエストする非同期関数
# async def request_token(websocket, plugin_name, plugin_developer, plugin_icon=None):
#     # 認証トークンリクエストのためのリクエストボディを定義
#     request = {
#         "apiName": "VTubeStudioPublicAPI",
#         "apiVersion": "1.0",
#         "requestID": "TokenRequestID",
#         "messageType": "AuthenticationTokenRequest",
#         "data": {
#             "pluginName": plugin_name,
#             "pluginDeveloper": plugin_developer,
#             "pluginIcon": plugin_icon
#         }
#     }

#     # WebSocket経由でリクエストを送信し、レスポンスを待機
#     await websocket.send(json.dumps(request))
#     response = await websocket.recv()
#     json_response = json.loads(response)

#     # 認証トークンが含まれていればそれを返し、そうでなければNoneを返す
#     if json_response["messageType"] == "AuthenticationTokenResponse":
#         return json_response["data"]["authenticationToken"]
#     else:
#         return None

# # 認証を行う非同期関数
# async def authenticate(websocket, plugin_name, plugin_developer, authentication_token):
#     # 認証リクエストのためのリクエストボディを定義
#     request = {
#         "apiName": "VTubeStudioPublicAPI",
#         "apiVersion": "1.0",
#         "requestID": "AuthenticationRequestID",
#         "messageType": "AuthenticationRequest",
#         "data": {
#             "pluginName": plugin_name,
#             "pluginDeveloper": plugin_developer,
#             "authenticationToken": authentication_token
#         }
#     }

#     # WebSocket経由でリクエストを送信し、レスポンスを待機
#     await websocket.send(json.dumps(request))
#     response = await websocket.recv()
#     json_response = json.loads(response)

#     # 認証が成功したかどうかを判定
#     if json_response["messageType"] == "AuthenticationResponse":
#         return json_response["data"]["authenticated"]
#     else:
#         return False

# # フレームデータを取得する非同期関数
# async def get_frame_data(websocket):
#     while True:
#         try:
#             message = await websocket.recv()
#             data = json.loads(message)
#             if data["messageType"] == "APIStateResponse" and "currentFrame" in data["data"]:
#                 frame_data = data["data"]["currentFrame"]
#                 frame_base64 = frame_data.split(",")[1]
#                 frame_bytes = base64.b64decode(frame_base64)
#                 frame_np = np.frombuffer(frame_bytes, dtype=np.uint8)
#                 frame = cv2.imdecode(frame_np, cv2.IMREAD_COLOR)
#                 frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#                 yield frame
#         except Exception as e:
#             print(f"Error: {e}")
#             break

# # フレームを表示するGUIウィンドウを作成する関数
# def create_gui(frame_generator):
#     root = tk.Tk()
#     root.title("VTube Studio Screen Capture")

#     label = tk.Label(root)
#     label.pack()

#     async def update_frame():
#         async for frame in frame_generator:
#             image = Image.fromarray(frame)
#             photo = ImageTk.PhotoImage(image)
#             label.config(image=photo)
#             label.image = photo
#             await asyncio.sleep(0.01)

#     asyncio.create_task(update_frame())
#     root.mainloop()

# # メイン関数
# async def main():
#     uri = "ws://localhost:8001"
#     plugin_name = "My Cool Plugin"
#     plugin_developer = "My Name"

#     async with websockets.connect(uri) as websocket:
#         # 認証トークンをリクエスト
#         authentication_token = await request_token(websocket, plugin_name, plugin_developer)

#         if authentication_token:
#             print(f"Token: {authentication_token}")
#             # 認証処理を行う
#             is_authenticated = await authenticate(websocket, plugin_name, plugin_developer, authentication_token)
#             print(f"Authenticated: {is_authenticated}")

#             if is_authenticated:
#                 # APIステートリクエストを送信
#                 request = {
#                     "apiName": "VTubeStudioPublicAPI",
#                     "apiVersion": "1.0",
#                     "requestID": "APIStateRequestID",
#                     "messageType": "APIStateRequest"
#                 }
#                 await websocket.send(json.dumps(request))

#                 # フレームデータを取得するジェネレータを作成
#                 frame_generator = get_frame_data(websocket)
#                 # GUIウィンドウを作成し、フレームを表示
#                 create_gui(frame_generator)
#         else:
#             print("Token request failed")

# # イベントループを開始し、メイン関数を実行
# asyncio.get_event_loop().run_until_complete(main())