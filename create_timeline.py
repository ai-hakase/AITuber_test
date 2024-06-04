import threading
import sys
import os
import random
import asyncio

from PIL import Image
from moviepy.editor import AudioFileClip, ImageClip, VideoFileClip, CompositeVideoClip, concatenate_videoclips, ColorClip
from render import FrameData
from vts_hotkey_trigger import VTubeStudioHotkeyTrigger


# 一つ上の階層のパスを取得
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

from vtuber_camera import VTuberCamera
from utils import *


# タイムラインの作成
class Timeline:
    def __init__(self, frame_data_list: list[FrameData], output_file: str, background_video_path: str):
        self.vtuber_camera = VTuberCamera()
        self.hotkey_trigger = VTubeStudioHotkeyTrigger()

        # フレームのクリップを格納するリスト
        self.final_clip = None
        self.frame_clips = []

        self.background_video_path = background_video_path

        # ストリーミング中の映像を録画するためのクリップリスト
        self.streaming_clips = []
        self.hotkeys = []

        # ショートカットキーのIDを格納するリスト
        self.emotion_shortcut_keys = []
        self.motion_shortcut_keys = []
        # 既存の初期化コード
        self.previous_emotion_shortcut = None
        self.previous_motion_shortcut = None

        self.frame_data_list = frame_data_list
        self.output_file = output_file

        self.background_video_start_time = 0# 背景動画の再生時間
        self.explanation_video_start_time = 0# 解説動画の再生時間
        self.previous_video_duration = 0# 前の動画の長さ

    # タイムラインの作成
    async def create(self):

        await self.hotkey_trigger.connect()
        self.hotkeys = await self.hotkey_trigger.get_hotkeys()

        for frame_data in self.frame_data_list:
            await self._add_media_to_timeline(frame_data)

        await self.hotkey_trigger.disconnect()

        # frame_clips = [frame_data[11] for frame_data in self.frame_data_list]
        # フレームのクリップを連結して最終的な動画を作成
        self.final_clip = concatenate_videoclips(self.frame_clips)

        # 動画の再生とショートカットキーの送信を別スレッドで開始
        # threading.Thread(target=self.play_video).start()

        # self.play_video()
    

    # アスペクト比を維持しながら、指定した横幅または高さに基づいてリサイズ後の寸法を計算
    def resize_aspect_ratio(self, current_width, current_height, target_width, target_height):

        aspect_ratio = current_width / current_height
        
        if target_width is not None and target_height is not None:
            target_aspect_ratio = target_width / target_height
            if aspect_ratio > target_aspect_ratio:
                new_width = target_width
                new_height = int(new_width / aspect_ratio)
            else:
                new_height = target_height
                new_width = int(new_height * aspect_ratio)
        elif target_width is not None:
            new_width = target_width
            new_height = int(new_width / aspect_ratio)
        elif target_height is not None:
            new_height = target_height
            new_width = int(new_height * aspect_ratio)
        else:
            new_width = current_width
            new_height = current_height
        
        return new_width, new_height


    # ショートカットキーを押す関数
    def press_shortcut(self, emotion_shortcut, motion_shortcut):
        # 表情のショートカットキーを送信
        print(f"Pressing emotion shortcut: {emotion_shortcut}")
        for key in emotion_shortcut.split('+'):
            print(f"Press {key}")
        for key in reversed(emotion_shortcut.split('+')):
            print(f"Release {key}")

        # 動作のショートカットキーを送信
        print(f"Pressing motion shortcut: {motion_shortcut}")
        for key in motion_shortcut.split('+'):
            print(f"Press {key}")
        for key in reversed(motion_shortcut.split('+')):
            print(f"Release {key}")


    # 動画の切り替え時にショートカットキーを押す
    def on_clip_change(self, t):
        # フレームデータリストから表情と動作のショートカットキーを取得
        emotion_shortcut = self.frame_data_list[self.frame_index].emotion_shortcut
        motion_shortcut = self.frame_data_list[self.frame_index].motion_shortcut
        self.press_shortcut(emotion_shortcut,motion_shortcut)  # 表情の切り替え時にショートカットキーを押す

    # フェードイン・フェードアウトの処理
    def _fade_opacity(self, t, duration):
        fade_duration = 0.5  # フェードイン・フェードアウトの時間を調整
        if t < fade_duration:
            opacity = t / fade_duration
        elif t > duration - fade_duration:
            opacity = (duration - t) / fade_duration
        else:
            opacity = 1
        print(f"t: {t}, duration: {duration}, opacity: {opacity}")  # デバッグプリント
        return opacity

     # フェードイン・フェードアウトの時間を調整
    def _fade_clip(self, clip, duration, fade_duration=0.5):
        clip = clip.crossfadein(fade_duration).crossfadeout(fade_duration)
        return clip



    # 黒い枠をつける関数
    def _add_black_frame(self, explanation_clip):
        # 黒い枠を作成
        border_width = 5
        # border_color = (0, 0, 0)  # 黒色（RGB）
        # レインボークカラーの辞書
        border_colors = {
            'black': (0, 0, 0),       # 黒
            'red': (255, 0, 0),       # 赤
            'orange': (255, 165, 0),  # オレンジ
            'yellow': (255, 255, 0),  # 黄
            'green': (0, 128, 0),     # 緑
            'blue': (0, 0, 255),      # 青
            'indigo': (75, 0, 130),   # インディゴ
            'violet': (238, 130, 238) # バイオレット
        }
        selected_color = 'black'  # 使用する色を変数で指定
        border_clip = ColorClip(size=(explanation_clip.w + 2 * border_width, explanation_clip.h + 2 * border_width),
                                color=border_colors['violet']).set_duration(explanation_clip.duration)

        # 元のクリップと黒い枠を合成
        final_clip = CompositeVideoClip([border_clip,
                                        explanation_clip.set_position((border_width, border_width))],
                                        size=border_clip.size)
        return final_clip
    

    def _add_streaming_video(self, audio_duration):
        # 音声ファイルが流れている間、ストリーミング中の映像を録画
        for t in range(int(audio_duration * 24)):  # 24fpsを想定
            # frame = self.vtuber_camera.capture_camera_frame()
            # frame = self.vtuber_camera.get_frame()
            # frame = next(self.vtuber_camera.capture_camera_frame())
            frame = next(self.vtuber_camera.get_frame())
            # frame = next(frame)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            cv2.imshow("Frame", frame)
            cv2.waitKey(1)

            frame_RGBA = process_transparentize_green_back(frame_rgb)

            streaming_clip = ImageClip(frame_RGBA).set_duration(1/24)  # 24fpsを想定
            self.streaming_clips.append(streaming_clip)


    # 各音声ファイルを順番にフィルターグラフに追加
    # 対応する解説用の画像や動画を、音声ファイルの開始から終了まで表示するようにフィルターグラフに追加  
    # バーチャルキャラクターをストリーミングで表示しながらクリップを作成する。そしてショートカットキーもその時に入力するようにする点
    async def _add_media_to_timeline(self, frame_data: FrameData):

        # 音声ファイルの再生時間を取得
        audio_clip = AudioFileClip(frame_data.audio_file).set_fps(44100)  # 44100は一般的なサンプリングレートです
        audio_duration = audio_clip.duration
        # frame_data.audio_duration = audio_duration

        # ショートカットキーの入力
        # self.hotkeys から Name がemotion_shortcut_key と motion_shortcut_key と一致するhotkeyIDを取得
        self.emotion_shortcut_keys = [hotkey['hotkeyID'] for hotkey in self.hotkeys if hotkey['name'] in frame_data.emotion_shortcut]
        self.motion_shortcut_keys = [hotkey['hotkeyID'] for hotkey in self.hotkeys if hotkey['name'] in frame_data.motion_shortcut]
        print()
        
        # ショートカットキーの入力
        if self.motion_shortcut_keys:
            print(f"motion_shortcut_keys: {self.motion_shortcut_keys}")
            selected_motion_shortcut = random.choice(self.motion_shortcut_keys)
            if selected_motion_shortcut != self.previous_motion_shortcut:
                await self.hotkey_trigger.trigger_hotkey(selected_motion_shortcut)
                self.previous_motion_shortcut = selected_motion_shortcut
                print(f"Triggering motion shortcut: {selected_motion_shortcut}")
            else:
                print(f"Skipping duplicate motion shortcut: {selected_motion_shortcut}")
            # await asyncio.sleep(0.3)  # 適宜、待機時間を調整してください

        if self.emotion_shortcut_keys:
            print(f"emotion_shortcut_keys: {self.emotion_shortcut_keys}")
            selected_emotion_shortcut = random.choice(self.emotion_shortcut_keys)
            if selected_emotion_shortcut != self.previous_emotion_shortcut:
                await self.hotkey_trigger.trigger_hotkey(selected_emotion_shortcut)
                self.previous_emotion_shortcut = selected_emotion_shortcut
                print(f"Triggering emotion shortcut: {selected_emotion_shortcut}")
            else:
                print(f"Skipping duplicate emotion shortcut: {selected_emotion_shortcut}")
            # await asyncio.sleep(0.3)  # 適宜、待機時間を調整してください

        # ストリーミング中の映像を録画  
        # streaming_thread = threading.Thread(target=self._add_streaming_video, args=(audio_duration,))
        # streaming_thread.start()
        self._add_streaming_video(audio_duration)

        preview_height, preview_width = 1080,1920 # 解像度を取得

        # 背景動画をクリップに変換
        background_video = VideoFileClip(self.background_video_path)
        video_duration = background_video.duration

        if hasattr(self, 'background_video_start_time'):
            start_time = self.background_video_start_time
        else:
            start_time = 0

        if round(start_time + audio_duration, 3) > video_duration:
            start_time = 0  # 動画の長さを超えた場合は最初から再生

        background_video_clip = background_video.subclip(start_time, start_time + audio_duration)
        self.background_video_start_time = start_time + audio_duration

        # ホワイトボード画像をクリップに変換
        whiteboard_image_clip = ImageClip(frame_data.whiteboard_image_path).set_duration(audio_duration) 

       
        # 解説画像をクリップに変換
        # 画像か動画化で分岐
        print(f"frame_data.explanation_image_path: {frame_data.explanation_image_path}")
        if frame_data.explanation_image_path.endswith(('.png', '.jpg', '.jpeg','webp')):
            explanation_clip = ImageClip(frame_data.explanation_image_path).set_duration(audio_duration) 
        else:
            # 動画の長さを小数点第3位まで取得し、それが一致していれば続きから再生
            explanation_video = VideoFileClip(frame_data.explanation_image_path)
            video_duration = round(explanation_video.duration, 3)

            if hasattr(self, 'explanation_video_start_time') and hasattr(self, 'previous_video_duration') and self.previous_video_duration == video_duration:
                start_time = self.explanation_video_start_time
            else:
                start_time = 0

            if round(start_time + audio_duration, 3) > video_duration:
                start_time = 0  # 動画の長さを超えた場合は最初から再生

            explanation_clip = explanation_video.subclip(start_time, start_time + audio_duration).set_duration(audio_duration)
            self.explanation_video_start_time = start_time + audio_duration
            self.previous_video_duration = video_duration

        # エフェクトの追加
        explanation_clip = self._add_black_frame(explanation_clip)# 黒い枠の追加
        explanation_clip = self._fade_clip(explanation_clip, audio_duration,fade_duration=0.3)# 解説画像のフェードイン・フェードアウト


        # 字幕画像をクリップに変換
        subtitle_image_clip = ImageClip(frame_data.subtitle_image_path).set_duration(audio_duration)
        # subtitle_image_clip = self._fade_clip(subtitle_image_clip, audio_duration,fade_duration=0.1)# 字幕画像のフェードイン・フェードアウト

        
        # streaming_thread.join()# ストリーミングの録画が完了するのを待つ
        streaming_video_clip = concatenate_videoclips(self.streaming_clips)# ストリーミング中の映像のクリップを結合

        # リサイズ
        # 1.background_video_clipをリサイズ
        background_video_stream = background_video_clip.resize((preview_width, preview_height))
        background_video_stream = background_video_stream.set_position((0, 0))

        # 2.streaming_video_clipをリサイズ
        # 左右から1/4ずつ切り取る
        streaming_video_clip_w_start = streaming_video_clip.w/4 -20#調整
        streaming_video_clip_w_end = streaming_video_clip.w*3/4 +20#調整
        streaming_video_clip = streaming_video_clip.crop(x1=streaming_video_clip_w_start, x2=streaming_video_clip_w_end)
        streaming_video_clip = streaming_video_clip.resize(height=preview_height*0.7)
        streaming_video_clip = streaming_video_clip.set_position(("right", "center"))

        # 3.subtitle_image_clipをリサイズ
        subtitle_image_clip = subtitle_image_clip.resize(width=preview_width)
        subtitle_image_clip = subtitle_image_clip.set_position(("center", "bottom"))

        # 4.whiteboard_image_clipをリサイズ
        # ホワイトボード画像のサイズを調整
        target_height = preview_height - subtitle_image_clip.h +160#調整
        target_width = preview_width - streaming_video_clip.w +100#調整
        new_width, new_height = self.resize_aspect_ratio(whiteboard_image_clip.w, whiteboard_image_clip.h, target_width, target_height)
        whiteboard_image_clip = whiteboard_image_clip.resize((new_width, new_height))
        # ホワイトボード画像の位置を計算
        whiteboard_position_w, whiteboard_position_h = 30, 30
        whiteboard_image_clip = whiteboard_image_clip.set_position((whiteboard_position_w, whiteboard_position_h))
        # 黒塗りの画像を作成_テスト用
        black_image = Image.new("RGB", (whiteboard_image_clip.w, whiteboard_image_clip.h), "black")
        # 一時ファイルのパスを作成 → 
        with tempfile.TemporaryFile(suffix=".png") as temp_file:
            # 現在のディレクトリに保存
            black_image.save("black_image.png")
            whiteboard_bk_image_clip = ImageClip("black_image.png").set_duration(audio_duration) 
        whiteboard_bk_image_clip = whiteboard_bk_image_clip.set_position((whiteboard_position_w, whiteboard_position_h))

        # 5.explanation_clipをリサイズ
        # 解説画像のサイズを調整
        new_width, new_height = self.resize_aspect_ratio(explanation_clip.w, explanation_clip.h, whiteboard_image_clip.w-10, whiteboard_image_clip.h-10)
        print(f"new_width: {new_width}")
        print(f"new_height: {new_height}")
        explanation_clip = explanation_clip.resize((new_width, new_height))
        # 解説画像の位置を計算
        explanation_x = (whiteboard_image_clip.w - explanation_clip.w) // 2
        explanation_y = (whiteboard_image_clip.h - explanation_clip.h) // 2
        explanation_clip = explanation_clip.set_position((explanation_x + whiteboard_position_w, explanation_y + whiteboard_position_h))
        

        # ホワイトボード画像を合成,字幕画像を合成
        composed_stream = CompositeVideoClip([
            background_video_stream,
            whiteboard_image_clip,
            # whiteboard_bk_image_clip,
            explanation_clip,
            streaming_video_clip,
            subtitle_image_clip,
        ])

        # 音声を設定
        composed_stream = composed_stream.set_audio(audio_clip)

        # フレームのクリップをリストに追加
        self.frame_clips.append(composed_stream)
        # frame_data.frame_clips.append(composed_stream)
        # print(f"frame_data.frame_clips: {composed_stream}")
        # # 座標調整用
        # subtitle_img = Image.open(frame_data.subtitle_image_path).convert("RGBA") # 字幕画像を読み込む       
        # vtuber_img = Image.open(TestData.vtuber_character_path).convert("RGBA")  # Vキャラ画像を読み込む





